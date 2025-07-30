#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

########################################
# Set up env variables for credentials #
########################################

# 1. Espera inicial de 3 segundos
echo "⏳ Esperando 6 segundos..."
sleep 6 

./credentials.sh

# Verificación del comando curl
# Si el comando anterior falló (código de salida diferente de 0), sale del script.
if [ $? -ne 0 ]; then
  echo "❌ Error: El comando curl falló."
  exit 1
fi

echo -e "\n✅ Usuario creado exitosamente."

# 4. Ejecución del script de automatización de Python
echo "🐍 Ejecutando el script de Python para crear workflows..."
python3 create_workflows.py --host="http://${URL}:5678"

if [ $? -ne 0 ]; then
  echo "❌ Error: El script de Python falló."
  exit 1
fi

echo "🎉 ¡Proceso completado!"
