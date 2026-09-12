# Mantenimiento compartido

Esta guía explica qué hace la automatización, qué necesita una persona revisora y cómo activar las agendas sin convertir el catálogo en una fuente de cambios sin control.

## Qué se comprueba

| Frecuencia prevista | Alcance | Resultado |
|---|---|---|
| En cada propuesta | Datos, documentos, enlaces internos, índice y pruebas | Aceptación o error comprobable |
| Diaria | Recursos críticos y revisiones vencidas | Informe agrupado y, si hace falta, incidencia |
| Semanal | Resto de recursos aprobados | Estado técnico, redirecciones y cambios que revisar |
| Mensual | Catálogos institucionales aprobados | Lista de candidatos, nunca altas automáticas |

Los informes distinguen disponibilidad técnica de revisión editorial. Un error temporal, un bloqueo 403 o un límite 429 no retiran una fuente. Un cambio de teléfono, destinatario o procedimiento siempre requiere revisión humana.

## Estado inicial de las agendas

Los tres flujos periódicos incluyen ejecución manual y la expresión de su agenda está comentada. Esta decisión permite comprobar primero tiempos, cuotas, gasto, permisos e incidencias generadas.

Para activarlos:

1. Asigna responsable y suplente reales en `data/maintainers.yaml`.
2. Comprueba que esas personas tienen acceso al repositorio privado.
3. Ejecuta manualmente `Mantenimiento diario`, `Mantenimiento semanal` y `Descubrimiento mensual`.
4. Revisa artefactos, duración y consumo en GitHub Actions.
5. Descomenta `schedule` en cada flujo y abre una propuesta de cambio.

La hora de creación de cada informe demuestra cuándo terminó una comprobación. Las ejecuciones programadas de GitHub pueden retrasarse, por lo que nunca debe deducirse actualidad solo de la agenda configurada.

## Reparto de revisiones

`data/maintainers.yaml` es el registro principal. Define seis especialidades, un responsable y un suplente. Las propuestas críticas pasan al suplente tras 48 horas sin respuesta; las ordinarias, tras siete días. El autor no puede ser la única persona que apruebe su cambio.

Cuando el plan de GitHub lo permita, copia `.github/CODEOWNERS.example` a `.github/CODEOWNERS` y sustituye todos los marcadores por usuarios reales. El registro del proyecto sigue siendo la referencia aunque CODEOWNERS no esté disponible.

## Qué puede cambiar automáticamente

La automatización puede producir fechas de comprobación, códigos de estado, huellas parciales, informes y documentos derivados de contenido aprobado. No modifica por sí sola explicaciones, cobertura, condiciones, contactos, destinatarios ni procedimientos.

Las respuestas externas se leen como datos. Los comprobadores limitan el cuerpo leído, el número de procesos, el tiempo por petición y la frecuencia por dominio. No ejecutan código ni instrucciones encontradas en una web.

## Cómo se agrupan los avisos

Cada incidencia usa una huella estable de los elementos que requieren acción. Las marcas de tiempo y la duración de una petición no crean duplicados. Un problema ya abierto no vuelve a publicarse hasta que cambie el conjunto material de elementos afectados.
