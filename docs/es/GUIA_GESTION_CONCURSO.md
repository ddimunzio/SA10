# Guía de Gestión de Concursos

## Descripción General

El sistema de puntuación SA10 requiere la creación explícita de un concurso antes de importar logs. Este diseño garantiza:
- **Un concurso a la vez**: Enfoque en puntuar un único concurso
- **Sin auto-población**: Control explícito sobre los datos del concurso
- **Separación clara**: Los metadatos del concurso se gestionan de forma independiente a los logs

## Flujo de Trabajo

### 1. Crear un Concurso

Antes de importar logs, crear el concurso:

```bash
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"
```

Parámetros:
- **name**: Nombre completo del concurso (ej: "SA10M 2025")
- **slug**: Identificador único (ej: "sa10m-2025")
- **start_date**: Fecha y hora de inicio (YYYY-MM-DD HH:MM)
- **end_date**: Fecha y hora de fin (YYYY-MM-DD HH:MM)
- **--rules**: (Opcional) Ruta a archivo YAML de reglas personalizado

El comando mostrará el ID del concurso, necesario para importar logs.

### 2. Importar Logs

Importar logs con el ID del concurso:

```bash
# Importar directorio completo
python import_logs.py --contest-id 1 --clean logs_sa10m_2025/

# Importar un único archivo
python import_logs.py --contest-id 1 ruta/al/log.cbr
```

## Comandos de Gestión

### Listar Todos los Concursos

```bash
python manage_contest.py list
```

Salida:
```
ID    Nombre                         Slug                 Fecha Inicio
================================================================================
1     SA10M 2025                     sa10m-2025           2025-03-08 00:00

Total: 1 concurso(s)
```

### Ver Detalles de un Concurso

```bash
python manage_contest.py show 1
```

Salida:
```
======================================================================
Detalles del Concurso (ID: 1)
======================================================================
Nombre:         SA10M 2025
Slug:           sa10m-2025
Fecha Inicio:   2025-03-08 00:00:00
Fecha Fin:      2025-03-09 23:59:59
Archivo Reglas: config/contests/sa10m.yaml
Creado:         2025-11-19 10:30:45

Logs Enviados: 150

Indicativos:
  - K1ABC
  - W2DEF
  ...
```

### Eliminar un Concurso

⚠️ **Advertencia**: ¡Esto elimina el concurso y TODOS los logs y contactos asociados!

```bash
python manage_contest.py delete 1
```

Se pedirá confirmación:
```
ADVERTENCIA: Está a punto de eliminar:
  Concurso: SA10M 2025 (ID: 1)
  ¡Esto también eliminará 150 log(s) y todos sus contactos!

Escriba 'yes' para confirmar:
```

## Esquema de la Base de Datos

La tabla de concursos almacena:
- **id**: Identificador único (auto-incremento)
- **name**: Nombre completo del concurso
- **slug**: Identificador amigable único
- **start_date**: Fecha y hora de inicio
- **end_date**: Fecha y hora de fin
- **rules_file**: Ruta al archivo YAML de reglas
- **created_at**: Fecha de creación del registro
- **updated_at**: Última actualización

## Fundamento del Diseño

### ¿Por qué crear el concurso manualmente?

1. **Control explícito**: Usted decide cuándo y cómo se crean los concursos
2. **Integridad de datos**: Previene la creación accidental de concursos duplicados
3. **Flujo simplificado**: Un concurso a la vez, puntuación enfocada
4. **Separación clara**: Metadatos del concurso gestionados independientemente

### ¿Por qué se requiere el ID del concurso?

- **Sin ambigüedad**: Los logs siempre se asocian al concurso correcto
- **Operaciones en lote**: Importar múltiples logs al mismo concurso eficientemente
- **Validación**: Las fechas del concurso se usan para validar marcas de tiempo de los QSOs

## Ejemplos

### Escenario 1: Configuración inicial

```bash
# Paso 1: Crear concurso
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"
# Salida: Concurso creado exitosamente! ID: 1

# Paso 2: Importar logs
python import_logs.py --contest-id 1 --clean logs_sa10m_2025/
```

### Escenario 2: Importar logs adicionales

```bash
# El concurso ya existe (ID: 1)
python import_logs.py --contest-id 1 logs_nuevos/CE2ABC_SSB.txt
```

### Escenario 3: Re-importar desde cero

```bash
# Eliminar concurso existente
python manage_contest.py delete 1

# Crear nuevo concurso
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"

# Importar todos los logs
python import_logs.py --contest-id 1 --clean logs_sa10m_2025/
```

### Escenario 4: Múltiples Concursos (futuro)

```bash
# Crear primer concurso
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"
# ID: 1

# Importar logs del primer concurso
python import_logs.py --contest-id 1 logs_sa10m_2025/

# Crear segundo concurso
python manage_contest.py create "SA10M 2026" sa10m-2026 "2026-03-14 00:00" "2026-03-15 23:59"
# ID: 2

# Importar logs del segundo concurso
python import_logs.py --contest-id 2 logs_sa10m_2026/
```

## Consejos

- **Anotar siempre el ID del concurso** al crearlo
- **Usar slugs descriptivos** con el año para fácil identificación
- **Verificar concursos existentes** con `list` antes de crear nuevos
- **Hacer backup de la base de datos** antes de eliminar concursos

## Resolución de Problemas

### "Contest ID X not found"
- Ejecutar `python manage_contest.py list` para ver concursos disponibles
- Crear el concurso si no existe

### "Contest with slug 'xxx' already exists"
- Usar un slug diferente o eliminar el concurso existente
- Verificar con `python manage_contest.py list`

### La importación falla con errores de validación
- Verificar que las fechas del concurso coincidan con las fechas de los QSOs
- Comprobar que los logs estén en formato Cabrillo correcto

---

**Ver también:**
- `docs/DATABASE_SCHEMA.md` — Documentación completa de la base de datos
- `docs/IMPORT_LOGS_GUIDE.md` — Guía detallada de importación
- `docs/es/GUIA_IMPORTACION_LOGS.md` — Esta guía en español
