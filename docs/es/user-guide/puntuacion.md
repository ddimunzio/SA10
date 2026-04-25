# Pestaña Puntuar

La pestaña **Puntuar** calcula los puntos QSO y multiplicadores para cada log del concurso activo y almacena los resultados en la base de datos.

---

## Configuración

| Campo | Descripción |
|-------|-------------|
| **Concurso** | Nombre del concurso activo (solo lectura — se establece en la pestaña Concursos) |
| **Slug de reglas** | Identificador del archivo YAML de reglas del concurso en `config/contests/`. Por defecto: `sa10m` |

El slug de reglas apunta a un archivo como `config/contests/sa10m.yaml`, que define los valores de puntos, tipos de multiplicadores, bandas válidas y requisitos de intercambio.

---

## Ejecutar el Cálculo de Puntajes

Haz clic en **▶ Puntuar Todos los Logs**. El motor procesa cada log del concurso activo de forma secuencial.

### Salida de progreso

```
Puntuando 601 logs…
  Progreso: 50/601  (50 OK, 0 errores)
  Progreso: 100/601  (100 OK, 0 errores)
  ...
Puntuación completada — 601 OK, 0 errores.
```

Cualquier log que no pueda puntuarse (por ejemplo, datos malformados) se cuenta como error y se reporta en amarillo, pero el procesamiento continúa para los logs restantes.

---

## Qué se Calcula

Para cada log el motor de puntuación:

1. **Filtra contactos** — solo se cuentan los contactos marcados como válidos tras la validación cruzada
2. **Calcula puntos QSO** — aplica la tabla de puntos SA10M según la ubicación del operador y el tipo de contacto (ver [Referencia Rápida SA10M](../SA10M_REFERENCIA_RAPIDA.md))
3. **Cuenta prefijos WPX** — prefijos únicos de indicativos trabajados en todo el concurso
4. **Cuenta zonas CQ por banda** — zonas CQ únicas trabajadas en cada banda
5. **Calcula puntaje por banda** — `Puntos QSO × (Prefijos WPX + Zonas CQ en esa banda)`
6. **Suma todos los puntajes de banda** — para SA10M es un total de una sola banda

Los resultados se almacenan en la tabla `scores` y están disponibles inmediatamente en la pestaña **Tabla de Clasificación**.

---

## Recalcular

Puedes volver a ejecutar la puntuación en cualquier momento. Cada ejecución sobreescribe los puntajes anteriores. Esto es útil si:

- Reimportaste logs tras encontrar un error
- Volviste a ejecutar la validación cruzada con datos actualizados
- Cambiaste las reglas del concurso

!!! note "Valida primero"
    Para resultados precisos, siempre ejecuta la validación cruzada antes de puntuar. Puntuar sin validación cruzada contará todos los contactos como válidos, incluyendo los NIL.
