# Mantenimiento y revisión compartida

El mantenimiento comprueba documentación aprobada, conserva resultados y prepara propuestas. Su ejecución puede continuar aunque falten revisores; los cambios sensibles permanecen pendientes.

## Qué hace cada proceso

- **Diario:** páginas de contactos, fuentes y procedimientos críticos; revisiones editoriales pendientes.
- **Semanal:** el conjunto de fuentes y referencias aprobadas, incluidas páginas de documentación de API.
- **Mensual:** candidatos de seis catálogos de datos institucionales, el repositorio OSINT Brazuca y el canal institucional de INCIBE. Lee enlaces HTML y Markdown, conserva procedencia y condiciones conocidas. Un enlace nuevo del mismo dominio también puede ser candidato.
- **En propuestas de cambio:** validación de datos, documentos, índice y pruebas.

[Últimas ejecuciones satisfactorias e incidencias](https://github.com/P3M-ACTF/osint-atlas/blob/maintenance-state/README.md).

## Cómo interpretar un resultado técnico

- **ok / not-modified:** respuesta utilizable o sin cambios respecto a la anterior.
- **blocked:** acceso bloqueado o redirección fuera de los destinos aprobados. No presupone que baste crear una cuenta.
- **auth-required:** el servicio ha solicitado autenticación.
- **rate-limited:** hay un límite de peticiones. Se respeta la espera indicada dentro del tiempo disponible.
- **temporary-error:** fallo de red, certificado, tiempo máximo o servidor. Se abre incidencia tras tres ejecuciones consecutivas fallidas.
- **offline:** respuesta de retirada o ausencia; requiere revisión, no elimina la fuente.
- **partial:** no se pudo analizar el documento completo dentro de los límites. No se compara una huella incompleta como si fuera completa.
- **redirected:** la documentación responde en otra dirección de los dominios aprobados; revisar si debe corregirse el enlace.

Las peticiones usan límites por dominio y reintentos moderados. Las respuestas no se ejecutan ni se adoptan como instrucciones. No se descargan avisos personales ni contenido de casos: las fuentes sensibles tienen direcciones de mantenimiento documental específicas.

El informe y cada ficha resumen la última comprobación con una palabra y una fecha. La palabra sale del estado publicado. No se copia al YAML.

- **disponible:** la página respondió (ok, redirected, not-modified o partial).
- **sin respuesta:** no hubo respuesta utilizable (offline, temporary-error, blocked, rate-limited o retired).
- **autenticación:** el servicio pidió identificarse (auth-required).
- **sin comprobación:** no hay una ejecución publicada para esa página, o el catálogo se generó sin el estado.

## Qué se conserva

La rama separada maintenance-state contiene estado técnico e informe legible. Guarda última ejecución, huellas, cabeceras de caché, fallos consecutivos e incidencias. El historial resumido dura 90 días; los artefactos de Actions, siete. No conserva cuerpos completos de páginas.

Un cambio del texto visible puede producir una propuesta editorial aunque la página responda correctamente. La propuesta enlaza la fuente e identifica las huellas anterior y observada; una persona deberá comprobar la diferencia. La automatización no atribuye significado jurídico al cambio.

## Reparto del trabajo

El registro data/maintainers.yaml conserva personas, especialidades, responsables, suplentes y permisos comprobados. P3M-ACTF es coordinador; las plazas especializadas siguen vacantes.

Las incidencias se agrupan por especialidad y finalidad, con identidad estable. Al transcurrir 48 horas para propuestas críticas o siete días para ordinarias se selecciona al suplente. Si falta una persona competente, se muestra missing-reviewer; no se inventa una asignación.

Para cambios sensibles, una persona competente distinta de la autoría humana debe aprobar la versión concreta propuesta. Una cuenta de bot no sustituye a la autoría humana. Las aprobaciones antiguas no sirven tras cambiar la propuesta.

El control usa el registro de la rama base y consulta los permisos reales en GitHub. El proceso diario con publicación vuelve a comprobar las propuestas abiertas y solicita revisión al responsable o suplente elegible. Tras una revisión también puede actualizarse mediante un comentario en la propuesta o la ejecución manual de Revisión humana; no necesita interpretar el texto del comentario.

## Resolver incidencias

Una recuperación cierra automáticamente solo incidencias técnicas explícitamente resueltas. Una propuesta editorial requiere revisión.

Para registrar una resolución de cambio de contenido, una propuesta revisada añade a data/resolutions.yaml la clave de incidencia, la huella comprobada y el enlace de revisión. La siguiente comprobación resolverá únicamente esa huella. Si la página vuelve a cambiar, aparece otra observación en la misma propuesta agrupada.

Los candidatos siguen pendientes de selección y revisión; no se incorporan automáticamente. Cerrar una incidencia editorial indica una decisión humana, no una comprobación técnica.

## Activación y gasto

Los tres procesos permiten ejecución manual. El parámetro publish está desactivado por defecto: el ensayo produce artefactos; al activarlo publica estado técnico y propuestas. Ejecuta los ensayos uno después de otro: comparten una cola para no sobrescribir el historial y GitHub puede sustituir una ejecución que aún esté esperando.

Antes de habilitar una agenda hay que verificar los ensayos, duración, cuotas y límite de gasto. La falta de especialistas no impide activar las comprobaciones técnicas. Si no se confirma el control del gasto, las agendas permanecen manuales.

En la comprobación del 13 de septiembre de 2026, GitHub rechazó la protección de la rama privada por requerir un plan superior. La consulta de facturación no proporcionó información suficiente. No se ha cambiado la suscripción ni se han activado agendas. Sin protección disponible, el estado de revisión avisa pero no impide que una cuenta administradora fuerce una incorporación manual.

La fecha de última ejecución importa: una agenda de GitHub puede retrasarse. El MCP marca como atrasado un proceso diario sin éxito durante 48 horas, uno semanal durante diez días y uno mensual durante cuarenta. Si ningún proceso se ejecuta, no puede generar un aviso nuevo por sí mismo; el informe y el MCP permiten detectar esa ausencia.

## Ensayos locales

Desde la raíz del repositorio, con dependencias instaladas, los comandos de comprobación son:

~~~console
uv run python tools/check_links.py --scope critical --output reports/daily.json
uv run python tools/check_reviews.py
uv run python tools/check_links.py --scope all --state reports/state.json --output reports/weekly.json
uv run python tools/discover_candidates.py --state reports/state.json
~~~

Estas operaciones no envían reportes a autoridades ni plataformas.
