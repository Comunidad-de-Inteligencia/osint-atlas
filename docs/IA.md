# Usar OSINT Atlas con IA

## Qué puede hacer el conector

El MCP local permite buscar fichas, jurisdicciones, procedimientos, documentación y rutas oficiales de asistencia. Devuelve referencias, cobertura y revisión. No visita las fuentes al responder una consulta, no vigila canales y no envía reportes.

## Instalación

Necesitas Python 3.12, Git y uv. Clona el repositorio privado usando tus permisos habituales. En su raíz:

~~~console
uv sync --locked
uv run python tools/build_catalog.py --check
uv run osint-atlas-mcp
~~~

Configura el cliente MCP para ejecutar uv con los argumentos --directory, la ruta absoluta del repositorio, run, --locked y osint-atlas-mcp. El transporte es stdio: entrada y salida estándar. Los mensajes de diagnóstico utilizan la salida de errores.

## Sincronización en una copia dedicada

La sincronización está desactivada por defecto. Para habilitarla en una copia exclusiva del conector, configura en el cliente la variable OSINT_ATLAS_DEDICATED con valor 1.

El lanzador sincroniza antes de cargar el servidor. Solo admite el remoto de P3M-ACTF/osint-atlas y avances compatibles con main. Prepara una instantánea separada, instala las dependencias fijadas y valida los datos antes de iniciarla en otro proceso. No fusiona conflictos ni sobrescribe tus cambios.

Ante falta de Git, red, permisos, dependencias o validación, conserva la última instantánea utilizable. La antigüedad procede del commit, no de la fecha de copia de los archivos. Si no puede conocerse, se devuelve null.

## Herramientas disponibles

- search_resources: texto, territorio, categoría, escenario, acceso, input_type, output_type y platform.
- get_resource: ficha completa, referencias, revisión y cobertura.
- get_jurisdiction: particularidades territoriales, total de recursos y página de resultados.
- search_playbooks y get_playbook: búsqueda y lectura de procedimientos.
- search_docs y get_doc: búsqueda y lectura de toda la documentación de consulta.
- list_scenarios: cobertura y carencias, por territorio o para toda la matriz.
- get_reporting_routes: vías filtradas por escenario, territorio, plataforma y clase de actuación.

Las búsquedas utilizan limit y offset. Devuelven count, total y next_offset. Los filtros se aplican antes de paginar. Una consulta vacía lista elementos; una consulta formada únicamente por puntuación devuelve invalid_query. Un territorio o filtro desconocido devuelve unknown_filter.

Se aceptan identificadores territoriales y nombres del catálogo, sin distinguir mayúsculas ni acentos. Los nombres de escenarios y tipos siguen la taxonomía del proyecto.

## Ejemplos

~~~json
{"query":"","jurisdiction":"España","scenario":"procurement","limit":5,"offset":0}
~~~

El resultado ofrece hasta cinco fichas y el total que cumple los filtros. Si next_offset contiene un número, úsalo para obtener la siguiente página.

~~~json
{"scenario":"platform-report","jurisdiction":"ES","platform":"telegram","kind":"platform-report"}
~~~

Esta consulta recupera información sobre el canal de la plataforma. No envía comunicaciones ni equivale a una denuncia.

get_doc acepta identificadores como empezar, mantenimiento, ia, business y fuentes/de-handelsregister. search_docs devuelve los identificadores disponibles.

## Cómo debe responder un asistente

Cita la fuente responsable y conserva las limitaciones. Explica qué revisión falta y distingue evidencia, observación e inferencia. En escenarios sensibles, mantén expresiones como «posible» o «no confirmado».

Los resultados separan versión del catálogo, estado del índice, antigüedad del commit y mantenimiento. Un índice desactualizado se reconstruye de forma atómica; si el nuevo contenido es inválido, el estado last-valid-snapshot identifica la copia anterior utilizada.

Las mediciones técnicas locales se leen desde .cache/maintenance-state/state.json. Sin una copia del estado se indica unknown, nunca una ejecución satisfactoria inventada.
