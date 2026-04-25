# Pestaña Tabla de Clasificación

La pestaña **Tabla de Clasificación** muestra los resultados finales clasificados del concurso activo, con opciones de filtrado, ordenamiento y exportación.

---

## Tabla de Clasificación

| Columna | Descripción |
|---------|-------------|
| **#** | Posición (en el orden de clasificación actual) |
| **Indicativo** | Indicativo de la estación |
| **Categoría** | Categoría combinada de operador / modo / potencia |
| **Puntaje Final** | Puntaje total del concurso (puntos × multiplicadores) |
| **Total QSOs** | Todos los contactos enviados |
| **QSOs Válidos** | Contactos que superaron la validación cruzada |
| **Dupes** | Contactos duplicados eliminados |
| **Puntos** | Total bruto de puntos QSO |
| **Multiplicadores** | Conteo total de multiplicadores (WPX + zonas CQ) |

Haz clic en cualquier **encabezado de columna** para ordenar por esa columna. Haz clic nuevamente para invertir el orden.

---

## Filtros

### Filtro de indicativo

Escribe parte de un indicativo en el cuadro **Filtrar indicativo**. La tabla se actualiza en tiempo real mientras escribes, mostrando solo las filas donde el indicativo contiene el texto ingresado.

### Filtro de categoría

El desplegable **Categoría** se rellena automáticamente con las categorías presentes en el concurso actual. Selecciona una categoría para mostrar solo esas entradas, o elige **Todas** para ver a todos.

### Filtro de área

| Opción | Muestra |
|--------|---------|
| **Mundo** | Todas las estaciones (por defecto) |
| **Argentina** | Estaciones con prefijos LU, LW, LO, LP, LQ, AY, AZ |
| **América del Sur** | Todas las estaciones SA (incluyendo Argentina) |
| **DX** | Estaciones fuera de América del Sur |

---

## Acciones

### ↻ Actualizar Clasificación

Recarga los puntajes desde la base de datos. Usa esto después de ejecutar la puntuación para ver los resultados actualizados.

### ⬇ Exportar a Excel

Exporta la tabla de clasificación completa (todas las filas, sin ningún filtro) a un archivo Excel `.xlsx`. Un cuadro de diálogo de guardado permite elegir la ubicación.

El libro de trabajo contiene una hoja con todas las columnas más la posición calculada.

### ⬇ Exportar Puntajes CSV

Exporta un CSV liviano con indicativo y las columnas clave de puntaje. Útil para compartir o para análisis adicional en herramientas de planilla de cálculo.

### ⬇ Reporte QSO (Excel)

Exporta un libro de trabajo detallado por QSO con una fila por contacto de todos los logs. Las columnas incluyen indicativo, banda, modo, frecuencia, marca de tiempo, RST enviado/recibido, valores de intercambio, puntos QSO y estado de validación cruzada.

!!! tip "Consejo de exportación"
    Todas las exportaciones usan el **conjunto de datos completo sin filtrar**, independientemente del filtro activo de indicativo / categoría / área.
