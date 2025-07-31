#!/bin/bash

# Exit immediately if any command fails.
set -e

# --- Determine Script Directory ---
# SCRIPT_DIR is the directory where this script is located.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- Main Script Logic ---

echo "🔄 Starting workflow automation process..."

# 1. Validate the 'IP' environment variable
# This variable is crucial for the Python script's --host argument.
if [ -z "$IP" ]; then
    echo "❌ Error: The 'IP' environment variable is not set or is empty."
    echo "Please ensure the VM IP has been extracted and exported (e.g., by sourcing 'get_vm_ip.sh')."
    exit 1
fi
echo "✅ IP variable confirmed: IP=${IP}"


# 3. Execute credentials setup script
# Using the full path to credentials.sh relative to the script's directory.
echo "🔐 Running credentials setup..."
$SCRIPT_DIR/credentials.sh

# Check if the previous command failed.
if [ $? -ne 0 ]; then
  echo "❌ Error: The 'credentials.sh' script failed."
  exit 1
fi

echo -e "\n✅ User created successfully."

# 4. Execute the Python automation script
# Using the full path to create_workflows.py relative to the script's directory.
echo "🐍 Executing Python script to create workflows..."
python3 "$SCRIPT_DIR/../create_workflows.py" --host="http://${IP}:5678"

# Check if the Python script failed.
if [ $? -ne 0 ]; then
  echo "❌ Error: The Python script 'create_workflows.py' failed."
  exit 1
fi

echo "🎉 Process completed successfully!"