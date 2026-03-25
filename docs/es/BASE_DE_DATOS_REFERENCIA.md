# Referencia Rápida de Base de Datos

## Inicializar la Base de Datos

```python
from src.database.db_manager import init_database, populate_reference_data

# Crear base de datos con tablas
db = init_database("sqlite:///sa10_contest.db")

# Agregar datos de referencia (provincias, DXCC)
with db.get_session() as session:
    populate_reference_data(session)
```

## Consultas Frecuentes

### Obtener todos los logs de un concurso
```python
from src.database.models import Log

with db.get_session() as session:
    logs = session.query(Log).filter_by(contest_id=1).all()
```

### Obtener contactos de un log
```python
from src.database.models import Contact

with db.get_session() as session:
    contacts = session.query(Contact).filter_by(log_id=1).all()
```

### Obtener solo contactos válidos
```python
contacts = session.query(Contact)\
    .filter_by(log_id=1, is_valid=True)\
    .all()
```

### Obtener contactos por banda y modo
```python
contacts = session.query(Contact)\
    .filter_by(log_id=1, band="10m", mode="PH")\
    .all()
```

### Contar duplicados
```python
duplicates = session.query(Contact)\
    .filter_by(log_id=1, is_duplicate=True)\
    .count()
```

### Obtener multiplicadores
```python
from src.database.models import CTYData

# Obtener todas las entidades sudamericanas del CTY data
sa_entities = session.query(CTYData)\
    .filter_by(continent="SA")\
    .all()

# Buscar prefijo de indicativo
def lookup_prefix(callsign):
    for entry in session.query(CTYData).all():
        for prefix in entry.prefixes:
            if callsign.startswith(prefix):
                return entry
    return None
```

## Uso de Modelos Pydantic

### Validar un contacto
```python
from src.core.models import ContactCreate

# La validación ocurre automáticamente
contact_data = ContactCreate(
    log_id=1,
    frequency=28300,
    mode="PH",
    qso_date="2025-03-08",
    qso_time="1207",
    call_sent="LU1HLH",
    rst_sent="59",
    exchange_sent="13",
    call_received="DP7D",
    rst_received="59",
    exchange_received="14"
)

# Acceder a campos calculados
print(contact_data.qso_datetime)  # objeto datetime
print(contact_data.band)          # "10m"
```

## Esquema de Base de Datos (Resumen)

```
contests
├── id (PK)
├── name
├── slug
├── start_date
├── end_date
└── rules_file

logs
├── id (PK)
├── contest_id (FK → contests.id)
├── callsign
├── category_* (9 campos)
├── operators, name, address, email
└── claimed_score

contacts
├── id (PK)
├── log_id (FK → logs.id)
├── frequency, mode, qso_datetime
├── call_sent, rst_sent, exchange_sent
├── call_received, rst_received, exchange_received
├── band (derivado)
├── points, is_multiplier
├── is_valid, is_duplicate
└── matched_contact_id (FK → contacts.id)

scores
├── id (PK)
├── log_id (FK → logs.id, único)
├── total_qsos, valid_qsos
├── total_points, multipliers
├── final_score
└── *_by_band, *_by_mode (JSON)
```

## Comandos CLI

```bash
# Inicializar desde Python
python -c "from src.database.db_manager import init_database; db = init_database('sqlite:///contest.db')"
```
