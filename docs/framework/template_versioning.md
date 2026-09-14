# Versionado de la plantilla y actualizaciones del host

Esta guía explica cómo el instalador detecta si un repositorio host necesita
actualizarse, cómo se clasifica la divergencia, y cuándo subir la versión del
framework.

## Cómo funciona la detección de divergencia

Cada instalación escribe un archivo `.framework-version.json` en la raíz del
repositorio host. Registra la versión de la plantilla, el conjunto de
capacidades instaladas, y **huellas de contenido** (fingerprints) de cada
archivo propiedad del framework:

```json
{
  "framework_version": "0.2.0",
  "installed_at": "...",
  "include_structure": false,
  "tree_digest": "a3f8…",
  "framework_manifest": {
    "AGENTS.md":              {"sha256": "b1c2…", "ownership": "managed"},
    "ai/policies/global.md":  {"sha256": "d4e5…", "ownership": "managed"},
    "…": {}
  }
}
```

`tree_digest` es un hash agregado de todo el árbol propiedad del framework
(todos los valores `sha256`, ordenados por ruta). Cuando ejecutas el
instalador contra un host ya instalado, `update_template` lo usa como filtro
rápido:

```python
if template_tree_digest == state["tree_digest"] and not locally_modified:
    return {"up_to_date": True, ...}
```

Si el árbol coincide **y** ningún archivo del host fue modificado localmente,
la actualización se omite de inmediato sin leer cada archivo.

### Clasificación de tres vías

Cuando el árbol cambió (o se pasa `--force`), cada archivo propiedad del
framework se clasifica comparando tres hashes:

| Archivo host vs hash de estado | Plantilla vs hash de estado | Clasificación | Acción |
|---|---|---|---|
| igual | igual | `unchanged` | nada |
| igual | distinto | `updatable` | sobrescribir |
| distinto | igual | `locally-modified` | conservar + advertir |
| distinto | distinto | `conflict` | conservar + advertir |
| falta | — | `missing` | volver a copiar |

`--force` omite la clasificación y sobrescribe todos los archivos `managed`.

### Propiedad (ownership)

Cada entrada del manifiesto lleva un valor `ownership`:

| Valor | Significado |
|---|---|
| `managed` | El framework es dueño de este archivo; se sobrescribe en cada actualización. |
| `append-only` | Se copia una sola vez en la primera instalación; en actualizaciones posteriores solo se fusionan las entradas faltantes. Actualmente no hay archivos registrados en esta categoría. |

`src/`, `infra/`, `tests/`, y `specs/project/` son **propiedad del host** y
nunca aparecen en el manifiesto — el instalador nunca los toca.

## Rol de `framework_version`

`framework_version` es una **etiqueta de gobernanza** (changelog, ancla de
cambios disruptivos), no un detector de sincronización. Cambiar archivos en
la plantilla sin subir la versión **igual se propagará** al host — el
detector de divergencia es el hash del árbol y los hashes por archivo, no la
cadena de versión.

Usa `framework_version` para:

- Comunicar qué versión está corriendo un host (p. ej. `0.2.0`).
- Anclar cambios disruptivos que requieren una reinstalación forzada.
- Construir un changelog entre releases.

## Soluciones alternativas

### `--force`: omitir la clasificación

Pasa `--force` para sobrescribir todos los archivos `managed`/`generated` sin
importar su clasificación:

```powershell
python install_windows.py --target <ruta-al-host> --force
```

Usa `--dry-run --force` primero para previsualizar qué se escribiría:

```powershell
python install_windows.py --target <ruta-al-host> --force --dry-run
```

### Manejar `locally-modified` / `conflict`

Si la actualización reporta archivos modificados localmente o en conflicto,
revisa las diferencias manualmente y luego vuelve a ejecutar con `--force`
para aceptar la versión de la plantilla, o conserva tus cambios tal cual.

## Cuándo subir la versión

Sube la versión en el archivo `VERSION` cuando:

- Quieras un rastro de auditoría claro de qué generación está corriendo un
  host.
- Estés introduciendo un cambio disruptivo que requiera volver a ejecutar el
  instalador.
- La automatización de CI/CD necesite reportar la generación en ejecución.

Los incrementos de versión siguen [Semantic Versioning](https://semver.org/):

| Tipo de cambio | Ejemplo de incremento |
|---|---|
| Patch — corrección menor o actualización de contenido | `0.1.0` → `0.1.1` |
| Minor — nueva capacidad o archivo agregado | `0.1.0` → `0.2.0` |
| Major — cambio disruptivo en la estructura | `0.1.0` → `1.0.0` |

Después de subir la versión, ejecuta el instalador normalmente — el detector
de divergencia encontrará los archivos cambiados de todas formas:

```powershell
python install_windows.py --target <ruta-al-host>
```

## Referencia rápida

| Objetivo | Comando |
|---|---|
| Actualizar host (diff inteligente) | `python install_windows.py --target <ruta>` |
| Forzar sobrescritura de todos los archivos del framework | `python install_windows.py --target <ruta> --force` |
| Previsualizar actualización (sin escribir) | `python install_windows.py --target <ruta> --dry-run` |
| Previsualizar actualización forzada | `python install_windows.py --target <ruta> --force --dry-run` |
| Comprobar la versión actual de la plantilla | `cat VERSION` |
| Comprobar la versión instalada en el host | `cat <host>/.framework-version.json` |

## Referencia de arquitectura

El mecanismo de huellas (fingerprints) está especificado en
[`specs/rework/ADR-FW-003.md`](../../../specs/rework/ADR-FW-003.md) y
analizado en
[`specs/rework/SPEC-FW-016.md`](../../../specs/rework/SPEC-FW-016.md).
