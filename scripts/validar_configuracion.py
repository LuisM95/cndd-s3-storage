"""
Script de validación de configuración AWS
Verifica que todos los servicios estén correctamente configurados
"""

import boto3
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

# Configuración
REGION = os.getenv('AWS_REGION', 'us-east-2')
USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
BUCKET_PUBLICA = os.getenv('BUCKET_PUBLICA', 'cndd-publica')
BUCKET_PROYECTOS = os.getenv('BUCKET_PROYECTOS', 'cndd-proyectos')
BUCKET_RRHH = os.getenv('BUCKET_RRHH', 'cndd-rrhh')
BUCKET_LOGS = os.getenv('BUCKET_LOGS', 'cndd-logs')
OPENSEARCH_ENDPOINT = os.getenv('OPENSEARCH_ENDPOINT')
OPENSEARCH_DOMAIN = 'cndd-opensearch'

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprimir encabezado."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    """Imprimir éxito."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """Imprimir error."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    """Imprimir advertencia."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    """Imprimir información."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


class AWSValidator:
    """Validador de configuración AWS."""
    
    def __init__(self):
        """Inicializar clientes AWS."""
        self.s3 = boto3.client('s3', region_name=REGION)
        self.cognito = boto3.client('cognito-idp', region_name=REGION)
        self.iam = boto3.client('iam', region_name=REGION)
        self.opensearch = boto3.client('opensearch', region_name=REGION)
        self.cloudtrail = boto3.client('cloudtrail', region_name=REGION)
        self.sts = boto3.client('sts', region_name=REGION)
        
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
    
    def validate_s3_buckets(self):
        """Validar buckets S3."""
        print_header("VALIDACIÓN DE BUCKETS S3")
        
        buckets = [BUCKET_PUBLICA, BUCKET_PROYECTOS, BUCKET_RRHH, BUCKET_LOGS]
        
        for bucket in buckets:
            self.results['total'] += 1
            try:
                # Verificar existencia
                self.s3.head_bucket(Bucket=bucket)
                print_success(f"Bucket '{bucket}' existe")
                
                # Verificar versionado
                try:
                    versioning = self.s3.get_bucket_versioning(Bucket=bucket)
                    if versioning.get('Status') == 'Enabled':
                        print_info(f"  Versionado: Habilitado")
                    else:
                        print_warning(f"  Versionado: Deshabilitado")
                        self.results['warnings'] += 1
                except:
                    print_warning(f"  No se pudo verificar versionado")
                
                # Verificar cifrado
                try:
                    encryption = self.s3.get_bucket_encryption(Bucket=bucket)
                    print_info(f"  Cifrado: Habilitado")
                except:
                    print_warning(f"  Cifrado: No configurado")
                    self.results['warnings'] += 1
                
                # Verificar logging (excepto bucket de logs)
                if bucket != BUCKET_LOGS:
                    try:
                        logging = self.s3.get_bucket_logging(Bucket=bucket)
                        if 'LoggingEnabled' in logging:
                            print_info(f"  Logging: Habilitado → {logging['LoggingEnabled']['TargetBucket']}")
                        else:
                            print_warning(f"  Logging: Deshabilitado")
                    except:
                        pass
                
                self.results['passed'] += 1
                self.results['details'].append({
                    'componente': f'S3 Bucket: {bucket}',
                    'estado': 'OK',
                    'detalles': 'Bucket configurado correctamente'
                })
                
            except Exception as e:
                print_error(f"Bucket '{bucket}' no existe o no es accesible: {e}")
                self.results['failed'] += 1
                self.results['details'].append({
                    'componente': f'S3 Bucket: {bucket}',
                    'estado': 'FALLO',
                    'detalles': str(e)
                })
    
    def validate_cognito(self):
        """Validar Cognito User Pool."""
        print_header("VALIDACIÓN DE COGNITO USER POOL")
        
        self.results['total'] += 1
        try:
            # Verificar User Pool
            pool = self.cognito.describe_user_pool(UserPoolId=USER_POOL_ID)
            print_success(f"User Pool '{USER_POOL_ID}' existe")
            print_info(f"  Nombre: {pool['UserPool']['Name']}")
            
            # Verificar grupos
            groups = self.cognito.list_groups(UserPoolId=USER_POOL_ID)
            print_info(f"  Grupos configurados: {len(groups['Groups'])}")
            for group in groups['Groups']:
                print_info(f"    - {group['GroupName']}")
            
            # Verificar usuarios
            users = self.cognito.list_users(UserPoolId=USER_POOL_ID)
            print_info(f"  Usuarios creados: {len(users['Users'])}")
            
            self.results['passed'] += 1
            self.results['details'].append({
                'componente': 'Cognito User Pool',
                'estado': 'OK',
                'detalles': f'{len(users["Users"])} usuarios, {len(groups["Groups"])} grupos'
            })
            
        except Exception as e:
            print_error(f"User Pool no accesible: {e}")
            self.results['failed'] += 1
            self.results['details'].append({
                'componente': 'Cognito User Pool',
                'estado': 'FALLO',
                'detalles': str(e)
            })
    
    def validate_iam_roles(self):
        """Validar roles IAM."""
        print_header("VALIDACIÓN DE ROLES IAM")
        
        roles = [
            'Cognito-Admin',
            'Cognito-LecturaEscritura',
            'Cognito-SoloLectura',
            'Cognito-SoloCarga',
            'Cognito-SoloDescarga'
        ]
        
        for role_name in roles:
            self.results['total'] += 1
            try:
                role = self.iam.get_role(RoleName=role_name)
                print_success(f"Rol '{role_name}' existe")
                
                # Verificar políticas adjuntas
                policies = self.iam.list_attached_role_policies(RoleName=role_name)
                print_info(f"  Políticas adjuntas: {len(policies['AttachedPolicies'])}")
                
                self.results['passed'] += 1
                self.results['details'].append({
                    'componente': f'IAM Role: {role_name}',
                    'estado': 'OK',
                    'detalles': f'{len(policies["AttachedPolicies"])} políticas'
                })
                
            except Exception as e:
                print_error(f"Rol '{role_name}' no existe: {e}")
                self.results['failed'] += 1
                self.results['details'].append({
                    'componente': f'IAM Role: {role_name}',
                    'estado': 'FALLO',
                    'detalles': str(e)
                })
    
    def validate_opensearch(self):
        """Validar OpenSearch."""
        print_header("VALIDACIÓN DE OPENSEARCH")
        
        self.results['total'] += 1
        try:
            domain = self.opensearch.describe_domain(DomainName=OPENSEARCH_DOMAIN)
            print_success(f"Dominio OpenSearch '{OPENSEARCH_DOMAIN}' existe")
            print_info(f"  Endpoint: {domain['DomainStatus']['Endpoint']}")
            print_info(f"  Estado: {domain['DomainStatus']['Created']}")
            print_info(f"  Versión: {domain['DomainStatus']['EngineVersion']}")
            
            # Verificar cifrado
            if domain['DomainStatus'].get('EncryptionAtRestOptions', {}).get('Enabled'):
                print_info(f"  Cifrado en reposo: Habilitado")
            else:
                print_warning(f"  Cifrado en reposo: Deshabilitado")
            
            self.results['passed'] += 1
            self.results['details'].append({
                'componente': 'OpenSearch Domain',
                'estado': 'OK',
                'detalles': f'Versión {domain["DomainStatus"]["EngineVersion"]}'
            })
            
        except Exception as e:
            print_error(f"OpenSearch no accesible: {e}")
            self.results['failed'] += 1
            self.results['details'].append({
                'componente': 'OpenSearch Domain',
                'estado': 'FALLO',
                'detalles': str(e)
            })
    
    def validate_cloudtrail(self):
        """Validar CloudTrail."""
        print_header("VALIDACIÓN DE CLOUDTRAIL")
        
        self.results['total'] += 1
        try:
            trails = self.cloudtrail.list_trails()
            print_success(f"CloudTrail configurado: {len(trails['Trails'])} trail(s)")
            
            for trail in trails['Trails']:
                trail_status = self.cloudtrail.get_trail_status(Name=trail['TrailARN'])
                if trail_status['IsLogging']:
                    print_info(f"  Trail activo: {trail['Name']}")
                else:
                    print_warning(f"  Trail inactivo: {trail['Name']}")
            
            self.results['passed'] += 1
            self.results['details'].append({
                'componente': 'CloudTrail',
                'estado': 'OK',
                'detalles': f'{len(trails["Trails"])} trail(s) configurado(s)'
            })
            
        except Exception as e:
            print_error(f"CloudTrail no accesible: {e}")
            self.results['failed'] += 1
            self.results['details'].append({
                'componente': 'CloudTrail',
                'estado': 'FALLO',
                'detalles': str(e)
            })
    
    def validate_account_info(self):
        """Validar información de la cuenta."""
        print_header("INFORMACIÓN DE LA CUENTA AWS")
        
        try:
            identity = self.sts.get_caller_identity()
            print_info(f"Account ID: {identity['Account']}")
            print_info(f"ARN: {identity['Arn']}")
            print_info(f"User ID: {identity['UserId']}")
        except Exception as e:
            print_warning(f"No se pudo obtener información de la cuenta: {e}")
    
    def generate_report(self):
        """Generar reporte de validación."""
        print_header("RESUMEN DE VALIDACIÓN")
        
        # Estadísticas
        stats_data = [
            ["Total de validaciones", self.results['total']],
            ["✅ Exitosas", self.results['passed']],
            ["❌ Fallidas", self.results['failed']],
            ["⚠️  Advertencias", self.results['warnings']],
            ["% Éxito", f"{(self.results['passed']/self.results['total']*100):.1f}%"]
        ]
        
        print(tabulate(stats_data, headers=["Métrica", "Valor"], tablefmt="grid"))
        
        # Detalles
        print(f"\n{Colors.BOLD}DETALLES POR COMPONENTE:{Colors.RESET}\n")
        
        details_table = [[d['componente'], d['estado'], d['detalles']] 
                        for d in self.results['details']]
        
        print(tabulate(details_table, 
                      headers=["Componente", "Estado", "Detalles"], 
                      tablefmt="grid"))
        
        # Guardar reporte JSON
        report_file = f'docs/VALIDACION_CONFIG_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'fecha': datetime.now().isoformat(),
                'estadisticas': {
                    'total': self.results['total'],
                    'exitosas': self.results['passed'],
                    'fallidas': self.results['failed'],
                    'advertencias': self.results['warnings'],
                    'porcentaje_exito': round(self.results['passed']/self.results['total']*100, 2)
                },
                'detalles': self.results['details']
            }, f, indent=2)
        
        print(f"\n{Colors.GREEN}✅ Reporte JSON guardado: {report_file}{Colors.RESET}")
        
        return self.results
    
    def run_all_validations(self):
        """Ejecutar todas las validaciones."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║     VALIDACIÓN DE CONFIGURACIÓN AWS - CNDD PROJECT                 ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.RESET}")
        
        self.validate_account_info()
        self.validate_s3_buckets()
        self.validate_cognito()
        self.validate_iam_roles()
        self.validate_opensearch()
        self.validate_cloudtrail()
        
        return self.generate_report()


def main():
    """Ejecutar validación completa."""
    validator = AWSValidator()
    results = validator.run_all_validations()
    
    # Resultado final
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ VALIDACIÓN EXITOSA - Todos los componentes están correctamente configurados{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ VALIDACIÓN CON ERRORES - Revisa los componentes fallidos{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    exit(main())