# Instalación de servidores MCP (AWS y Terraform) en Claude Code

> Guía operativa, no ejecutable automáticamente. Cubre cómo instalar los
> servidores MCP de AWS Documentation y HashiCorp Terraform en Claude Code
> para este curso. Complementa `ai/domains/aws.md` y `ai/domains/terraform.md`,
> que documentan qué contenido delega el framework de skills a estos MCP en
> lugar de mantenerlo como skill local (ver también la nota de alcance en
> `ai/domains/terraform.md`).

---

## Por qué estos dos MCP

- **AWS Documentation MCP Server** — da acceso a la documentación oficial de
  AWS (búsqueda, lectura de páginas, recomendaciones, tablas de servicio) sin
  salir de Claude Code. Sustituye la necesidad de mantener skills locales que
  solo resumían teoría genérica de un servicio.
- **Terraform MCP Server** — da acceso a la documentación de providers,
  módulos y el Registry de HashiCorp. Cubre mecánica genérica de Terraform
  (sintaxis, argumentos de recursos, versiones de provider) que ya no vive en
  `ai/skills/terraform/` tras la limpieza de skills redundantes.

Ambos son servidores **remotos/oficiales** — no requieren credenciales AWS
para consultarlos (son de solo documentación), y no ejecutan `terraform apply`
ni llaman a la API de AWS por sí mismos.

---

## Prerrequisitos

- Claude Code instalado y funcionando (`claude --version`).
- Node.js disponible si el servidor MCP se ejecuta vía `npx` (el servidor de
  AWS Documentation lo soporta).
- **Docker Desktop instalado y en ejecución** — el Terraform MCP Server
  oficial de HashiCorp se distribuye como imagen de contenedor
  (`docker.io/hashicorp/terraform-mcp-server`) y Claude Code lo arranca con
  `docker run`. Sin el daemon de Docker activo, el servidor queda registrado
  pero falla al conectar (`claude mcp list` lo muestra como
  `✘ Failed to connect — Connection closed`). Verificar con:

  ```bash
  docker info
  ```

  Si el comando falla, abrir Docker Desktop y esperar a que el daemon esté
  listo antes de invocar cualquier herramienta del MCP de Terraform.

---

## Instalación — AWS Documentation MCP Server

Ejecutar desde una terminal (Git Bash o PowerShell):

```bash
claude mcp add aws-documentation-mcp-server -- npx -y @aws/mcp-server-aws-documentation
```

Verificar que quedó registrado:

```bash
claude mcp list
```

Debe aparecer `aws-documentation-mcp-server` en la lista. Las herramientas
expuestas (`search_documentation`, `read_documentation`, `read_sections`,
`recommend`, `search_table`) quedan disponibles automáticamente en la próxima
sesión de Claude Code.

---

## Instalación — Terraform MCP Server

Requiere Docker Desktop en ejecución (ver Prerrequisitos). El servidor se
lanza como contenedor efímero por invocación:

```bash
claude mcp add terraform -- docker run -i --rm docker.io/hashicorp/terraform-mcp-server:1.0.0
```

Verificar:

```bash
claude mcp list
```

Debe aparecer `terraform: docker run -i --rm docker.io/hashicorp/terraform-mcp-server:1.0.0 - ✔ Connected`.
Si aparece `✘ Failed to connect`, la causa casi siempre es que Docker Desktop
no está corriendo — confirmar con `docker info` y reintentar.

> Si el tag de imagen (`1.0.0`) difiere en el momento de instalar, confirmar
> la versión actual en la documentación oficial del servidor MCP de
> Terraform antes de ejecutarlo — las imágenes MCP cambian de versión con
> cierta frecuencia mientras el ecosistema madura.

---

## Alcance por sesión

- Instalar ambos MCP en **Sesión 1** (fundamentos y preparación del entorno),
  junto con la configuración de AWS CLI — ver
  `ai/skills/aws/aws_cli.md` y `docs/student/03_temario.md`.
- A partir de **Sesión 2** (Terraform), el MCP de Terraform reemplaza la
  necesidad de una skill local de estilo/sintaxis genérica: usar el MCP para
  dudas de sintaxis, argumentos de recursos, diseño de módulos, o versiones
  de provider (nunca fijar un número de versión de memoria — consultarlo);
  usar `ai/skills/terraform/state_management.md` y `terraform_governance.md`
  para las convenciones y decisiones propias de este proyecto.

---

## Qué NO reemplazan estos MCP

- Decisiones de diseño específicas del curso (por ejemplo, HTTP API vs REST
  API en API Gateway, o cuándo usar Glue vs Lambda) — eso vive en
  `ai/skills/aws/*.md`.
- Políticas de gobernanza del proyecto (tags obligatorios, budgets, SPEC-009)
  — eso vive en `ai/skills/terraform/terraform_governance.md` y
  `ai/policies/global.md`.
- Ejecución de comandos reales (`terraform apply`, `aws <servicio> <acción>`)
  — los MCP de este curso son de solo documentación/consulta.

---

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `claude mcp list` no muestra el servidor recién agregado | Comando ejecutado en un directorio distinto o con alcance de proyecto en vez de global | Repetir `claude mcp add` con el flag de alcance deseado, o revisar `claude mcp add --help` |
| Timeout o error al invocar una herramienta del MCP | Sin conexión a internet, o `npx` no pudo descargar el paquete la primera vez | Verificar conectividad; volver a intentar la invocación (npx cachea el paquete tras la primera descarga) |
| `terraform` aparece como `✘ Failed to connect — Connection closed` en `claude mcp list` | Docker Desktop no está en ejecución — `docker run` no puede arrancar el contenedor del servidor | Abrir Docker Desktop, esperar a que `docker info` responda sin error, y volver a intentar (no requiere reinstalar el MCP) |
| El MCP no aparece como disponible dentro de una sesión ya abierta | Los MCP se cargan al iniciar la sesión | Cerrar y reabrir Claude Code después de instalar |

---

## Ver también

- `ai/domains/aws.md` — dominio AWS y su relación con el MCP de documentación
- `ai/domains/terraform.md` — dominio Terraform, incluye la nota de qué mecánica genérica se delega al MCP
- `ai/skills/aws/aws_cli.md` — configuración de credenciales AWS (independiente de estos MCP)
