<!-- GENERADO: editar data/ o content/ y reconstruir con tools/build_catalog.py -->
# Examinar la huella pública de un dominio

> Guía pendiente de revisión humana. Comprueba siempre la fuente competente.

## Objetivo

Obtener contexto pasivo sobre un dominio y su infraestructura sin acceder a sistemas ni eludir controles.

## Procedimiento

1. Normaliza el dominio y confirma que no contiene credenciales o tokens.
2. Consulta registros públicos, certificados y capturas históricas.
3. Separa observaciones actuales de datos históricos.
4. Contrasta relaciones de IP, ASN y nombres con sus fechas.
5. Si una herramienta agrega detecciones, abre la fuente de cada señal.
6. Documenta únicamente lo necesario para la pregunta.

## Ejemplo ficticio

Una captura histórica muestra un logotipo y un aviso legal. Esto indica que el archivo conservó esa página en una fecha; no prueba quién controlaba el servidor.

## Límites

No realices escaneos activos, intentos de acceso ni pruebas de vulnerabilidad sin autorización. IP compartida, DNS antiguo o un certificado no prueban propiedad actual.

## Recursos

Consulta el [índice de huella de dominio](../indices/escenario-domain-footprint.md).

## Recorrido de práctica y resultado esperado

El dominio reservado example.org sirve como entrada didáctica, sin escanearlo ni enviar archivos.

1. Abre el índice de este escenario y selecciona el territorio.
2. Comprueba si el recurso es local o aporta orientación general y lee sus carencias.
3. Sigue los pasos anteriores usando únicamente datos ficticios; no envíes comunicaciones de prueba.
4. Registra la referencia consultada, su fecha y las dudas pendientes.

Se registra fuente, fecha y tipo de observación. Compartir infraestructura no identifica a una persona ni acredita control.

## Si la fuente no responde o no cubre el caso

No interpretes un bloqueo o una búsqueda vacía como ausencia del hecho. Consulta las alternativas y la fuente territorial competente. Ante peligro inmediato, prioriza el servicio oficial; no esperes al mantenimiento del catálogo.

## Plantilla del resultado

- Observación: descripción concreta y proporcionada, sin datos de víctimas.
- Referencia: fuente responsable y fecha de consulta; en este ejercicio, referencia ficticia.
- Incertidumbre: qué falta comprobar y qué otras explicaciones siguen siendo posibles.
- Siguiente actuación: consulta o canal competente, distinguiendo ayuda, reporte y denuncia.

## Cobertura territorial y revisión

Guía general con ejemplos de España. La adaptación de otros territorios está pendiente.

Estado editorial: **pendiente**. Revisión humana: **pendiente**; persona revisora: **por asignar**.

## Referencias responsables

- [INCIBE](https://www.incibe.es/)
- [CCN-CERT](https://www.ccn-cert.cni.es/)
- [Internet Archive Wayback Machine](https://web.archive.org/)
- [VirusTotal](https://www.virustotal.com/)
- [Shodan](https://www.shodan.io/)
