# Migraciu00f3n de BigQuery a Supabase

Este documento describe los pasos para completar la migraciu00f3n de BigQuery a Supabase en la aplicaciu00f3n Avianca Flight Report.

## Pasos Completados

1. Se han creado nuevos archivos de configuraciu00f3n y servicios para Supabase:
   - `src/config/supabase_config.py`: Configuraciu00f3n del cliente de Supabase
   - `src/services/supabase_service.py`: Servicios para enviar y obtener datos de Supabase

2. Se han modificado los archivos existentes para usar Supabase en lugar de BigQuery:
   - `src/utils/form_utils.py`: Se cambiu00f3 `format_time_for_bigquery` a `format_time_for_database`
   - `src/components/flight_form.py`: Se actualizu00f3 para usar la nueva funciu00f3n y nomenclatura
   - `src/components/timeline_chart.py`: Se cambiaron las consultas SQL por consultas a la API de Supabase
   - `app.py`: Se actualizu00f3 para usar Supabase en lugar de BigQuery

## Pasos Pendientes

1. **Configurar Supabase**:
   - Crear una cuenta en [Supabase](https://supabase.io/) si au00fan no tienes una
   - Crear un nuevo proyecto
   - Crear una tabla llamada `FlightReport` con la misma estructura que la tabla de BigQuery

2. **Configurar Secretos**:
   - Actualizar el archivo `.streamlit/secrets.toml` con las credenciales de Supabase
   - Puedes usar `example_secrets.toml` como referencia

3. **Migrar Datos Existentes (opcional)**:
   - Si necesitas migrar datos existentes de BigQuery a Supabase, puedes exportar los datos de BigQuery a CSV y luego importarlos a Supabase

## Estructura de la Tabla en Supabase

La tabla `FlightReport` en Supabase debe tener la siguiente estructura (basada en la estructura actual de BigQuery):

```sql
CREATE TABLE "FlightReport" (
  id SERIAL PRIMARY KEY,
  flight_date DATE NOT NULL,
  origin TEXT NOT NULL,
  destination TEXT NOT NULL,
  flight_number TEXT NOT NULL,
  std TEXT,
  atd TEXT,
  groomers_in TEXT,
  groomers_out TEXT,
  crew_at_gate TEXT,
  ok_to_board TEXT,
  flight_secure TEXT,
  cierre_de_puerta TEXT,
  push_back TEXT,
  pax_ob_total INTEGER,
  customs_in TEXT,
  delay INTEGER,
  gate TEXT,
  carrousel TEXT,
  delay_code TEXT,
  WCHR TEXT,
  comments TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Verificaciu00f3n

Despuu00e9s de completar la migraciu00f3n, verifica que:

1. La aplicaciu00f3n pueda conectarse a Supabase correctamente
2. Los datos se envu00eden correctamente a la tabla de Supabase
3. La visualizaciu00f3n de eventos funcione correctamente con los datos de Supabase

## Soporte

Si encuentras algu00fan problema durante la migraciu00f3n, revisa los logs de la aplicaciu00f3n para obtener mu00e1s informaciu00f3n sobre posibles errores.
