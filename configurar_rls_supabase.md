# Configurar Políticas de Seguridad en Supabase

El error que estás viendo (`new row violates row-level security policy for table "FlightReport"`) se debe a que Supabase tiene habilitadas políticas de seguridad de nivel de fila (RLS - Row Level Security) que impiden la inserción de datos en la tabla.

## Opción 1: Desactivar RLS para la tabla FlightReport

1. Inicia sesión en el panel de control de Supabase (https://app.supabase.io)
2. Selecciona tu proyecto
3. Ve a la sección "Table Editor" en el menú lateral
4. Busca la tabla "FlightReport"
5. Haz clic en "Authentication" en el menú superior de la tabla
6. En la sección "Row Level Security (RLS)", desactiva la opción "Enable RLS"

## Opción 2: Crear una política de seguridad permisiva

Si prefieres mantener RLS activado por razones de seguridad, puedes crear una política que permita las operaciones necesarias:

1. Inicia sesión en el panel de control de Supabase
2. Selecciona tu proyecto
3. Ve a la sección "Table Editor" en el menú lateral
4. Busca la tabla "FlightReport"
5. Haz clic en "Authentication" en el menú superior de la tabla
6. En la sección "Policies", haz clic en "New Policy"
7. Selecciona "Create a policy from scratch"
8. Configura la política:
   - **Policy name**: `allow_all_operations`
   - **Target roles**: `authenticated, anon`
   - **Using expression**: `true`
   - **Check expression**: `true`
   - **Operations**: Selecciona todas (SELECT, INSERT, UPDATE, DELETE)
9. Haz clic en "Save Policy"

## Opción 3: Usar un token de servicio

Si necesitas más control, puedes crear un token de servicio con más privilegios:

1. Inicia sesión en el panel de control de Supabase
2. Ve a la sección "Settings" > "API"
3. En la sección "Project API keys", copia el "service_role" key
4. Actualiza tu archivo `.streamlit/secrets.toml` para usar este token en lugar del token anónimo

```toml
[supabase]
url = "TU_URL_DE_SUPABASE"
key = "TU_SERVICE_ROLE_KEY" # Reemplaza con el service_role key
project_ref = "TU_PROJECT_REF"
```

**NOTA**: El uso del token de servicio otorga acceso completo a tu base de datos, así que ten cuidado al usarlo en entornos de producción.

## Después de configurar las políticas

Una vez que hayas configurado las políticas de seguridad, vuelve a ejecutar el script de inserción de datos:

```bash
streamlit run src/insert_test_data.py
```

Y luego ejecuta la aplicación principal:

```bash
streamlit run app.py
```
