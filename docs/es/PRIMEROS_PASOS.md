# Primeros Pasos — Calculadora de Concursos de Radioafición

## Configuración del Entorno de Desarrollo

### 1. Requisitos previos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Git (opcional, para control de versiones)

### 2. Configuración inicial

```bash
# Navegar al directorio del proyecto
cd C:\Users\lw5hr\proyects\SA10

# Activar el entorno virtual (debe estar ya creado)
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python main.py
```

### 3. Ejecutar pruebas

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con cobertura
pytest --cov=src tests/

# Ejecutar un archivo de prueba específico
pytest tests/test_models.py -v
```

### 4. Estructura del proyecto

```
SA10/
├── src/                          # Código fuente
│   ├── core/                     # Lógica de negocio principal
│   │   ├── models/              # Modelos de dominio (Pydantic)
│   │   │   └── contest.py       # ✅ Modelos de datos del concurso
│   │   ├── rules/               # Motor de reglas
│   │   ├── scoring/             # Lógica de puntuación
│   │   └── validation/          # Lógica de validación
│   ├── database/                # Capa de base de datos (SQLAlchemy)
│   │   └── repositories/        # Acceso a datos
│   ├── parsers/                 # Parsers de archivos de log
│   └── utils/                   # Funciones utilitarias
├── config/                      # Archivos de configuración
│   └── contests/
│       └── sa10m.yaml          # ✅ Reglas del concurso SA10M
├── tests/                       # Archivos de prueba
│   └── test_models.py          # ✅ Pruebas de modelos
├── docs/                        # Documentación
├── main.py                      # ✅ Punto de entrada principal
├── requirements.txt             # ✅ Dependencias de Python
├── IMPLEMENTATION_PLAN.md       # ✅ Hoja de ruta de desarrollo
└── README.md                    # ✅ Descripción general del proyecto
```

## Estado Actual

### ✅ Completado
- [x] Estructura del proyecto creada
- [x] Dependencias definidas
- [x] Modelos de datos principales (Pydantic)
- [x] Configuración de reglas del concurso SA10M
- [x] Pruebas unitarias básicas
- [x] Documentación de desarrollo

### ⏳ En Progreso / Próximos Pasos
Siguiendo las fases del Plan de Implementación:

**Fase 1: Fundamentos y Modelos** (actual)
- [x] Configuración del proyecto
- [x] Modelos de datos principales
- [ ] Esquema de base de datos (modelos SQLAlchemy)
- [ ] Configuración de migraciones de base de datos

**Fase 2: Motor de Reglas** (siguiente)
- [ ] Cargador de reglas YAML
- [ ] Validador de reglas
- [ ] Núcleo del motor de reglas

**Fase 3: Parsing de Logs**
- [ ] Parser Cabrillo
- [ ] Parser ADIF (opcional)
- [ ] Parser CSV

**Fase 4: Validación y Puntuación**
- [ ] Validación de contactos
- [ ] Detección de duplicados
- [ ] Cálculo de puntos
- [ ] Identificación de multiplicadores

## Flujo de Trabajo de Desarrollo

### Agregar una Nueva Funcionalidad

1. **Revisar el Plan de Implementación**
   - Verificar a qué fase pertenece la funcionalidad
   - Entender las dependencias

2. **Crear una rama** (si se usa Git)
   ```bash
   git checkout -b feature/nombre-funcionalidad
   ```

3. **Escribir pruebas primero** (enfoque TDD)
   - Crear archivo de prueba en `tests/`
   - Escribir pruebas fallidas para la funcionalidad

4. **Implementar la funcionalidad**
   - Agregar código al módulo correspondiente
   - Ejecutar pruebas con frecuencia

5. **Validar**
   ```bash
   pytest
   python main.py  # Pruebas manuales
   ```

6. **Documentar**
   - Agregar docstrings
   - Actualizar README si es necesario

### Próximas Tareas Inmediatas

1. **Completar Fase 1: Modelos de Base de Datos**
   ```python
   # Crear: src/database/models.py
   # - Modelos SQLAlchemy para concursos, logs, contactos, puntajes
   # - Configuración de migración con Alembic
   ```

2. **Crear Migración Inicial**
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "Esquema inicial"
   alembic upgrade head
   ```

3. **Construir Capa de Repositorios**
   ```python
   # Crear: src/database/repositories/contest_repository.py
   # - Operaciones CRUD para concursos
   # - Métodos de consulta
   ```

## Comandos Frecuentes

### Pruebas
```bash
# Ejecutar todas las pruebas
pytest

# Con salida detallada
pytest -v

# Prueba específica
pytest tests/test_models.py::test_contact_creation -v

# Con reporte de cobertura
pytest --cov=src --cov-report=html tests/
```

### Base de Datos (cuando esté implementada)
```bash
# Crear migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir
alembic downgrade -1
```

### Ejecutar la Aplicación
```bash
# Actual (marcador de posición)
python main.py

# Comandos CLI futuros (a implementar)
python main.py process --log ruta/al/log.cbr --contest sa10m
python main.py score --log-id 123
python main.py export --contest sa10m --format html
```

## Conceptos Clave

### Modelos del Concurso (Pydantic)
- **Contact**: QSO individual con validación
- **Station**: Información del operador
- **ContestLog**: Envío completo del log
- **ScoreBreakdown**: Resultados calculados

### Configuración de Reglas (YAML)
- Define reglas específicas del concurso
- Lógica de puntuación
- Reglas de validación
- Formato del intercambio (exchange)

### Modelos de Base de Datos (SQLAlchemy) — A implementar
- Almacenamiento persistente
- Seguimiento histórico
- Optimización de consultas

## Consejos para el Desarrollo

1. **Seguir el Plan de Implementación**: Está estructurado para construir funcionalidades en orden lógico
2. **Escribir pruebas primero**: Ayuda a clarificar los requisitos
3. **Usar type hints**: Ya establecidos en los modelos, continuar con la práctica
4. **Documentar mientras se desarrolla**: Docstrings claros ayudan al desarrollo futuro
5. **Mantener los modelos separados**: Pydantic para lógica de negocio, SQLAlchemy para persistencia

## Recursos

### Estándares de Concursos de Radioafición
- Formato Cabrillo: http://www.kkn.net/~trey/cabrillo/
- Especificación ADIF: https://adif.org/
- Reglas SA10M: https://sa10m.com.ar/wp/rules/

### Documentación de Librerías Python
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- Alembic: https://alembic.sqlalchemy.org/
- Click: https://click.palletsprojects.com/
- pytest: https://docs.pytest.org/

## ¿Preguntas?

Consultar:
- `IMPLEMENTATION_PLAN.md` para arquitectura y hoja de ruta
- `README.md` para descripción general del proyecto
- Docstrings del código para detalles de la API

---

¡Buen desarrollo! 73! 📻
