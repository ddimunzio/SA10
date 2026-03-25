# Documentación del Esquema de Base de Datos

## Descripción General

El Sistema de Gestión de Concursos SA10 utiliza una base de datos relacional para almacenar logs, contactos QSO, puntajes y datos de referencia. El esquema está diseñado para soportar completamente la **especificación del formato Cabrillo v3.0** mientras proporciona capacidades eficientes de consulta y validación.

## Esquema de Base de Datos

### Tablas Principales

#### 1. **contests** (concursos)
Almacena la definición y metadatos del concurso.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| name | VARCHAR(100) | Nombre del concurso (ej: "SA10M Contest") |
| slug | VARCHAR(50) | Identificador URL-amigable (único) |
| start_date | DATETIME | Fecha/hora de inicio del concurso (UTC) |
| end_date | DATETIME | Fecha/hora de fin del concurso (UTC) |
| rules_file | VARCHAR(200) | Ruta al archivo YAML de reglas |
| created_at | DATETIME | Timestamp de creación del registro |
| updated_at | DATETIME | Timestamp de última actualización |

**Índices:**
- Clave primaria en `id`
- Índice único en `slug`

---

#### 2. **logs**
Almacena los envíos de logs Cabrillo con la información del encabezado.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| contest_id | INTEGER | Clave foránea a contests.id |
| cabrillo_version | VARCHAR(10) | Versión del formato Cabrillo (por defecto: "3.0") |
| callsign | VARCHAR(20) | Indicativo de la estación (requerido) |
| location | VARCHAR(50) | Código de ubicación (DX, SA, etc.) |
| club | VARCHAR(100) | Afiliación al club |
| contest_name | VARCHAR(100) | Campo CONTEST del Cabrillo |
| **Campos de Categoría** | | |
| category_operator | VARCHAR(50) | SINGLE-OP, MULTI-OP, etc. |
| category_assisted | VARCHAR(50) | ASSISTED, NON-ASSISTED |
| category_band | VARCHAR(20) | 10M, ALL, etc. |
| category_mode | VARCHAR(20) | SSB, CW, MIXED |
| category_power | VARCHAR(20) | HIGH, LOW, QRP |
| category_station | VARCHAR(50) | FIXED, MOBILE, PORTABLE |
| category_transmitter | VARCHAR(20) | ONE, TWO, etc. |
| category_overlay | VARCHAR(50) | TB-WIRES, ROOKIE, etc. |
| category_time | VARCHAR(20) | 6-HOURS, 12-HOURS, etc. |
| **Info del Operador** | | |
| operators | TEXT | Indicativos de operadores separados por coma |
| name | VARCHAR(200) | Nombre del operador |
| address | TEXT | Dirección completa |
| address_city | VARCHAR(100) | Ciudad |
| address_state_province | VARCHAR(100) | Provincia/Estado |
| address_postalcode | VARCHAR(20) | Código postal |
| address_country | VARCHAR(100) | País |
| grid_locator | VARCHAR(10) | Locator Maidenhead |
| email | VARCHAR(200) | Correo electrónico |
| **Puntaje y Procesamiento** | | |
| claimed_score | INTEGER | Puntaje reclamado en el log |
| created_by | VARCHAR(200) | Software de log (ej: N1MM Logger+) |
| submitted_at | DATETIME | Timestamp de envío |
| file_path | TEXT | Ruta al archivo original |
| file_hash | VARCHAR(64) | Hash SHA256 para detección de duplicados |
| status | ENUM | pending, validated, scored, published, error |
| validation_notes | TEXT | Errores/advertencias de validación |
| processed_at | DATETIME | Timestamp de procesamiento |
| metadata | JSON | Campos Cabrillo adicionales |
| created_at | DATETIME | Timestamp de creación |
| updated_at | DATETIME | Última actualización |

**Índices:**
- Clave primaria en `id`
- Índice compuesto en `(contest_id, callsign)`
- Índice en `status`
- Índice en `file_hash`

---

#### 3. **contacts** (contactos)
Almacena los registros QSO individuales de las líneas QSO del Cabrillo.

**Formato QSO Cabrillo:**
```
QSO: freq mo date time call-sent rst-sent exch-sent call-rcvd rst-rcvd exch-rcvd t
QSO:   28300 PH 2025-03-08 1207 CE1KR         59   12   DP7D          59   14
```

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| log_id | INTEGER | Clave foránea a logs.id |
| **Detalles QSO** | | |
| frequency | INTEGER | Frecuencia en kHz (requerido) |
| mode | VARCHAR(10) | PH (SSB), CW, RY (RTTY), DG (Digital) |
| qso_date | VARCHAR(10) | Fecha en formato YYYY-MM-DD |
| qso_time | VARCHAR(4) | Hora en formato HHMM UTC |
| qso_datetime | DATETIME | Datetime combinado para consultas |
| **Transmisor (Enviado)** | | |
| call_sent | VARCHAR(20) | Indicativo propio |
| rst_sent | VARCHAR(10) | Reporte de señal enviado |
| exchange_sent | VARCHAR(50) | Datos del exchange enviado (provincia/zona) |
| **Receptor (Recibido)** | | |
| call_received | VARCHAR(20) | Indicativo de la otra estación |
| rst_received | VARCHAR(10) | Reporte de señal recibido |
| exchange_received | VARCHAR(50) | Datos del exchange recibido |
| transmitter_id | VARCHAR(5) | ID de transmisor multi (0, 1, etc.) |
| **Campos Derivados** | | |
| band | VARCHAR(10) | Derivado de la frecuencia (10m, 20m, etc.) |
| **Puntuación** | | |
| points | INTEGER | Puntos otorgados por este QSO |
| is_multiplier | BOOLEAN | ¿Es un nuevo multiplicador? |
| multiplier_type | VARCHAR(50) | Tipo (provincia, país, zona) |
| multiplier_value | VARCHAR(50) | Valor (ej: "BA", "W") |
| **Validación** | | |
| is_valid | BOOLEAN | ¿Es válido este QSO? |
| is_duplicate | BOOLEAN | ¿Es un duplicado? |
| duplicate_of_id | INTEGER | FK a la primera ocurrencia |
| validation_status | ENUM | valid, duplicate, invalid_callsign, etc. |
| validation_notes | TEXT | Detalles de error de validación |
| **Verificación Cruzada** | | |
| matched_contact_id | INTEGER | FK al contacto coincidente en el otro log |
| time_diff_seconds | INTEGER | Diferencia de tiempo con el contacto coincidente |
| frequency_diff_khz | INTEGER | Diferencia de frecuencia |
| **Metadatos** | | |
| metadata | JSON | Campos adicionales |
| created_at | DATETIME | Timestamp de creación |
| updated_at | DATETIME | Última actualización |

**Valores de Estado de Validación:**
- `valid` — Contacto válido
- `duplicate` — Contacto duplicado en misma banda/modo
- `invalid_callsign` — Indicativo malformado
- `invalid_exchange` — Datos de exchange inválidos
- `out_of_period` — QSO fuera del período del concurso
- `invalid_band` — Banda inválida para el concurso
- `invalid_mode` — Modo inválido para el concurso
- `not_in_log` — No encontrado en el log de la otra estación
- `time_mismatch` — Diferencia de tiempo significativa con el contacto coincidente
- `exchange_mismatch` — Discrepancia en los datos del exchange

**Índices:**
- Clave primaria en `id`
- Índice en `log_id`
- Índice en `qso_datetime`
- Índice en `call_received`
- Índice compuesto en `(band, mode)`
- Índice en `is_valid`
- Índice en `is_duplicate`
- Índice compuesto en `(log_id, qso_datetime)`
- **Restricción única** en `(log_id, qso_datetime, call_received, band, mode)` para prevenir duplicados verdaderos

---

#### 4. **scores** (puntajes)
Almacena los puntajes calculados y desgloses detallados.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| log_id | INTEGER | Clave foránea a logs.id (único) |
| **Estadísticas QSO** | | |
| total_qsos | INTEGER | Total de QSOs en el log |
| valid_qsos | INTEGER | QSOs válidos |
| duplicate_qsos | INTEGER | QSOs duplicados |
| invalid_qsos | INTEGER | QSOs inválidos |
| not_in_log_qsos | INTEGER | QSOs no encontrados en otro log |
| **Puntuación** | | |
| total_points | INTEGER | Puntos totales antes de multiplicadores |
| multipliers | INTEGER | Número de multiplicadores trabajados |
| final_score | INTEGER | Puntaje final (puntos × multiplicadores) |
| **Desgloses Detallados (JSON)** | | |
| points_by_band | JSON | `{"10m": 1000, "20m": 500}` |
| points_by_mode | JSON | `{"CW": 800, "SSB": 700}` |
| qsos_by_band | JSON | `{"10m": 50, "20m": 30}` |
| qsos_by_mode | JSON | `{"CW": 40, "SSB": 40}` |
| qsos_by_hour | JSON | `{"12": 10, "13": 15, ...}` |
| **Detalle de Multiplicadores** | | |
| multipliers_list | JSON | `["BA", "CF", "CO", "W", "K", ...]` |
| multipliers_by_band | JSON | Multiplicadores por banda |
| **Rankings** | | |
| rank_overall | INTEGER | Ranking general |
| rank_category | INTEGER | Ranking dentro de la categoría |
| rank_country | INTEGER | Ranking dentro del país |
| **Metadatos** | | |
| calculated_at | DATETIME | Timestamp de cálculo |
| calculation_version | VARCHAR(20) | Versión del algoritmo de scoring |
| notes | TEXT | Notas adicionales |

---

### Tablas de Referencia

#### 5. **reference_provinces** (provincias de referencia)
Provincias argentinas y otros códigos de ubicación para validación.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| code | VARCHAR(10) | Código de provincia (BA, CF, CO, etc.) — único |
| name | VARCHAR(100) | Nombre completo (Buenos Aires, etc.) |
| country | VARCHAR(10) | Código de país (AR para Argentina) |
| region | VARCHAR(50) | Agrupación regional opcional |
| is_active | BOOLEAN | Para provincias históricas |

---

#### 6. **reference_dxcc**
Entidades/países DXCC para puntuación y validación.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| prefix | VARCHAR(10) | Prefijo de indicativo (LU, W, K, etc.) — único |
| entity_code | INTEGER | Número de entidad DXCC |
| entity_name | VARCHAR(100) | Nombre del país |
| continent | VARCHAR(2) | SA, NA, EU, AS, AF, OC |
| itu_zone | INTEGER | Número de zona ITU |
| cq_zone | INTEGER | Número de zona CQ |
| is_deleted | BOOLEAN | Para entidades DXCC eliminadas |

---

#### 7. **audit_logs** (logs de auditoría)
Rastro de auditoría para seguimiento de cambios y operaciones.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| entity_type | VARCHAR(50) | Log, Contact, Score |
| entity_id | INTEGER | ID de la entidad afectada |
| action | VARCHAR(50) | INSERT, UPDATE, DELETE, VALIDATE, SCORE |
| user | VARCHAR(100) | Quién realizó la acción |
| changes | JSON | Qué cambió |
| timestamp | DATETIME | Cuándo se realizó la acción |

---

## Relaciones entre Entidades

```
contests (1) ─────< (N) logs
                        │
                        ├─────< (N) contacts
                        │
                        └─────< (1) scores

contacts (1) ────< (N) contacts (auto-referencia para duplicados y coincidencias)
```

## Mapeo del Formato Cabrillo

### Mapeo de Campos del Encabezado

| Campo Cabrillo | Columna en BD |
|----------------|---------------|
| START-OF-LOG | cabrillo_version |
| LOCATION | location |
| CALLSIGN | callsign |
| CLUB | club |
| CONTEST | contest_name |
| CATEGORY-OPERATOR | category_operator |
| CATEGORY-ASSISTED | category_assisted |
| CATEGORY-BAND | category_band |
| CATEGORY-MODE | category_mode |
| CATEGORY-POWER | category_power |
| CATEGORY-STATION | category_station |
| CATEGORY-TRANSMITTER | category_transmitter |
| CATEGORY-OVERLAY | category_overlay |
| CATEGORY-TIME | category_time |
| CLAIMED-SCORE | claimed_score |
| OPERATORS | operators |
| NAME | name |
| ADDRESS | address |
| ADDRESS-CITY | address_city |
| ADDRESS-STATE-PROVINCE | address_state_province |
| ADDRESS-POSTALCODE | address_postalcode |
| ADDRESS-COUNTRY | address_country |
| GRID-LOCATOR | grid_locator |
| EMAIL | email |
| CREATED-BY | created_by |

### Mapeo de Línea QSO

```
QSO:   28300 PH 2025-03-08 1207 CE1KR         59   12   DP7D          59   14
       │     │  │          │    │             │    │    │             │    │
       │     │  │          │    │             │    │    │             │    └─ exchange_received
       │     │  │          │    │             │    │    │             └────── rst_received
       │     │  │          │    │             │    │    └──────────────────── call_received
       │     │  │          │    │             │    └───────────────────────── exchange_sent
       │     │  │          │    │             └────────────────────────────── rst_sent
       │     │  │          │    └──────────────────────────────────────────── call_sent
       │     │  │          └───────────────────────────────────────────────── qso_time
       │     │  └──────────────────────────────────────────────────────────── qso_date
       │     └─────────────────────────────────────────────────────────────── mode
       └───────────────────────────────────────────────────────────────────── frequency
```

## Decisiones de Diseño Clave

### 1. **Detección de Duplicados**
- Restricción única en `(log_id, qso_datetime, call_received, band, mode)` previene duplicados accidentales
- El flag `is_duplicate` marca QSOs duplicados dentro de un log
- `duplicate_of_id` apunta a la primera ocurrencia válida

### 2. **Validación Cruzada de Logs**
- `matched_contact_id` enlaza con el QSO correspondiente en el log de la otra estación
- `time_diff_seconds` y `frequency_diff_khz` almacenan discrepancias
- Permite detección de "no en el log" y verificación de exchanges

### 3. **Campos JSON para Flexibilidad**
- `metadata` en logs y contactos almacena campos Cabrillo poco comunes
- Los desgloses de puntaje usan JSON para análisis detallado
- Permite evolución del esquema sin migraciones

### 4. **Optimizaciones de Rendimiento**
- Índices compuestos en columnas frecuentemente consultadas
- Campo `band` desnormalizado (derivado de frecuencia) para filtrado más rápido
- `qso_datetime` pre-calculado para consultas basadas en tiempo

### 5. **Integridad de Datos**
- Restricciones de clave foránea garantizan integridad referencial
- Enums restringen valores de estado a opciones válidas
- Timestamps rastrean todos los cambios

## Ejemplos de Uso

### Crear un Concurso
```python
contest = Contest(
    name="SA10M Contest 2025",
    slug="sa10m-2025",
    start_date=datetime(2025, 3, 8, 12, 0, 0),
    end_date=datetime(2025, 3, 9, 12, 0, 0),
    rules_file="config/contests/sa10m_2025.yaml"
)
```

### Insertar un Log
```python
log = Log(
    contest_id=1,
    callsign="LU1HLH",
    category_band="10M",
    category_mode="MIXED",
    claimed_score=402720
)
```

### Agregar un Contacto
```python
contact = Contact(
    log_id=1,
    frequency=28300,
    mode="PH",
    qso_date="2025-03-08",
    qso_time="1207",
    qso_datetime=datetime(2025, 3, 8, 12, 7, 0),
    call_sent="LU1HLH",
    rst_sent="59",
    exchange_sent="13",
    call_received="DP7D",
    rst_received="59",
    exchange_received="14",
    band="10m"
)
```
