# Contribuir

Puedes mejorar una explicación, corregir una ficha o cubrir un hueco. Otra persona tiene que poder comprobar el cambio. Patrocinar no compra una ficha ni una revisión. No pegues casos ni datos de personas.

El mismo recorrido, en inglés, está en [How to contribute](https://comunidad-de-inteligencia.github.io/osint-atlas/en/contributing/).

## Preparar un cambio

1. Busca la ficha y el escenario. No dupliques una fuente que ya existe.
2. Edita su archivo en `data/resources/`. Conserva el identificador, aunque cambie el nombre del servicio.
3. Cita la página responsable de cada corrección. Si no puedes comprobar el idioma, el coste o el acceso, déjalo como desconocido.
4. Explica la entrada, los pasos, el resultado esperado, cómo leerlo y los límites.
5. Usa ejemplos ficticios, sin una persona identificable y sin material sensible.
6. Abre una propuesta con el problema, el cambio observado y cómo comprobarlo.

Los procedimientos originales están en `content/procedimientos/`. Las páginas de `docs/es/procedimientos/` se generan. Una referencia de contacto se escribe `{{contact:identificador}}`. El valor vive en `data/contacts.yaml`.

La ficha va en `data/resources/`. El procedimiento va en `content/procedimientos/`. Una guía o una lista que no cabe en una ficha va en `docs/es/referencias/`. Una ficha nueva con `maintenance_urls` entra sola en la comprobación semanal de enlaces.

Las preguntas, las ideas de traducción y los métodos van a Discussions. Un cambio de ficha o de procedimiento es una incidencia, con el formulario en castellano o en inglés. No pegues casos, datos de personas ni texto de un manual de pago.

## Antes de abrir la propuesta

~~~console
uv sync --locked
uv run python tools/build_catalog.py
uv run python tools/validate_docs.py
uv run python -m unittest discover -s tests -v
~~~

No edites a mano las fichas generadas, los índices ni las exportaciones. El generador no inventa explicaciones. Usa el contenido original.

Para ver la guía: `uv sync --locked --group docs` y `uv run mkdocs serve`.

Si cambias un texto que tiene par en inglés, actualiza el otro archivo y la huella en `docs/i18n-pares.yaml` en el mismo cambio. La validación no traduce.

## Qué significa aprobar

Una observación de un asistente no es una revisión humana. El estado `verified` pide una referencia, la fecha en que se comprobó y una persona registrada en los datos. Esa fecha es la excepción: la página puede mostrarla. El identificador de quien revisa no se imprime. Una ficha nueva no enseña fecha de alta. El campo `created_at` sigue en los datos porque el generador lo usa por dentro.

Lo sensible necesita la aprobación de otra persona competente sobre la versión actual de la propuesta. Mientras esa persona no exista, la propuesta sigue pendiente. Un bot puede preparar incidencias. No puede aprobar ni fusionar esos cambios.

## Añadir quien revisa

Añade la cuenta real, el tipo de cuenta, las especialidades y un permiso comprobado al registro de mantenimiento. Asignar revisiones pide acceso de escritura y una comprobación reciente del permiso. Anota un responsable y un suplente por especialidad. No rellenes un hueco con un nombre inventado.

Añadir revisores y cambiar la política también se revisa. La primera incorporación necesita una decisión explícita de quien administra el repositorio, nombrando a la persona competente. Una propuesta no puede darse a sí misma el poder de aprobarse.

## Accesibilidad y privacidad

Usa un lenguaje que se pueda leer en voz alta, encabezados en orden y enlaces que digan a dónde van. Evita tablas grandes y explica cualquier esquema con texto. Las comprobaciones están en [accesibilidad](accesibilidad.md).

La primera vez que uses una sigla, escribe el nombre completo y después la sigla.

No añadas investigaciones reales, datos de víctimas, capturas sensibles ni direcciones de un caso. Para una incidencia del catálogo basta la página de documentación del organismo o de la plataforma.
