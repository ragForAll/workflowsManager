import requests
import json
import os

# --- Configuration ---
# Ensure this is the correct URL and port for your n8n instance
N8N_HOST = "http://localhost:5678"
# API key for n8n from environment variables.

API_KEY = os.getenv("N8N_API_KEY")

# --- Data Storage Configuration ---
DATA_DIR = "data"
WORKFLOW_IDS_FILE = os.path.join(DATA_DIR, "workflows_ids.json")

def activate_n8n_workflow(workflow_id: str) -> bool:
    """
    Activates a specific n8n workflow by its ID.

    Args:
        workflow_id (str): The ID of the workflow to activate.

    Returns:
        bool: True if the workflow was activated successfully, False otherwise.
    """
    # --- Request Headers ---
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json", # Even for POST without body, it's good practice
        "X-N8N-API-KEY": API_KEY
    }

    # --- API Endpoint URL ---
    url = f"{N8N_HOST}/api/v1/workflows/{workflow_id}/activate"

    print(f"Attempting to activate workflow with ID: '{workflow_id}' at {url}...")
    try:
        response = requests.post(url, headers=headers)
        # Raise an exception for HTTP 4xx/5xx status codes
        response.raise_for_status()

        print(f"Workflow ID '{workflow_id}' activated successfully.")
        return True

    except requests.exceptions.HTTPError as err:
        # Specific handling for common activation errors
        if response.status_code == 404:
            print(f"ERROR: Workflow with ID '{workflow_id}' not found (404). It might have been deleted or the ID is incorrect. Error: {err}")
        elif response.status_code == 400:
            print(f"ERROR: Bad Request for workflow ID '{workflow_id}'. It might already be active or there's another issue (e.g., validation failure if n8n returns details). Response: {response.text}. Error: {err}")
        else:
            print(f"ERROR HTTP when activating workflow ID '{workflow_id}': {err}")
            print(f"Response body: {response.text}")
        return False
    except requests.exceptions.ConnectionError as err:
        print(f"ERROR: Connection error. Ensure n8n is running and accessible at {N8N_HOST}. Error: {err}")
        return False
    except requests.exceptions.Timeout as err:
        print(f"ERROR: Request timed out when connecting to n8n. Error: {err}")
        return False
    except requests.exceptions.RequestException as err:
        print(f"ERROR: An unexpected request error occurred for workflow ID '{workflow_id}': {err}")
        return False
    except Exception as err:
        print(f"ERROR: A general error occurred while activating workflow ID '{workflow_id}': {err}")
        return False

def main():
    """
    Main function to read workflow IDs from 'data/workflows_ids.json' and activate them in n8n.
    """
    # Check if the file containing workflow IDs exists
    if not os.path.exists(WORKFLOW_IDS_FILE):
        print(f"ERROR: Workflow IDs file not found: '{WORKFLOW_IDS_FILE}'.")
        print("Please ensure you have run 'deploy_workflows.py' first to create and save the workflow IDs.")
        return

    # Load workflow IDs from the JSON file
    try:
        with open(WORKFLOW_IDS_FILE, 'r', encoding='utf-8') as f:
            workflow_ids = json.load(f)
        print(f"Successfully loaded workflow IDs from: '{WORKFLOW_IDS_FILE}'.")
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from '{WORKFLOW_IDS_FILE}': {e}.")
        print("Ensure the file contains a valid JSON array of workflow IDs.")
        return
    except Exception as e:
        print(f"ERROR: Unexpected error reading '{WORKFLOW_IDS_FILE}': {e}.")
        return

    # Check if any IDs were loaded
    if not workflow_ids:
        print("No workflow IDs found in the file to activate.")
        return

    print(f"\nStarting activation of {len(workflow_ids)} workflow(s) in n8n...")
    successful_activations = 0
    total_ids = len(workflow_ids)

    # Iterate through each workflow ID and attempt to activate it
    for i, workflow_id in enumerate(workflow_ids):
        print(f"\n--- Processing workflow {i+1}/{total_ids} (ID: {workflow_id}) ---")
        if activate_n8n_workflow(workflow_id):
            successful_activations += 1
        print(f"--- Finished processing workflow {workflow_id} ---")

    print(f"\n--- Activation Summary ---")
    print(f"Total workflows attempted: {total_ids}")
    print(f"Workflows activated successfully: {successful_activations}")
    print(f"Workflows failed to activate: {total_ids - successful_activations}")

if __name__ == "__main__":
    main()