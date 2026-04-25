# Pestaña Importar Logs

La pestaña **Importar Logs** carga archivos de log Cabrillo (`.cbr`, `.txt`) en la base de datos para el concurso activo.

---

## Fuente de Logs

Elige cómo proporcionar los archivos de log:

| Modo | Cuándo usarlo |
|------|--------------|
| **Directorio** | Tienes una carpeta con muchos archivos de log (típico para una ejecución completa del concurso) |
| **Archivo único** | Quieres agregar o actualizar el log de una estación específica |

Haz clic en **Explorar…** para abrir un cuadro de diálogo selector de archivos, o escribe la ruta directamente en el campo Ruta.

!!! info "Extensiones de archivo admitidas"
    La importación por directorio reconoce archivos `.txt`, `.log` y `.cbr`. Otros tipos de archivo en la carpeta son ignorados.

---

## Opciones

### ID de Concurso

Se rellena automáticamente desde el **concurso activo** establecido en la pestaña Concursos. También puedes escribir un ID de concurso manualmente si necesitas importar a un concurso diferente sin cambiar el activo.

### Borrar TODOS los datos del concurso antes de importar

Cuando está marcado, todos los logs, contactos y puntajes pertenecientes al concurso activo son **eliminados** antes de procesar los nuevos archivos. Usa esto para una reimportación limpia desde cero.

!!! warning "La opción de borrar es destructiva"
    Borrar los datos del concurso es irreversible dentro de la sesión actual. Actívala solo cuando quieras deliberadamente empezar de cero.

---

## Ejecutar la Importación

Haz clic en **▶ Importar Logs** para comenzar. La operación se ejecuta en un hilo en segundo plano para que la interfaz permanezca responsiva.

### Qué ocurre durante la importación

1. Cada archivo Cabrillo es analizado (metadatos del encabezado + líneas QSO)
2. El indicativo de la estación se extrae del encabezado `CALLSIGN:`
3. Si ya existe un log para el mismo indicativo en el concurso, este es **reemplazado** (gana el envío más reciente)
4. Todos los contactos se almacenan con su banda, modo, frecuencia, RST y campos de intercambio
5. Se imprime un resumen en el Log de Salida:

```
Importación completada — 666 archivo(s) aceptado(s): 604 nuevos, 62 reemplazados, 3 omitidos/fallidos.
El concurso ahora tiene 601 log(s) de estación para puntuar.
```

### Lógica de reemplazo

Si una estación reenvía su log, el nuevo archivo **reemplaza** al anterior. Por lo tanto, el número de logs únicos de estación puede ser menor que el número de archivos aceptados.

### Archivos omitidos / fallidos

Un archivo es omitido cuando:
- No puede analizarse como un archivo Cabrillo válido
- El campo `CALLSIGN:` está ausente o malformado
- Ocurre un error de base de datos durante la inserción

Los errores se muestran en amarillo en el Log de Salida con el nombre del archivo y la razón.

---

## Después de la Importación

La lista de Concursos en la pestaña **Concursos** se actualiza automáticamente para reflejar el nuevo conteo de logs. Continúa con la pestaña **Validación Cruzada**.
