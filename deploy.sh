#!/bin/bash

# Simple Deployment Script for ORD Tariff Manager

echo "Preparing to upload changes to GitHub..."

# 1. Add all changes
git add .

# 2. Ask for a commit message (optional, defaults to "Update")
echo "Enter a description for this update (Press Enter for default 'Update'):"
read input_msg
msg="${input_msg:-Update}"

# 3. Commit
git commit -m "$msg"

# 4. Push
echo "Uploading to GitHub..."
git push

echo "---------------------------------------------------"
echo "Done! check your GitHub Actions for the new build."
echo "https://github.com/xhemo/ORD-TARIFF-MANAGER/actions"
echo "---------------------------------------------------"
