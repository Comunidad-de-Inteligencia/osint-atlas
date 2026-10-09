# Mantenimiento y revisión compartida

El mantenimiento comprueba documentación ya aceptada, guarda resultados y prepara propuestas. Puede seguir aunque falten revisores. Lo sensible permanece pendiente.

El mismo texto, en inglés, está en [maintenance](https://comunidad-de-inteligencia.github.io/osint-atlas/en/maintenance/).

## Qué hace cada proceso

- **Diario:** páginas de contactos, fuentes y procedimientos críticos, y revisiones editoriales que toca repetir.
- **Semanal:** el conjunto de fuentes y referencias aceptadas, incluidas las páginas de documentación de una API. API es Application Programming Interface, una interfaz para programas.
- **Mensual:** candidatos de seis catálogos de datos institucionales, el repositorio OSINT Brazuca y el canal institucional del Instituto Nacional de Ciberseguridad (INCIBE). OSINT quiere decir Open Source Intelligence, inteligencia de fuentes abiertas. Lee enlaces HTML y Markdown, y conserva la procedencia y las condiciones conocidas. HTML es HyperText Markup Language, el lenguaje de las páginas. Un enlace nuevo del mismo dominio también puede ser candidato.
- **En una propuesta:** validación de datos, documentos, índice y pruebas.

Las [últimas ejecuciones que salieron bien, y las incidencias](https://github.com/Comunidad-de-Inteligencia/osint-atlas/blob/maintenance-state/README.md), están en la rama de estado.

## Cómo leer un resultado técnico

- **ok / not-modified:** respuesta utilizable, o igual que la anterior.
- **blocked:** acceso bloqueado o redirección fuera de los destinos aceptados. No se supone que baste con crear una cuenta.
- **auth-required:** el servicio pidió autenticación.
- **rate-limited:** hay un límite de peticiones. Se respeta la espera indicada, dentro del tiempo disponible.
- **temporary-error:** fallo de red, certificado, tiempo máximo o servidor. Se abre incidencia tras tres ejecuciones seguidas que fallan.
- **offline:** respuesta de retirada o de ausencia. Pide revisión. No borra la fuente.
- **partial:** no se pudo leer el documento entero dentro de los límites. Una huella incompleta no se compara como si fuera completa.
- **redirected:** la documentación responde en otra dirección de los dominios aceptados. Hay que ver si el enlace debe corregirse.

Las peticiones tienen límite por dominio y reintentos cortos. Las respuestas no se ejecutan y no se adoptan como instrucciones. No se descargan avisos personales ni contenido de casos. Las fuentes sensibles tienen direcciones de mantenimiento documental propias.

El informe y cada ficha resumen la última comprobación con una palabra y, si existe, la fecha. La palabra sale del estado publicado. No se copia al archivo de la ficha.

- **disponible:** la página respondió (ok, redirected, not-modified o partial).
- **sin respuesta:** no hubo respuesta utilizable (offline, temporary-error, blocked, rate-limited o retired).
- **autenticación:** el servicio pidió identificarse (auth-required).
- **sin comprobación:** no hay una ejecución publicada para esa página, o el catálogo se generó sin el estado.

## Qué se guarda

La rama `maintenance-state` guarda el estado técnico y un informe legible. Conserva la última ejecución, huellas, cabeceras de caché, fallos seguidos e incidencias. El historial resumido dura noventa días. Los artefactos de Actions duran siete. No se guardan los cuerpos enteros de las páginas.

Un cambio del texto visible puede producir una propuesta editorial aunque la página responda. La propuesta enlaza la fuente y señala la huella anterior y la observada. Una persona tiene que mirar la diferencia. La automatización no le da un significado jurídico.

## Cómo se reparte

El registro `data/maintainers.yaml` guarda cuentas, especialidades, responsables, suplentes y permisos comprobados. Hay un coordinador. Las plazas especializadas siguen vacías.

Las incidencias se agrupan por especialidad y por finalidad, con una identidad estable. A las cuarenta y ocho horas, en lo crítico, o a los siete días, en lo ordinario, se elige al suplente. Si falta una persona competente, se muestra `missing-reviewer`. No se inventa una asignación.

En lo sensible, una persona competente distinta de quien escribió el cambio tiene que aprobar esa versión. Una cuenta de bot no sustituye a una persona. Una aprobación vieja no sirve si la propuesta cambió.

El control usa el registro de la rama base y consulta los permisos reales en GitHub. El proceso diario, cuando publica, vuelve a mirar las propuestas abiertas y pide revisión a quien corresponda, responsable o suplente. Después de una revisión también puede actualizarse con un comentario en la propuesta o con la ejecución manual de la revisión humana. No hace falta interpretar el texto del comentario.

## Cerrar una incidencia

Una recuperación cierra sola solo las incidencias técnicas que quedaron resueltas de forma explícita. Una propuesta editorial pide revisión.

Para registrar que un cambio de contenido ya se miró, una propuesta revisada añade a `data/resolutions.yaml` la clave de la incidencia, la huella comprobada y el enlace de la revisión. La comprobación siguiente resuelve solo esa huella. Si la página vuelve a cambiar, aparece otra observación en la misma propuesta agrupada.

Los candidatos siguen pendientes de selección y de revisión. No entran solos. Cerrar una incidencia editorial es una decisión humana, no una comprobación técnica.

## Activación y gasto

Los tres procesos se pueden lanzar a mano. El parámetro `publish` está apagado por defecto: el ensayo deja artefactos; al activarlo publica el estado técnico y las propuestas. Lanza los ensayos uno detrás de otro. Comparten una cola para no pisar el historial, y GitHub puede sustituir una ejecución que aún espera.

Antes de encender una agenda hay que mirar los ensayos, la duración, las cuotas y el límite de gasto. Que falten especialistas no impide las comprobaciones técnicas. Si no se confirma el control del gasto, las agendas siguen siendo manuales.

GitHub rechazó proteger la rama privada porque el plan no lo incluye. La consulta de facturación no dio bastante información. No se ha cambiado la suscripción y no se han activado las agendas. Sin esa protección, el estado de revisión avisa, y no impide que una cuenta administradora incorpore un cambio a mano.

La fecha de la última ejecución importa: una agenda de GitHub puede retrasarse. El MCP marca como atrasado un proceso diario sin éxito durante cuarenta y ocho horas, uno semanal durante diez días y uno mensual durante cuarenta. Si no corre ningún proceso, no puede crear un aviso nuevo por sí mismo. El informe y el MCP permiten ver esa ausencia.

## Ensayos locales

Desde la raíz, con las dependencias instaladas:

~~~console
uv run python tools/check_links.py --scope critical --output reports/daily.json
uv run python tools/check_reviews.py
uv run python tools/check_links.py --scope all --state reports/state.json --output reports/weekly.json
uv run python tools/discover_candidates.py --state reports/state.json
~~~

Estas operaciones no envían reportes a autoridades ni a plataformas.
