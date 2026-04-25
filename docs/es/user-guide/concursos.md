# Pestaña Concursos

![Pestaña Concursos](../../assets/images/tab-contests.png)

La pestaña **Concursos** es donde se crean y gestionan los registros de concurso. Cada importación y cálculo de puntaje está vinculado a un concurso específico, por lo que este es siempre el primer paso.

---

## Crear Nuevo Concurso

Completa los cuatro campos y haz clic en **Crear Concurso**:

| Campo | Ejemplo | Descripción |
|-------|---------|-------------|
| **Nombre** | `SA10M 2026` | Nombre legible del concurso |
| **Slug** | `sa10m-2026` | Identificador único usado internamente y por el motor de reglas |
| **Inicio (YYYY-MM-DD HH:MM)** | `2026-03-14 00:00` | Hora de inicio del concurso en UTC |
| **Fin (YYYY-MM-DD HH:MM)** | `2026-03-15 23:59` | Hora de fin del concurso en UTC |

!!! tip "Convención del slug"
    Usa solo letras minúsculas, dígitos y guiones. El slug debe coincidir con un archivo YAML de reglas en `config/contests/`. Para el concurso SA10M estándar usa `sa10m`.

Al hacer clic en **Crear Concurso**, el nuevo registro aparece en la tabla inferior y se imprime un mensaje de confirmación en el Log de Salida.

---

## Lista de Concursos

La tabla muestra todos los concursos almacenados en la base de datos actual:

| Columna | Descripción |
|---------|-------------|
| **ID** | Identificador numérico asignado automáticamente |
| **Nombre** | Nombre del concurso |
| **Slug** | Identificador interno |
| **Inicio / Fin** | Período del concurso |
| **Logs** | Número de logs de estación importados para este concurso |

### Botones

- **↻ Actualizar** — recarga la lista desde la base de datos (útil tras cambios externos)
- **Seleccionar Activo** — marca el concurso resaltado como el *concurso activo*; esto se propaga automáticamente a las pestañas Importar Logs y Puntuar
- **Eliminar** — elimina permanentemente el concurso seleccionado y todos sus logs y puntajes

!!! warning "Eliminar es permanente"
    Eliminar un concurso borra todos los logs, contactos y puntajes asociados de la base de datos. Esta acción no se puede deshacer.

---

## Concurso Activo

El **concurso activo** se muestra en negrita en el lado derecho de la fila de botones. Una vez establecido, todas las demás pestañas (Importar Logs, Validación Cruzada, Puntuar, Tabla de Clasificación) apuntan automáticamente a este concurso, sin necesidad de volver a ingresar el ID del concurso en ningún lado.

Para cambiar el concurso activo, haz clic en una fila diferente de la tabla y presiona **Seleccionar Activo**.
