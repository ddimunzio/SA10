# Primeros Pasos

Esta guia describe la aplicacion actual tal como existe en este repositorio. El punto de entrada normal es la interfaz de escritorio en `app_ui.py`; los scripts auxiliares siguen disponibles para importacion por lotes y mantenimiento.

## Requisitos Previos

- Python 3.10 o superior
- pip
- PowerShell en Windows, o una shell capaz de activar el entorno virtual

## Instalar e Iniciar

```powershell
# Desde la raiz del repositorio
cd C:\Users\lw5hr\proyects\SA10

# Crear el entorno virtual si hace falta
python -m venv .venv

# Activarlo
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Iniciar la aplicacion de escritorio
python app_ui.py
```

Si solo quieres comprobar el entorno sin abrir la interfaz grafica, ejecuta:

```powershell
python manage_contest.py list
```

## Flujo Recomendado para la Primera Ejecucion

1. Abre `Archivo -> Nueva Base de Datos...` y crea una base para la temporada.
2. Deja que la aplicacion inicialice las tablas e importe los datos DXCC incluidos.
3. Ve a la pestana `Concursos` y crea o selecciona el concurso activo.
4. Importa logs Cabrillo desde la pestana `Importar Logs`.
5. Ejecuta `Validacion Cruzada` para generar resultados NIL, indicativos errados y contactos unicos.
6. Ejecuta `Puntuacion` para calcular el puntaje final y los multiplicadores.
7. Revisa `Tabla de Clasificacion` y `Estadisticas`, y exporta reportes Excel o CSV si hace falta.

## Comandos de Prueba Recomendados

```powershell
# Suite completa
pytest

# Reglas y puntuacion
pytest tests/test_rules_engine.py tests/test_sa10m_scoring.py -v

# Importacion y validacion cruzada
pytest tests/test_log_import.py tests/test_cross_check_rules.py -v
```

## Estructura Principal del Repositorio

```text
SA10/
|-- app_ui.py
|-- manage_contest.py
|-- import_logs.py
|-- run_cross_check.py
|-- update_dxcc_data.py
|-- config/
|   `-- contests/
|-- docs/
|   |-- user-guide/
|   `-- es/
|-- src/
|   |-- core/
|   |-- database/
|   |-- parsers/
|   `-- services/
`-- tests/
```

## Comandos Utiles

```powershell
# Listar concursos
python manage_contest.py list

# Crear un concurso
python manage_contest.py create "SA10M 2026" sa10m-2026 "2026-03-14 00:00" "2026-03-15 23:59"

# Importar una carpeta de logs
python import_logs.py --contest-id 1 logs_sa10m__2026

# Ejecutar la validacion cruzada desde CLI
python run_cross_check.py --contest-id 1
```

## Notas

- `main.py` sigue presente, pero no es el punto de entrada principal.
- Las bases nuevas cargan automaticamente los datos DXCC desde el archivo `cty_wt.dat` incluido.
- El sitio de documentacion en `docs/` incluye contenido en ingles y espanol.

## Siguiente Lectura

- `docs/es/user-guide/index.md` para el flujo de la interfaz
- `docs/es/GUIA_IMPORTACION_LOGS.md` para detalles de importacion por lotes
- `docs/es/GUIA_DATOS_DXCC.md` para mantenimiento de prefijos y paises
- `docs/GETTING_STARTED.md` para la version en ingles de esta guia
