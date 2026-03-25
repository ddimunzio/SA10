# Pipeline de Procesamiento de Logs — Referencia Rápida

**Última Actualización**: Noviembre 17, 2025

## Descripción General

El Pipeline de Procesamiento de Logs proporciona un flujo de trabajo completo para importar y validar logs de concurso. Combina parsing Cabrillo, almacenamiento en base de datos y validación exhaustiva en un único proceso simplificado.

---

## Inicio Rápido

### Procesar un Archivo Único

```python
from src.services.log_processing_pipeline import process_cabrillo_files

# Importar y validar
result = process_cabrillo_files("log.txt", validate=True)

print(result['message'])
# Salida: Successfully processed AA2A: 718 QSOs (711 valid, 6 duplicates, 1 invalid)
```

### Procesar un Directorio

```python
result = process_cabrillo_files("logs_sa10m_2025/", validate=True)

print(f"Archivos: {result['successful']}/{result['total_files']}")
print(f"QSOs: {result['total_contacts']} ({result['valid_contacts']} válidos)")
```

---

## Flujo del Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              PIPELINE DE PROCESAMIENTO DE LOGS               │
└─────────────────────────────────────────────────────────────┘

1. FASE DE IMPORTACIÓN
   ├─ Parsear archivo Cabrillo
   ├─ Extraer encabezado y datos de QSO
   ├─ Crear/encontrar concurso en base de datos
   ├─ Crear entrada de log
   └─ Importar TODOS los contactos (incluyendo duplicados)

2. FASE DE VALIDACIÓN
   ├─ Cargar reglas del concurso
   ├─ Ordenar contactos por timestamp
   ├─ Detección de duplicados
   ├─ Validación de exchange (RS/RST, zona CQ)
   ├─ Validación de indicativo
   ├─ Validación de tiempo (período del concurso)
   ├─ Validación de banda/modo
   └─ Actualizar base de datos con resultados

3. RESULTADOS
   └─ Retornar estadísticas completas
```

---

## Referencia de API

### Clase LogProcessingPipeline

```python
from src.services.log_processing_pipeline import LogProcessingPipeline
from src.database.db_manager import DatabaseManager

db = DatabaseManager("contest.db")
pipeline = LogProcessingPipeline(db, rules_file=None)
```

**Métodos:**

#### process_file()
```python
result = pipeline.process_file(
    file_path="log.txt",
    contest_id=None,  # Auto-detectado del log
    validate=True     # Ejecutar validación después de importar
)
```

**Retorna:**
```python
{
    'success': True,
    'file': 'log.txt',
    'import': {...},      # Resultados de importación
    'validation': {...},  # Resultados de validación
    'message': 'Successfully processed AA2A: 718 QSOs...'
}
```

#### process_directory()
```python
results = pipeline.process_directory(
    directory_path="logs/",
    pattern="*.txt",
    contest_id=None,
    validate=True
)
```

**Retorna:**
```python
{
    'total_files': 916,
    'successful': 850,
    'failed': 66,
    'total_contacts': 45123,
    'valid_contacts': 44892,
    'duplicate_contacts': 189,
    'invalid_contacts': 42,
    'details': [...],
    'message': 'Processed 850/916 files successfully...'
}
```

#### validate_existing_logs()
```python
# Re-validar logs ya presentes en la base de datos
results = pipeline.validate_existing_logs(log_ids=None)
```

---

## Reglas de Validación

### Detección de Duplicados

**Regla**: Mismo indicativo + misma banda + mismo modo

```python
# Primer contacto: OK
QSO: 28500 PH 2025-03-08 1200 TEST 59 13 W1AW 59 05  ✓

# Misma estación, misma banda, mismo modo: DUPLICADO
QSO: 28500 PH 2025-03-08 1300 TEST 59 13 W1AW 59 05  ✗ DUPLICADO

# Misma estación, modo diferente: OK
QSO: 28025 CW 2025-03-08 1400 TEST 599 13 W1AW 599 05  ✓
```

### Validación de Exchange

**Formato RS/RST:**
- SSB/PH: 2 dígitos (ej: "59")
- CW: 3 dígitos (ej: "599")

**Zona CQ:**
- Debe ser número del 1 al 40

**Ejemplos:**
```
✓ Válido:   59 13  (SSB)
✓ Válido:   599 25 (CW)
✗ Inválido: 5 13   (falta dígito)
✗ Inválido: 59 45  (zona > 40)
✗ Inválido: 599 D  (no es número)
```

### Validación de Indicativo

**Formato Básico:**
- Debe tener letras y números
- Solo se permiten A-Z, 0-9 y /

**Ejemplos:**
```
✓ Válido:   W1AW, K1ABC, LU1ABC
✓ Válido:   G4OPE/P, W1AW/MM
✗ Inválido: 123, ABC, W1AW!
```

### Validación de Tiempo

**Regla**: El QSO debe estar dentro del período del concurso

```python
Concurso: 2025-03-08 00:00 a 2025-03-09 23:59:59

✓ 2025-03-08 12:00  (OK)
✗ 2025-03-07 23:00  (antes del concurso)
✗ 2025-03-10 01:00  (después del concurso)
```

---

## Estructuras de Resultado

### Resultado de Importación

```python
{
    'success': True,
    'log_id': 1,
    'callsign': 'AA2A',
    'qso_count': 718,
    'contest_id': 3,
    'contest_name': 'SA10-DX',
    'parse_errors': [],
    'parse_warnings': [],
    'message': 'Successfully imported 718 QSOs for AA2A'
}
```

### Resultado de Validación

```python
{
    'total_contacts': 718,
    'valid_contacts': 711,
    'duplicate_contacts': 6,
    'invalid_contacts': 1,
    'errors': [
        'Contacto duplicado (mismo indicativo/banda/modo)',
        'Formato de zona CQ inválido: "D" (debe ser número 1-40)',
        ...
    ],
    'warnings': [
        'Estación móvil: W1AW/MM',
        ...
    ]
}
```

---

## Actualizaciones en la Base de Datos

### Campos de Contacto Actualizados

Después de la validación, se actualizan los siguientes campos:

```python
contact.is_valid = True/False
contact.is_duplicate = True/False
contact.validation_status = 'valid' | 'duplicate' | 'invalid'
contact.validation_message = 'Detalles del error...'
contact.points = 0  # Para duplicados/inválidos
```

### Consultar Contactos Validados

```python
from src.database.repositories import ContactRepository

with db.get_session() as session:
    repo = ContactRepository(session)
    
    # Obtener todos los contactos
    all_contacts = repo.get_all_for_log(log_id=1)
    
    # Obtener solo contactos válidos
    valid_contacts = repo.get_valid_for_log(log_id=1)
    
    # Obtener duplicados
    duplicates = [c for c in all_contacts if c.is_duplicate]
```

---

## Manejo de Errores

### Errores Comunes

**1. Archivo no encontrado**
```python
{
    'success': False,
    'message': 'File not found: log.txt'
}
```

**2. Errores de parsing**
```python
{
    'success': False,
    'message': 'Parse errors: Missing CALLSIGN tag; Invalid QSO format'
}
```

**3. Errores de base de datos**
```python
{
    'success': False,
    'message': 'Error importing log: UNIQUE constraint failed'
}
```

### Gestionar Errores

```python
result = pipeline.process_file("log.txt")

if not result['success']:
    print(f"Error: {result['message']}")
    
    if result['import']:
        print(f"Errores de parsing: {result['import']['parse_errors']}")
        print(f"Advertencias: {result['import']['parse_warnings']}")
```

---

## Configuración

### Archivo de Reglas Personalizado

```python
pipeline = LogProcessingPipeline(
    db_manager,
    rules_file="config/contests/mi_concurso.yaml"
)
```

### Omitir Validación

```python
# Solo importar, sin validar
result = pipeline.process_file("log.txt", validate=False)
```

### Base de Datos Personalizada

```python
db = DatabaseManager("mi_concurso.db")
pipeline = LogProcessingPipeline(db)
```

---

## Consejos de Rendimiento

### Procesamiento en Lote

Para directorios grandes, usar procesamiento por lotes:

```python
# Procesar todos los archivos a la vez
results = pipeline.process_directory("logs/")
# Mucho más rápido que procesar individualmente
```

### Procesamiento en Chunks (para 1000+ archivos)

```python
import glob
from pathlib import Path

files = list(Path("logs/").glob("*.txt"))

# Procesar en bloques de 100
for i in range(0, len(files), 100):
    chunk = files[i:i+100]
    for file in chunk:
        result = pipeline.process_file(str(file))
```

---

## Ejemplos

### Ejemplo 1: Importar Todos los Logs y luego Validar

```python
# Paso 1: Importar todos los logs (rápido)
for file in log_files:
    pipeline.process_file(file, validate=False)

# Paso 2: Validar todos los logs en lote
pipeline.validate_existing_logs()
```

### Ejemplo 2: Encontrar Todos los Duplicados

```python
from src.database.repositories import ContactRepository

with db.get_session() as session:
    repo = ContactRepository(session)
    contacts = repo.get_all_for_log(log_id=1)
    
    duplicates = [c for c in contacts if c.is_duplicate]
    
    for dup in duplicates:
        print(f"{dup.qso_datetime} - {dup.call_received} "
              f"({dup.band} {dup.mode})")
```

### Ejemplo 3: Generar Reporte de Validación

```python
result = pipeline.process_file("log.txt")

if result['validation']:
    val = result['validation']
    callsign = result['import']['callsign']
    
    print(f"Reporte de Validación para {callsign}")
    print(f"=" * 60)
    print(f"Total QSOs:     {val['total_contacts']}")
    print(f"Válidos:        {val['valid_contacts']}")
    print(f"Duplicados:     {val['duplicate_contacts']}")
    print(f"Inválidos:      {val['invalid_contacts']}")
    
    if val['errors']:
        print("\nErrores:")
        for error in val['errors']:
            print(f"  - {error}")
```

---

## Resolución de Problemas

### Problema: "No such table: contests"

**Solución**: Las tablas de la base de datos no fueron creadas

```python
db = DatabaseManager("contest.db")
db.create_all_tables()  # Crear tablas
pipeline = LogProcessingPipeline(db)
```

### Problema: Los duplicados no se marcan

**Verificar**:
1. La validación está habilitada: `validate=True`
2. La base de datos fue actualizada: verificar `contact.is_duplicate`
3. Las fechas del concurso son correctas

### Problema: Todos los QSOs marcados como inválidos

**Verificar**:
1. Fechas del concurso en la base de datos
2. Los timestamps de los QSOs están dentro del período del concurso
3. Las fechas de inicio/fin del concurso son correctas

---

**Versión del Documento**: 1.0  
**Creado**: Noviembre 17, 2025  
**Estado**: Fase 4.1 Completa
