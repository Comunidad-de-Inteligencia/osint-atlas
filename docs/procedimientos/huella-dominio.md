# Examinar la huella pública de un dominio

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
