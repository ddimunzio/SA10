# Especificación del Formato de Reporte UBN

**UBN**: Reporte de Únicos / Erróneos / No en el Log (Unique / Busted / Not-in-log)  
**Propósito**: Identificar errores en los envíos de logs mediante validación cruzada entre logs

## Estructura del Reporte UBN

### Formato de Reporte por Estación

```
================================================================================
REPORTE UBN PARA: K1ABC
Concurso: SA10M Contest 2025
Categoría: Operador Único Mixto
================================================================================

ESTADÍSTICAS RESUMEN:
  Total QSOs reclamados:     234
  QSOs válidos confirmados:  218
  QSOs duplicados:           3
  QSOs inválidos:            1
  
  Indicativos ÚNICOS:        8  (3.4%)
  Indicativos ERRÓNEOS:      3  (1.3%)
  NO EN EL LOG:              4  (1.7%)
  
  Tasa de Error:             6.4%
  Tasa de Confirmación:      93.6%

================================================================================
INDICATIVOS ÚNICOS (no encontrados en ningún otro log enviado):
================================================================================

Estos indicativos aparecen solo en su log. Pueden ser:
- Estaciones que no enviaron log
- Indicativos copiados incorrectamente
- Indicativos inexistentes

  Banda  Modo  Fecha-Hora (UTC) Indicativo  Exchange
  -----  ----  ---------------  ----------  -------------
  28MHz  SSB   2025-03-08 1234  K9XYZ       59  05
  28MHz  CW    2025-03-08 1456  LU9ZZZ      599 13
  28MHz  SSB   2025-03-08 1823  W1ABC/MM    59  11
  ...

================================================================================
INDICATIVOS ERRÓNEOS (indicativo copiado incorrectamente):
================================================================================

Su log muestra un indicativo que no coincide con ningún log enviado, pero es muy
similar a otro que sí fue enviado. La otra estación puede haberle trabajado.

  Banda  Modo  Fecha-Hora (UTC) Anotado Como  Debe Ser    Exchange
  -----  ----  ---------------  ------------  ----------  -------------
  28MHz  SSB   2025-03-08 1456  W1ZZZ         W1XXX (*)   59  05
  28MHz  CW    2025-03-08 1634  K9JX          K9JY  (*)   599 04
  28MHz  SSB   2025-03-08 2103  LU1AZ         LU1AB (*)   59  13

  (*) = La estación envió log y lo tiene a usted con el indicativo correcto

================================================================================
NO EN EL LOG (NIL) - La otra estación no tiene registro del QSO:
================================================================================

Estos contactos aparecen en su log, pero el log de la otra estación no muestra
este QSO. Posibles razones:
- La otra estación no anotó el contacto
- Discrepancia de tiempo/banda/modo (fuera de la ventana de tolerancia)
- La otra estación anotó su indicativo de forma diferente

  Banda  Modo  Fecha-Hora (UTC) Indicativo  Su Exchange    Su Exchange (ellos)
  -----  ----  ---------------  ----------  -------------  -------------------
  28MHz  CW    2025-03-08 1834  LU5ABC      599 05         599 13 (*)
  28MHz  SSB   2025-03-08 1945  EA5BH       59  05         59  14 (*)
  28MHz  SSB   2025-03-08 2234  PY2AA       59  05         (NO ENCONTRADO)

  (*) = El log de la otra estación muestra un contacto cerca de esta hora/banda/modo
        pero no dentro de la ventana de tolerancia de ±5 minutos

================================================================================
NOTAS:
================================================================================

1. Tolerancia de tiempo: ±5 minutos para hacer coincidir QSOs
2. Los indicativos ÚNICOS pueden ser válidos si la estación no envió log
3. Los indicativos ERRÓNEOS son errores de alta confianza — revisar el log original
4. Los contactos NIL pueden ser errores de tiempo o errores de anotación de la otra estación
```

## Formato de Reporte Agregado

```
================================================================================
SA10M CONTEST 2025 - RESUMEN AGREGADO UBN
================================================================================

Total de Logs Enviados: 844
Total QSOs Reclamados:  82,028
QSOs Válidos:           79,345 (96.7%)
QSOs Duplicados:        1,876  (2.3%)
QSOs Inválidos:         148    (0.2%)

Resumen de Verificación Cruzada:
  Indicativos ÚNICOS:   4,234  (5.2%)
  Indicativos ERRÓNEOS: 892    (1.1%)
  NO EN EL LOG:         1,567  (1.9%)
  
Tasa de error promedio: 8.2%
Tasa de error mediana:  5.1%

================================================================================
TOP 20 ESTACIONES POR TASA DE ERROR:
================================================================================

  Rank  Indicativo  QSOs  Errores  Error%  UNQ  BST  NIL
  ----  ---------   ----  -------  ------  ---  ---  ---
  1     XX1XXX      145   42       29.0%   18   12   12
  2     YY2YYY      89    23       25.8%   8    9    6
  ...

================================================================================
TOP 20 ESTACIONES POR CALIDAD (Menor Tasa de Error):
================================================================================

  Rank  Indicativo  QSOs  Errores  Error%  UNQ  BST  NIL
  ----  ---------   ----  -------  ------  ---  ---  ---
  1     AA1AAA      456   2        0.4%    1    0    1
  2     BB2BBB      389   3        0.8%    2    0    1
  ...

================================================================================
INDICATIVOS ERRÓNEOS MÁS FRECUENTES:
================================================================================

  Indicativo Correcto  Anotado Como       Veces  Similar A
  -------------------  -----------------  -----  ----------
  K9JY                 K9JX, K9JZ         12     K9JX(8), K9JZ(4)
  W1XXX                W1ZZZ, W1YYY       9      W1ZZZ(5), W1YYY(4)
  LU1AB                LU1AZ, LU1AC       7      LU1AZ(4), LU1AC(3)
  ...
```

## Modelos de Datos

### UBNEntry (Modelo Pydantic)

```python
class UBNType(str, Enum):
    UNIQUE = "unique"      # Único
    BUSTED = "busted"      # Erróneo
    NOT_IN_LOG = "nil"     # No en el log

class UBNEntry(BaseModel):
    """Entrada UBN única para un contacto"""
    log_id: int
    contact_id: int
    callsign: str
    timestamp: datetime
    band: str
    mode: str
    ubn_type: UBNType
    
    # Para indicativos ERRÓNEOS
    suggested_call: Optional[str] = None
    similarity_score: Optional[float] = None
    other_station_has_qso: bool = False
    
    # Para NIL
    other_log_id: Optional[int] = None
    time_difference_minutes: Optional[float] = None
    
    # Datos de exchange
    rst_sent: str
    exchange_sent: str
    rst_received: str
    exchange_received: str

class UBNReport(BaseModel):
    """Reporte UBN completo para una estación"""
    callsign: str
    log_id: int
    contest_name: str
    category: str
    
    # Estadísticas
    total_qsos: int
    valid_qsos: int
    duplicate_qsos: int
    invalid_qsos: int
    
    unique_count: int
    busted_count: int
    nil_count: int
    
    error_rate: float
    confirmed_rate: float
    
    # Entradas
    unique_entries: List[UBNEntry]
    busted_entries: List[UBNEntry]
    nil_entries: List[UBNEntry]
    
    generated_at: datetime
```

## Consultas SQL

### 1. Detección de Indicativos Únicos

```sql
-- Encontrar indicativos que aparecen en un solo log
SELECT 
    c.callsign,
    COUNT(DISTINCT c.log_id) as log_count,
    COUNT(*) as qso_count
FROM contacts c
WHERE c.is_valid = 1
GROUP BY c.callsign
HAVING log_count = 1;
```

### 2. Detección de No-En-El-Log

```sql
-- Encontrar contactos donde falta el QSO recíproco
SELECT 
    c1.id as contact_id,
    c1.log_id,
    l1.callsign as station_call,
    c1.callsign as worked_call,
    c1.timestamp,
    c1.band,
    c1.mode
FROM contacts c1
INNER JOIN logs l1 ON c1.log_id = l1.id
LEFT JOIN logs l2 ON l2.callsign = c1.callsign
LEFT JOIN contacts c2 ON 
    c2.log_id = l2.id
    AND c2.callsign = l1.callsign
    AND c2.band = c1.band
    AND c2.mode = c1.mode
    AND ABS(JULIANDAY(c2.timestamp) - JULIANDAY(c1.timestamp)) < 0.000694  -- 1 min
WHERE 
    c1.is_valid = 1
    AND l2.id IS NOT NULL  -- La otra estación envió log
    AND c2.id IS NULL;     -- Pero no se encontró QSO coincidente
```

### 3. Detección de Indicativos Erróneos (Python + SQL)

La detección de indicativos erróneos utiliza un **proceso en dos etapas**:

**Etapa 1 — Generación de candidatos (filtro grueso)** (independiente del modo)  
Se utiliza la distancia de edición Levenshtein 1–2 como filtro rápido para
construir una lista de candidatos entre los indicativos enviados.

**Etapa 2 — Reordenamiento según el modo de operación**  
Los candidatos se puntúan con una función de similitud que depende del modo
antes de verificar si existe un QSO recíproco:

| Modo | Algoritmo | Justificación |
|------|-----------|---------------|
| `CW` | Distancia de edición ponderada por Morse | Los caracteres con secuencias Morse similares (E/I, T/N, D/B, U/V …) reciben un costo de sustitución menor y se ordenan primero |
| `PH` / `SSB` / `FM` | Jaro-Winkler | Premio al prefijo compartido; adecuado para errores de copia fonética |
| Otros | Ratio Levenshtein estándar | Comportamiento sin cambios |

**Protecciones contra falsos positivos**
- Un indicativo nunca es sugerido como corrección de error para sí mismo
  (protección contra auto-referencia).
- El mismo indicativo sugerido no puede asignarse a dos indicativos erróneos
  distintos en el mismo log dentro de una ventana de 10 minutos.

```python
# Representación simplificada de la implementación real

# Etapa 1: filtro grueso (distancia de edición 1-2)
for worked_call in indicativos_no_enviados:
    candidatos = [
        (sub, Levenshtein.ratio(worked_call, sub))
        for sub in indicativos_enviados
        if 1 <= Levenshtein.distance(worked_call, sub) <= 2
        and Levenshtein.ratio(worked_call, sub) >= 0.65
    ]

# Etapa 2: reordenar por similitud según el modo
reclasificados = sorted(
    [(sug, callsign_similarity(worked_call, sug, row.mode))
     for sug, _ in candidatos],
    key=lambda x: x[1], reverse=True
)

for indicativo_sugerido, similitud in reclasificados:
    if indicativo_sugerido == row.log_callsign:   # protección auto-referencia
        continue
    if existe_qso_reciproco(indicativo_sugerido, log_callsign, timestamp, ±5min):
        marcar_como_erroneo(worked_call, indicativo_sugerido, similitud)
        break
    if edit_distance == 1 and zona_coincide(indicativo_sugerido, exchange_recibido):
        # Alternativa por zona cuando no hay QSO recíproco
        marcar_como_erroneo(worked_call, indicativo_sugerido, similitud)
        break
```

**Reinicio de la verificación cruzada**  
Antes de cada ejecución, los contactos previamente marcados como
`invalid_callsign`, `not_in_log` o `unique_call` se **restauran a `valid`**
para que cada re-ejecución parta de los datos tal como fueron importados.
Esto evita que un indicativo erróneamente penalizado permanezca
`is_valid=0` en ejecuciones posteriores.

```python
# Se ejecuta automáticamente al inicio de check_all_logs()
UPDATE contacts
SET validation_status = 'valid', validation_notes = NULL, is_valid = 1
WHERE log_id IN (SELECT id FROM logs WHERE contest_id = :contest_id)
  AND validation_status IN ('invalid_callsign', 'not_in_log', 'unique_call')
```

## Formatos de Exportación

### Archivo de Texto (.txt)
- Formato estándar mostrado arriba
- Un archivo por estación: `UBN_K1ABC.txt`
- Reporte agregado: `UBN_RESUMEN.txt`

### Exportación CSV (.csv)
```csv
Indicativo,Tipo_UBN,Banda,Modo,FechaHora,IndTrabajado,IndSugerido,Exchange_Env,Exchange_Rec,Notas
K1ABC,UNIQUE,28MHz,SSB,2025-03-08 12:34,K9XYZ,,59 05,599 13,No encontrado en ningún log
K1ABC,BUSTED,28MHz,SSB,2025-03-08 14:56,W1ZZZ,W1XXX,59 05,599 05,Similar a W1XXX
K1ABC,NIL,28MHz,CW,2025-03-08 18:34,LU5ABC,,599 05,599 13,LU5ABC no tiene registro
```

### Exportación JSON (.json)
```json
{
  "callsign": "K1ABC",
  "log_id": 123,
  "contest": "SA10M 2025",
  "statistics": {
    "total_qsos": 234,
    "valid_qsos": 218,
    "unique_count": 8,
    "busted_count": 3,
    "nil_count": 4,
    "error_rate": 6.4
  },
  "entries": [
    {
      "type": "unique",
      "callsign": "K9XYZ",
      "band": "28MHz",
      "mode": "SSB",
      "timestamp": "2025-03-08T12:34:00Z"
    }
  ]
}
```

## Ejemplo de Uso

```python
from src.services.cross_check_service import CrossCheckService
from src.services.ubn_report_generator import UBNReportGenerator

# Verificación cruzada de todos los logs
cross_check = CrossCheckService(db_session)
results = cross_check.check_all_logs(contest_id=1)

# Generar reportes UBN
ubn_gen = UBNReportGenerator(db_session)

# Reportes por estación
for log in logs:
    report = ubn_gen.generate_report(log.id)
    ubn_gen.export_text(report, f"reportes/UBN_{log.callsign}.txt")

# Resumen agregado
summary = ubn_gen.generate_summary(contest_id=1)
ubn_gen.export_text(summary, "reportes/UBN_RESUMEN.txt")
```

---

**Versión del Documento**: 1.2  
**Creado**: Noviembre 19, 2025  
**Actualizado**: 7 de Abril de 2026  
**Cambios**:
- Corregida la tolerancia de tiempo de ±1 min a ±5 min
- Documentada la detección de indicativos erróneos con similitud según el modo (CW: distancia ponderada por Morse; PH: Jaro-Winkler)
- Documentada la protección contra auto-referencia
- Documentado el mecanismo de reinicio de la verificación cruzada
