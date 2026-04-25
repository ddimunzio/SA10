# Guía de Usuario — Aplicación de Escritorio

SA10M Contest Manager es una aplicación de escritorio construida con Python/Tkinter. Ofrece una interfaz con pestañas que guía al usuario a través del flujo de trabajo completo de puntuación del concurso.

---

## Estructura de la Aplicación

![SA10M Contest Manager — ventana principal](../../assets/images/app-overview.png)

```
┌──────────────────────────────────────────────────────────────────┐
│  SA10M Contest Manager          DB: sa10_contest.db  [Cambiar]   │
├──────────────────────────────────────────────────────────────────┤
│  Concursos │ Importar Logs │ Validación Cruzada │ Puntuar │ Tabla│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   (contenido de la pestaña activa)                               │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Log de Salida                                  [Limpiar Log]    │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ [00:00:00] Listo...                                        │   │
│  └───────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│  Listo                                       [barra de progreso] │
└──────────────────────────────────────────────────────────────────┘
```

### Barra de Encabezado
- Muestra la ruta del **archivo de base de datos activo** a la derecha
- El botón **Cambiar** abre un explorador de archivos para cambiar de base de datos

### Log de Salida
- Consola deslizante en la parte inferior que captura toda la salida de operaciones
- Con código de color: blanco = normal, amarillo = advertencias, verde = éxito, rojo = errores
- **Limpiar Log** elimina todos los mensajes

### Barra de Estado
- Muestra el estado de la operación actual (Listo / Importando logs… / Calculando puntajes…)
- Barra de progreso animada mientras se ejecuta una tarea en segundo plano

---

## Flujo de Trabajo Recomendado

Sigue las pestañas en orden para una ejecución limpia del concurso:

```
1. Concursos  →  2. Importar Logs  →  3. Validación Cruzada  →  4. Puntuar  →  5. Tabla
```

| Paso | Pestaña | Qué ocurre |
|------|---------|-----------|
| 1 | [Concursos](concursos.md) | Crear el registro del concurso y establecerlo como activo |
| 2 | [Importar Logs](importar-logs.md) | Cargar archivos de log Cabrillo desde una carpeta |
| 3 | [Validación Cruzada](validacion-cruzada.md) | Validar contactos entre todos los logs (NIL / erróneos) |
| 4 | [Puntuar](puntuacion.md) | Calcular puntos y multiplicadores |
| 5 | [Tabla de Clasificación](tabla-clasificacion.md) | Navegar resultados, exportar a Excel o CSV |

---

## Iniciar la Aplicación

```bash
# Activar el entorno virtual primero
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / Mac

# Iniciar
python app_ui.py
```
