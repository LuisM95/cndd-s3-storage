from CNDD_Project.utils.opensearch_client import OpenSearchClient

try:
    client = OpenSearchClient()
    
    # Obtener UN log para ver su estructura
    response = client.client.search(
        index='cloudtrail-logs',
        body={
            "size": 1,
            "query": {"match_all": {}}
        }
    )
    
    if response['hits']['hits']:
        log = response['hits']['hits'][0]['_source']
        
        print("\n📄 Estructura de un log de CloudTrail:\n")
        import json
        print(json.dumps(log, indent=2))
    
except Exception as e:
    print(f"❌ Error: {str(e)}")