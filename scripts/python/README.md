# Elegir tu terminal: Git Bash o PowerShell

Este framework fue diseñado pensando en Git Bash como terminal por defecto
(así corren los scripts internos del proyecto), pero en Windows la mayoría de
las máquinas solo traen PowerShell instalado de fábrica. **No necesitas
instalar Git Bash para hacer el curso** — cada script de setup en esta
carpeta tiene una versión equivalente para cada terminal.

---

## ¿Cuál uso?

| Si tú... | Usa |
|---|---|
| Ya tienes Git para Windows instalado (trae Git Bash) | Git Bash — es lo que usa el resto de la documentación interna del framework |
| Solo tienes PowerShell (instalación por defecto de Windows) | PowerShell nativo — no necesitas instalar nada más |
| No sabes cuál tienes | Abre una terminal y escribe `git --version`. Si responde, ya tienes Git Bash disponible (búscalo como "Git Bash" en el menú de inicio) |

No mezcles ambos en el mismo `.venv` a mitad de sesión — cualquiera de los
dos funciona igual de bien, pero usa siempre el mismo para evitar rutas de
intérprete inconsistentes.

---

## Scripts equivalentes

| Tarea | Git Bash | PowerShell |
|---|---|---|
| Crear el entorno virtual e instalar dependencias | `./scripts/python/setup_env.sh` | `.\scripts\python\setup_env.ps1` |
| Actualizar dependencias en un `.venv` existente | `./scripts/python/update_venv.sh` | `.\scripts\python\update_venv.ps1` |

Ambas versiones aceptan las mismas opciones (`--include-dev` / `-IncludeDev`,
`--no-dev` / `-NoDev`, `-h` / `Get-Help`) y hacen exactamente lo mismo: crean
o reutilizan `.venv`, instalan `requirements.txt` (y `requirements-dev.txt`
salvo que pidas lo contrario) con `pip`. El proyecto no usa UV — todo el
manejo de dependencias es pip + `requirements.txt` plano.

Si PowerShell bloquea la ejecución de scripts `.ps1` con un error de
"execution policy", ejecuta esto una sola vez en tu sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Esto no cambia ninguna configuración del sistema — solo habilita scripts
locales para la ventana de PowerShell abierta.

---

## El resto del curso (Terraform, AWS CLI)

Los comandos de Terraform y AWS CLI en
[`docs/student/01_setup_windows.md`](../../docs/student/01_setup_windows.md)
son los mismos en ambas terminales — `terraform`, `aws` y `python` son
binarios, no scripts de shell, así que no necesitan una versión distinta por
terminal.
