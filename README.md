<p align="center">
  <img src="docs/assets/logo.svg" alt="OSINT Atlas" width="128">
</p>

# OSINT Atlas

Catálogo de consulta. Ayuda a elegir una fuente, leer su resultado y ver qué falta comprobar. No es una aplicación, ni un visor, ni un mapa en directo.

> Ante un peligro inmediato, acude al servicio oficial de emergencias de tu territorio. Consulta el [procedimiento de emergencia](docs/procedimientos/emergencia-inmediata.md) y las [vías oficiales](docs/CONTACTOS.md). Atlas no recibe denuncias ni envía alertas.

La consulta con un asistente usa el MCP de solo lectura. Sigue siendo una forma de leer el catálogo.

## Índice

- [Qué necesito hacer](#qué-necesito-hacer)
- [En qué territorio](#en-qué-territorio)
- [Qué información tengo](#qué-información-tengo)
- [Qué está revisado](#qué-está-revisado)
- [Guías de referencia](#guías-de-referencia)
- [Cómo proponer una fuente](#cómo-proponer-una-fuente)
- [Panel de trabajo humano](#panel-de-trabajo-humano)
- [Licencia](#licencia)

## Qué necesito hacer

- **Empezar:** [un recorrido en cinco minutos](docs/EMPEZAR.md).
- **Investigar y contrastar:** [empresas](docs/procedimientos/investigar-empresa.md), [contratos y ayudas](docs/procedimientos/contratos-subvenciones.md), [publicaciones oficiales](docs/procedimientos/publicaciones-oficiales.md), [dominios](docs/procedimientos/huella-dominio.md), [imágenes](docs/procedimientos/verificar-imagen.md), [conclusiones](docs/procedimientos/contrastar-conclusiones.md), [afirmaciones jurídicas](docs/procedimientos/afirmacion-juridica.md) o [estadísticas](docs/procedimientos/afirmacion-estadistica.md).
- **Desapariciones:** [adultos](docs/procedimientos/desaparicion-adulto.md) o [menores](docs/procedimientos/desaparicion-menor.md).
- **Emergencias:** [actuación inmediata](docs/procedimientos/emergencia-inmediata.md) o [desastres y crisis](docs/procedimientos/desastre-crisis.md).
- **Protección y reporte:** [grooming y sextorsión](docs/procedimientos/grooming-sextorsion.md), [violencia sexual digital](docs/procedimientos/violencia-sexual-digital.md), [posible abuso sexual infantil](docs/procedimientos/reportar-csam.md) o [Telegram y otras plataformas](docs/procedimientos/reportar-plataformas.md).

## En qué territorio

- [Global](docs/indices/jurisdiccion-global.md)
  - [Europa](docs/indices/jurisdiccion-europe.md)
    - [Unión Europea](docs/indices/jurisdiccion-eu.md)
      - [España](docs/indices/jurisdiccion-es.md)
        - [País Vasco](docs/indices/jurisdiccion-es-pv.md)
          - [Bilbao](docs/indices/jurisdiccion-es-bi.md)
        - [Comunidad Foral de Navarra](docs/indices/jurisdiccion-es-nc.md)
        - [Madrid](docs/indices/jurisdiccion-es-mad.md)
      - [Portugal](docs/indices/jurisdiccion-pt.md)
      - [Francia](docs/indices/jurisdiccion-fr.md)
      - [Alemania](docs/indices/jurisdiccion-de.md)
      - [Italia](docs/indices/jurisdiccion-it.md)
    - [Reino Unido](docs/indices/jurisdiccion-gb.md)
  - [América](docs/indices/jurisdiccion-america.md)
    - [Brasil](docs/indices/jurisdiccion-br.md)
    - [México](docs/indices/jurisdiccion-mx.md)
    - [Colombia](docs/indices/jurisdiccion-co.md)
    - [Argentina](docs/indices/jurisdiccion-ar.md)

El Reino Unido no forma parte de la Unión Europea. Una cámara de Madrid se encuentra desde España y en su propia página. La [cobertura](docs/COBERTURA.md) usa el mismo árbol. Un recurso global puede ayudar sin cubrir el procedimiento local.

## Qué información tengo

Parte de una [organización](docs/indices/entrada-organizacion.md), un [expediente](docs/indices/entrada-expediente.md), un [documento](docs/indices/entrada-documento.md), un [dominio](docs/indices/entrada-dominio.md), un [lugar](docs/indices/entrada-lugar.md), un [indicador](docs/indices/entrada-indicador.md), una [situación](docs/indices/entrada-situacion.md), una [plataforma](docs/indices/entrada-plataforma.md) o una [pregunta por contrastar](docs/indices/entrada-pregunta.md).

[Explorar el catálogo](docs/CATALOGO.md).

## Qué está revisado

Hay **100 fichas** y **16 procedimientos**. Las fichas nuevas de esta entrega están pendientes. Una fecha de creación no es una revisión humana.

Los cambios sensibles necesitan otra persona competente. Mientras no esté registrada, las propuestas siguen pendientes.

La última comprobación de una página se lee en su ficha y en el [informe de mantenimiento](https://github.com/P3M-ACTF/osint-atlas/blob/maintenance-state/README.md): disponible, sin respuesta, autenticación o sin comprobación. Si no hubo ejecución, es sin comprobación. Un escudo de Actions solo dice si el proceso corrió. Las agendas siguen comentadas.

## Guías de referencia

- [Radiotelefonía](docs/referencias/radiotelefonia.md)
- [GEOINT abierto](docs/referencias/geoint-abierto.md)
- [Copernicus en QGIS](docs/referencias/qgis-copernicus.md)

## Cómo proponer una fuente

Abre una incidencia con la plantilla en [castellano](https://github.com/P3M-ACTF/osint-atlas/issues/new?template=proponer-fuente.yml) o en [inglés](https://github.com/P3M-ACTF/osint-atlas/issues/new?template=propose-source.yml). Para una corrección, usa [castellano](https://github.com/P3M-ACTF/osint-atlas/issues/new?template=corregir-contenido.yml) o [inglés](https://github.com/P3M-ACTF/osint-atlas/issues/new?template=correct-content.yml). No pegues casos ni datos personales. El detalle está en [CONTRIBUTING.md](CONTRIBUTING.md).

## Panel de trabajo humano

El panel es un Project de GitHub para el trabajo de las personas: fuentes propuestas, correcciones, guías y revisión. No lista la salud de cada ficha.

En esta entrega el token no pudo crearlo: la cuenta del agente no tiene permiso para crear proyectos del propietario. Créalo en GitHub con este nombre y estos datos.

- **Nombre:** Trabajo humano del catálogo
- **Columnas:** Por hacer, En curso, En revisión, Hecho
- **Campos:** Territorio; Tipo, con los valores fuente, guía y corrección

Las tarjetas son las incidencias de las plantillas del apartado anterior.

## Con qué está hecho

| Pieza | Papel en este catálogo |
| --- | --- |
| Python 3.12 | Generador, pruebas y MCP |
| uv | Entorno y dependencias bloqueadas |
| GitHub Actions | Validación de cada propuesta y comprobación manual de enlaces |
| QGIS | Programa externo para ver una capa. No vive en este repositorio |

## Licencia

Uso bajo la licencia MIT. Lee [LEGAL.md](LEGAL.md) y el archivo [LICENSE](LICENSE).

El repositorio es privado. Los escudos públicos de estrellas, bifurcaciones e incidencias no muestran una cifra. No se inventa un número. [Incidencias][issues]. [Licencia MIT][license].

[Glosario](docs/GLOSARIO.md). [Mantenimiento](docs/MANTENIMIENTO.md). [Accesibilidad](docs/ACCESIBILIDAD.md).

[issues]: https://github.com/P3M-ACTF/osint-atlas/issues
[license]: https://github.com/P3M-ACTF/osint-atlas/blob/main/LICENSE
