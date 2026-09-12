# Usar OSINT Atlas con IA

## Qué puede hacer el conector

El servidor MCP local permite buscar fichas, jurisdicciones, procedimientos, documentación y rutas oficiales de asistencia. Devuelve referencias y fechas de revisión. No visita las fuentes externas, no vigila canales y no envía reportes.

## Instalación

Necesitas `uv` y Python 3.12. Desde la raíz del repositorio:

```console
uv sync
uv run python tools/build_catalog.py --check
```

Clona el repositorio en una carpeta dedicada para el MCP y configura tu cliente para ejecutar:

```text
uv --directory RUTA_ABSOLUTA_A_OSINT_ATLAS run osint-atlas-mcp
```

En Windows, usa una ruta absoluta con barras `/` o barras invertidas escapadas según el formato de configuración del cliente.

## Herramientas disponibles

| Herramienta | Uso |
|---|---|
| `search_resources` | Buscar fuentes por texto, territorio, categoría o escenario |
| `get_resource` | Abrir una ficha completa |
| `get_jurisdiction` | Consultar particularidades territoriales |
| `search_playbooks` | Buscar procedimientos |
| `get_playbook` | Recuperar un procedimiento completo |
| `search_docs` | Buscar explicaciones |
| `get_doc` | Abrir una guía por identificador |
| `list_scenarios` | Mostrar cobertura y lagunas |
| `get_reporting_routes` | Recuperar vías oficiales sin enviar comunicaciones |

## Consultas de ejemplo

- “Busca fuentes oficiales para comprobar una empresa española.”
- “Abre el procedimiento de desaparición de menor.”
- “¿Qué cobertura existe para contratos en Portugal?”
- “Recupera las rutas de ayuda para violencia sexual digital en España.”

## Cómo debe responder un asistente

- Citar la ficha y enlazar la fuente original.
- Mostrar fecha de revisión y limitaciones.
- Mantener expresiones como “posible”, “indicio” o “no confirmado”.
- Distinguir asistencia, retirada, reporte, emergencia y denuncia.
- Confirmar contactos críticos en la web oficial antes de utilizarlos.
- No determinar por sí mismo que una persona ha cometido un delito.

## Actualización local

Al arrancar, el MCP intenta actualizar esa copia solo si está limpia y puede avanzar hasta la rama remota sin crear una fusión. Si hay cambios locales, historias divergentes o un fallo de red, conserva la versión disponible. El resultado indica la versión y la antigüedad de las fuentes. El índice se reconstruye si no coincide con el catálogo. El proceso no resuelve conflictos ni edita fichas.
