# Manejo de Contactos Duplicados en el Sistema SA10M

**Última Actualización**: Noviembre 17, 2025

## Descripción General

El sistema maneja los contactos duplicados usando un **enfoque de dos fases**:

1. **Fase 5.1 (Importación)**: Importar TODOS los contactos sin filtrar — ✅ Completo
2. **Fase 4.1 (Puntuación)**: Detectar y excluir duplicados durante el scoring — ✅ Completo

Este enfoque garantiza la preservación completa de datos y permite una detección de duplicados flexible basada en reglas específicas del concurso.

---

## Fase 5.1: Fase de Importación (ACTUAL — COMPLETA ✅)

### Qué Ocurre Durante la Importación

Cuando se importa un log Cabrillo mediante `LogImportService`:

1. **SE IMPORTAN TODOS los contactos** del archivo Cabrillo
2. Cada contacto se guarda en la base de datos con:
   - `is_duplicate = False` (por defecto)
   - `is_valid = True` (por defecto)
   - `validation_status = 'valid'` (por defecto)
3. **NO se realiza** ninguna verificación o filtrado de duplicados

### ¿Por qué este enfoque?

**Beneficios:**
- ✅ **Integridad de Datos**: Preservación completa del log tal como fue enviado
- ✅ **Auditoría**: Todos los contactos disponibles para revisión
- ✅ **Flexibilidad**: Distintos concursos pueden tener distintas reglas de duplicados
- ✅ **Verificación cruzada**: Se puede verificar si un duplicado también fue anotado por la otra estación
- ✅ **Control de Puntuación**: La detección ocurre durante el scoring con contexto completo del concurso

### Ejemplo

Si un log contiene:
```
QSO: 28500 PH 2025-03-08 1200 TEST1ABC 59 13 W1AW 59 05
QSO: 28500 PH 2025-03-08 1210 TEST1ABC 59 13 W1AW 59 05  <- Duplicado
QSO: 28500 PH 2025-03-08 1220 TEST1ABC 59 13 W1AW 59 05  <- Duplicado
```

**Los 3 contactos se importan** a la base de datos con `is_duplicate=False`.

### Implementación en Código

**ContactRepository.create_batch()** — Sin verificación de duplicados:
```python
def create_batch(self, contacts_data: List[ContactBase], log_id: int) -> List[DBContact]:
    """Crear múltiples contactos en lote para mejor rendimiento."""
    db_contacts = []
    
    for contact_data in contacts_data:
        db_contact = DBContact(
            log_id=log_id,
            # ... otros campos ...
            is_valid=True,
            is_duplicate=False,  # Por defecto - se actualizará en Fase 4.1
            validation_status='valid',
        )
        db_contacts.append(db_contact)
    
    self.session.add_all(db_contacts)
    self.session.flush()
    return db_contacts
```

---

## Fase 4.1: Fase de Puntuación (COMPLETA ✅)

La detección de duplicados se ejecuta dentro del **Motor de Puntuación** al procesar cada log. El motor identifica duplicados (mismo indicativo + misma banda + mismo modo), los excluye del cálculo de puntos y almacena el conteo en la tabla `scores` como `duplicate_qsos`. El resultado es visible en la pestaña **Tabla de Clasificación** bajo la columna **Dupes**.

### Reglas de Duplicados por Concurso

Distintos concursos pueden tener distintas ventanas de duplicados:

**Concurso SA10M:**
- **Regla**: Duplicado = mismo indicativo + misma banda + mismo modo
- **Ventana**: Por banda por modo (puede trabajarse la misma estación en CW y SSB)
- **Puntuación**: El primer QSO cuenta, los duplicados suman 0 puntos

| Caso | ¿Duplicado? |
|------|------------|
| Mismo indicativo + misma banda + mismo modo | ✅ Sí (0 pts) |
| Mismo indicativo + **modo diferente** (CW vs SSB) | ❌ No (QSO válido) |
| Mismo indicativo + **banda diferente** | ❌ No (QSO válido) |

**Otros Concursos (Futuro):**
- Algunos concursos: Duplicado solo en misma banda (el modo no importa)
- Algunos concursos: Se puede volver a trabajar la misma estación después de X horas
- Algunos concursos: Distintas reglas para distintas categorías

#### Ejemplo Real: N6AR trabajó AY7J dos veces

En el log SA10M 2026 enviado por N6AR, AY7J aparece dos veces:

```
QSO:   28040 CW 2026-03-14 2013 N6AR       599  05 AY7J          599  13         AY7
QSO:   28480 PH 2026-03-14 2034 N6AR       59   05 AY7J          59   13         AY7
```

- Primer QSO: **28 MHz CW** a las 2013z
- Segundo QSO: **28 MHz PH (SSB)** a las 2034z

**No son duplicados** porque el modo es diferente (CW ≠ PH). Ambos QSOs son válidos y suman puntos para N6AR.

> **Nota sobre reportes UBN**: El reporte UBN de AY7J lista a N6AR en *"Estaciones que copiaron incorrectamente el exchange de AY7J"* porque N6AR anotó el campo de exchange como `AY7` (el prefijo del indicativo) en lugar de `13` (la zona CQ). Sin embargo, **AY7J no pierde crédito** — es N6AR quien tiene el error de copiado.

### Implementación (A Realizar)

Crear `src/core/validation/contact_validator.py`:

```python
class ContactValidator:
    """Validar contactos y marcar duplicados"""
    
    def validate_log(self, log_id: int, contest_rules: ContestRules):
        """Validar todos los contactos de un log"""
        
        # Obtener todos los contactos
        contacts = self.contact_repo.get_all_for_log(log_id)
        
        # Ordenar por timestamp
        contacts.sort(key=lambda c: c.qso_datetime)
        
        # Rastrear estaciones trabajadas
        worked = set()  # (indicativo, banda, modo)
        
        for contact in contacts:
            key = (contact.call_received, contact.band, contact.mode)
            
            if key in worked:
                # ¡Duplicado!
                self.contact_repo.mark_as_duplicate(contact.id)
            else:
                # Primera vez trabajando esta estación
                worked.add(key)
```

### Soporte de Base de Datos

El modelo `Contact` ya tiene todo lo necesario:

```python
class Contact(Base):
    # ... otros campos ...
    
    # Campos de validación
    is_duplicate = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    validation_status = Column(String(50))  # 'valid', 'duplicate', 'invalid', etc.
    validation_message = Column(Text)
    
    # Indexado para consultas rápidas de duplicados
    Index("idx_contact_duplicate", "is_duplicate")
```

El `ContactRepository` ya tiene el método:

```python
def mark_as_duplicate(self, contact_id: int) -> DBContact:
    """Marcar un contacto como duplicado"""
    db_contact = self.get_by_id(contact_id)
    if db_contact:
        db_contact.is_duplicate = True
        db_contact.validation_status = 'duplicate'
        db_contact.points = 0
        self.session.flush()
    return db_contact
```

---

## Integración con la Puntuación

### Fase 4.2: Motor de Puntuación

Al calcular puntajes, el motor:

1. **Excluye los duplicados** de la puntuación:
   ```python
   valid_contacts = [c for c in contacts if not c.is_duplicate and c.is_valid]
   ```

2. **Genera reportes** con:
   - Total QSOs anotados
   - QSOs válidos (puntuados)
   - QSOs duplicados (0 puntos)
   - QSOs inválidos (0 puntos)

3. **Desglose detallado**:
   ```
   Total QSOs:         150
   QSOs Válidos:       145
   QSOs Duplicados:      3  (0 puntos)
   QSOs Inválidos:       2  (0 puntos)
   ```

---

## Beneficios del Enfoque de Dos Fases

### Integridad de Datos
✅ Preservación completa del log  
✅ Revisión de lo enviado originalmente  
✅ Auditoría para adjudicación

### Flexibilidad
✅ Distintas reglas por concurso  
✅ Re-validación con distintas reglas  
✅ Detección de patrones (misma estación trabajada múltiples veces)

### Verificación Cruzada
✅ Verificar si el duplicado fue anotado por la otra estación  
✅ Detectar discrepancias de tiempo  
✅ Mejor detección de NIL (No en el Log)

### Rendimiento
✅ Importación en lote rápida (sin consultas de duplicados)  
✅ Detección de duplicados una sola vez después de la importación  
✅ Campos de base de datos indexados para consultas rápidas

---

## Estado Actual

| Fase | Estado | Descripción |
|------|--------|-------------|
| 5.1 Importación | ✅ Completo | Todos los contactos importados sin filtrar |
| 4.1 Validación | ⏳ Pendiente | Detección de duplicados a implementar |
| 4.2 Puntuación | ⏳ Pendiente | Excluir duplicados de la puntuación |

---

## Referencias

- **Plan de Implementación**: `IMPLEMENTATION_PLAN.md`
- **Esquema de Base de Datos**: `docs/DATABASE_SCHEMA.md`
- **Motor de Reglas**: `docs/RULES_ENGINE_QUICK_REF.md`
- **Reglas SA10M**: `config/contests/sa10m.yaml`

---

**Versión del Documento**: 1.0  
**Creado**: Noviembre 17, 2025  
**Estado**: Fase de importación completa, fase de validación pendiente
