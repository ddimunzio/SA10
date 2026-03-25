# Guía de Datos DXCC

Guía completa para gestionar datos de entidades DXCC usados en validación de indicativos y determinación de zonas en el sistema SA10M.

## ¿Qué son los Datos DXCC?

Los datos DXCC (DX Century Club) identifican entidades de radio amateur en todo el mundo:
- **Prefijos de indicativo** mapeados a entidades y zonas CQ
- **Latitud/Longitud** para cálculo de distancia
- **Zona ITU** además de la zona CQ
- **Continente** para estadísticas de categoría

El sistema descarga estos datos del archivo **CTY.DAT** estándar de la industria.

## Archivo CTY.DAT

El archivo CTY.DAT es el estándar de la industria para datos de prefijos DXCC. Se mantiene en:
- [https://www.country-files.com/](https://www.country-files.com/) (BigCTY - más completo)
- [http://www.k1jt.com/wsjtx/countries2.txt](http://www.k1jt.com/wsjtx/countries2.txt) (WSJT-X)

### Formato del Archivo CTY.DAT

```
Callsign Prefix Data Format:

Country Name;   <= Campo: nombre del país
CQ Zone;        <= Zona CQ
ITU Zone;       <= Zona ITU
Continent;      <= Código de continente (NA, SA, EU, AF, AS, OC)
Latitude;       <= Latitud (Norte = positivo)
Longitude;      <= Longitud (Oeste = negativo en CTY.DAT)
UTC Offset;     <= Diferencia horaria UTC
Primary DXCC Prefix: <= Prefijo principal del país
    prefix1,
    =exact_call,     <= '=' indica indicativo exacto en vez de prefijo
    prefix2/;         <= '/' al final termina el bloque del país
```

### Ejemplo de Entradas CTY.DAT

```
Argentina:                            <= Nombre del país
  13:                                 <= Zona CQ
  14:                                 <= Zona ITU
  SA:                                 <= Continente
  -38.0:                              <= Latitud
  -65.0:                              <= Longitud
  -3.0:                               <= Diferencia UTC
  LU:                                 <= Prefijo principal
     AY,AZ,L2,L3,...,LU,LV,LW,LX,...; <= Prefijos adicionales

Chile:
  12:     <= Zona CQ
  14:
  SA:
  -30.0:
  -71.0:
  -4.0:
  CE:
     3G,CA,CB,CC,CD,CE,XQ,XR;

Germany:
  14:
  28:
  EU:
  51.0:
  10.0:
  -1.0:
  DL:
     DA,DB,DC,DD,DE,DF,DG,DH,DI,DJ,DK,DL,DM,DN,DO,DP,DQ,DR,Y2,...;
```

## Cargador de Datos DXCC

### DXCCDataLoader

El servicio `DXCCDataLoader` analiza CTY.DAT y lo almacena en la base de datos:

```python
from src.services.dxcc_data_loader import DXCCDataLoader

# Inicializar el cargador
loader = DXCCDataLoader(db_session)

# Descargar y cargar datos frescos
loader.download_and_load(url="https://www.country-files.com/cty/cty.dat")

# Cargar desde archivo local
loader.load_from_file("data/cty.dat")

# Actualizar entrada específica
loader.update_entry(prefix="LU", cq_zone=13)

# Buscar información de indicativo
info = loader.lookup_callsign("LU2HF")
# Retorna: {'prefix': 'LU', 'country': 'Argentina', 'cq_zone': 13, 'continent': 'SA'}
```

### Esquema de la Tabla CTYData

```python
class CTYData(Base):
    """Entidades DXCC de CTY.DAT"""
    __tablename__ = "cty_data"
    
    id = Column(Integer, primary_key=True)
    country = Column(String, nullable=False)
    cq_zone = Column(Integer, nullable=False)
    itu_zone = Column(Integer, nullable=False)
    continent = Column(String(2), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    utc_offset = Column(Float, nullable=False)
    primary_prefix = Column(String, unique=True, nullable=False)
    prefixes = Column(JSON, nullable=False, default=list)  # Lista de prefijos adicionales
    exact_calls = Column(JSON, nullable=False, default=list)  # Indicativos exactos con '='
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    def lookup(prefix: str) -> Optional['CTYData']:
        """Buscar datos por prefijo (método estático)"""
        ...
```

## Actualización de Datos DXCC

### Usando update_dxcc_data.py

```bash
# Descargar y actualizar datos DXCC desde la fuente predeterminada
python update_dxcc_data.py

# Descargar desde URL específica
python update_dxcc_data.py --url https://www.country-files.com/cty/cty.dat

# Cargar desde archivo local (sin descarga)
python update_dxcc_data.py --file data/cty.dat

# Verificar datos actuales sin actualizar
python update_dxcc_data.py --check

# Forzar actualización aunque ya esté actualizado
python update_dxcc_data.py --force
```

### Salida Esperada

```
SA10M Contest Manager — Actualización de Datos DXCC
==========================================
Descargando CTY.DAT desde https://www.country-files.com/cty/cty.dat...
✓ Descargado: 482KB, 5847 prefijos
Analizando archivo CTY.DAT...
✓ Encontradas 340 entidades DXCC
✓ 4823 prefijos estándar
✓ 198 indicativos exactos (=)
✓ 34 divisiones/excepciones DXCC
Actualizando base de datos...
✓ 312 entidades nuevas insertadas
✓ 28 entidades existentes actualizadas
✓ 0 entidades eliminadas (sin cambios)

Datos DXCC actualizados exitosamente
Fecha: None
Total entidades: 340
Total prefijos: 4823
```

## Integración con Scoring del Concurso

### Búsqueda de Zona CQ

El motor de reglas del SA10M usa CTY.DAT para validar las zonas CQ reportadas:

```python
from src.services.dxcc_service import DXCCService

dxcc = DXCCService(db_session)

# Buscar zona CQ para un indicativo
info = dxcc.lookup_callsign("K1ABC")
print(info.cq_zone)  # 5 (Estados Unidos - Este)

info = dxcc.lookup_callsign("LU2HF")
print(info.cq_zone)  # 13 (Argentina)

info = dxcc.lookup_callsign("CE3XYZ")
print(info.cq_zone)  # 12 (Chile)

# Buscar país/entidad
print(info.country)    # "Chile"
print(info.continent)  # "SA"
```

### Validación de Exchange

Durante la importación y el scoring, el sistema SA10M valida la zona CQ reportada contra CTY.DAT:

```python
def validate_exchange(contact: Contact, dxcc: DXCCService) -> ValidationResult:
    # Obtener zona CQ esperada de CTY.DAT
    info = dxcc.lookup_callsign(contact.their_callsign)
    expected_zone = info.cq_zone if info else None
    
    # Comparar con la zona reportada en el log
    reported_zone = int(contact.exchange_received)
    
    if expected_zone and reported_zone != expected_zone:
        return ValidationResult(
            is_valid=False,
            error=f"Zona CQ reportada {reported_zone} no coincide con {expected_zone} esperada para {contact.their_callsign}"
        )
    
    return ValidationResult(is_valid=True)
```

### Multiplicadores por Zona

El SA10M usa zonas CQ como multiplicadores:

```python
from src.core.rules.rules_engine import RulesEngine

engine = RulesEngine(db_session)

# Las zonas CQ únicas trabajadas desde SA son multiplicadores
multipliers = engine.calculate_multipliers(log_id=1)
# Retorna: {'zones': [3, 4, 5, 8, 9, 10, 11, 12, 13, 14, 15], 'count': 11}
```

## Resolución de Indicativos Especiales

### Indicativos con Modificadores

CTY.DAT maneja indicativos especiales:

```python
# Indicativos portátiles — se resuelven por sufijo/prefijo
"W1ABC/4"   -> Zona 4 (sureste de EE.UU.)
"K9XYZ/VE3" -> Canadá
"G0ABC/P"   -> G (Reino Unido), sin cambio de zona

# Indicativos de isla/prefijo especial
"=W1AW"     -> Indicativo exacto, tratamiento especial DXCC
"VP5/K1ABC" -> VP5 (Islas Turcas y Caicos)
```

### Lógica de Resolución del DXCCService

```python
def resolve_callsign(callsign: str) -> DXCCInfo:
    # 1. Manejar indicativos portátiles (ej: LU2HF/CE)
    if '/' in callsign:
        prefix_part, suffix_part = split_portable(callsign)
        # Intentar sufijo primero, luego prefijo
    
    # 2. Buscar indicativo exacto (=indicativo en CTY.DAT)
    exact_match = lookup_exact(callsign)
    if exact_match:
        return exact_match
    
    # 3. Búsqueda por prefijo (de más largo a más corto)
    for length in range(len(callsign), 0, -1):
        prefix = callsign[:length]
        result = lookup_prefix(prefix)
        if result:
            return result
    
    # 4. Falló la búsqueda — indicativo desconocido
    return DXCCInfo(country="Desconocido", cq_zone=0)
```

## Mantenimiento y Solución de Problemas

### Actualización Periódica

Los datos DXCC cambian raramente, pero actualizar antes de cada concurso major es una buena práctica:

```bash
# Antes de un concurso importante
python update_dxcc_data.py --force

# Programar actualización mensual (crontab en Linux/Mac)
# 0 0 1 * * cd /path/to/sa10m && python update_dxcc_data.py
```

### Problemas Comunes

#### 1. Indicativo no encontrado

```
Problema: DXCCService retorna None para un indicativo
Causas:
  - Prefijo muy nuevo no en CTY.DAT
  - Prefijo no estándar o experimental
  - Indicativo malformado en el log

Solución:
  1. Actualizar CTY.DAT: python update_dxcc_data.py --force
  2. Verificar el indicativo en QRZ.com
  3. Agregar excepción manual en el archivo de config del concurso
```

#### 2. Error de zona CQ

```
Problema: Zona CQ incorrecta asignada a un indicativo
Causas:
  - Datos CTY.DAT desactualizados
  - Indicativo portátil con prefijo ambiguo
  - Excepción de subdivisión DXCC no cargada

Solución:
  1. Actualizar CTY.DAT: python update_dxcc_data.py --force
  2. Verificar manualmente en https://www.country-files.com/
  3. Ajuste manual en entry.zone_override en la base de datos
```

#### 3. Archivo CTY.DAT no puede descargarse

```
Problema: Error de red al descargar CTY.DAT
Solución:
  1. Descargar manualmente desde https://www.country-files.com/cty/cty.dat
  2. Guardar como data/cty.dat
  3. Cargar: python update_dxcc_data.py --file data/cty.dat
```

### Inspección de Datos

```bash
# Verificar entidad específica de datos cargados
python -c "
from src.services.dxcc_service import DXCCService
from src.database import get_session
service = DXCCService(next(get_session()))
info = service.lookup_callsign('LU2HF')
print(f'País: {info.country}, Zona CQ: {info.cq_zone}')
"

# Generar reporte de entidades cargadas
python update_dxcc_data.py --report
```

---

**Última modificación**: Noviembre 19, 2025  
**Aplica a**: SA10M Contest Manager v1.0+
