# Integración de pyhamtools

Documentación de la integración de pyhamtools para búsqueda de información de indicativos en el SA10M Contest Manager.

## Descripción General

pyhamtools es una biblioteca Python para radioaficionados que proporciona:
- **Búsqueda de indicativos** — zona CQ, zona ITU, continente, país
- **Extracción de prefijo WPX** — para scoring WPX y análisis de indicativos
- **Validación de indicativos** — verificar si un indicativo es válido y bien formado

La integración de pyhamtools complementa los datos internos de CTY.DAT en el SA10M.

## Instalación

```bash
pip install pyhamtools

# Verificar instalación
python -c "import pyhamtools; print(pyhamtools.__version__)"
```

## Búsqueda de Información de Indicativo

### Uso Básico

```python
from pyhamtools.locator import calculate_distance, calculate_heading
from pyhamtools.callinfo import CallInfo
from pyhamtools.consts import LookupLib

# Inicializar con servicio de búsqueda CTY.DAT (sin internet requerido)
callinfo = CallInfo(LookupLib.CLUBLOGAPI)
# O con datos locales:
callinfo = CallInfo(LookupLib.COUNTRYFILE, filename="data/cty.dat")

# Buscar indicativo
result = callinfo.get_all("LU2HF")
print(result)
# {
#   'adif': 100,
#   'continent': 'SA',
#   'country': 'Argentina',
#   'cqz': 13,
#   'ituz': 14,
#   'latitude': -34.0,
#   'longitude': -64.0,
#   'utc_offset': -3.0
# }
```

### get_callsign_info()

Función wrapper del SA10M que retorna información normalizada:

```python
from src.services.callsign_service import CallsignService

service = CallsignService(db_session)

# Buscar información de indicativo
info = service.get_callsign_info("LU2HF")
# CallsignInfo(
#   callsign='LU2HF',
#   country='Argentina',
#   cq_zone=13,
#   itu_zone=14,
#   continent='SA',
#   latitude=-34.0,
#   longitude=-64.0,
#   source='cty_dat'  # o 'pyhamtools' o 'manual'
# )

# Fallback automático si CTY.DAT no encuentra el indicativo
info = service.get_callsign_info("VK9/G0ABC")
# Intenta pyhamtools si CTY.DAT falla
```

### Indicativos Especiales

```python
# Portátiles
info = service.get_callsign_info("K1ABC/4")
# Resultado: SE EE.UU., zona CQ 4

info = service.get_callsign_info("LU2HF/W3")
# Resultado: EE.UU. - Este, zona CQ 5

# Especiales de DX
info = service.get_callsign_info("ZL9HR")
# Resultado: Islas Campbell, zona CQ 32

# Indicativos con sufijos no-geográficos
info = service.get_callsign_info("K1ABC/P")    # Portátil — sin cambio de zona
info = service.get_callsign_info("W1AW/MM")    # Marítimo Móvil — zona especial
info = service.get_callsign_info("VK4ABC/QRP") # QRP — sin cambio de zona
```

## Extracción de Prefijo WPX

### extract_wpx_prefix()

```python
from pyhamtools.utils import extract_wpx_prefix

# Extracciones estándar
extract_wpx_prefix("LU2HF")   # "LU2"
extract_wpx_prefix("K1ABC")   # "K1"
extract_wpx_prefix("W1AW")    # "W1"
extract_wpx_prefix("DL3SDE")  # "DL3"
extract_wpx_prefix("CE3XYZ")  # "CE3"
extract_wpx_prefix("UA9XYZ")  # "UA9"

# Indicativos portátiles
extract_wpx_prefix("K1ABC/4")  # "K4" (número del sufijo toma efecto)
extract_wpx_prefix("W1AW/0")   # "W0"
extract_wpx_prefix("LU2HF/DL") # "DL" (prefijo del país de operación)
```

### Función Wrapper SA10M

```python
from src.services.callsign_service import CallsignService

service = CallsignService(db_session)

# Obtener prefijo WPX
prefix = service.extract_wpx_prefix("LU2HF")  # "LU2"
prefix = service.extract_wpx_prefix("CE3/W1ABC")  # "CE3"

# Usar durante scoring para multiplicadores WPX
def calculate_wpx_multipliers(log_id: int) -> int:
    contacts = db.query(Contact).filter_by(log_id=log_id, is_valid=True)
    prefixes = set()
    for contact in contacts:
        prefix = service.extract_wpx_prefix(contact.callsign)
        prefixes.add(prefix)
    return len(prefixes)
```

## Validación de Indicativos

### Verificaciones Básicas

```python
from pyhamtools.callinfo import CallInfo

def validate_callsign(callsign: str) -> ValidationResult:
    """Verificar si un indicativo tiene formato válido"""
    # Verificación de regex básica
    import re
    pattern = r'^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,3}[A-Z]$'
    
    if not re.match(pattern, callsign.upper()):
        return ValidationResult(
            is_valid=False,
            error=f"Indicativo '{callsign}' no coincide con el patrón estándar"
        )
    
    # Verificar si es reconocible (pyhamtools puede buscarlo)
    try:
        info = callinfo.get_all(callsign)
        if info.get('country') == 'Unknown':
            return ValidationResult(
                is_valid=True,
                warning=f"Indicativo '{callsign}' no reconocido en base de datos DXCC"
            )
    except Exception:
        pass  # pyhamtools falló — aún puede ser válido
    
    return ValidationResult(is_valid=True)
```

### Validación de Exchange con Zona CQ

```python
def validate_cq_zone_exchange(contact: Contact, service: CallsignService) -> bool:
    """Validar que la zona CQ reportada sea correcta para el indicativo"""
    info = service.get_callsign_info(contact.their_callsign)
    
    if info is None:
        # No se pudo buscar — no podemos validar
        return True  # Beneficio de la duda
    
    try:
        reported_zone = int(contact.exchange_received)
    except ValueError:
        return False  # El exchange no es un número
    
    return reported_zone == info.cq_zone
```

## Integración durante la Importación de Logs

### Flujo de Trabajo

Cuando se importa un log, para cada contacto:

1. **Análisis del indicativo** — obtener zona CQ esperada de CTY.DAT/pyhamtools
2. **Validación del exchange** — comparar zona CQ reportada con la esperada
3. **Enriquecimiento de datos** — almacenar país/continente para estadísticas

```python
# En src/services/log_import_service.py

class LogImportService:
    def import_contact(self, contact_data: dict) -> Contact:
        contact = Contact(**contact_data)
        
        # Obtener info del indicativo de la contraparte
        their_info = self.callsign_service.get_callsign_info(
            contact.their_callsign
        )
        
        if their_info:
            # Almacenar zona esperada para comparación
            contact.their_expected_zone = their_info.cq_zone
            contact.their_country = their_info.country
            contact.their_continent = their_info.continent
            
            # Validar zona CQ en el exchange
            try:
                reported_zone = int(contact.exchange_received)
                contact.zone_mismatch = (reported_zone != their_info.cq_zone)
            except (ValueError, TypeError):
                contact.zone_mismatch = False  # No podemos validar sin número
        
        self.db.add(contact)
        return contact
```

## Modo de Fallback

Cuando pyhamtools no puede resolver un indicativo, el sistema recurre a un sistema de respaldo en capas:

```python
class CallsignService:
    def get_callsign_info(self, callsign: str) -> Optional[CallsignInfo]:
        # Capa 1: Caché de la base de datos (más rápida)
        cached = self.db.query(CallsignCache).filter_by(callsign=callsign).first()
        if cached and not cached.is_stale():
            return cached.to_info()
        
        # Capa 2: Búsqueda en base de datos CTY.DAT (sin internet)
        result = self.cty_service.lookup(callsign)
        if result:
            self._cache_result(callsign, result, source='cty_dat')
            return result
        
        # Capa 3: pyhamtools con fuentes remotas (necesita internet)
        if self.config.allow_remote_lookup:
            try:
                result = self._pyhamtools_lookup(callsign)
                if result:
                    self._cache_result(callsign, result, source='pyhamtools')
                    return result
            except Exception as e:
                logger.warning(f"pyhamtools falló para {callsign}: {e}")
        
        # Capa 4: Indicativo desconocido — retornar None
        logger.info(f"No se pudo resolver el indicativo: {callsign}")
        return None
```

## Consideraciones de Rendimiento

### Estrategia de Caché

pyhamtools puede ser lento para muchas búsquedas. El SA10M caché resultados en la base de datos:

```python
class CallsignCache(Base):
    __tablename__ = "callsign_cache"
    
    callsign = Column(String, primary_key=True)
    country = Column(String)
    cq_zone = Column(Integer)
    itu_zone = Column(Integer)
    continent = Column(String(2))
    source = Column(String)  -- 'cty_dat', 'pyhamtools', 'manual'
    cached_at = Column(DateTime)
    
    def is_stale(self, max_age_days=30) -> bool:
        return (datetime.utcnow() - self.cached_at).days > max_age_days
```

### Pre-carga de Batch

Para procesamiento de logs grandes, pre-cargar todos los indicativos:

```python
def preload_callsign_cache(contacts: List[Contact], service: CallsignService):
    """Pre-cargar cache para todos los indicativos en el log"""
    callsigns = {c.their_callsign for c in contacts}
    
    # Buscar todos a la vez
    for callsign in callsigns:
        if not service.is_cached(callsign):
            service.get_callsign_info(callsign)  # Se almacena en caché automáticamente
    
    logger.info(f"Pre-cargados {len(callsigns)} indicativos")
```

## Configuración

En `config/settings.py`:

```python
# Configuración de pyhamtools
PYHAMTOOLS_CONFIG = {
    # Fuente de datos preferida
    "lookup_source": "countryfile",  # 'countryfile', 'clublog', 'qrz'
    
    # Ruta al archivo CTY.DAT local
    "cty_dat_path": "data/cty.dat",
    
    # Permitir búsquedas remotas (requiere internet + API keys)
    "allow_remote_lookup": False,
    
    # Expiración de caché de indicativos (días)
    "cache_days": 30,
    
    # Claves de API (solo si use_online_services=True)
    "clublog_api_key": "",
    "qrz_username": "",
    "qrz_password": "",
}
```

## Solución de Problemas

### pyhamtools No Instalado

```bash
pip install pyhamtools
# Si falla:
pip install pyhamtools --upgrade
# Verificar instalación:
python -c "from pyhamtools.callinfo import CallInfo; print('OK')"
```

### Indicativo No Resuelto

```python
# Problema: service.get_callsign_info() retorna None
# Verificar manualmente:

from pyhamtools.callinfo import CallInfo
from pyhamtools.consts import LookupLib

ci = CallInfo(LookupLib.COUNTRYFILE, filename="data/cty.dat")
try:
    result = ci.get_all("EL_INDICATIVO")
    print(result)
except Exception as e:
    print(f"Error: {e}")
```

### CTY.DAT Desactualizado

```bash
# Actualizar CTY.DAT:
python update_dxcc_data.py --force

# Verificar fecha del archivo:
python update_dxcc_data.py --check
```

---

**Versión del Documento**: 1.0  
**Actualizado**: Noviembre 2025  
**Aplica a**: SA10M Contest Manager v1.0+
