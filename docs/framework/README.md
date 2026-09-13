# Configuración en Windows

Esta guía prepara una máquina Windows para usar esta plantilla y para
instalarla en otro repositorio.

## Preparar el repositorio de la plantilla

Desde la raíz del repositorio:

```powershell
.\scripts\python\setup_env.ps1
```

O, en Git Bash:

```bash
./scripts/python/setup_env.sh
```

Este wrapper resuelve Python automáticamente, crea `.venv` si es necesario
con `python -m venv`, e instala las dependencias con `pip` a partir del
`requirements.txt` actual del proyecto (y `requirements-dev.txt`, a menos que
se pase `-NoDev`).

Cuando instalas esta plantilla en otro repositorio, el instalador copia
`requirements.txt` y `requirements-dev.txt`.

Instalar pre-commit en el entorno del repositorio actual:

```powershell
.\.venv\Scripts\pre-commit.exe install
.\.venv\Scripts\pre-commit.exe --version
```

Para ejecutar todos los hooks configurados manualmente:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

Referencia: https://pre-commit.com/

## Refrescar o cambiar el entorno

Para refrescar el entorno local después de editar dependencias:

```powershell
.\scripts\python\update_venv.ps1
```

Para sincronizar solo las dependencias de runtime (omitiendo herramientas de
desarrollo):

```powershell
.\scripts\python\setup_env.ps1 -NoDev
.\scripts\python\update_venv.ps1 -NoDev
```

## Instalar esta plantilla en otro repositorio

Previsualizar la instalación sin escribir archivos:

```powershell
.\.venv\Scripts\python.exe install_windows.py --dry-run --target C:\ruta\al\repo-destino
```

Instalar la plantilla seleccionando la carpeta del repositorio destino en el
Explorador:

```powershell
.\.venv\Scripts\python.exe install_windows.py
```

Instalar la plantilla con una ruta destino explícita:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\ruta\al\repo-destino
```

Sobrescribir archivos existentes en el destino solo cuando sea intencional:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\ruta\al\repo-destino --force
```

Si el repositorio destino ya tiene un `.gitignore`, el instalador conserva ese
archivo y solo añade las reglas de ignorado presentes en el `.gitignore` de la
plantilla que falten en el destino. Si el repositorio destino no tiene
`.gitignore`, el `.gitignore` de la plantilla se copia tal cual.

El instalador no ejecuta Terraform, no instala dependencias, no inicializa
Git ni ejecuta pre-commit en el repositorio destino.

El instalador también deja fuera los puntos de entrada del instalador y la
documentación de la plantilla: `install_windows.py`, `install_linux.py`, los
archivos llamados `README.md`, y `docs/` no se copian al repositorio destino.

## Cómo funciona la instalación en el host

El instalador:

- copia `requirements.txt` y `requirements-dev.txt`
- escribe `.framework-version.json` para llevar registro de la versión de
  plantilla instalada

El empaquetado incluye el `requirements.txt` de runtime junto con `src/` para
el despliegue.
