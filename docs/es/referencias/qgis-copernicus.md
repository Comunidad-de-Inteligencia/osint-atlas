# Ver Copernicus en QGIS

QGIS es un programa de escritorio. No se instala con este repositorio. Esta guía dice cómo abrir una capa. No analiza la imagen por ti.

Las pantallas de alta de cliente se leyeron en la [documentación del complemento Sentinel Hub](https://documentation.dataspace.copernicus.eu/Applications/QGIS.html) el 8 de octubre de 2026. No se abrió la sesión real del panel. Si un botón no coincide, manda la pantalla del servicio.

## 1. Instalar QGIS

Descarga QGIS de escritorio desde [qgis.org](https://qgis.org/). Usa el instalador del proyecto. No hace falta ningún paquete de este catálogo.

## 2. Un mapa sin clave

Sirve para comprobar que QGIS abre un servicio público.

1. Crea un proyecto nuevo.
2. Añade una conexión WMS. En la URL puedes probar el servicio PNOA de máxima actualidad: `https://www.ign.es/wms-inspire/pnoa-ma`. El 8 de octubre de 2026 esa dirección respondió a una petición de capacidades. No se recorrió el asistente de QGIS en un escritorio.
3. Carga una capa de prueba y anota el nombre del servicio.
4. La ficha del producto sigue siendo [CNIG y PNOA](../geoint/es-cnig-pnoa.md). El directorio de servicios está en [IDEE](../geoint/es-idee.md).

Si la capa no carga, anota el error. No concludes que el lugar no existe.

## 3. Cuenta y cliente OAuth

Hace falta una cuenta gratuita en [Copernicus Data Space](https://dataspace.copernicus.eu/). La documentación del complemento dice esto:

1. En el panel, abre User Settings.
2. En OAuth clients, crea un cliente.
3. El tipo de concesión es Client Credentials.
4. El secreto se muestra una vez. Cópialo entonces. Después el panel ya no lo enseña.
5. En QGIS, instala el complemento Sentinel Hub desde el gestor de complementos.
6. Pega el identificador y el secreto en la pestaña de acceso del complemento.

El secreto se queda en tu equipo, dentro de QGIS. No lo pegues en un `.env` de este repositorio, ni en un commit, ni en una incidencia.

Un marcador, solo para reconocer la forma. No es una clave válida:

~~~text
identificador: el que muestra el panel
secreto: el que copias una sola vez
~~~

## 4. Una capa Sentinel

La documentación dice que el complemento enseña una capa. No hace el análisis.

1. En el panel del servicio, prepara una configuración y una capa de visualización. No desactives las peticiones OGC si quieres verla en QGIS.
2. En el complemento, elige esa configuración y una capa Sentinel de visualización.
3. Anota misión, fecha y que la vista no es un análisis ni tiempo real.
4. La ficha de acceso es [Copernicus Data Space](../geoint/eu-copernicus.md).

## 5. Otras puertas

[Copernicus Connect](https://plugins.qgis.org/plugins/Copernicus_Connect/) es otro complemento. La ficha del complemento, leída el mismo día, dice que descarga datos de WEkEO y que también puede añadir WMS o WMTS. La credencial queda en el equipo. No la subas a Git.

Copernicus Marine ofrece productos del mar en [su portal](https://marine.copernicus.eu/). En esta entrega no se abrió una capa WMTS concreta. Si la usas, anota el mismo límite: no es tiempo real. La ficha es [Copernicus Marine](../geoint/eu-copernicus-marine.md).

## 6. Qué no concluye la imagen

- La posición del satélite no es la escena.
- La imagen llega con retraso. Las horas que se citan en otras guías no se contrastaron en el servicio.
- Las nubes tapan el óptico.
- La licencia es la del producto, no la de esta página.

Vuelve a [cómo verificar una imagen](../procedimientos/verificar-imagen.md) antes de afirmar un lugar.
