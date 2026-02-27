"""
Auditoría de Seguridad - CNDD Project
Verifica medidas de seguridad implementadas
"""

import boto3
import os
from datetime import datetime
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

REGION = os.getenv('AWS_REGION', 'us-east-2')
BUCKETS = ['cndd-publica', 'cndd-proyectos', 'cndd-recursoshumanos', 'cndd-logs']
USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
OPENSEARCH_DOMAIN = 'cndd-opensearch'


class SecurityAuditor:
    """Auditor de seguridad AWS."""
    
    def __init__(self):
        self.s3 = boto3.client('s3', region_name=REGION)
        self.cognito = boto3.client('cognito-idp', region_name=REGION)
        self.iam = boto3.client('iam', region_name=REGION)
        self.opensearch = boto3.client('opensearch', region_name=REGION)
        self.cloudtrail = boto3.client('cloudtrail', region_name=REGION)
        
        self.findings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'passed': []
        }
    
    def print_header(self, text):
        print(f"\n{'='*70}")
        print(f"{text.center(70)}")
        print(f"{'='*70}\n")
    
    def add_finding(self, severity, component, check, status, details):
        """Agregar hallazgo."""
        finding = {
            'componente': component,
            'verificacion': check,
            'estado': status,
            'detalles': details
        }
        
        if status == 'PASS':
            self.findings['passed'].append(finding)
        else:
            self.findings[severity.lower()].append(finding)
    
    def audit_s3_encryption(self):
        """Auditar cifrado de buckets S3."""
        self.print_header("AUDITORÍA: CIFRADO EN S3")
        
        for bucket in BUCKETS:
            try:
                encryption = self.s3.get_bucket_encryption(Bucket=bucket)
                self.add_finding('low', f'S3: {bucket}', 'Cifrado en reposo', 'PASS',
                               f'AES-256 habilitado')
                print(f"✅ {bucket}: Cifrado habilitado")
            except:
                self.add_finding('high', f'S3: {bucket}', 'Cifrado en reposo', 'FAIL',
                               'Cifrado no configurado')
                print(f"❌ {bucket}: Cifrado NO configurado (CRÍTICO)")
    
    def audit_s3_versioning(self):
        """Auditar versionado de buckets."""
        self.print_header("AUDITORÍA: VERSIONADO EN S3")
        
        for bucket in BUCKETS:
            try:
                versioning = self.s3.get_bucket_versioning(Bucket=bucket)
                if versioning.get('Status') == 'Enabled':
                    self.add_finding('low', f'S3: {bucket}', 'Versionado', 'PASS',
                                   'Versionado habilitado')
                    print(f"✅ {bucket}: Versionado habilitado")
                else:
                    self.add_finding('medium', f'S3: {bucket}', 'Versionado', 'WARN',
                                   'Versionado deshabilitado (recomendado para recuperación)')
                    print(f"⚠️  {bucket}: Versionado deshabilitado")
            except Exception as e:
                self.add_finding('medium', f'S3: {bucket}', 'Versionado', 'ERROR',
                               str(e))
    
    def audit_s3_public_access(self):
        """Auditar acceso público."""
        self.print_header("AUDITORÍA: ACCESO PÚBLICO EN S3")
        
        for bucket in BUCKETS:
            try:
                public_block = self.s3.get_public_access_block(Bucket=bucket)
                config = public_block['PublicAccessBlockConfiguration']
                
                if all([config.get('BlockPublicAcls'),
                       config.get('IgnorePublicAcls'),
                       config.get('BlockPublicPolicy'),
                       config.get('RestrictPublicBuckets')]):
                    self.add_finding('low', f'S3: {bucket}', 'Bloqueo acceso público', 'PASS',
                                   'Acceso público bloqueado completamente')
                    print(f"✅ {bucket}: Acceso público bloqueado")
                else:
                    self.add_finding('critical', f'S3: {bucket}', 'Bloqueo acceso público', 'FAIL',
                                   'Acceso público NO bloqueado completamente (CRÍTICO)')
                    print(f"❌ {bucket}: Acceso público NO bloqueado (CRÍTICO)")
            except:
                self.add_finding('high', f'S3: {bucket}', 'Bloqueo acceso público', 'WARN',
                               'No se pudo verificar configuración')
                print(f"⚠️  {bucket}: No se pudo verificar")
    
    def audit_cognito_mfa(self):
        """Auditar MFA en Cognito."""
        self.print_header("AUDITORÍA: AUTENTICACIÓN COGNITO")
        
        try:
            pool = self.cognito.describe_user_pool(UserPoolId=USER_POOL_ID)
            mfa_config = pool['UserPool'].get('MfaConfiguration', 'OFF')
            
            if mfa_config == 'ON' or mfa_config == 'OPTIONAL':
                self.add_finding('low', 'Cognito', 'MFA', 'PASS',
                               f'MFA configurado: {mfa_config}')
                print(f"✅ MFA: {mfa_config}")
            else:
                self.add_finding('medium', 'Cognito', 'MFA', 'WARN',
                               'MFA no habilitado (recomendado para producción)')
                print(f"⚠️  MFA: Deshabilitado (recomendado habilitarlo)")
            
            # Política de contraseñas
            password_policy = pool['UserPool'].get('Policies', {}).get('PasswordPolicy', {})
            min_length = password_policy.get('MinimumLength', 0)
            
            if min_length >= 8:
                self.add_finding('low', 'Cognito', 'Política de contraseñas', 'PASS',
                               f'Longitud mínima: {min_length} caracteres')
                print(f"✅ Contraseñas: Mínimo {min_length} caracteres")
            else:
                self.add_finding('high', 'Cognito', 'Política de contraseñas', 'FAIL',
                               f'Longitud mínima débil: {min_length}')
                print(f"❌ Contraseñas: Política débil")
                
        except Exception as e:
            self.add_finding('high', 'Cognito', 'Configuración', 'ERROR', str(e))
    
    def audit_iam_roles(self):
        """Auditar roles IAM."""
        self.print_header("AUDITORÍA: ROLES Y POLÍTICAS IAM")
        
        roles = ['Cognito-Admin', 'Cognito-LecturaEscritura', 'Cognito-SoloLectura',
                'Cognito-SoloCarga', 'Cognito-SoloDescarga']
        
        for role_name in roles:
            try:
                # Verificar políticas inline (no recomendadas)
                inline_policies = self.iam.list_role_policies(RoleName=role_name)
                
                if len(inline_policies['PolicyNames']) > 0:
                    self.add_finding('medium', f'IAM: {role_name}', 'Políticas inline', 'WARN',
                                   f'{len(inline_policies["PolicyNames"])} políticas inline (usar managed)')
                    print(f"⚠️  {role_name}: Tiene políticas inline")
                else:
                    self.add_finding('low', f'IAM: {role_name}', 'Políticas inline', 'PASS',
                                   'Sin políticas inline (buena práctica)')
                    print(f"✅ {role_name}: Sin políticas inline")
                    
            except:
                pass
    
    def audit_opensearch(self):
        """Auditar OpenSearch."""
        self.print_header("AUDITORÍA: OPENSEARCH")
        
        try:
            domain = self.opensearch.describe_domain(DomainName=OPENSEARCH_DOMAIN)
            
            # Cifrado en reposo
            if domain['DomainStatus'].get('EncryptionAtRestOptions', {}).get('Enabled'):
                self.add_finding('low', 'OpenSearch', 'Cifrado en reposo', 'PASS',
                               'Cifrado habilitado')
                print(f"✅ Cifrado en reposo: Habilitado")
            else:
                self.add_finding('high', 'OpenSearch', 'Cifrado en reposo', 'FAIL',
                               'Cifrado deshabilitado')
                print(f"❌ Cifrado en reposo: Deshabilitado")
            
            # HTTPS obligatorio
            if domain['DomainStatus'].get('DomainEndpointOptions', {}).get('EnforceHTTPS'):
                self.add_finding('low', 'OpenSearch', 'HTTPS', 'PASS',
                               'HTTPS obligatorio')
                print(f"✅ HTTPS: Obligatorio")
            else:
                self.add_finding('critical', 'OpenSearch', 'HTTPS', 'FAIL',
                               'HTTPS no obligatorio (CRÍTICO)')
                print(f"❌ HTTPS: No obligatorio (CRÍTICO)")
                
        except Exception as e:
            self.add_finding('high', 'OpenSearch', 'Configuración', 'ERROR', str(e))
    
    def audit_cloudtrail(self):
        """Auditar CloudTrail."""
        self.print_header("AUDITORÍA: CLOUDTRAIL (LOGGING)")
        
        try:
            trails = self.cloudtrail.list_trails()
            active_trails = 0
            
            for trail in trails['Trails']:
                status = self.cloudtrail.get_trail_status(Name=trail['TrailARN'])
                if status['IsLogging']:
                    active_trails += 1
            
            if active_trails > 0:
                self.add_finding('low', 'CloudTrail', 'Logging activo', 'PASS',
                               f'{active_trails} trail(s) activo(s)')
                print(f"✅ CloudTrail: {active_trails} trail(s) activo(s)")
            else:
                self.add_finding('critical', 'CloudTrail', 'Logging activo', 'FAIL',
                               'Sin trails activos (CRÍTICO para auditoría)')
                print(f"❌ CloudTrail: Sin trails activos (CRÍTICO)")
                
        except Exception as e:
            self.add_finding('critical', 'CloudTrail', 'Configuración', 'ERROR', str(e))
    
    def generate_report(self):
        """Generar reporte de auditoría."""
        self.print_header("RESUMEN DE AUDITORÍA DE SEGURIDAD")
        
        # Estadísticas
        total_checks = (len(self.findings['critical']) + 
                       len(self.findings['high']) + 
                       len(self.findings['medium']) + 
                       len(self.findings['low']) + 
                       len(self.findings['passed']))
        
        stats = [
            ['Total de verificaciones', total_checks],
            ['✅ Aprobadas', len(self.findings['passed'])],
            ['🔴 Críticas', len(self.findings['critical'])],
            ['🟠 Altas', len(self.findings['high'])],
            ['🟡 Medias', len(self.findings['medium'])],
            ['🔵 Bajas', len(self.findings['low'])],
            ['% Cumplimiento', f"{(len(self.findings['passed'])/total_checks*100):.1f}%"]
        ]
        
        print(tabulate(stats, headers=['Métrica', 'Valor'], tablefmt='grid'))
        
        # Hallazgos por severidad
        if self.findings['critical']:
            print(f"\n🔴 HALLAZGOS CRÍTICOS ({len(self.findings['critical'])}):")
            print(tabulate([[f['componente'], f['verificacion'], f['detalles']] 
                          for f in self.findings['critical']],
                         headers=['Componente', 'Verificación', 'Detalles'],
                         tablefmt='grid'))
        
        if self.findings['high']:
            print(f"\n🟠 HALLAZGOS ALTOS ({len(self.findings['high'])}):")
            print(tabulate([[f['componente'], f['verificacion'], f['detalles']] 
                          for f in self.findings['high']],
                         headers=['Componente', 'Verificación', 'Detalles'],
                         tablefmt='grid'))
        
        if self.findings['medium']:
            print(f"\n🟡 HALLAZGOS MEDIOS ({len(self.findings['medium'])}):")
            print(tabulate([[f['componente'], f['verificacion'], f['detalles']] 
                          for f in self.findings['medium']],
                         headers=['Componente', 'Verificación', 'Detalles'],
                         tablefmt='grid'))
        
        # Guardar reporte
        report = {
            'fecha': datetime.now().isoformat(),
            'estadisticas': {
                'total': total_checks,
                'aprobadas': len(self.findings['passed']),
                'criticas': len(self.findings['critical']),
                'altas': len(self.findings['high']),
                'medias': len(self.findings['medium']),
                'bajas': len(self.findings['low']),
                'porcentaje_cumplimiento': round(len(self.findings['passed'])/total_checks*100, 2)
            },
            'hallazgos': self.findings
        }
        
        filename = f'docs/AUDITORIA_SEGURIDAD_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Reporte guardado: {filename}")
        
        return report
    
    def run_audit(self):
        """Ejecutar auditoría completa."""
        print("\n╔════════════════════════════════════════════════════════════════════╗")
        print("║       AUDITORÍA DE SEGURIDAD AWS - CNDD PROJECT                   ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        
        self.audit_s3_encryption()
        self.audit_s3_versioning()
        self.audit_s3_public_access()
        self.audit_cognito_mfa()
        self.audit_iam_roles()
        self.audit_opensearch()
        self.audit_cloudtrail()
        
        return self.generate_report()


def main():
    auditor = SecurityAuditor()
    report = auditor.run_audit()
    
    # Resultado final
    if report['estadisticas']['criticas'] == 0 and report['estadisticas']['altas'] == 0:
        print("\n✅ AUDITORÍA APROBADA - No se encontraron vulnerabilidades críticas o altas\n")
        return 0
    else:
        print("\n⚠️  AUDITORÍA CON HALLAZGOS - Revisa los hallazgos críticos y altos\n")
        return 1


if __name__ == '__main__':
    exit(main())