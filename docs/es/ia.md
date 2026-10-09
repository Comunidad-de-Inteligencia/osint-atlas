# Usar el catálogo con un asistente

## Qué puede hacer el conector

El Model Context Protocol (MCP) local permite buscar fichas, territorios, procedimientos, documentación y vías oficiales de asistencia. Devuelve referencias, cobertura y revisión. No visita las fuentes al responder, no vigila canales y no envía reportes.

## Instalación

Hacen falta Python 3.12, Git y uv. Clona el repositorio con tus permisos habituales. En la raíz:

~~~console
uv sync --locked
uv run python tools/build_catalog.py --check
uv run osint-atlas-mcp
~~~

Configura el cliente MCP para ejecutar `uv` con los argumentos `--directory`, la ruta absoluta del repositorio, `run`, `--locked` y `osint-atlas-mcp`. El transporte es stdio, standard input and output, la entrada y la salida estándar. Los avisos de diagnóstico salen por la salida de errores.

## Sincronizar una copia dedicada

La sincronización está apagada por defecto. Para encenderla en una copia que solo usa el conector, define en el cliente la variable `OSINT_ATLAS_DEDICATED` con valor `1`.

El lanzador sincroniza antes de cargar el servidor. Solo admite el remoto de este repositorio, también si la dirección anterior sigue apuntando al mismo proyecto, y solo avances compatibles con `main`. Prepara una instantánea aparte, instala las dependencias fijadas y valida los datos antes de arrancar en otro proceso. No fusiona conflictos y no pisa tus cambios.

Si falta Git, red, permiso, una dependencia o la validación, se queda con la última instantánea que servía. La antigüedad sale del commit, no de la fecha en que se copiaron los archivos. Si no se puede saber, el valor es nulo.

## Herramientas

- `search_resources`: texto, territorio, categoría, escenario, acceso, `input_type`, `output_type` y `platform`.
- `get_resource`: ficha, referencias, revisión y cobertura.
- `get_jurisdiction`: notas del territorio, total de fichas y una página de resultados.
- `search_playbooks` y `get_playbook`: buscar y leer procedimientos.
- `search_docs` y `get_doc`: buscar y leer la documentación de consulta.
- `list_scenarios`: cobertura y carencias, de un territorio o de toda la matriz.
- `get_reporting_routes`: vías filtradas por escenario, territorio, plataforma y clase de actuación.

Las búsquedas usan `limit` y `offset`. Devuelven `count`, `total` y `next_offset`. Los filtros se aplican antes de paginar. Una consulta vacía lista elementos. Una consulta que solo tiene puntuación devuelve `invalid_query`. Un territorio o un filtro desconocido devuelve `unknown_filter`.

Se aceptan identificadores y nombres del catálogo, sin distinguir mayúsculas ni acentos. Los nombres de escenario y de tipo siguen la taxonomía del proyecto.

## Ejemplos

~~~json
{"query":"","jurisdiction":"España","scenario":"procurement","limit":5,"offset":0}
~~~

El resultado ofrece hasta cinco fichas y el total que cumple los filtros. Si `next_offset` trae un número, úsalo para la página siguiente.

~~~json
{"scenario":"platform-report","jurisdiction":"ES","platform":"telegram","kind":"platform-report"}
~~~

Esta consulta describe el canal de la plataforma. No envía nada y no es una denuncia.

`get_doc` acepta identificadores como `empezar`, `mantenimiento`, `ia`, `business` y `es/empresas/de-handelsregister`. `search_docs` devuelve los identificadores que hay.

## Cómo debe responder un asistente

Cita la fuente responsable y conserva los límites. Di qué revisión falta y separa evidencia, observación e inferencia. En lo sensible, mantén fórmulas como «posible» o «no confirmado».

Los resultados separan la versión del catálogo, el estado del índice, la antigüedad del commit y el mantenimiento. Un índice viejo se reconstruye de forma atómica. Si el contenido nuevo no vale, el estado `last-valid-snapshot` señala la copia anterior.

Las mediciones técnicas locales se leen en `.cache/maintenance-state/state.json`. La copia dedicada intenta recuperar ese archivo de la rama `maintenance-state`. Sin una copia del estado se indica desconocido, nunca una ejecución que no ocurrió.

El mismo texto, en inglés, está en [using an assistant](https://comunidad-de-inteligencia.github.io/osint-atlas/en/ai/).
