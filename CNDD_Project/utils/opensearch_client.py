"""
Cliente para conectar con AWS OpenSearch
"""

import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection

# Cargar variables de entorno
load_dotenv()


class OpenSearchClient:
    """Cliente para interactuar con OpenSearch."""
    
    def __init__(self):
        """Inicializar cliente de OpenSearch."""
        self.endpoint = os.getenv('OPENSEARCH_ENDPOINT')
        self.region = os.getenv('AWS_REGION')
        self.index_name = os.getenv('OPENSEARCH_INDEX_NAME', 'cloudtrail-logs')
        
        # Master user credentials
        self.master_user = os.getenv('OPENSEARCH_MASTER_USER', 'admin')
        self.master_password = os.getenv('OPENSEARCH_MASTER_PASSWORD')
        
        # Verificar configuración
        if not self.endpoint:
            raise ValueError("OPENSEARCH_ENDPOINT no está configurado en .env")
        
        if not self.master_password:
            raise ValueError("OPENSEARCH_MASTER_PASSWORD no está configurado en .env")
        
        # DEBUG: Mostrar las credenciales (quitar después de probar)
        print(f"DEBUG - Endpoint: {self.endpoint}")
        print(f"DEBUG - Master User: {self.master_user}")
        print(f"DEBUG - Password length: {len(self.master_password)} caracteres")
        if self.master_password:
            print(f"DEBUG - Password starts with: {self.master_password[:3]}...")
        
        # Cliente OpenSearch con autenticación básica (master user)
        try:
            self.client = OpenSearch(
                hosts=[{'host': self.endpoint, 'port': 443}],
                http_auth=(self.master_user, self.master_password),
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=30
            )
            
            # Verificar conexión
            info = self.client.info()
            print(f"✅ Conectado a OpenSearch: {info['version']['number']}")
            
        except Exception as e:
            raise ValueError(f"Error conectando a OpenSearch: {str(e)}")
    
    def search_logs(self, query: str = "*", size: int = 100, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Buscar logs en OpenSearch.
        
        Args:
            query: Término de búsqueda
            size: Cantidad de resultados
            start_date: Fecha inicio (formato: YYYY-MM-DD)
            end_date: Fecha fin (formato: YYYY-MM-DD)
            
        Returns:
            Tuple (éxito, lista_logs, mensaje_error)
        """
        try:
            # Construir query
            search_query = {
                "size": size,
                #"sort": [{"event_id": {"order": "desc"}}],
                "query": {
                    "bool": {
                        "must": []
                    }
                }
            }
            
            # Agregar búsqueda de texto
            if query and query != "*":
                search_query["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "event_name", 
                            "user_arn",
                            "source_ip",
                            "event_source"
                        ]
                    }
                })
            else:
                search_query["query"]["bool"]["must"].append({"match_all": {}})
            
            # Agregar filtro de fechas
            if start_date or end_date:
                date_filter = {"range": {"timestamp": {}}}
            if start_date:
                date_filter["range"]["timestamp"]["gte"] = start_date
            if end_date:
                date_filter["range"]["timestamp"]["lte"] = end_date
            
            # Ejecutar búsqueda
            response = self.client.search(
                index=self.index_name,
                body=search_query
            )
            
            # Procesar resultados
            logs = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                
                # Extraer datos del log (estructura real de tu CloudTrail)
                # Determinar el usuario
                user = 'N/A'
                if source.get('user_arn'):
                    # Extraer nombre del ARN (última parte después de /)
                    user_arn = source.get('user_arn')
                    if '/' in user_arn:
                        user = user_arn.split('/')[-1]
                    else:
                        user = source.get('user_type', 'N/A')
                else:
                    user = source.get('user_identity', 'N/A')

                # Extraer recurso (ARN completo)
                resource = 'N/A'
                if source.get('resources') and len(source.get('resources')) > 0:
                    resource = source['resources'][0].get('ARN', 'N/A')

                log_entry = {
                    'timestamp': source.get('timestamp', 'N/A'),
                    'event_name': source.get('event_name', 'N/A'),
                    'user': user,
                    'source_ip': source.get('source_ip', 'N/A'),
                    'resource': resource,
                    'event_type': source.get('event_type', 'N/A'),
                    'event_source': source.get('event_source', 'N/A'),
                }
                logs.append(log_entry)
            
            return True, logs, None
            
        except Exception as e:
            error_msg = f"Error buscando logs: {str(e)}"
            print(error_msg)
            return False, [], error_msg
    
    def get_recent_logs(self, limit: int = 50) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Obtener los logs más recientes.
        
        Args:
            limit: Cantidad de logs a obtener
            
        Returns:
            Tuple (éxito, lista_logs, mensaje_error)
        """
        return self.search_logs(query="*", size=limit)
    
    def search_by_user(self, username: str, limit: int = 50) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Buscar logs de un usuario específico.
        
        Args:
            username: Nombre del usuario
            limit: Cantidad de logs
            
        Returns:
            Tuple (éxito, lista_logs, mensaje_error)
        """
        return self.search_logs(query=username, size=limit)
    
    def get_event_stats(self) -> Tuple[bool, Dict, Optional[str]]:
        """
        Obtener estadísticas de eventos usando agregaciones.
        
        Returns:
            Tuple (éxito, estadísticas, mensaje_error)
        """
        try:
            # Query de agregación
            agg_query = {
                "size": 0,
                "aggs": {
                    "events_by_name": {
                        "terms": {
                            "field": "event_name.keyword",
                            "size": 10
                        }
                    },
                    "events_by_source": {
                        "terms": {
                            "field": "event_source.keyword",
                            "size": 10
                        }
                    },
                    "events_by_type": {
                        "terms": {
                            "field": "event_type.keyword",
                            "size": 10
                        }
                    }
                }
            }
            
            response = self.client.search(
                index=self.index_name,
                body=agg_query
            )
            
            # Procesar agregaciones
            stats = {
                'total_events': response['hits']['total']['value'],
                'top_events': [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in response['aggregations']['events_by_name']['buckets']
                ],
                'top_users': [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in response['aggregations']['events_by_user']['buckets']
                ],
                'top_sources': [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in response['aggregations']['events_by_source']['buckets']
                ]
            }
            
            return True, stats, None
            
        except Exception as e:
            error_msg = f"Error obteniendo estadísticas: {str(e)}"
            print(error_msg)
            return False, {}, error_msg
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Probar conexión a OpenSearch.
        
        Returns:
            Tuple (éxito, mensaje)
        """
        try:
            info = self.client.info()
            return True, f"Conexión exitosa. OpenSearch {info['version']['number']}"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"