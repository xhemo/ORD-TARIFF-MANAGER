import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict, Optional, Any
import json
import datetime
import os
import copy

from .utils import get_resource_path

class TariffEngine:
    def __init__(self):
        self.tree = None
        self.root = None
        self.current_file_path = None
        self.namespace = None
        # Use utils to get path
        self.definitions_folder = get_resource_path("TariffDefinitions")
        self.parameter_template = None # XML Element to use as template for new rows

    def get_available_definitions(self) -> List[str]:
        """Returns a list of available JSON definition files."""
        if not os.path.exists(self.definitions_folder):
            return []
        return [f for f in os.listdir(self.definitions_folder) if f.endswith('.json')]

    def create_from_definition(self, definition_filename: str) -> Dict:
        """
        Creates a new in-memory XML and DataFrame based on a JSON definition.
        """
        def_path = os.path.join(self.definitions_folder, definition_filename)
        with open(def_path, 'r', encoding='utf-8') as f:
            definition = json.load(f)

        # 1. Create Basic XML Structure
        # Root <comtec>
        self.root = ET.Element("comtec", version="2014")
        self.tree = ET.ElementTree(self.root)
        
        # <resource_tariff>
        res_tariff = ET.SubElement(self.root, "resource_tariff")
        
        # Default Metadata
        today = datetime.date.today().isoformat()
        future = (datetime.date.today() + datetime.timedelta(days=365*5)).isoformat()
        
        ET.SubElement(res_tariff, "id").text = "NEW_TARIFF"
        ET.SubElement(res_tariff, "code").text = "NEW_TARIFF"
        ET.SubElement(res_tariff, "name").text = "New Tariff"
        ET.SubElement(res_tariff, "valid_from_date").text = today
        ET.SubElement(res_tariff, "valid_till_date").text = future
        ET.SubElement(res_tariff, "price_kind_code").text = "Erlös"
        
        tariff_items = ET.SubElement(res_tariff, "tariff_items")
        tariff_item = ET.SubElement(tariff_items, "tariff_item")
        
        ET.SubElement(tariff_item, "name").text = "New Tariff"
        ET.SubElement(tariff_item, "tariff_item_spec").text = definition.get("spec_name", "UnknownSpec")
        ET.SubElement(tariff_item, "currency_code").text = definition.get("currency_code", "EUR")
        ET.SubElement(tariff_item, "valid_from_date").text = today
        ET.SubElement(tariff_item, "valid_till_date").text = future
        ET.SubElement(tariff_item, "unit_code").text = definition.get("unit_code", "XXX")
        
        # Prepare Parameter Tuples Container with explicit structure
        tuples_container = ET.SubElement(tariff_item, "parameter_tuples")
        
        # Create a "seed" tuple so that update_tuples has a template to work with
        seed_tuple = ET.SubElement(tuples_container, "parameter_tuple")
        columns = definition.get("columns", [])
        defaults = definition.get("defaults", {})
        
        for col in columns:
            param = ET.SubElement(seed_tuple, "parameter")
            ET.SubElement(param, "code").text = col
            val = defaults.get(col, 0.00)
            if isinstance(val, (int, float)):
                 ET.SubElement(param, "value").text = f"{val:.2f}"
            else:
                 ET.SubElement(param, "value").text = str(val)

        # 2. Create Initial DataFrame (Empty)
        # We store the seed as template, then clear local XML so update_tuples can manage it?
        # Actually create_from_definition sets up 'seed_tuple' in XML.
        # We should capture it as template.
        self.parameter_template = copy.deepcopy(seed_tuple)
        
        # Return EMPTY DataFrame
        df = pd.DataFrame(columns=columns)
        
        # Ensure we construct the XML parameter_tuple structure correctly immediately
        self.update_tuples(df)
        
        return {'schema': columns, 'data': df}


    def load_template(self, file_path: str):
        """Loads an XML template and parses it."""
        try:
            self.current_file_path = file_path
            self.tree = ET.parse(file_path)
            self.root = self.tree.getroot()
            
            # Detect namespace if present (often comtec xmls have attributes but no explicit xmlns, 
            # but sometimes they might. For this specific file structure, standard parsing seems fine
            # as seen in the view_file output, it's just <comtec version="2014"> without xmlns)
            
            # Capture template if possible
            tuples_container = self.root.find('.//tariff_item/parameter_tuples')
            if tuples_container is not None:
                first = tuples_container.find('parameter_tuple')
                if first is not None:
                    self.parameter_template = copy.deepcopy(first)

            return True, "Template loaded successfully."
        except Exception as e:
            return False, f"Error loading template: {str(e)}"

    def get_metadata(self) -> Dict[str, str]:
        """Extracts high-level metadata like ID, Name, Validity."""
        if not self.root:
            return {}
        
        # Adjust paths based on the viewed XML structure
        # Structure: root -> resource_tariff -> id, name, valid_from_date, etc.
        res_tariff = self.root.find('resource_tariff')
        if res_tariff is None:
            return {}

        data = {
            'id': res_tariff.findtext('id', ''),
            'name': res_tariff.findtext('name', ''),
            'valid_from': res_tariff.findtext('valid_from_date', ''),
            'valid_to': res_tariff.findtext('valid_till_date', ''),
            'spec': self.root.findtext('.//tariff_item/tariff_item_spec', '')
        }
        return data

    def extract_tuples_check_schema(self) -> Dict:
        """
        Parses the first tuple to determine the schema (columns).
        Returns a dictionary with 'schema' (list of columns) and 'data' (list of dicts).
        """
        if not self.root:
            return {'schema': [], 'data': []}

        # Navigate to parameter tuples
        # root -> resource_tariff -> tariff_items -> tariff_item -> parameter_tuples
        tuples_container = self.root.find('.//tariff_item/parameter_tuples')
        if tuples_container is None:
            return {'schema': [], 'data': []}

        all_tuples = tuples_container.findall('parameter_tuple')
        
        # If no tuples in XML, but we have a template, use template for schema
        if not all_tuples:
            if self.parameter_template is not None:
                schema = []
                for param in self.parameter_template.findall('parameter'):
                    code = param.findtext('code')
                    if code: schema.append(code)
                return {'schema': schema, 'data': []}
            return {'schema': [], 'data': []}

        # 1. Infer Schema from the first tuple
        first_tuple = all_tuples[0]
        schema = []
        for param in first_tuple.findall('parameter'):
            code = param.findtext('code')
            if code:
                schema.append(code)

        # 2. Extract Data
        data_rows = []
        for t_idx, t in enumerate(all_tuples):
            row = {} # Removed _index
            for param in t.findall('parameter'):
                code = param.findtext('code')
                val = param.findtext('value')
                if code in schema:
                    # Try converting to float for numerical processing
                    try:
                        row[code] = float(val)
                    except (ValueError, TypeError):
                        row[code] = val
            data_rows.append(row)

        return {'schema': schema, 'data': data_rows}

    def update_metadata(self, new_data: Dict[str, str]):
        """Updates valid_from, valid_to, name in the XML tree."""
        if not self.root:
            return

        res_tariff = self.root.find('resource_tariff')
        if res_tariff is None:
            return

        if 'name' in new_data:
            elem = res_tariff.find('name')
            if elem is not None: elem.text = new_data['name']
            # Also update tariff_item name if it matches
            item_name = self.root.find('.//tariff_item/name')
            if item_name is not None: item_name.text = new_data['name']

        if 'valid_from' in new_data:
            elem = res_tariff.find('valid_from_date')
            if elem is not None: elem.text = new_data['valid_from']
            item_elem = self.root.find('.//tariff_item/valid_from_date')
            if item_elem is not None: item_elem.text = new_data['valid_from']

        if 'valid_to' in new_data:
            elem = res_tariff.find('valid_till_date')
            if elem is not None: elem.text = new_data['valid_to']
            item_elem = self.root.find('.//tariff_item/valid_till_date')
            if item_elem is not None: item_elem.text = new_data['valid_to']

        if 'id' in new_data:
            elem = res_tariff.find('id')
            if elem is not None: elem.text = new_data['id']
            # Assuming code often matches ID
            code_elem = res_tariff.find('code')
            if code_elem is not None: code_elem.text = new_data['id']

    def update_tuples(self, df: pd.DataFrame):
        """
        Reconstructs the parameter_tuples list in the XML tree from the DataFrame.
        This ensures that added/removed rows are reflected in the output.
        """
        if not self.root:
            return

        tuples_container = self.root.find('.//tariff_item/parameter_tuples')
        if tuples_container is None:
            return

        all_tuples = tuples_container.findall('parameter_tuple')
        if not all_tuples and not self.parameter_template:
            # If there were no tuples originally AND no template, we can't guess structure
            return

        # 1. Start with template
        if self.parameter_template:
            template_tuple = self.parameter_template
        elif all_tuples:
            template_tuple = copy.deepcopy(all_tuples[0])
            self.parameter_template = template_tuple # cache it
        else:
            return
        
        # 2. Clear existing tuples from the XML container
        # Note: 'remove' only removes direct children. We need to iterate and remove.
        # list(tuples_container) gets all children.
        for child in list(tuples_container):
            tuples_container.remove(child)

        # 3. Rebuild based on DataFrame
        for _, row in df.iterrows():
            # Create a new tuple from template
            new_tuple = copy.deepcopy(template_tuple)
            
            # Update its values
            for param in new_tuple.findall('parameter'):
                code = param.findtext('code')
                val_elem = param.find('value')
                
                if code in row and val_elem is not None:
                    new_val = row[code]
                    if isinstance(new_val, (int, float)):
                        # Special handling for IDs or clean integers
                        if code.startswith('id_'):
                            val_elem.text = str(int(new_val))
                        elif isinstance(new_val, float) and new_val.is_integer() and 'price' not in code.lower():
                             # Optional: also strip .00 for other non-price integer-like floats if desired
                             # But user specifically mentioned IDs. Let's stick to IDs being strict ints.
                             # Actually, let's just properly format based on value if it's not a price/rate might be risky.
                             # Safer: Explicit checks for known int columns? Or just id_ prefix.
                             # Let's trust id_ prefix for now as it's standard here.
                             val_elem.text = f"{new_val:.2f}"
                        else:
                            val_elem.text = f"{new_val:.2f}"
                    else:
                        val_elem.text = str(new_val)
            
            # Append to container
            tuples_container.append(new_tuple)

    def save_to_file(self, output_path: str):
        """Saves the modified tree to a new XML file with pretty printing."""
        if self.root:
            # Use minidom to pretty print
            import xml.dom.minidom
            xml_str = ET.tostring(self.root, encoding='utf-8')
            parsed = xml.dom.minidom.parseString(xml_str)
            pretty_xml = parsed.toprettyxml(indent="  ")
            
            # Remove extra newlines sometimes caused by toprettyxml on text nodes
            # A simple way is to filter empty lines if they are problematic, 
            # but usually standard pretty print is enough.
            # However, minidom adds declaration <?xml ... ?> automatically.
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(pretty_xml)

    def apply_bulk_change(self, df: pd.DataFrame, column: str, percentage: float, rows: List[int] = None) -> pd.DataFrame:
        """Applies a percentage change to a column in the DataFrame, optionally only on specific rows."""
        if column in df.columns:
            # Only apply if column is numeric
            if pd.api.types.is_numeric_dtype(df[column]):
                multiplier = (1 + percentage / 100)
                if rows is not None and len(rows) > 0:
                    # Apply only to specific rows
                    # Use df.loc[rows, column] to update specific cells
                    # Ensure rows are valid indices
                    valid_rows = [r for r in rows if r in df.index]
                    if valid_rows:
                        df.loc[valid_rows, column] = df.loc[valid_rows, column] * multiplier
                else:
                    # Apply to all
                    df[column] = df[column] * multiplier
        return df

    def get_current_schema(self) -> List[str]:
        """Returns the list of columns for the current tariff."""
        res = self.extract_tuples_check_schema()
        return res.get('schema', [])

    def get_parameter_defaults(self) -> Dict[str, Any]:
        """Returns default values from the current parameter template."""
        defaults = {}
        if self.parameter_template:
            for param in self.parameter_template.findall('parameter'):
                code = param.findtext('code')
                val_text = param.findtext('value')
                if code:
                    # Try converting to number
                    try:
                        defaults[code] = float(val_text)
                    except (ValueError, TypeError):
                        defaults[code] = val_text if val_text else ""
        return defaults
    def set_order_kind(self, df: pd.DataFrame, order_kind_value: int):
        """Sets the id_orderkind for all rows."""
        if 'id_orderkind' in df.columns:
             df['id_orderkind'] = order_kind_value
        return df

    def save_definition(self, data: Dict, filename: str) -> str:
        """Saves a new tariff definition JSON file."""
        if not filename.endswith('.json'):
            filename += '.json'
        
        path = os.path.join(self.definitions_folder, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return path


