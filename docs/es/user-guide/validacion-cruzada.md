# Pestaña Validación Cruzada

![Pestaña Validación Cruzada](../../assets/images/tab-crosscheck.png)

La pestaña **Validación Cruzada** valida cada contacto en cada log enviado contra todos los demás logs del concurso. Identifica tres tipos de problemas y escribe reportes UBN (Único / Errado / No-en-log).

---

## Cómo Funciona la Validación Cruzada

Para cada QSO en un log, el sistema busca un **contacto coincidente** en el log de la otra estación:

| Resultado | Significado |
|-----------|------------|
| **Coincidente** | Ambas estaciones registraron el QSO con detalles consistentes |
| **NIL** (No en Log) | El log de la otra estación no tiene registro de este contacto |
| **Errado** | El indicativo registrado difiere ligeramente del indicativo real (probable error de copia) |
| **Único** | El contacto aparece en un solo log — podría ser un QSO válido con una estación que no envió log |

---

## Base de Datos de Indicativos (SCP)

La base de datos Super Check Partial (SCP) es una lista grande de indicativos activos conocidos. Se usa para validar si un indicativo registrado es real y reconocido.

### Indicador de estado SCP

La línea de estado muestra:

- `⚠ Aún no descargado` — el archivo no existe
- `✓ 215.000 indicativos — última actualización: 2026-03-10` — el archivo está presente con el conteo y la fecha

### Descargar MASTER.SCP

Haz clic en **⬇ Descargar MASTER.SCP** para obtener el archivo más reciente de [supercheckpartial.com](https://www.supercheckpartial.com). El archivo se guarda en `config/master.scp` y es actualizado dos veces por semana por el equipo SCP.

!!! note
    Se requiere conexión a internet para la descarga. La validación cruzada seguirá funcionando sin el archivo SCP, pero se omitirá la validación de indicativos contra la base de datos de indicativos conocidos.

---

## Configuración

| Opción | Descripción |
|--------|-------------|
| **Concurso** | Muestra el concurso activo actualmente (solo lectura) |
| **Guardar reportes UBN en carpeta ubn_reports/** | Cuando está marcado, se escribe un reporte de texto para cada log que tenga entradas NIL o erróneas |

---

## Ejecutar la Validación Cruzada

Haz clic en **▶ Ejecutar Validación Cruzada**. La operación se ejecuta en un hilo en segundo plano.

### Ejemplo de salida

```
Validación cruzada completada en 12.4 s — 487 logs con incidencias.
```

### Reportes UBN

Cuando "Guardar reportes UBN" está habilitado, se crea un archivo `.txt` por log afectado en el directorio `ubn_reports/`. Cada reporte lista:

- El indicativo del log y el concurso
- Total de contactos vs. contactos válidos
- Entradas NIL y erróneas individuales con detalles

Consulta [Formato de Reporte UBN](../FORMATO_REPORTE_UBN.md) para la especificación completa.

---

## Después de la Validación Cruzada

Los resultados de la validación cruzada se almacenan de vuelta en la tabla `contacts` (cada contacto queda marcado como válido, NIL o errado). Estos indicadores son usados luego por el motor de **Puntuación** para excluir contactos inválidos del puntaje.

Continúa con la pestaña **Puntuar**.

!!! tip
    Puedes volver a ejecutar la validación cruzada en cualquier momento. Cada ejecución sobreescribe los resultados anteriores.
