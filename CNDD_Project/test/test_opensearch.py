import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
env_path = Path(__file__).parent / '.env'
print(f"Buscando .env en: {env_path}")
print(f"¿Existe el archivo? {env_path.exists()}")

load_dotenv(env_path)

# Verificar que se cargó
endpoint = os.getenv('OPENSEARCH_ENDPOINT')
print(f"OPENSEARCH_ENDPOINT cargado: {endpoint}")

if not endpoint:
    print("\n❌ ERROR: No se pudo cargar OPENSEARCH_ENDPOINT")
    print("Verifica que el archivo .env existe y tiene la variable configurada.")
else:
    print("\n✅ Variable cargada correctamente. Probando conexión...")
    
    try:
        from CNDD_Project.utils.opensearch_client import OpenSearchClient
        
        client = OpenSearchClient()
        
        success, message = client.test_connection()
        if success:
            print(f"✅ {message}")
            
            # Probar búsqueda de logs
            print("\nBuscando logs recientes...")
            success, logs, error = client.get_recent_logs(limit=5)
            
            if success:
                print(f"✅ Se encontraron {len(logs)} logs")
                for log in logs:
                    print(f"  - {log['timestamp']}: {log['event_name']} por {log['user']}")
            else:
                print(f"❌ Error buscando logs: {error}")
        else:
            print(f"❌ {message}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")