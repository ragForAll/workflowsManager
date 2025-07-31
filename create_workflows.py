import requests
import json
import os
import getpass
import argparse

# --- Get Script's Own Directory ---
# This ensures paths are relative to the script's actual location, not the CWD.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Deploys n8n workflows from JSON files.",
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '--host',
    type=str,
    default=os.getenv("N8N_HOST", "http://localhost:5678"),
    help='The URL of the n8n instance.\nExample: --host="http://my-n8n.com:1234"\nCan also be set via the N8N_HOST environment variable.'
)
args = parser.parse_args()


# --- Configuration ---
N8N_HOST = args.host
API_KEY = os.getenv("N8N_API_KEY", "")

print(f"✅ Connecting to n8n instance at: {N8N_HOST}")

if not API_KEY:
    print("🔑 n8n API key not defined.")
    try:
        API_KEY = getpass.getpass("Please enter your API key and press Enter: ").strip()
    except KeyboardInterrupt:
        print("\n🚫 Operation cancelled by user.")
        exit()

if not API_KEY:
    print("❌ Error: API key cannot be empty. Script will stop.")
    exit()


# --- Data Storage Configuration ---
# Construct DATA_DIR relative to SCRIPT_DIR
# From workflowsManager/ (SCRIPT_DIR), go up one (..) to ragForAll/, then into jsons/
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'jsons')
WORKFLOW_IDS_FILE = os.path.join(DATA_DIR, "workflows_ids.json")

# Ensure DATA_DIR exists for saving output
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"Created directory: {DATA_DIR}")


def create_n8n_workflow_from_file(workflow_file_path: str) -> tuple[bool, str | None]:
    """
    Creates an n8n workflow from a given JSON file.

    Args:
        workflow_file_path (str): Path to the JSON file with the workflow definition.

    Returns:
        tuple[bool, str | None]: True/False for success, and the workflow ID if successful.
    """
    if not os.path.exists(workflow_file_path):
        print(f"ERROR: File '{workflow_file_path}' not found. Skipping.")
        return False, None

    try:
        with open(workflow_file_path, 'r', encoding='utf-8') as f:
            workflow_payload = json.load(f)
        print(f"\nLoading workflow from: '{workflow_file_path}'...")
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from '{workflow_file_path}': {e}. Skipping.")
        return False, None
    except Exception as e:
        print(f"ERROR: Unexpected error reading '{workflow_file_path}': {e}. Skipping.")
        return False, None

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-N8N-API-KEY": API_KEY
    }
    url = f"{N8N_HOST}/api/v1/workflows"

    workflow_name = workflow_payload.get('name', 'Unknown Name')
    print(f"Attempting to create workflow '{workflow_name}' at {url}...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(workflow_payload))
        response.raise_for_status()

        response_data = response.json()
        created_workflow_name = response_data.get('name', 'N/A')
        created_workflow_id = response_data.get('id', 'N/A')
        print(f"Workflow '{created_workflow_name}' (ID: {created_workflow_id}) created successfully.")
        return True, created_workflow_id

    except requests.exceptions.RequestException as err:
        print(f"ERROR: Request failed for '{workflow_file_path}': {err}")
        if hasattr(err, 'response') and err.response is not None:
            print(f"Response body: {err.response.text}")
        return False, None
    except Exception as err:
        print(f"ERROR: A general error occurred while processing '{workflow_file_path}': {err}")
        return False, None


def deploy_n8n_workflows(workflow_files: list[str]):
    """
    Deploys multiple n8n workflows from a list of JSON file paths and saves their IDs.

    Args:
        workflow_files (list[str]): List of paths to JSON workflow definition files.
    """
    if not workflow_files:
        print("No workflow files provided for deployment.")
        return

    print(f"Starting deployment of {len(workflow_files)} workflow(s) to n8n...")
    successful_deploys = 0
    deployed_workflow_ids = []
    total_files = len(workflow_files)

    for i, file_path in enumerate(workflow_files):
        print(f"\n--- Processing file {i+1}/{total_files}: {file_path} ---")
        success, workflow_id = create_n8n_workflow_from_file(file_path)
        if success:
            successful_deploys += 1
            if workflow_id:
                deployed_workflow_ids.append(workflow_id)
        print(f"--- Finished processing {file_path} ---")

    print(f"\n--- Deployment Summary ---")
    print(f"Total files attempted: {total_files}")
    print(f"Workflows created successfully: {successful_deploys}")
    print(f"Workflows failed: {total_files - successful_deploys}")

    # No need to check/create DATA_DIR here, it's done at the top level
    try:
        with open(WORKFLOW_IDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(deployed_workflow_ids, f, indent=2)
        print(f"Successfully saved deployed workflow IDs to: {WORKFLOW_IDS_FILE}")
    except Exception as e:
        print(f"ERROR: Failed to save workflow IDs to {WORKFLOW_IDS_FILE}: {e}")

# --- Example Usage ---
if __name__ == "__main__":
    # Now, paths are relative to create_workflows.py's own location (SCRIPT_DIR)
    # create_workflows.py is in /mnt/tera/ragForAll/workflowsManager/
    # JSONs are in /mnt/tera/ragForAll/jsons/
    # To get there from SCRIPT_DIR, go up one (..) and then into 'jsons'
    workflow_json_files = [
        os.path.join(SCRIPT_DIR, '..', 'jsons', 'vectorial.json'),
        os.path.join(SCRIPT_DIR, '..', 'jsons', 'chat.json')
    ]

    deploy_n8n_workflows(workflow_json_files)