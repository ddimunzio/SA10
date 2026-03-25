# Referencia Rápida del Motor de Reglas

## Inicio Rápido

```python
from src.core.rules import load_sa10m_rules, RulesEngine, Contact
from datetime import datetime

# 1. Cargar reglas del concurso
rules = load_sa10m_rules()

# 2. Configurar información del operador
operator_info = {
    'callsign': 'LU1ABC',
    'continent': 'SA',
    'dxcc': 100,
    'cq_zone': 13
}

# 3. Crear el motor de reglas
engine = RulesEngine(rules, operator_info)

# 4. Procesar contactos
contact = Contact(
    timestamp=datetime.now(),
    callsign='W1AW',
    band='10m',
    mode='SSB',
    frequency=28500,
    rst_sent='59',
    rst_received='59',
    exchange_sent={'cq_zone': '13'},
    exchange_received={'cq_zone': '5'}
)

result = engine.process_contact(contact)

# 5. Calcular puntaje
contacts = [result]
score = engine.calculate_final_score(contacts)

print(f"Puntaje Final: {score['final_score']}")
```

## Cargar Reglas

```python
from src.core.rules import RulesLoader, load_sa10m_rules

# Método 1: Función de conveniencia
rules = load_sa10m_rules()

# Método 2: Usando el loader
loader = RulesLoader()
rules = loader.load_contest('sa10m')

# Listar concursos disponibles
contests = loader.list_contests()

# Obtener información del concurso
info = loader.get_contest_info('sa10m')
```

## Validar Reglas

```python
from src.core.rules import RulesValidator, validate_contest_rules

# Método 1: Usando la clase validadora
validator = RulesValidator(rules)
is_valid, errors, warnings = validator.validate()

if not is_valid:
    for error in errors:
        print(f"Error: {error}")

# Método 2: Función de conveniencia
result = validate_contest_rules(rules)
print(f"Válido: {result['valid']}")
print(f"Errores: {result['error_count']}")
print(f"Advertencias: {result['warning_count']}")

# Validar valores individuales del exchange
is_valid, error = validator.validate_exchange_value('cq_zone', '13', 'SSB')
```

## Crear Contactos

```python
from src.core.rules import Contact
from datetime import datetime

contact = Contact(
    timestamp=datetime.now(),
    callsign='W1AW',           # Estación trabajada
    band='10m',                # Banda
    mode='SSB',                # Modo
    frequency=28500,           # Frecuencia en kHz
    rst_sent='59',             # Reporte enviado
    rst_received='59',         # Reporte recibido
    exchange_sent={'cq_zone': '13'},      # Exchange enviado
    exchange_received={'cq_zone': '5'}    # Exchange recibido
)
```

## Procesar Contactos

```python
# Crear motor
engine = RulesEngine(rules, operator_info)

# Procesar un contacto
result = engine.process_contact(contact)

# Ver resultados
print(f"Puntos: {result.points}")
print(f"Duplicado: {result.is_duplicate}")
print(f"Multiplicador: {result.is_multiplier}")
print(f"Tipos de mult.: {result.multiplier_types}")
```

## Calcular Puntajes

```python
# Procesar todos los contactos
processed_contacts = [engine.process_contact(c) for c in contacts]

# Calcular puntaje final
score = engine.calculate_final_score(processed_contacts)

# Acceder al desglose
print(f"Total QSOs:        {score['total_qsos']}")
print(f"QSOs Válidos:      {score['valid_qsos']}")
print(f"Duplicados:        {score['duplicate_qsos']}")
print(f"Total Puntos:      {score['total_points']}")
print(f"Mults WPX:         {score['wpx_multipliers']}")
print(f"Mults Zona:        {score['zone_multipliers']}")
print(f"Puntaje Final:     {score['final_score']}")

# Desglose por banda
for band, band_score in score['band_scores'].items():
    print(f"\n{band}:")
    print(f"  QSOs: {band_score['qsos']}")
    print(f"  Puntos: {band_score['points']}")
    print(f"  Mults Zona: {band_score['zone_mults']}")
    print(f"  Puntaje: {band_score['score']}")
```

## Información del Operador

```python
operator_info = {
    'callsign': 'LU1ABC',      # Su indicativo
    'continent': 'SA',          # Su continente (SA, NA, EU, AS, AF, OC, AN)
    'dxcc': 100,               # Código de entidad DXCC
    'cq_zone': 13              # Su zona CQ (1-40)
}
```

## Extracción de Prefijo WPX

```python
# Extraer prefijo WPX de un indicativo
prefix = engine._extract_wpx_prefix('W1AW')      # Retorna: 'W1'
prefix = engine._extract_wpx_prefix('LU3DRP')    # Retorna: 'LU3'
prefix = engine._extract_wpx_prefix('9A3YT')     # Retorna: '9A3'
```

## Reglas de Puntuación SA10M

### Puntos
| Tipo de Contacto | Puntos |
|-----------------|--------|
| Mismo DXCC | 0 |
| SA → estación no-SA | 4 |
| SA → estación SA (distinto DXCC) | 2 |
| no-SA → estación SA | 4 |
| no-SA → estación no-SA | 2 |

### Multiplicadores
1. **Prefijo WPX** — Cada prefijo único (en todo el concurso)
2. **Zona CQ** — Cada zona única por banda

### Fórmula de Puntaje Final
```
Puntaje por Banda = Puntos QSO × (Mults Prefijo WPX + Mults Zona CQ en esa banda)
Puntaje Final = Suma de puntajes de todas las bandas
```

### Ejemplo de Cálculo
```
Banda 10m:
  - 10 QSOs = 50 puntos
  - 3 prefijos WPX (W1, K3, CE7)
  - 2 zonas CQ (5, 12)
  
Puntaje 10m = 50 × (3 + 2) = 250

Si solo se trabajó la banda 10m:
Puntaje Final = 250
```

## Detección de Duplicados

SA10M usa ventana de duplicados **banda_modo**:
- Mismo indicativo en misma banda Y mismo modo = Duplicado (0 puntos)
- Mismo indicativo en modo diferente = Nuevo QSO ✓
- Mismo indicativo en banda diferente = Nuevo QSO ✓

```python
# Primer contacto
contact1 = Contact(..., callsign='W1AW', band='10m', mode='SSB', ...)
result1 = engine.process_contact(contact1)  # is_duplicate = False

# Duplicado - misma banda, mismo modo
contact2 = Contact(..., callsign='W1AW', band='10m', mode='SSB', ...)
result2 = engine.process_contact(contact2)  # is_duplicate = True, points = 0

# No duplicado - modo diferente
contact3 = Contact(..., callsign='W1AW', band='10m', mode='CW', ...)
result3 = engine.process_contact(contact3)  # is_duplicate = False
```

## Patrones Comunes

### Procesar Archivo de Log (Conceptual)

```python
from src.core.rules import load_sa10m_rules, RulesEngine
from src.parsers import CabrilloParser

# Cargar reglas y parsear log
rules = load_sa10m_rules()
parser = CabrilloParser()
log_data = parser.parse('ruta/al/log.cbr')

# Crear motor con datos del operador del log
operator_info = {
    'callsign': log_data.callsign,
    'continent': log_data.continent,
    'dxcc': log_data.dxcc,
    'cq_zone': log_data.cq_zone
}
engine = RulesEngine(rules, operator_info)

# Procesar todos los contactos
results = [engine.process_contact(c) for c in log_data.contacts]

# Calcular puntaje
score = engine.calculate_final_score(results)
```

## Pruebas

```bash
# Ejecutar todas las pruebas del motor de reglas
python -m pytest tests/test_rules_engine.py -v

# Ejecutar clase de prueba específica
python -m pytest tests/test_rules_engine.py::TestRulesEngine -v

# Ejecutar prueba específica
python -m pytest tests/test_rules_engine.py::TestRulesEngine::test_wpx_prefix_extraction -v
```

## Resolución de Problemas

### Problema: Archivo de reglas no encontrado
```python
# Asegurarse de estar en el directorio raíz del proyecto
# O especificar ruta completa a config/contests/
loader = RulesLoader(Path('/ruta/completa/a/config/contests'))
```

### Problema: Errores de validación
```python
validator = RulesValidator(rules)
is_valid, errors, warnings = validator.validate()
for error in errors:
    print(error)
```

### Problema: Puntos calculados incorrectamente
```python
for rule in rules.scoring.points:
    if engine._evaluate_conditions(rule.conditions, contact):
        print(f"Regla coincidente: {rule.description} = {rule.value} puntos")
        break
```

## Referencia de API

### Contact
```python
Contact(
    timestamp: datetime,
    callsign: str,
    band: str,
    mode: str,
    frequency: int,
    rst_sent: str,
    rst_received: str,
    exchange_sent: Dict[str, str],
    exchange_received: Dict[str, str],
    operator_info: Optional[Dict[str, Any]] = None
)

# Campos calculados (establecidos por RulesEngine):
contact.points: int
contact.is_duplicate: bool
contact.is_multiplier: bool
contact.multiplier_types: List[str]
contact.validation_errors: List[str]
```

### RulesEngine
```python
engine = RulesEngine(rules: ContestRules, operator_info: Dict[str, Any])

# Métodos
engine.process_contact(contact: Contact) -> Contact
engine.calculate_final_score(contacts: List[Contact]) -> Dict[str, Any]

# Propiedades
engine.worked_prefixes: Set[str]
engine.worked_zones_per_band: Dict[str, Set[str]]
engine.worked_calls: Dict[str, List[Contact]]
```

### Diccionario de Puntaje
```python
{
    'total_qsos': int,
    'valid_qsos': int,
    'duplicate_qsos': int,
    'total_points': int,
    'wpx_multipliers': int,
    'zone_multipliers': int,
    'zone_mults_per_band': Dict[str, int],
    'band_scores': Dict[str, Dict],
    'final_score': int
}
```

---

**Última Actualización:** Noviembre 17, 2025
