"""
Gestor de operaciones con AWS S3
"""

import os
import boto3
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Cargar variables de entorno
load_dotenv()


class S3Manager:
    """Clase para gestionar operaciones con S3."""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Inicializar cliente de S3.
        
        Args:
            access_token: Token de acceso de Cognito (para credenciales temporales)
        """
        self.region = os.getenv('AWS_REGION')
        
        # Nombres de buckets desde .env
        self.bucket_publica = os.getenv('BUCKET_PUBLICA')
        self.bucket_proyectos = os.getenv('BUCKET_PROYECTOS')
        self.bucket_rrhh = os.getenv('BUCKET_RRHH')
        self.bucket_logs = os.getenv('BUCKET_LOGS')
        
        # Cliente de S3
        self.s3_client = boto3.client('s3', region_name=self.region)
    
    def get_available_buckets(self, role: str) -> List[str]:
        """
        Obtener buckets disponibles según el rol del usuario.
        
        Args:
            role: Rol del usuario (admin, solo-lectura, etc.)
            
        Returns:
            Lista de nombres de buckets disponibles
        """
        buckets = []
        
        if role == 'admin':
            # Admin puede ver todos los buckets
            buckets = [
                self.bucket_publica,
                self.bucket_proyectos,
                self.bucket_rrhh,
                self.bucket_logs
            ]
        elif role in ['lectura-escritura', 'solo-carga', 'solo-descarga']:
            # Estos roles pueden acceder a publica y proyectos
            buckets = [
                self.bucket_publica,
                self.bucket_proyectos
            ]
        elif role == 'solo-lectura':
            # Solo lectura solo puede ver publica
            buckets = [self.bucket_publica]
        
        return buckets
    
    def list_files(self, bucket_name: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Listar archivos en un bucket.
        
        Args:
            bucket_name: Nombre del bucket
            
        Returns:
            Tuple (éxito, lista_archivos, mensaje_error)
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                return True, [], None
            
            files = []
            for obj in response['Contents']:
                file_info = {
                    'key': obj['Key'],
                    'name': obj['Key'].split('/')[-1],  # Nombre del archivo
                    'size': obj['Size'],
                    'size_mb': round(obj['Size'] / (1024 * 1024), 2),
                    'last_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                }
                files.append(file_info)
            
            # Ordenar por fecha (más recientes primero)
            files.sort(key=lambda x: x['last_modified'], reverse=True)
            
            return True, files, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return False, [], f"El bucket '{bucket_name}' no existe"
            elif error_code == 'AccessDenied':
                return False, [], "No tienes permisos para acceder a este bucket"
            else:
                return False, [], f"Error: {str(e)}"
        except Exception as e:
            return False, [], f"Error inesperado: {str(e)}"
    
    def upload_file(self, file_path: str, bucket_name: str, object_key: str) -> Tuple[bool, Optional[str]]:
        """
        Subir un archivo a S3.
        
        Args:
            file_path: Ruta local del archivo
            bucket_name: Nombre del bucket
            object_key: Nombre del archivo en S3
            
        Returns:
            Tuple (éxito, mensaje_error)
        """
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_key)
            return True, None
            
        except FileNotFoundError:
            return False, f"El archivo '{file_path}' no existe"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                return False, "No tienes permisos para subir archivos a este bucket"
            else:
                return False, f"Error: {str(e)}"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def download_file(self, bucket_name: str, object_key: str, download_path: str) -> Tuple[bool, Optional[str]]:
        """
        Descargar un archivo de S3.
        
        Args:
            bucket_name: Nombre del bucket
            object_key: Nombre del archivo en S3
            download_path: Ruta local donde guardar
            
        Returns:
            Tuple (éxito, mensaje_error)
        """
        try:
            self.s3_client.download_file(bucket_name, object_key, download_path)
            return True, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return False, f"El archivo '{object_key}' no existe"
            elif error_code == 'AccessDenied':
                return False, "No tienes permisos para descargar este archivo"
            else:
                return False, f"Error: {str(e)}"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def delete_file(self, bucket_name: str, object_key: str) -> Tuple[bool, Optional[str]]:
        """
        Eliminar un archivo de S3.
        
        Args:
            bucket_name: Nombre del bucket
            object_key: Nombre del archivo en S3
            
        Returns:
            Tuple (éxito, mensaje_error)
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            return True, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                return False, "No tienes permisos para eliminar archivos"
            else:
                return False, f"Error: {str(e)}"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def get_download_url(self, bucket_name: str, object_key: str, expiration: int = 3600) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generar URL pre-firmada para descargar un archivo.
        
        Args:
            bucket_name: Nombre del bucket
            object_key: Nombre del archivo
            expiration: Tiempo de expiración en segundos (default: 1 hora)
            
        Returns:
            Tuple (éxito, url, mensaje_error)
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return True, url, None
            
        except ClientError as e:
            return False, None, f"Error generando URL: {str(e)}"
        except Exception as e:
            return False, None, f"Error inesperado: {str(e)}”"""
Cliente para conectar con AWS OpenSearch
"""

import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# Cargar variables de entorno
load_dotenv()


class OpenSearchClient:
    """Cliente para interactuar con OpenSearch."""
    
    def __init__(self):
        """Inicializar cliente de OpenSearch."""
        self.endpoint = os.getenv('OPENSEARCH_ENDPOINT')
        self.region = os.getenv('AWS_REGION')
        self.index_name = os.getenv('OPENSEARCH_INDEX_NAME', 'cloudtrail-logs')
        
        # Credenciales AWS
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            'es',
            session_token=credentials.token
        )
        
        # Cliente OpenSearch
        self.client = OpenSearch(
            hosts=[{'host': self.endpoint, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
    
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
                "sort": [{"eventTime": {"order": "desc"}}],
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
                        "fields": ["eventName", "userIdentity.userName", "sourceIPAddress"]
                    }
                })
            else:
                search_query["query"]["bool"]["must"].append({"match_all": {}})
            
            # Agregar filtro de fechas
            if start_date or end_date:
                date_filter = {"range": {"eventTime": {}}}
                if start_date:
                    date_filter["range"]["eventTime"]["gte"] = start_date
                if end_date:
                    date_filter["range"]["eventTime"]["lte"] = end_date
                search_query["query"]["bool"]["must"].append(date_filter)
            
            # Ejecutar búsqueda
            response = self.client.search(
                index=self.index_name,
                body=search_query
            )
            
            # Procesar resultados
            logs = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                log_entry = {
                    'timestamp': source.get('eventTime', 'N/A'),
                    'event_name': source.get('eventName', 'N/A'),
                    'user': source.get('userIdentity', {}).get('userName', 'N/A'),
                    'source_ip': source.get('sourceIPAddress', 'N/A'),
                    'resource': source.get('resources', [{}])[0].get('ARN', 'N/A') if source.get('resources') else 'N/A',
                    'event_type': source.get('eventType', 'N/A'),
                }
                logs.append(log_entry)
            
            return True, logs, None
            
        except Exception as e:
            return False, [], f"Error buscando logs: {str(e)}"
    
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
        Obtener estadísticas de eventos.
        
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
                            "field": "eventName.keyword",
                            "size": 10
                        }
                    },
                    "events_by_user": {
                        "terms": {
                            "field": "userIdentity.userName.keyword",
                            "size": 10
                        }
                    }
                }
            }
            
            response = self.client.search(
                index=self.index_name,
                body=agg_query
            )
            
            stats = {
                'total_events': response['hits']['total']['value'],
                'top_events': [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in response['aggregations']['events_by_name']['buckets']
                ],
                'top_users': [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in response['aggregations']['events_by_user']['buckets']
                ]
            }
            
            return True, stats, None
            
        except Exception as e:
            return False, {}, f"Error obteniendo estadísticas: {str(e)}"
