"""
Módulo de autenticación con AWS Cognito
"""

import os
import boto3
from typing import Optional, Dict, Tuple, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class CognitoAuth:
    """Clase para manejar autenticación con AWS Cognito."""
    
    def __init__(self):
        """Inicializar cliente de Cognito."""
        self.region = os.getenv('AWS_REGION')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        
        # Cliente de Cognito
        self.client = boto3.client(
            'cognito-idp',
            region_name=self.region
        )
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Autenticar usuario con Cognito.
        
        Args:
            username: Email del usuario
            password: Contraseña
        
        Returns:
            Tuple (éxito, datos_usuario, mensaje_error)
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            # Extraer tokens
            access_token = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']
            
            # Obtener info del usuario y sus grupos
            user_info = self.get_user_info(access_token)
            groups = self.get_user_groups(username)

            # DEBUG - Ver qué contiene user_info
            print(f"DEBUG Cognito - user_info completo: {user_info}")
            print(f"DEBUG Cognito - user_info['attributes']: {user_info.get('attributes', {})}")
            
            # Validar que el usuario tenga un grupo asignado
            if not groups:
                return False, None, "Usuario sin grupo asignado. Contacta al administrador."
            
            # Determinar el rol principal (primer grupo)
            role = groups[0]
            
            # Extraer el nombre del usuario (si existe)
            user_name = user_info.get('attributes', {}).get('name', '')
            
            # DEBUG - Ver extracción del nombre
            print(f"DEBUG Cognito - Atributo 'name' en attributes: '{user_info.get('attributes', {}).get('name', 'NO ENCONTRADO')}'")
            print(f"DEBUG Cognito - user_name extraído: '{user_name}'")
            
            if not user_name:
                # Si no tiene nombre, usar el email
                user_name = username
                print(f"DEBUG Cognito - No había nombre, usando email: '{user_name}'")

            #Debug
            print(f"DEBUG Cognito - user_info completo: {user_info}")
            print(f"DEBUG Cognito - user_name extraído: '{user_name}'")
            
            user_data = {
                'username': username,
                'name': user_name,
                'email': username,
                'access_token': access_token,
                'id_token': id_token,
                'role': role,
                'groups': groups,
                'user_info': user_info
            }

            # DEBUG
            # DEBUG - Verificar user_data
            print(f"DEBUG Cognito - user_data['name'] final: '{user_data['name']}'")
            
            return True, user_data, None
            
        except self.client.exceptions.NotAuthorizedException:
            return False, None, "Usuario o contraseña incorrectos"
        except self.client.exceptions.UserNotFoundException:
            return False, None, "Usuario no encontrado"
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Obtener información del usuario.
        
        Args:
            access_token: Token de acceso de Cognito
        
        Returns:
            Diccionario con información del usuario
        """
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            user_info = {
                'username': response['Username'],
                'attributes': {}
            }
            
            for attr in response['UserAttributes']:
                user_info['attributes'][attr['Name']] = attr['Value']
            
            return user_info
            
        except Exception as e:
            print(f"Error obteniendo info: {e}")
            return {}
    
    def get_user_groups(self, username: str) -> List[str]:
        """
        Obtener grupos del usuario en Cognito.
        
        Args:
            username: Nombre del usuario
        
        Returns:
            Lista de nombres de grupos
        """
        try:
            response = self.client.admin_list_groups_for_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            groups = [group['GroupName'] for group in response.get('Groups', [])]
            return groups
            
        except Exception as e:
            print(f"Error obteniendo grupos: {e}")
            return []
    
    def create_user(self, username: str, password: str, email: str, group: str, name: str = "") -> Tuple[bool, Optional[str]]:
        """
        Crear un nuevo usuario (solo admin).
        
        Args:
            username: Email del usuario (será el username)
            password: Contraseña
            email: Email (mismo que username en Cognito)
            group: Grupo/rol a asignar
            name: Nombre completo del usuario (opcional)
        
        Returns:
            Tuple (éxito, mensaje_error)
        """
        try:
            # Preparar atributos del usuario
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ]
            
            # Agregar nombre si se proporciona
            if name:
                user_attributes.append({'Name': 'name', 'Value': name})
            
            # Crear usuario
            self.client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=user_attributes,
                TemporaryPassword=password,
                MessageAction='SUPPRESS'
            )
            
            # Establecer contraseña permanente
            self.client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=username,
                Password=password,
                Permanent=True
            )
            
            # Agregar a grupo
            if group:
                self.client.admin_add_user_to_group(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    GroupName=group
                )
            
            return True, None
            
        except Exception as e:
            return False, f"Error creando usuario: {str(e)}"
    
    def update_user_name(self, username: str, name: str) -> Tuple[bool, Optional[str]]:
        """
        Actualizar el nombre de un usuario existente.
        
        Args:
            username: Email del usuario
            name: Nuevo nombre completo
        
        Returns:
            Tuple (éxito, mensaje_error)
        """
        try:
            self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'name', 'Value': name}
                ]
            )
            return True, None
            
        except Exception as e:
            return False, f"Error actualizando nombre: {str(e)}"
    
    def list_all_users(self) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Listar todos los usuarios del User Pool.
        
        Returns:
            Tuple (éxito, lista_usuarios, mensaje_error)
        """
        try:
            response = self.client.list_users(
                UserPoolId=self.user_pool_id
            )
            
            users = []
            for user in response.get('Users', []):
                # Extraer atributos
                attributes = {}
                for attr in user.get('Attributes', []):
                    attributes[attr['Name']] = attr['Value']
                
                # Obtener grupos del usuario
                groups = self.get_user_groups(user['Username'])
                
                user_info = {
                    'username': user['Username'],
                    'email': attributes.get('email', 'N/A'),
                    'name': attributes.get('name', 'N/A'),
                    'status': user['UserStatus'],
                    'enabled': user['Enabled'],
                    'created': user['UserCreateDate'].strftime('%Y-%m-%d %H:%M:%S'),
                    'groups': groups,
                    'role': groups[0] if groups else 'sin-grupo'
                }
                users.append(user_info)
            
            return True, users, None
            
        except Exception as e:
            return False, [], f"Error listando usuarios: {str(e)}"