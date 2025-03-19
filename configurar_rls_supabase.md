# Configurar Polu00edticas de Seguridad en Supabase

El error que estu00e1s viendo (`new row violates row-level security policy for table "FlightReport"`) se debe a que Supabase tiene habilitadas polu00edticas de seguridad de nivel de fila (RLS - Row Level Security) que impiden la inserciu00f3n de datos en la tabla.

## Opciu00f3n 1: Desactivar RLS para la tabla FlightReport

1. Inicia sesiu00f3n en el panel de control de Supabase (https://app.supabase.io)
2. Selecciona tu proyecto
3. Ve a la secciu00f3n "Table Editor" en el menu00fa lateral
4. Busca la tabla "FlightReport"
5. Haz clic en "Authentication" en el menu00fa superior de la tabla
6. En la secciu00f3n "Row Level Security (RLS)", desactiva la opciu00f3n "Enable RLS"

## Opciu00f3n 2: Crear una polu00edtica de seguridad permisiva

Si prefieres mantener RLS activado por razones de seguridad, puedes crear una polu00edtica que permita las operaciones necesarias:

1. Inicia sesiu00f3n en el panel de control de Supabase
2. Selecciona tu proyecto
3. Ve a la secciu00f3n "Table Editor" en el menu00fa lateral
4. Busca la tabla "FlightReport"
5. Haz clic en "Authentication" en el menu00fa superior de la tabla
6. En la secciu00f3n "Policies", haz clic en "New Policy"
7. Selecciona "Create a policy from scratch"
8. Configura la polu00edtica:
   - **Policy name**: `allow_all_operations`
   - **Target roles**: `authenticated, anon`
   - **Using expression**: `true`
   - **Check expression**: `true`
   - **Operations**: Selecciona todas (SELECT, INSERT, UPDATE, DELETE)
9. Haz clic en "Save Policy"

## Opciu00f3n 3: Usar un token de servicio

Si necesitas mu00e1s control, puedes crear un token de servicio con mu00e1s privilegios:

1. Inicia sesiu00f3n en el panel de control de Supabase
2. Ve a la secciu00f3n "Settings" > "API"
3. En la secciu00f3n "Project API keys", copia el "service_role" key
4. Actualiza tu archivo `.streamlit/secrets.toml` para usar este token en lugar del token anu00f3nimo

```toml
[supabase]
url = "https://lperiyftrgzchrzvutgx.supabase.co"
key = "TU_SERVICE_ROLE_KEY" # Reemplaza con el service_role key
project_ref = "lperiyftrgzchrzvutgx"
```

**NOTA**: El uso del token de servicio otorga acceso completo a tu base de datos, asu00ed que ten cuidado al usarlo en entornos de producciu00f3n.

## Despuu00e9s de configurar las polu00edticas

Una vez que hayas configurado las polu00edticas de seguridad, vuelve a ejecutar el script de inserciu00f3n de datos:

```
streamlit run src/insert_test_data.py
```

Y luego ejecuta la aplicaciu00f3n principal:

```
streamlit run app.py
```
