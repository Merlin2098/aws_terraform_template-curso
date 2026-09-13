# Instalar Terraform en Windows

Usa esta guía cuando necesites una ruta clara de configuración en Windows
para:

* Instalación de Terraform usando el binario oficial de HashiCorp
* Configuración manual del `PATH`
* Compatibilidad con entornos corporativos/restringidos
* Flujo inicial de validación de Terraform + AWS CLI

Esta guía evita intencionalmente gestores de paquetes como Chocolatey, para
mantener el proceso de instalación explícito, portable y reproducible.

> Los comandos de Terraform y AWS CLI de esta guía funcionan igual en Git
> Bash o en PowerShell. Si buscas el script para crear tu entorno virtual de
> Python (`.venv`), ve primero a
> [`scripts/python/README.md`](../../scripts/python/README.md) — tiene la
> versión para cada terminal.

---

## 1. Descargar Terraform desde el sitio oficial de HashiCorp

Abre la página oficial de descargas de Terraform:

[Terraform Downloads](https://developer.hashicorp.com/terraform/downloads)

Descarga:

* El paquete ZIP de Windows AMD64

Ejemplo:

```text
terraform_1.x.x_windows_amd64.zip
```

---

## 2. Extraer Terraform

Crea un directorio local para herramientas.

Ejemplo recomendado:

```text
C:\approved-tools\terraform\
```

Extrae el contenido del ZIP en esa carpeta.

Estructura esperada:

```text
C:\approved-tools\terraform\terraform.exe
```

---

## 3. Verificar el binario de Terraform directamente

Abre PowerShell y ejecuta:

```powershell
C:\approved-tools\terraform\terraform.exe version
```

Salida esperada:

```text
Terraform v1.x.x
```

---

## 4. Agregar Terraform al PATH (solo sesión actual)

Usa esto cuando quieras acceso temporal sin modificar la configuración de la
máquina.

```powershell
$env:Path = "C:\approved-tools\terraform;$env:Path"

terraform version
Get-Command terraform
```

Esto solo afecta a la sesión actual de PowerShell.

---

## 5. Agregar Terraform al PATH de usuario de forma permanente (sin derechos de administrador)

Usa esto cuando no tengas derechos de administrador disponibles.

```powershell
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

[System.Environment]::SetEnvironmentVariable(
    "Path",
    "$userPath;C:\approved-tools\terraform",
    "User"
)

Write-Host "Terraform agregado al PATH de usuario"
```

Cierra y vuelve a abrir PowerShell, luego verifica:

```powershell
terraform version
Get-Command terraform
```

Esto conserva el acceso a Terraform solo para el perfil del usuario actual.

---

## 6. Agregar Terraform al PATH del sistema de forma permanente (administrador)

Usa esto cuando administras la máquina y quieres que Terraform esté
disponible para todo el sistema.

Abre PowerShell como Administrador:

```powershell
$terraformPath = "C:\approved-tools\terraform"

[System.Environment]::SetEnvironmentVariable(
    "Path",
    [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";$terraformPath",
    "Machine"
)

Write-Host "Terraform agregado al PATH del sistema"
```

Cierra y vuelve a abrir PowerShell, luego verifica:

```powershell
terraform version
Get-Command terraform
```

---

## 7. Instalar AWS CLI

Terraform normalmente interactúa con servicios de AWS, así que AWS CLI
también debe instalarse y validarse.

Descarga:

[AWS CLI Installer](https://aws.amazon.com/cli/)

Verificar la instalación:

```powershell
aws --version
Get-Command aws
```

---

## 8. Configurar credenciales de AWS

### Opción A: `aws configure` estándar

Ejecuta:

```powershell
aws configure
```

Proporciona:

```text
AWS Access Key ID
AWS Secret Access Key
Default region
Default output format
```

Esto crea:

```text
C:\Users\<USUARIO>\.aws\credentials
C:\Users\<USUARIO>\.aws\config
```

---

### Opción B: variables de entorno (`.env.credentials`)

Ejemplo:

```text
AWS_ACCESS_KEY_ID=XXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXX
AWS_DEFAULT_REGION=us-east-1
```

Cargar las credenciales en la sesión actual de PowerShell:

```powershell
Get-Content infra\env\.env.credentials | ForEach-Object {
  if ($_ -match "^\s*#" -or $_ -match "^\s*$") { return }

  $name, $value = $_ -split "=", 2
  [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}
```

Validar las credenciales:

```powershell
aws sts get-caller-identity
```

---

## 9. Flujo inicial de validación de Terraform

Flujo de validación recomendado antes de cualquier despliegue.

---

### Terraform Init

```powershell
terraform -chdir=infra init
```

---

### Validación de formato de Terraform

```powershell
terraform -chdir=infra fmt -check
```

---

### Terraform Validate

```powershell
terraform -chdir=infra validate
```

---

### Terraform Plan

```powershell
terraform -chdir=infra plan -out="tfplan"
```

---

### Terraform Apply

```powershell
terraform -chdir=infra apply "tfplan"
```

---

### Terraform Outputs

```powershell
terraform -chdir=infra output
```

Formato JSON:

```powershell
terraform -chdir=infra output -json
```

---

## 10. Prácticas corporativas recomendadas

Para entornos corporativos restringidos:

* Preferir binarios portables oficiales
* Evitar gestores de paquetes cuando sea posible
* Mantener explícita la versión de Terraform
* Usar configuración de PATH de alcance local de usuario
* Guardar scripts auxiliares bajo:

```text
tests/aws/
scripts/python/
```

* Evitar hardcodear credenciales dentro de `.tfvars`
* Preferir `.env.credentials` o perfiles de AWS
* Validar permisos IAM antes del despliegue

Comprobaciones de validación recomendadas antes de `apply`:

```powershell
terraform version
aws --version
aws sts get-caller-identity
terraform -chdir=infra validate
```

---

## 11. Comandos de verificación rápida

```powershell
terraform version
terraform -help
Get-Command terraform

aws --version
aws sts get-caller-identity

terraform -chdir=infra init
terraform -chdir=infra validate
```

---

## 12. Herramientas recomendadas

Conjunto de herramientas recomendado para un flujo de trabajo con Terraform
reproducible y asistido por IA:

* Terraform
* AWS CLI
* Python 3.12+
* pip
* Git
* VSCode
* Claude Code
* Codex
* Ruff
* Pytest
* pre-commit
