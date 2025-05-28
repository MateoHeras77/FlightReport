# Avianca - Sistema de Reporte de Vuelos

Aplicación desarrollada en Streamlit para la gestión y envío de reportes de vuelos de Avianca a Supabase.

## Estructura del Proyecto

```
avianca/
├── app.py                  # Punto de entrada principal de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── logs/                   # Directorio para archivos de log
└── src/                    # Código fuente de la aplicación
    ├── components/         # Componentes UI de Streamlit
    │   ├── flight_form.py  # Formulario de vuelo
    │   └── timeline_chart.py # Visualización de línea de tiempo
    ├── config/             # Configuraciones
    │   ├── supabase_config.py  # Configuración de Supabase
    │   └── logging_config.py   # Configuración de logging
    ├── models/             # Modelos de datos
    ├── services/           # Servicios externos
    │   └── supabase_service.py  # Servicios para Supabase
    └── utils/              # Utilidades
        └── form_utils.py   # Utilidades para formularios
```

## Requisitos

- Python 3.8 o superior
- Streamlit
- Supabase
- Otras dependencias en `requirements.txt`

## Instalación

1. Clonar el repositorio
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Configurar credenciales:
   - Crear un archivo `.streamlit/secrets.toml` con las credenciales de Supabase
   - Ver `example_secrets.toml` para un ejemplo de configuración

## Ejecución

Para ejecutar la aplicación localmente:

```bash
streamlit run app.py
```

## Logging

Los logs se almacenan en el directorio `logs/` con archivos diarios con formato `app_YYYY-MM-DD.log`.

## Supabase

La aplicación envía datos a la tabla `FlightReport` en Supabase. Esta tabla debe estar configurada con las columnas apropiadas para recibir los datos del formulario.
Para más detalles sobre la estructura de la tabla `FlightReport` y otras tablas relevantes, consulta el archivo [`sql.Schema.md`](sql.Schema.md) en el directorio raíz.

## Pruebas

Este proyecto utiliza `pytest` para las pruebas unitarias y de integración. Para ejecutar las pruebas, asegúrate de haber instalado las dependencias de desarrollo (incluyendo `pytest` desde `requirements.txt`) y luego ejecuta el siguiente comando desde el directorio raíz del proyecto:

```bash
pytest
```

Los archivos de prueba se encuentran en el directorio `tests/`. Te animamos a agregar más pruebas para cubrir nuevas funcionalidades y refactorizaciones.

## Estilo de Código y Linting

Para mantener un estilo de código consistente y detectar errores potenciales, este proyecto utiliza las siguientes herramientas:

- **Black:** Para el formateo automático del código.
- **Flake8:** Para el linting (detección de errores y problemas de estilo según PEP 8).
- **isort:** Para organizar automáticamente los imports.

La configuración de estas herramientas se encuentra en el archivo `pyproject.toml`.

Para aplicar el formateo y el linting manualmente, puedes ejecutar los siguientes comandos desde el directorio raíz del proyecto:

```bash
# Formatear el código con Black
black .

# Ordenar imports con isort
isort .

# Revisar el código con Flake8
flake8 .
```

Se recomienda configurar [pre-commit hooks](https://pre-commit.com/) para automatizar estas revisiones antes de cada commit. También puedes considerar explorar [Ruff](https://beta.ruff.rs/docs/) como una alternativa moderna y extremadamente rápida para linting y formateo.