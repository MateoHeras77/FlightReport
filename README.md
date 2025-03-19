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