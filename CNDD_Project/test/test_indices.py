from CNDD_Project.utils.opensearch_client import OpenSearchClient

try:
    client = OpenSearchClient()
    
    # Listar todos los índices
    indices = client.client.cat.indices(format='json')
    
    print("\n📋 Índices disponibles en OpenSearch:")
    for index in indices:
        print(f"  - {index['index']} ({index['docs.count']} documentos)")
    
    # Verificar si existe cloudtrail-logs
    if any(idx['index'] == 'cloudtrail-logs' for idx in indices):
        print("\n✅ El índice 'cloudtrail-logs' existe")
        
        # Ver el mapping del índice
        mapping = client.client.indices.get_mapping(index='cloudtrail-logs')
        print("\n📄 Campos disponibles:")
        properties = mapping['cloudtrail-logs']['mappings'].get('properties', {})
        for field in list(properties.keys())[:10]:  # Mostrar solo los primeros 10
            print(f"  - {field}")
    else:
        print("\n❌ El índice 'cloudtrail-logs' NO existe")
        print("\nÍndices que parecen relacionados con CloudTrail:")
        for index in indices:
            if 'cloud' in index['index'].lower() or 'trail' in index['index'].lower() or 'log' in index['index'].lower():
                print(f"  → {index['index']}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")