# Guía de Importación de Logs

## Inicio Rápido

### Importar logs con base de datos limpia (recomendado para inicio fresco)

```bash
python import_logs.py --clean logs_sa10m_2025/
```

Esto hará:
1. **Eliminar todos los datos** de la base de datos
2. Recrear todas las tablas
3. Importar todos los archivos `.txt` de `logs_sa10m_2025/`
4. Validar todos los contactos
5. Mostrar estadísticas resumidas

### Importar sin limpiar la base de datos

```bash
python import_logs.py logs_sa10m_2025/
```

Esto agregará/actualizará logs sin eliminar datos existentes.

### Importar un único archivo

```bash
python import_logs.py --clean logs_sa10m_2025/CE1KR_SSB_4B4W.txt
```

### Importar sin validación (más rápido)

```bash
python import_logs.py --clean --no-validate logs_sa10m_2025/
```

## Opciones de Línea de Comandos

| Opción | Descripción |
|--------|-------------|
| `path` | **(Requerido)** Ruta al archivo Cabrillo o directorio |
| `--clean` | Limpiar base de datos antes de importar |
| `--db PATH` | Ruta al archivo de base de datos (por defecto: `sa10_contest.db`) |
| `--rules PATH` | Archivo YAML de reglas personalizado |
| `--no-validate` | Omitir validación después de importar |
| `--pattern PATTERN` | Patrón de archivos para importar directorio (por defecto: `*.txt`) |
| `-v, --verbose` | Habilitar log detallado |

## Ejemplos

### Ejemplo 1: Importación fresca de todos los logs

```bash
python import_logs.py --clean logs_sa10m_2025/
```

Salida:
```
======================================================================
IMPORTADOR DE LOGS SA10M
======================================================================

🗑️  Limpiando base de datos...
✓ Base de datos limpiada

📂 Fuente: logs_sa10m_2025
💾 Base de datos: sa10_contest.db
✓ Validación: habilitada

Procesando directorio: logs_sa10m_2025
Patrón: *.txt
----------------------------------------------------------------------
Procesando 100 archivos de logs_sa10m_2025
...

Resumen del lote:
  Archivos procesados: 98/100
  Total QSOs: 15234
  Válidos: 14502
  Duplicados: 532
  Inválidos: 200

======================================================================
✓ Importación completa
======================================================================
```

### Ejemplo 2: Importar log único

```bash
python import_logs.py --clean CE1KR_SSB_4B4W.txt
```

### Ejemplo 3: Importar solo logs CW

```bash
python import_logs.py --clean --pattern "*_CW_*.txt" logs_sa10m_2025/
```

### Ejemplo 4: Importar a base de datos diferente

```bash
python import_logs.py --clean --db prueba.db logs_sa10m_2025/
```

### Ejemplo 5: Importación rápida sin validación

```bash
python import_logs.py --clean --no-validate logs_sa10m_2025/
```

Validar luego:
```python
from src.database.db_manager import DatabaseManager
from src.services.log_processing_pipeline import LogProcessingPipeline

db = DatabaseManager('sa10_contest.db')
pipeline = LogProcessingPipeline(db)
results = pipeline.validate_existing_logs()
print(results)
```

## Uso Programático

### API Python

```python
from src.database.db_manager import DatabaseManager
from src.services.log_processing_pipeline import LogProcessingPipeline

# Inicializar
db_manager = DatabaseManager('sa10_contest.db')

# Limpiar base de datos
db_manager.reset_database()

# Crear pipeline
pipeline = LogProcessingPipeline(db_manager)

# Importar archivo único
result = pipeline.process_file('logs_sa10m_2025/CE1KR_SSB_4B4W.txt')
print(result)

# Importar directorio
result = pipeline.process_directory('logs_sa10m_2025/')
print(result)

# Validar logs existentes
result = pipeline.validate_existing_logs()
print(result)
```

### Una línea simplificada

```python
from src.services.log_processing_pipeline import process_cabrillo_files

result = process_cabrillo_files('logs_sa10m_2025/', db_path='sa10_contest.db')
```

## ¿Qué Ocurre Durante la Importación?

### 1. Limpieza de la Base de Datos (si se usa `--clean`)
- Elimina todas las tablas
- Recrea todas las tablas (concursos, logs, contactos, resultados de validación)

### 2. Importación de Logs
Para cada archivo Cabrillo:
- Parsear el formato Cabrillo
- Extraer metadatos del log (indicativo, categoría, operadores, etc.)
- Verificar si el log ya existe (por indicativo)
- Si el log existe y el nuevo archivo es más reciente: **reemplazar** log y contactos
- Si el log no existe: **crear** nuevo log
- Importar todos los QSOs/contactos (incluidos duplicados)

### 3. Validación (si está habilitada)
Para cada log:
- Verificar contactos duplicados (mismo indicativo, banda, modo, hora)
- Validar formato de indicativo
- Validar formato del exchange (RST, Zona CQ, número de serie)
- Verificar si el contacto está dentro del período del concurso
- Marcar contactos como válidos/inválidos en la base de datos

### 4. Generación de Reportes
- Estadísticas de resumen
- Lista de errores (si los hay)

## Tablas de la Base de Datos

Después de la importación, los datos se almacenan en:

- **contests**: Definiciones de concursos (SA10M 2025, etc.)
- **logs**: Logs de estaciones (uno por indicativo)
- **contacts**: QSOs individuales
- **validation_results**: Estado de validación de cada contacto

## Resolución de Problemas

### Error: "UNIQUE constraint failed"

Ocurre al importar el mismo log dos veces. Soluciones:
- Usar `--clean` para comenzar desde cero
- El sistema ahora auto-reemplaza logs si el archivo es más reciente
- Eliminar el log específico de la base de datos primero

### Sin resultados de validación

Asegurarse de no estar usando la opción `--no-validate`.

### Importación lenta

- Usar `--no-validate` para importación más rápida
- Ejecutar validación por separado después

## Próximos Pasos

Después de importar:

1. **Consultar la base de datos** para verificar los datos:
   ```python
   from src.database.db_manager import DatabaseManager
   from src.database.repositories import LogRepository, ContactRepository
   
   db = DatabaseManager('sa10_contest.db')
   with db.get_session() as session:
       log_repo = LogRepository(session)
       logs = log_repo.get_all()
       print(f"Total logs: {len(logs)}")
       for log in logs[:5]:
           print(f"  {log.callsign}: {log.qso_count} QSOs")
   ```

2. **Calcular puntajes**

3. **Generar reportes**

## Ver También

- [Esquema de Base de Datos](../DATABASE_SCHEMA.md)
- [Referencia del Parser Cabrillo](../CABRILLO_PARSER_QUICK_REF.md)
- [Referencia del Motor de Reglas](../RULES_ENGINE_QUICK_REF.md)
