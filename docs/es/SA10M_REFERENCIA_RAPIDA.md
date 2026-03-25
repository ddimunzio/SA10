# Concurso SA10M — Tarjeta de Referencia Rápida

## Referencia Rápida de Reglas de Puntuación

### Tabla de Puntos

| Tipo de Operador | Tipo de Contacto | Puntos | Regla |
|-----------------|------------------|--------|-------|
| **Móvil (/MM, /AM) en Zonas 9-13** | | | |
| | → Estación SA | 2 | R3 |
| | → Estación no-SA | 4 | R4 |
| **Móvil (/MM, /AM) fuera de Zonas 9-13** | | | |
| | → Estación SA | 4 | R5 |
| | → Estación no-SA | 2 | R6 |
| **Cualquier estación** | → Estación móvil | 2 | R1 |
| **Cualquier estación** | → Mismo DXCC | 0 | R2 |
| **Estación no-SA** | → Estación SA | 4 | R7 |
| **Estación no-SA** | → Estación no-SA | 2 | R8 |
| **Estación SA** | → Estación no-SA | 4 | R9 |
| **Estación SA** | → Estación SA (distinto DXCC) | 2 | R10 |

### Multiplicadores

| Tipo | Alcance | Conteo | Descripción |
|------|---------|--------|-------------|
| **Prefijo WPX** | Todo el concurso | Una vez | Cada prefijo único (ej: LU1, LU2, W1) |
| **Zona CQ** | Por banda | Por banda | Cada zona trabajada (1-40) en cada banda |

### Fórmula de Puntuación

```
Por cada banda:
  Puntaje de banda = Puntos QSO × (Prefijos WPX + Zonas CQ en esa banda)

Puntaje Total = Suma de puntajes de todas las bandas
```

**Nota**: SA10M es solo 10m, por lo tanto hay una sola banda.

### Intercambio (Exchange)

**Enviar**: RS/RST + Zona CQ  
**Recibir**: RS/RST + Zona CQ

- **SSB**: RS (2 dígitos) - ej: "59"
- **CW**: RST (3 dígitos) - ej: "599"
- **Zona CQ**: 1-40 (Argentina = Zona 13)

### Categorías

- **SO-CW**: Operador único solo CW
- **SO-SSB**: Operador único solo SSB
- **SO-Mixto**: Operador único CW + SSB
- **MO**: Multi Operador

### Detalles del Concurso

- **Banda**: Solo 10m
- **Modos**: CW, SSB
- **Duración**: 24 horas
- **Regla de duplicados**: Mismo indicativo en misma banda + modo = duplicado

### Zonas CQ de Sudamérica

| Zona | Cobertura |
|------|-----------|
| 9 | Sudamérica (norte) |
| 10 | Sudamérica (Venezuela, Guyana) |
| 11 | Sudamérica (Brasil norte) |
| 12 | Sudamérica (Chile, Brasil sur) |
| 13 | **Argentina** (principal) |

### Ejemplos

#### Ejemplo 1: LU1ABC (Argentina, SA, Zona 13) opera

| Contacto | Continente | DXCC | Puntos | Por qué |
|----------|-----------|------|--------|---------|
| PY2XYZ | SA | PY | 2 | SA→SA distinto DXCC (R10) |
| LU2DEF | SA | LU | 0 | Mismo DXCC (R2) |
| W1ABC | NA | K | 4 | SA→no-SA (R9) |
| DL1XYZ | EU | DL | 4 | SA→no-SA (R9) |
| LU3GHI/MM | SA | LU | 2 | Contacto con móvil (R1) |

#### Ejemplo 2: W1ABC (EE.UU., NA, Zona 5) opera

| Contacto | Continente | DXCC | Puntos | Por qué |
|----------|-----------|------|--------|---------|
| LU1DEF | SA | LU | 4 | no-SA→SA (R7) |
| DL1XYZ | EU | DL | 2 | no-SA→no-SA (R8) |
| W2ABC | NA | K | 0 | Mismo DXCC (R2) |
| PY2GHI/MM | SA | PY | 2 | Contacto con móvil (R1) |

#### Ejemplo 3: LU1ABC/MM (Móvil en Zona 13)

| Contacto | Continente | Puntos | Por qué |
|----------|-----------|--------|---------|
| PY2XYZ | SA | 2 | Móvil en 9-13→SA (R3) |
| W1ABC | NA | 4 | Móvil en 9-13→no-SA (R4) |

#### Ejemplo 4: W1ABC/MM (Móvil en Zona 5)

| Contacto | Continente | Puntos | Por qué |
|----------|-----------|--------|---------|
| LU1DEF | SA | 4 | Móvil fuera de 9-13→SA (R5) |
| DL1XYZ | EU | 2 | Móvil fuera de 9-13→no-SA (R6) |

### Mapeo DXLog.net

Nuestra configuración YAML coincide exactamente con estos parámetros de DXLog:

```
BANDS=10
MODES=CW;SSB
CATEGORY_MODES=CW;SSB;Mixed
DOUBLE_QSO=PER_MODE
MULT1_TYPE=WPX, MULT1_COUNT=ALL
MULT2_TYPE=CQZONE, MULT2_COUNT=PER_BAND
POINTS_TYPE=CALC
SCORE=BY_BAND
```

Las 10 reglas POINTS_FIELD_BAND_MODE están implementadas en nuestro YAML.

---

**Última Actualización**: 2025-11-13  
**Archivo de Configuración**: `config/contests/sa10m.yaml`  
**Estado**: ✅ Validado contra la definición de DXLog.net
