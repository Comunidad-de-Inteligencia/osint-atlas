# Contribuir a OSINT Atlas

## Qué puedes proponer

Puedes añadir una fuente, corregir una ficha, actualizar un contacto, retirar un recurso o mejorar una explicación. No incluyas investigaciones reales ni datos personales.

## Requisitos de una ficha

1. Identifica al responsable y la procedencia.
2. Explica finalidad, entradas, resultados, interpretación y límites.
3. Indica jurisdicción, escenarios, acceso y frecuencia de revisión.
4. Añade referencias oficiales para las afirmaciones críticas.
5. Usa lenguaje de incertidumbre cuando corresponda.

Edita `data/resources/core.yaml`, ejecuta el generador y revisa los documentos producidos:

```console
uv run python tools/build_catalog.py --report
uv run python tools/build_catalog.py --check
uv run python -m unittest discover -s tests -v
```

## Cambios sensibles

Los contactos, destinatarios de reporte, procedimientos de emergencia y criterios jurídicos necesitan revisión humana. La automatización puede detectar un cambio y preparar un informe, pero no sustituye el contenido aprobado.

## Revisión por especialidad

El registro `data/maintainers.yaml` define responsable y suplente para legislación, datos públicos, geolocalización, ciberseguridad, protección y documentación. Antes de exigir revisiones, asigna usuarios reales con permiso de escritura.

Los cambios críticos se escalan al suplente tras 48 horas; los ordinarios, tras siete días. Una persona distinta del autor debe revisar el contenido.

## Accesibilidad

Usa un único título H1, no saltes niveles de encabezado, escribe enlaces descriptivos y proporciona texto alternativo y una explicación equivalente para cualquier elemento visual.
