# SA10M Contest Manager

**Sistema completo de puntuación y gestión para el concurso de radioaficionados SA10M.**

SA10M es un concurso de radioaficionados en la banda de 10 metros, con estaciones de América del Sur y todo el mundo. Esta aplicación gestiona el flujo de trabajo completo del concurso: desde la importación de archivos de log Cabrillo hasta la validación cruzada de contactos y la generación del cuadro de clasificación final.

---

## Características Principales

- **Importación de logs** — formato Cabrillo (`.cbr`, `.txt`) con detección automática de duplicados
- **Motor de puntuación configurable** — reglas en YAML para puntos por QSO y multiplicadores (prefijos WPX + zonas CQ)
- **Pipeline de validación cruzada** — valida contactos contra todos los demás logs, marcando NIL y señales erradas
- **Reportes UBN** — genera reportes por estación de tipo Único/Errado/No-en-log
- **Cuadro de clasificación con filtros** — ordenar y filtrar por categoría, área del operador, indicativo
- **Exportación Excel / CSV** — reporte completo de QSOs y planilla de puntajes
- **Interfaz de escritorio** — interfaz Tkinter simple, sin servidor requerido

---

## Navegación Rápida

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Primeros Pasos**

    ---

    Instala las dependencias y realiza tu primera importación en minutos.

    [:octicons-arrow-right-24: Primeros Pasos](PRIMEROS_PASOS.md)

-   :material-monitor:{ .lg .middle } **Guía de Usuario (Interfaz)**

    ---

    Guía paso a paso de cada pestaña de la aplicación de escritorio.

    [:octicons-arrow-right-24: Guía de Usuario](user-guide/index.md)

-   :material-trophy:{ .lg .middle } **Reglas del Concurso**

    ---

    Reglas de puntuación SA10M, multiplicadores y formato de intercambio.

    [:octicons-arrow-right-24: Referencia Rápida SA10M](SA10M_REFERENCIA_RAPIDA.md)

-   :material-book-open-variant:{ .lg .middle } **Referencia Técnica**

    ---

    Esquema de base de datos, pipeline de importación y arquitectura de servicios.

    [:octicons-arrow-right-24: Documentación Técnica](ESQUEMA_BASE_DATOS.md)

</div>

---

## Flujo de Trabajo Típico

```mermaid
graph LR
    A[Crear Concurso] --> B[Importar Logs]
    B --> C[Validación Cruzada]
    C --> D[Puntuar Logs]
    D --> E[Ver Clasificación]
    E --> F[Exportar Resultados]
```

1. **Crear un concurso** — define nombre, slug y rango de fechas en la pestaña Concursos
2. **Importar logs** — apunta a una carpeta con archivos Cabrillo; los duplicados se manejan automáticamente
3. **Validación cruzada** — compara cada contacto contra todos los demás logs para encontrar entradas NIL/erróneas
4. **Puntuar** — calcula puntos QSO, prefijos WPX y multiplicadores de zona CQ
5. **Clasificación** — navega resultados filtrados por categoría o área, exporta a Excel

---

## Estado del Proyecto

El sistema está completamente operativo para la temporada del **SA10M 2026** con **601 logs de estación** procesados y puntuados.

| Fase | Estado |
|------|--------|
| Modelos de Datos y Base | ✅ Completo |
| Motor de Reglas | ✅ Completo |
| Análisis de Logs (Cabrillo) | ✅ Completo |
| Pipeline de Validación Cruzada | ✅ Completo |
| Motor de Puntuación | ✅ Completo |
| Interfaz de Escritorio | ✅ Completo |
