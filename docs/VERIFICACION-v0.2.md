# Verificación de v0.2

## Estado de la entrega

La implementación está en la [propuesta v0.2](https://github.com/P3M-ACTF/osint-atlas/pull/1), en borrador y sin fusionar. Se conservan 84 recursos, 16 procedimientos y 14 jurisdicciones. La rama principal y la versión publicada siguen siendo v0.1.

Las fichas tienen campos explícitos para lo desconocido y para la revisión pendiente. Una observación del asistente no cuenta como aprobación humana. Quedan por contrastar condiciones concretas de numerosos servicios; no se presentan como revisados los 84 recursos.

## Datos, documentación y consultas

El 13 de septiembre de 2026 pasaron **51 pruebas** locales con Python 3.12 y la [validación en GitHub sobre Linux](https://github.com/P3M-ACTF/osint-atlas/actions/runs/34752875916). La [validación de la propuesta](https://github.com/P3M-ACTF/osint-atlas/pull/1/checks) permite comprobar los cambios posteriores.

Las pruebas cubren esquemas y referencias, más de 16 procedimientos, ausencia de contactos inventados, filtros antes de paginar, puntuación, territorios desconocidos y documentación consultable. Una conexión MCP real mediante stdio recorre las nueve herramientas y los 16 procedimientos.

La reconstrucción comprueba documentos y SQLite reproducibles, orden de archivos compatible entre Windows y Linux, cambios de versión al modificar documentación y conservación del índice válido si falla una reconstrucción. Se simulan falta de Git, tiempo máximo, cambios locales e historia divergente.

La matriz distingue apoyo global y preparación local. Exige revisiones vigentes, procedimiento territorial, responsable y canales competentes cuando corresponda. Las carencias actuales siguen visibles; contar enlaces no convierte un escenario en desarrollado.

## Mantenimiento publicado

Los ensayos manuales guardaron resultados en la [rama de mantenimiento](https://github.com/P3M-ACTF/osint-atlas/blob/maintenance-state/README.md). Su árbol contiene exclusivamente el informe y el estado técnico; las fichas originales no se modificaron.

| Proceso | Resultado observado | Evidencia |
|---|---|---|
| Diario | 32 páginas; propuestas editoriales agrupadas | [Ejecución diaria](https://github.com/P3M-ACTF/osint-atlas/actions/runs/34736110752) |
| Semanal | 85 páginas; conserva el historial diario | [Ejecución semanal](https://github.com/P3M-ACTF/osint-atlas/actions/runs/34736215403) |
| Mensual | 88 candidatos de ocho fuentes seleccionadas; sin errores en la recuperación | [Ejecución mensual satisfactoria](https://github.com/P3M-ACTF/osint-atlas/actions/runs/34752878833) |

Un ensayo mensual anterior agotó el tiempo de espera de INCIBE. El [fallo y su publicación](https://github.com/P3M-ACTF/osint-atlas/actions/runs/34736360622) quedaron registrados. La siguiente ejecución conservó ese intento, marcó recuperada la incidencia técnica y registró una nueva fecha satisfactoria.

El historial observado contiene cuatro intentos: diario, semanal, mensual fallido y mensual recuperado. Una ejecución satisfactoria significa que el proceso terminó; sigue habiendo páginas bloqueadas, ausentes o que superan los límites de análisis.

Se volvió a publicar exactamente el mismo informe: las 15 incidencias existentes conservaron sus identificadores, estado y fecha de actualización. No aparecieron duplicados. Los candidatos se acumulan para selección humana y no se suman automáticamente a los 84 recursos del catálogo.

Las simulaciones incluyen respuestas 304, 403 y 429, fallos persistentes, recuperación y cambio de un contacto en el pie de una página con respuesta 200. Las propuestas editoriales no se cierran por recuperación técnica. La asignación de una dirección compartida se comprueba entre procesos diarios y semanales.

## Revisión independiente

Solo está registrado P3M-ACTF como coordinador. Las especialidades y suplencias están vacantes. Las propuestas sensibles permanecen pendientes y no se asignan a personas inventadas.

Las pruebas comprueban suplencias a las 48 horas y a los siete días, ausencia de revisor, exclusión de bots y de la autoría, aprobación de la versión concreta y rechazo de aprobaciones antiguas. El estado de revisión se ha publicado como pendiente en la propuesta. La asignación con colaboradores reales queda pendiente de incorporar a esas personas y verificar su competencia y permisos.

La protección de la rama privada no está disponible con el plan observado: GitHub respondió que requiere un plan superior. El aviso de revisión no impide técnicamente una fusión manual por una cuenta administradora.

## Lectura y accesibilidad

Se validaron estructura, enlaces internos y anclas de 154 documentos. También se revisó una representación local del Markdown en Microsoft Edge: README, catálogo, índice de España, ficha de Handelsregister y procedimiento de posible abuso sexual infantil.

Las cinco páginas se comprobaron a 1280, 640 y 320 píxeles de ancho: 15 combinaciones sin desbordamiento horizontal ni enlaces sin texto. Se inspeccionaron visualmente capturas de README, ficha y procedimiento en vista estrecha. En el recorrido probado, Tab mostró foco visible y Enter abrió el procedimiento de emergencia. El aumento local de texto a 32 y 64 píxeles mantuvo la adaptación.

Estas comprobaciones usan una representación local. **Quedan pendientes la lectura en la interfaz real de GitHub, la ampliación nativa al 200 % y 400 % y la comprobación con lector de pantalla.** El navegador disponible utiliza otra cuenta sin acceso a este repositorio privado y devuelve una página 404; el acceso mediante la cuenta autorizada de desarrollo sí funciona. No se atribuye una certificación de accesibilidad a estas pruebas parciales.

## Activación pendiente

Las agendas siguen desactivadas. Las consultas disponibles no permiten confirmar las cuotas y el límite de gasto de la cuenta. Los procesos pueden ejecutarse manualmente; su activación programada requiere comprobar ese control de gasto.

La incorporación de cambios sensibles requiere una segunda persona competente. La publicación de v0.2 y la fusión de esta propuesta siguen pendientes de esa revisión. No se ha cambiado la privacidad ni contratado una suscripción.
