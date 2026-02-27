"""
Pruebas Funcionales End-to-End - CNDD Project
Simula flujos completos de usuario
"""

import boto3
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

REGION = os.getenv('AWS_REGION', 'us-east-2')
USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
BUCKET_PUBLICA = os.getenv('BUCKET_PUBLICA', 'cndd-publica')


class FunctionalTester:
    """Ejecutor de pruebas funcionales."""
    
    def __init__(self):
        self.cognito = boto3.client('cognito-idp', region_name=REGION)
        self.s3 = boto3.client('s3', region_name=REGION)
        
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def print_header(self, text):
        print(f"\n{'='*70}")
        print(f"{text.center(70)}")
        print(f"{'='*70}\n")
    
    def test_login(self, username, password, expected_result=True):
        """Probar login de usuario."""
        test_name = f"Login: {username}"
        
        try:
            response = self.cognito.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            if 'AuthenticationResult' in response:
                if expected_result:
                    print(f"✅ {test_name}: PASS")
                    self.test_results.append({
                        'Prueba': test_name,
                        'Resultado': 'PASS',
                        'Detalles': 'Login exitoso'
                    })
                    self.passed += 1
                    return response['AuthenticationResult']['AccessToken']
                else:
                    print(f"❌ {test_name}: FAIL (se esperaba fallo)")
                    self.test_results.append({
                        'Prueba': test_name,
                        'Resultado': 'FAIL',
                        'Detalles': 'Login exitoso cuando debería fallar'
                    })
                    self.failed += 1
                    return None
            else:
                if not expected_result:
                    print(f"✅ {test_name}: PASS (falló como se esperaba)")
                    self.passed += 1
                    return None
                    
        except Exception as e:
            if not expected_result:
                print(f"✅ {test_name}: PASS (falló como se esperaba)")
                self.test_results.append({
                    'Prueba': test_name,
                    'Resultado': 'PASS',
                    'Detalles': f'Falló correctamente: {type(e).__name__}'
                })
                self.passed += 1
            else:
                print(f"❌ {test_name}: FAIL - {str(e)}")
                self.test_results.append({
                    'Prueba': test_name,
                    'Resultado': 'FAIL',
                    'Detalles': str(e)
                })
                self.failed += 1
            return None
    
    def test_s3_operations(self, bucket, test_file='test-funcional.txt'):
        """Probar operaciones S3."""
        test_content = f"Test funcional - {datetime.now()}"
        
        # Test 1: Upload
        test_name = f"S3 Upload: {bucket}"
        try:
            self.s3.put_object(
                Bucket=bucket,
                Key=test_file,
                Body=test_content.encode('utf-8')
            )
            print(f"✅ {test_name}: PASS")
            self.test_results.append({
                'Prueba': test_name,
                'Resultado': 'PASS',
                'Detalles': 'Archivo subido correctamente'
            })
            self.passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAIL - {str(e)}")
            self.test_results.append({
                'Prueba': test_name,
                'Resultado': 'FAIL',
                'Detalles': str(e)
            })
            self.failed += 1
            return
        
        # Test 2: Download
        test_name = f"S3 Download: {bucket}"
        try:
            response = self.s3.get_object(Bucket=bucket, Key=test_file)
            content = response['Body'].read().decode('utf-8')
            
            if test_content in content:
                print(f"✅ {test_name}: PASS")
                self.test_results.append({
                    'Prueba': test_name,
                    'Resultado': 'PASS',
                    'Detalles': 'Archivo descargado correctamente'
                })
                self.passed += 1
            else:
                print(f"❌ {test_name}: FAIL - Contenido no coincide")
                self.failed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAIL - {str(e)}")
            self.test_results.append({
                'Prueba': test_name,
                'Resultado': 'FAIL',
                'Detalles': str(e)
            })
            self.failed += 1
        
        # Test 3: Delete
        test_name = f"S3 Delete: {bucket}"
        try:
            self.s3.delete_object(Bucket=bucket, Key=test_file)
            print(f"✅ {test_name}: PASS")
            self.test_results.append({
                'Prueba': test_name,
                'Resultado': 'PASS',
                'Detalles': 'Archivo eliminado correctamente'
            })
            self.passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAIL - {str(e)}")
            self.test_results.append({
                'Prueba': test_name,
                'Resultado': 'FAIL',
                'Detalles': str(e)
            })
            self.failed += 1
    
    def test_user_groups(self, username):
        """Verificar que usuario tenga grupos asignados."""
        test_name = f"Verificar grupos: {username}"
        
        try:
            response = self.cognito.admin_list_groups_for_user(
                UserPoolId=USER_POOL_ID,
                Username=username
            )
            
            groups = [g['GroupName'] for g in response.get('Groups', [])]
            
            if len(groups) > 0:
                print(f"✅ {test_name}: PASS ({', '.join(groups)})")
                self.test_results.append({
                    'Prueba': test_name,
                    'Resultado': 'PASS',
                    'Detalles': f'Grupos: {", ".join(groups)}'
                })
                self.passed += 1
            else:
                print(f"❌ {test_name}: FAIL (sin grupos)")
                self.test_results.append({
                    'Prueba': test_name,
                    'Resultado': 'FAIL',
                    'Detalles': 'Usuario sin grupos asignados'
                })
                self.failed += 1
                
        except Exception as e:
            print(f"❌ {test_name}: FAIL - {str(e)}")
            self.test_results.append({
                'Prueba': test_name,
                'Resultado': 'FAIL',
                'Detalles': str(e)
            })
            self.failed += 1
    
    def generate_report(self):
        """Generar reporte de pruebas."""
        self.print_header("RESUMEN DE PRUEBAS FUNCIONALES")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        stats = [
            ['Total de pruebas', total],
            ['✅ Exitosas', self.passed],
            ['❌ Fallidas', self.failed],
            ['% Éxito', f'{success_rate:.1f}%']
        ]
        
        print(tabulate(stats, headers=['Métrica', 'Valor'], tablefmt='grid'))
        
        print(f"\n{'DETALLE DE PRUEBAS':^70}\n")
        print(tabulate(self.test_results, 
                      headers='keys', 
                      tablefmt='grid'))
        
        # Guardar reporte
        import json
        report = {
            'fecha': datetime.now().isoformat(),
            'estadisticas': {
                'total': total,
                'exitosas': self.passed,
                'fallidas': self.failed,
                'porcentaje_exito': round(success_rate, 2)
            },
            'resultados': self.test_results
        }
        
        filename = f'docs/PRUEBAS_FUNCIONALES_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Reporte guardado: {filename}")
        
        return report
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas."""
        print("\n╔════════════════════════════════════════════════════════════════════╗")
        print("║        PRUEBAS FUNCIONALES END-TO-END - CNDD PROJECT              ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        
        # MÓDULO 1: Autenticación
        self.print_header("MÓDULO 1: AUTENTICACIÓN")
        
        # Listar usuarios existentes
        try:
            users = self.cognito.list_users(UserPoolId=USER_POOL_ID, Limit=10)
            test_users = []
            
            for user in users['Users']:
                email = next((attr['Value'] for attr in user['Attributes'] 
                            if attr['Name'] == 'email'), None)
                if email:
                    test_users.append(email)
            
            if len(test_users) > 0:
                print(f"ℹ️  Usuarios encontrados: {len(test_users)}")
                
                # Probar login con primer usuario (asumiendo contraseña conocida)
                # NOTA: En pruebas reales, deberías usar usuarios de prueba
                print("\n⚠️  Saltando pruebas de login (requiere contraseñas)")
                print("   En producción, configurar usuarios de prueba dedicados\n")
                
                # Verificar grupos de usuarios
                for email in test_users[:3]:  # Probar primeros 3
                    self.test_user_groups(email)
            else:
                print("⚠️  No se encontraron usuarios para probar")
                
        except Exception as e:
            print(f"❌ Error listando usuarios: {e}")
        
        # MÓDULO 2: S3 Operations
        self.print_header("MÓDULO 2: OPERACIONES S3")
        self.test_s3_operations(BUCKET_PUBLICA)
        
        # MÓDULO 3: Generar reporte
        return self.generate_report()


def main():
    tester = FunctionalTester()
    report = tester.run_all_tests()
    
    if report['estadisticas']['fallidas'] == 0:
        print("\n✅ TODAS LAS PRUEBAS PASARON\n")
        return 0
    else:
        print(f"\n⚠️  {report['estadisticas']['fallidas']} PRUEBA(S) FALLIDA(S)\n")
        return 1


if __name__ == '__main__':
    exit(main())