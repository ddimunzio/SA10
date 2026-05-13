# Pestaña Estadísticas

La pestaña **Estadísticas** ofrece un resumen compacto del concurso activo después de ejecutar la importación, la validación cruzada y la puntuación.

---

## Acciones

### Actualizar Estadísticas

Recarga desde la base de datos las tarjetas de resumen y la tabla de participantes para el concurso activo.

### Exportar Lista UBN (Excel)

Genera un archivo Excel con todos los contactos marcados como alguno de los siguientes casos:

- No en log
- Indicativo errado
- Indicativo único

La exportación incluye el indicativo del operador, fecha y hora del QSO, banda, modo, valores enviados y recibidos, tipo de UBN, motivo, país y prefijo WPX.

---

## Tarjetas de Resumen

### General

- **Total de Países Participantes** — países distintos representados por los logs enviados
- **Total de UBNs** — contactos marcados como NIL, indicativos errados o indicativos únicos

### CW

- **Zonas CQ** — zonas CQ recibidas distintas en CW
- **Prefijos** — prefijos WPX distintos trabajados en CW
- **Países** — países distintos trabajados en CW
- **UBNs** — incidencias detectadas por la validación cruzada en contactos CW

### SSB

- **Zonas CQ** — zonas CQ recibidas distintas en modos de fonía
- **Prefijos** — prefijos WPX distintos trabajados en modos de fonía
- **Países** — países distintos trabajados en modos de fonía
- **UBNs** — incidencias detectadas por la validación cruzada en contactos de fonía

Los totales de fonía incluyen contactos `PH`, `SSB`, `USB`, `LSB` y `FM`.

---

## Participantes por Continente

La tabla inferior agrupa los logs enviados por continente usando los datos de lookup del indicativo almacenados en la base activa. Sirve para validar rápidamente que la distribución geográfica tenga sentido antes de publicar resultados.

---

## Cuándo Usarla

- Después de **Importar Logs** para confirmar el volumen de participación
- Después de **Validación Cruzada** para revisar la cantidad de UBN
- Después de **Puntuación** para comprobar multiplicadores y cobertura por modo

Si las tarjetas muestran cero países o una geografía evidentemente incorrecta, actualiza los datos DXCC desde el menú Archivo y vuelve a ejecutar la puntuación.