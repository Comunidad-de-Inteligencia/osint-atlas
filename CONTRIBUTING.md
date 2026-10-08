# Contribuir a OSINT Atlas

Puedes mejorar una explicación, corregir una ficha o cubrir una carencia. Cada contribución debe permitir que otra persona compruebe el cambio.

## Preparar una propuesta

1. Busca la ficha y el escenario. Evita duplicar una fuente que ya existe.
2. Edita su archivo YAML en data/resources/. Conserva el identificador, incluso si cambia el nombre del servicio.
3. Cita la página responsable para cada corrección. Si no puedes verificar idioma, coste o acceso, conserva el estado desconocido.
4. Explica la entrada, los pasos, el resultado esperado, su interpretación y los límites.
5. Usa ejemplos ficticios sin personas identificables ni material sensible.
6. Abre una propuesta con el problema, el cambio observado y cómo comprobarlo.

Los procedimientos originales están en content/procedimientos/. Sus páginas de docs/procedimientos/ se generan. Usa referencias de contacto con la forma {{contact:identificador}}; los valores se mantienen en data/contacts.yaml.

La ficha va en data/resources/. El procedimiento va en content/procedimientos/. Una guía o una lista que no cabe en una ficha va en docs/referencias/. Una ficha nueva con maintenance_urls entra sola en el chequeo semanal.

## Revisar antes de entregar

~~~console
uv sync --locked
uv run python tools/build_catalog.py
uv run python tools/validate_docs.py
uv run python -m unittest discover -s tests -v
~~~

No edites a mano fichas generadas, índices o exportaciones. La generación no inventa explicaciones: usa el contenido original.

## Qué significa aprobar

Una observación del asistente no es una revisión humana. El estado verified exige referencia, fecha y persona registrada. La fecha de creación permanece separada.

Los cambios sensibles necesitan aprobación de otra persona competente sobre la versión actual de la propuesta. Mientras no exista esa persona, deben permanecer pendientes. El bot puede preparar incidencias; no puede aprobar ni fusionar esos cambios.

## Incorporar responsables

Añade el usuario real, tipo de cuenta, especialidades y permiso comprobado al registro de colaboradores. Para asignar revisiones se requiere acceso de escritura y comprobación reciente de permisos. Registra responsable y suplente por especialidad; no rellenes vacantes con nombres ficticios.

La incorporación de revisores y los cambios de política también requieren revisión. La primera incorporación necesita una decisión explícita del propietario que identifique a la persona competente; no se acepta que una propuesta se conceda capacidad de autoaprobarse.

## Accesibilidad y privacidad

Usa lenguaje sencillo, encabezados ordenados y enlaces descriptivos. Evita tablas extensas y explica cualquier diagrama con texto. Consulta la [guía de comprobación de accesibilidad](docs/ACCESIBILIDAD.md).

No añadas investigaciones reales, datos de víctimas, capturas sensibles ni URLs de casos. Para una incidencia del catálogo basta la página documental del organismo o plataforma.
