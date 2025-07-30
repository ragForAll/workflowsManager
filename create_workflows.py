import requests
import json
import os
import getpass
import argparse # Módulo para parsear argumentos de la línea de comandos


parser = argparse.ArgumentParser(
    description="Despliega workflows en n8n desde archivos JSON.",
    formatter_class=argparse.RawTextHelpFormatter # Para un mejor formato en el texto de ayuda
)
parser.add_argument(
    '--host',
    type=str,

    default=os.getenv("N8N_HOST", "http://localhost:5678"),
    help='La URL de la instancia de n8n.\nEjemplo: --host="http://mi-n8n.com:1234"\nTambién se puede configurar con la variable de entorno N8N_HOST.'
)
args = parser.parse_args()


# --- Configuration ---
# Ahora N8N_HOST se toma del argumento parseado.
N8N_HOST = args.host

# Intenta obtener la API key desde una variable de entorno.
# Si no la encuentra, la deja como una cadena vacía para solicitarla después.
API_KEY = os.getenv("N8N_API_KEY", "")

# Informa al usuario qué host se está utilizando.
print(f"✅ Conectando a la instancia de n8n en: {N8N_HOST}")

# Si la API_KEY no fue definida en las variables de entorno, la solicita al usuario.
if not API_KEY:
    print("🔑 La API key de n8n no ha sido definida.")
    try:
        # Usa getpass para que la API key no sea visible al escribirla.
        API_KEY = getpass.getpass("Por favor, ingresa tu API key y presiona Enter: ").strip()
        
    except KeyboardInterrupt:
        print("\n🚫 Operación cancelada por el usuario.")
        exit() # Sale del script si el usuario presiona Ctrl+C

# Valida que el usuario realmente haya ingresado una clave.
if not API_KEY:
    print("❌ Error: La API key no puede estar vacía. El script se detendrá.")
    exit() # Sale del script si la clave está vacía.


# --- Data Storage Configuration ---
DATA_DIR = "data"
WORKFLOW_IDS_FILE = os.path.join(DATA_DIR, "workflows_ids.json")


def create_n8n_workflow_from_file(workflow_file_path: str) -> tuple[bool, str | None]:
    """
    Creates an n8n workflow from a given JSON file.

    Args:
        workflow_file_path (str): The path to the JSON file containing the workflow definition.

    Returns:
        tuple[bool, str | None]: A tuple where the first element is True if the workflow
                                 was created successfully, False otherwise. The second element
                                 is the ID of the created workflow if successful, otherwise None.
    """
    # Check if the file exists before attempting to read it
    if not os.path.exists(workflow_file_path):
        print(f"ERROR: File '{workflow_file_path}' not found. Skipping this workflow.")
        return False, None

    try:
        # Open and load the workflow JSON from the specified file
        with open(workflow_file_path, 'r', encoding='utf-8') as f:
            workflow_payload = json.load(f)
        print(f"\nLoading workflow from: '{workflow_file_path}'...")

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from file '{workflow_file_path}': {e}. Skipping this workflow.")
        return False, None
    except Exception as e:
        print(f"ERROR: Unexpected error reading file '{workflow_file_path}': {e}. Skipping this workflow.")
        return False, None

    # --- Request Headers ---
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-N8N-API-KEY": API_KEY
    }

    # --- API Endpoint URL ---
    url = f"{N8N_HOST}/api/v1/workflows"

    # Get workflow name for logging, defaulting if not found
    workflow_name = workflow_payload.get('name', 'Unknown Name')
    print(f"Attempting to create workflow at {url} with name: '{workflow_name}'...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(workflow_payload))
        # Raise an exception for HTTP 4xx/5xx status codes
        response.raise_for_status()

        response_data = response.json()
        created_workflow_name = response_data.get('name', 'N/A')
        created_workflow_id = response_data.get('id', 'N/A')
        print(f"Workflow '{created_workflow_name}' (ID: {created_workflow_id}) created successfully.")
        return True, created_workflow_id

    except requests.exceptions.HTTPError as err:
        print(f"ERROR HTTP when creating workflow from '{workflow_file_path}': {err}")
        print(f"Response body: {response.text}")
        return False, None
    except requests.exceptions.ConnectionError as err:
        print(f"ERROR: Connection error. Ensure n8n is running and accessible at {N8N_HOST}. Error: {err}")
        return False, None
    except requests.exceptions.Timeout as err:
        print(f"ERROR: Request timed out when connecting to n8n. Error: {err}")
        return False, None
    except requests.exceptions.RequestException as err:
        print(f"ERROR: An unexpected request error occurred for '{workflow_file_path}': {err}")
        return False, None
    except Exception as err:
        print(f"ERROR: A general error occurred while processing '{workflow_file_path}': {err}")
        return False, None

def deploy_n8n_workflows(workflow_files: list[str]):
    """
    Deploys multiple n8n workflows from a list of JSON file paths and saves their IDs.

    Args:
        workflow_files (list[str]): A list of paths to the JSON workflow definition files.
    """
    if not workflow_files:
        print("No workflow files provided for deployment.")
        return

    print(f"Starting deployment of {len(workflow_files)} workflow(s) to n8n...")
    successful_deploys = 0
    deployed_workflow_ids = [] # List to store IDs of successfully created workflows
    total_files = len(workflow_files)

    for i, file_path in enumerate(workflow_files):
        print(f"\n--- Processing file {i+1}/{total_files}: {file_path} ---")
        success, workflow_id = create_n8n_workflow_from_file(file_path)
        if success:
            successful_deploys += 1
            if workflow_id: # Only add if a valid ID was returned
                deployed_workflow_ids.append(workflow_id)
        print(f"--- Finished processing {file_path} ---")

    print(f"\n--- Deployment Summary ---")
    print(f"Total files attempted: {total_files}")
    print(f"Workflows created successfully: {successful_deploys}")
    print(f"Workflows failed: {total_files - successful_deploys}")

    # Save the deployed workflow IDs to a JSON file
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created directory: {DATA_DIR}")

    try:
        with open(WORKFLOW_IDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(deployed_workflow_ids, f, indent=2)
        print(f"Successfully saved deployed workflow IDs to: {WORKFLOW_IDS_FILE}")
    except Exception as e:
        print(f"ERROR: Failed to save workflow IDs to {WORKFLOW_IDS_FILE}: {e}")

# --- Example Usage ---
if __name__ == "__main__":

    workflow_json_files = [ 
        "json_workflows/vectorial.json"
    ]

    # Call the main deployment function
    deploy_n8n_workflows(workflow_json_files)