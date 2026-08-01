# Terraform Cheat Sheet

Usa este flujo desde PowerShell en la raíz del repositorio.

Este laboratorio espera credenciales de AWS en `infra\env\.env.credentials`.
Mantén ese archivo solo en local. No subas claves de acceso reales.

## Sobre los dos estilos de comando

Cada paso de Terraform que sigue muestra dos bloques equivalentes, listos
para copiar y pegar:

- **Opción A — Inline con `-chdir`**: conciso, ideal para comandos cortos de
  una línea. Terraform trata `infra\` como su directorio de trabajo, así que
  rutas relativas como `terraform.tfvars` y `tfplan` se resuelven dentro de
  `infra\`.
- **Opción B — `Push-Location` + `try/finally`**: cambia el directorio de
  trabajo de la shell a `infra\`, ejecuta el/los comando(s), y luego regresa
  a la raíz del repo incluso si un comando falla. Preferible cuando los
  comandos se alargan, cuando encadenas varias llamadas a Terraform, o
  cuando mezclas Terraform con otros comandos de PowerShell (pipes,
  redirección, `terraform console`, `terraform import`, `terraform state
  mv`, etc.). Algunas combinaciones de flags pueden comportarse mal con
  `-chdir`; este patrón lo evita.

Elige el bloque que mejor se ajuste al momento. El wrapper
`try { ... } finally { Pop-Location }` garantiza que termines de vuelta en
la raíz del repo.

## 1. Cargar credenciales de AWS

```powershell
Get-Content infra\env\.env.credentials | ForEach-Object {
  if ($_ -match "^\s*#" -or $_ -match "^\s*$") { return }

  $name, $value = $_ -split "=", 2
  [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}
```

Verifica solo los valores que no son secretos:

```powershell
$env:AWS_ACCESS_KEY_ID
$env:AWS_DEFAULT_REGION
```

Evita imprimir `AWS_SECRET_ACCESS_KEY`.

## 2. Inicializar Terraform

Ejecuta esto antes del primer plan, y repítelo cuando cambien providers,
módulos, o la configuración del backend. Esto descarga los providers y
prepara el directorio local `.terraform`.

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra init
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform init
} finally {
  Pop-Location
}
```

## 3. Crear las variables locales de Terraform

Crea `infra\terraform.tfvars` a partir del archivo de ejemplo versionado.

**Opción A — Inline (sin Terraform, solo PowerShell):**

```powershell
Copy-Item infra\terraform.tfvars.example infra\terraform.tfvars
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  Copy-Item terraform.tfvars.example terraform.tfvars
} finally {
  Pop-Location
}
```

Edita `infra\terraform.tfvars` solo con valores que no sean secretos, como
nombre del proyecto, entorno, región, y tags. Este archivo está ignorado
por Git.

## 4. Validar Terraform

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra fmt -check
terraform -chdir=infra validate
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform fmt -check
  terraform validate
} finally {
  Pop-Location
}
```

## 5. Crear y guardar un plan

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra plan -var-file="terraform.tfvars" -out="tfplan"
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform plan -var-file="terraform.tfvars" -out="tfplan"
} finally {
  Pop-Location
}
```

Revisa el plan guardado en formato legible.

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra show tfplan
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform show tfplan
} finally {
  Pop-Location
}
```

## 6. Aplicar el plan guardado

Aplica únicamente el plan guardado que ya revisaste. Esto crea o modifica
recursos reales de AWS.

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra apply "tfplan"
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform apply "tfplan"
} finally {
  Pop-Location
}
```

## 7. Destruir los recursos del laboratorio

Primero crea y revisa un plan de destrucción.

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra plan -destroy -var-file="terraform.tfvars" -out="destroy.tfplan"
terraform -chdir=infra show destroy.tfplan
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform plan -destroy -var-file="terraform.tfvars" -out="destroy.tfplan"
  terraform show destroy.tfplan
} finally {
  Pop-Location
}
```

Luego aplica el plan de destrucción revisado. Esto elimina los recursos de
AWS gestionados por este state de Terraform.

**Opción A — Inline con `-chdir`:**

```powershell
terraform -chdir=infra apply "destroy.tfplan"
```

**Opción B — `Push-Location` + `try/finally`:**

```powershell
Push-Location infra
try {
  terraform apply "destroy.tfplan"
} finally {
  Pop-Location
}
```

## 8. Limpiar archivos de plan locales

Después de aplicar o destruir, elimina los archivos de plan guardados:

```powershell
Remove-Item infra\tfplan -ErrorAction SilentlyContinue
Remove-Item infra\destroy.tfplan -ErrorAction SilentlyContinue
```

## 9. Limpiar las credenciales de la sesión

Cuando termines, elimina las credenciales de AWS del proceso actual de
PowerShell:

```powershell
Remove-Item Env:\AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_DEFAULT_REGION -ErrorAction SilentlyContinue
```

Cierra también la ventana de la terminal si quieres descartar la sesión por
completo.
