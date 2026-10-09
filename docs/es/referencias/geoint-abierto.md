# Consulta GEOINT abierta

Lista para elegir una fuente y abrirla. No describe una aplicación. Un visor, QGIS o SNAP aparecen como programas que una persona abre, con un límite.

Compilada el 8 de octubre de 2026. Las latencias son orientativas y no se contrastaron en cada servicio, salvo la captura de Madrid, leída ese día en su ficha. Una cámara de tráfico no identifica a una persona ni prueba un hecho. Un marcador de satélite no es la imagen de ese satélite.

La ficha YAML es la entrada que el mantenimiento visita. Lo demás se queda en esta lista hasta que alguien decida darle ficha.

## Qué anotar de una observación

- Misión o sensor.
- Nombre del producto.
- Fecha de la escena, no solo la fecha en que miras.
- Resolución, si la ficha la dice.
- Latencia, si la conoces, y que puede no estar contrastada.
- Licencia del producto.

## Observación terrestre

- **Copernicus Data Space y Browser.** Para buscar escenas Sentinel. El navegador muestra; el Data Space entrega el producto. Una posición o un globo no es la imagen en directo. [Ficha](../geoint/eu-copernicus.md). [Data Space](https://dataspace.copernicus.eu/). [Browser](https://browser.dataspace.copernicus.eu/).
- **NASA Worldview.** Para ver una capa de NASA con fecha. No es un callejero. [Ficha](../geoint/global-nasa-worldview.md).
- **USGS Landsat.** Para escenas ópticas de la misión Landsat. No es tiempo real. [Ficha](../geoint/global-usgs-landsat.md).
- **NASA Earthdata.** Catálogo amplio de la NASA. No sustituye la ficha del producto. [earthdata.nasa.gov](https://earthdata.nasa.gov/).
- **Sentinel-1.** Radar. Útil con nubes. La disponibilidad que se cita, hasta cerca de un día, no se contrastó aquí. [Misión](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-1).
- **Sentinel-2.** Óptico, con bandas de unos 10 m. Tampoco es directo. [Misión](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2).
- **Sentinel-3.** Tierra, agua y temperatura. Se habla de unas tres horas. No contrastado. [Misión](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-3).
- **Sentinel-5P.** Gases y aerosoles. También se habla de unas tres horas. No contrastado. [Misión](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-5p).

## Meteorología

- **EUMETView.** Imagen meteorológica de EUMETSAT. No es una ortofoto. [Ficha](../geoint/eu-eumetview.md).
- **EUMETSAT.** Página del organismo. [eumetsat.int](https://www.eumetsat.int/).
- **EUMETSAT Data Store.** Descarga de productos. [data.eumetsat.int](https://data.eumetsat.int/).
- **ECMWF Open Data.** Modelos. Un modelo no es una medición en cada punto. [Conjunto abierto](https://www.ecmwf.int/en/forecasts/datasets/open-data).
- **AEMET OpenData.** Avisos y observaciones de España. Separa predicción y observación. [Ficha](../medio-ambiente/es-aemet.md).
- **Open-Meteo.** API de terceros. No es el aviso oficial. [open-meteo.com](https://open-meteo.com/).

## Incendios

- **EFFIS.** Panorama europeo de incendios forestales. No es una orden de evacuación. [Ficha](../geoint/eu-effis.md).
- **NASA FIRMS.** Detecciones térmicas. Una detección no prueba la causa. [Ficha](../geoint/global-nasa-firms.md).

## Emergencias

- **Copernicus EMS.** Mapas de una activación y una fecha. No es una imagen continua. [Ficha](../emergencias/eu-erascc-emergency-mapping.md).
- **GDACS.** Panorama inicial de grandes desastres. No sustituye la alerta local. [Ficha](../emergencias/global-gdacs.md).
- **EFAS.** Avisos europeos de inundación. [Servicio](https://european-flood.emergency.copernicus.eu/).
- **GloFAS.** Crecidas a escala amplia. [Servicio](https://global-flood.emergency.copernicus.eu/).

En un desastre, sigue el [procedimiento](../procedimientos/desastre-crisis.md). Estas fuentes no cambian esa prioridad.

## Océanos

- **Copernicus Marine.** Variables del mar. No es la foto de un barco. [Ficha](../geoint/eu-copernicus-marine.md).
- **EMODnet.** Datos marinos europeos reunidos. Comprueba el productor de cada capa. [emodnet.ec.europa.eu](https://emodnet.ec.europa.eu/).
- **Puertos del Estado y PORTUS.** Observación costera española. [puertos.es](https://www.puertos.es/). [PORTUS](https://portus.puertos.es/).

## Aviación

- **OpenSky Network.** Estados de vuelo publicados por una red de receptores. Puede faltar cobertura. No es ayuda a la navegación. La página no respondió en esta comprobación. [Ficha](../geoint/global-opensky.md).

Otras webs de ADS-B quedan fuera de las fichas. Si las usas, contrasta la hora y no sigas a una persona.

## AIS

- **AISStream.** Señales públicas de barcos. Lejos de la costa la cobertura baja. Un silencio no prueba que el barco no esté. [aisstream.io](https://aisstream.io/).

## Órbitas

- **CelesTrak.** Elementos orbitales. El marcador no es la imagen del satélite. [Ficha](../geoint/global-celestrak.md).
- **SatNOGS.** Red de recepción de aficionados. No es la telemetría oficial de la misión. [network.satnogs.org](https://network.satnogs.org/).

## Cartografía

- **OpenStreetMap.** Mapa colaborativo. Puede estar mal o recién editado. [Ficha](../geoint/global-osm.md).
- **Overpass Turbo.** Pregunta esos mismos datos. No es otra fuente. [Ficha](../geoint/global-overpass.md).
- **Natural Earth.** Capas generales para un mapa base. No detalla una calle. [naturalearthdata.com](https://www.naturalearthdata.com/).

## Infraestructura

- **OpenInfraMap.** Energía y telecomunicaciones dibujadas a partir de OpenStreetMap. No es el plano de la compañía. [openinframap.org](https://openinframap.org/).

## España: IDEE y cartografía oficial

- **IDEE.** Directorio de servicios de mapas. La capa la publica otro organismo. [Ficha](../geoint/es-idee.md).
- **CNIG, centro de descargas y PNOA.** Ortofotos y modelos. Cada vuelo tiene su fecha. [Ficha](../geoint/es-cnig-pnoa.md). [pnoa.ign.es](https://pnoa.ign.es/).
- **IGN.** Cartografía, sismos y volcanes. [ign.es](https://www.ign.es/). La ficha de geodesia es [IGN Información Geográfica](../geoint/es-ign-geodesia.md).
- **Catastro.** Parcelas en el territorio que cubre. No cubre País Vasco ni Navarra. [Ficha](../geoint/es-catastro.md).
- **SIOSE.** Ocupación del suelo. [siose.es](https://www.siose.es/).
- **MITECO.** Capas ambientales. [Ficha](../medio-ambiente/es-miteco-datos.md).

El servicio WMS de PNOA de máxima actualidad respondió el 8 de octubre de 2026. Cómo abrirlo en QGIS está en [la guía de QGIS](qgis-copernicus.md).

## Cámaras de tráfico en España

No hay un censo único. Usa solo páginas que el organismo publica. Una cámara abierta por error no cuenta como fuente.

- **DGT, punto de acceso nacional.** Cámaras y datos de la red que publica la DGT. No es la estadística de [DGT en cifras](../transporte/es-dgt-datos.md). [Ficha de cámaras](../geoint/es-dgt-camaras.md).
- **Ayuntamiento de Madrid.** Posición y captura. La ficha municipal habla de unos cinco minutos. [Ficha](../geoint/es-madrid-camaras.md).
- **Calle 30.** Tráfico de la M-30. No se leyó si cada imagen es pública. [mc30.es](https://mc30.es/).
- **Navarra.** Página de tráfico. No respondió en esta comprobación. [Ficha](../geoint/es-navarra-trafico.md).
- **Bilbao.** Conjunto municipal en el catálogo nacional. El título dice tiempo real y el intervalo no se leyó. [Ficha](../geoint/es-bilbao-camaras.md).
- **Servei Català de Trànsit.** Cámaras de la red catalana. [Página de cámaras](https://transit.gencat.cat/es/informacio-viaria/estat-transit/cameres-transit/).
- **Euskadi Trafikoa.** Tráfico del País Vasco. [trafikoa.euskadi.eus](https://www.trafikoa.euskadi.eus/).
- **Zaragoza.** Datos abiertos del Ayuntamiento. [Portal](https://www.zaragoza.es/sede/portal/datos-abiertos/).
- **València.** Portal VLCi. No des por hecho que cada punto tenga vídeo. [opendata.vlci.valencia.es](https://opendata.vlci.valencia.es/).
- **Málaga.** Conjunto de cámaras de tráfico. [datosabiertos.malaga.eu](https://datosabiertos.malaga.eu/dataset/camaras-de-trafico).
- **Sevilla.** Visor municipal de tráfico. [trafico.sevilla.org](https://trafico.sevilla.org/).

## Programas de consulta

No son software de este repositorio. No tienen ficha salvo SNAP y el visor experimental.

- **QGIS.** Programa para abrir capas. [Guía](qgis-copernicus.md). [qgis.org](https://qgis.org/).
- **ESA SNAP.** Para leer un producto Sentinel en el escritorio. [Ficha](../geoint/global-esa-snap.md).
- **GDAL.** Librería para convertir y leer archivos geoespaciales. No interpreta el hecho. [gdal.org](https://gdal.org/).
- **GRASS GIS.** Otro programa de análisis. [grass.osgeo.org](https://grass.osgeo.org/).
- **God's Eye View.** Visor experimental de fuentes públicas. No sirve para una operación crítica. El marcador no es la imagen. [Ficha](../geoint/global-gods-eye-view.md).

## Cortes territoriales

La lista sigue el mismo árbol que el catálogo: Europa y la Unión Europea, España y el municipio cuando hay ficha, América y Global. El deletreo de radio no se parte aquí. Está en [radiotelefonía](radiotelefonia.md).
