# Guía del estudiante — Curso AWS Data Engineering

Punto de entrada único para todo lo que necesitas antes y durante el curso.
Sigue el orden numerado la primera vez; después usa esta página como índice
para volver a cualquier sección.

---

## Antes de la Sesión 1

| Paso | Documento | Qué resuelve |
|---|---|---|
| 0 | [`../../scripts/python/README.md`](../../scripts/python/README.md) | Elegir terminal (Git Bash o PowerShell nativo) y saber qué script de setup usar en cada caso |
| 1 | [`01_setup_windows.md`](01_setup_windows.md) | Instalar Terraform y AWS CLI en Windows, configurar credenciales, primer `terraform init`/`validate` |
| 2 | [`02_mcp_setup.md`](02_mcp_setup.md) | Instalar los servidores MCP de AWS Documentation y Terraform en Claude Code (incluye el requisito de Docker Desktop) |

## Referencia del curso

| Documento | Qué resuelve |
|---|---|
| [`03_temario.md`](03_temario.md) | Temario completo del curso, sesión por sesión |
| [`04_course_scope.md`](04_course_scope.md) | Qué skills de `ai/skills/` aplican a cada sesión — para no perderte en el catálogo completo del framework |

## Referencia de Terraform (uso diario)

| Documento | Qué resuelve |
|---|---|
| [`05_terraform_cheatsheet.md`](05_terraform_cheatsheet.md) | Flujo de comandos copiar-pegar: `init` → `fmt` → `validate` → `plan` → `apply` |
| [`06_terraform_principles.md`](06_terraform_principles.md) | Principios de diseño de infraestructura (destroyability, costo, trazabilidad) que rigen los labs |

---

## Si algo no encaja

- **Dudas de sintaxis/argumentos de Terraform o AWS que no son específicas
  del curso** → usa el MCP de Terraform o el MCP de AWS Documentation
  (instalados en el paso 2), no busques una skill local para eso.
- **Convenciones propias de este proyecto** (tags obligatorios, budgets,
  state, gobernanza) → `ai/domains/terraform.md` y sus skills en
  `ai/skills/terraform/`.
- **Instalar o actualizar la plantilla en tu propio repositorio** (no es
  parte del curso, es para quien reutiliza este framework) →
  [`../framework/README.md`](../framework/README.md).
