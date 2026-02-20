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
            return False, None, f"Error inesperado: {str(e)}"
