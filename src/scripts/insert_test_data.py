import streamlit as st
import sys
import os
import datetime
import random
from datetime import timedelta

# Agregar el directorio rau00edz al path para que las importaciones funcionen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from src.config.supabase_config import initialize_supabase_client, DEFAULT_TABLE_NAME
from src.config.logging_config import setup_logger

# Configurar logger
logger = setup_logger()

def generate_time(base_hour, base_minute, variation_minutes=0):
    """Genera un tiempo aleatorio con variaciones."""
    if variation_minutes > 0:
        minutes_variation = random.randint(-variation_minutes, variation_minutes)
    else:
        minutes_variation = 0
        
    total_minutes = base_hour * 60 + base_minute + minutes_variation
    
    # Asegurar que estamos dentro de un día (24 horas)
    total_minutes = total_minutes % (24 * 60)
    
    hour = total_minutes // 60
    minute = total_minutes % 60
    
    return f"{hour:02d}:{minute:02d}:00"

def generate_sequential_times(base_hour, base_minute):
    """Genera tiempos secuenciales en orden cronológico."""
    # Definir intervalos en minutos entre eventos
    intervals = {
        "groomers_in": -120,  # 2 horas antes del STD
        "groomers_out": -90,  # 1.5 horas antes del STD
        "crew_at_gate": -60,  # 1 hora antes del STD
        "ok_to_board": -30,   # 30 minutos antes del STD
        "flight_secure": -15,  # 15 minutos antes del STD
        "cierre_de_puerta": -10,  # 10 minutos antes del STD
        "push_back": -5,      # 5 minutos antes del STD
        "std": 0,             # Hora base
        "atd": 5             # 5 minutos después del STD
    }
    
    times = {}
    for event, minutes in intervals.items():
        total_minutes = base_hour * 60 + base_minute + minutes
        # Asegurar que estamos dentro de un día (24 horas)
        total_minutes = total_minutes % (24 * 60)
        hour = total_minutes // 60
        minute = total_minutes % 60
        times[event] = f"{hour:02d}:{minute:02d}:00"
    
    return times

def generate_test_data():
    """Genera un conjunto de datos de prueba variados."""
    # Fechas de prueba (últimos 7 días)
    today = datetime.datetime.now().date()
    test_dates = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    # Rutas comunes
    routes = [
        ("YYZ", "BOG"), ("YYZ", "BOG2"),
        ("YYZ", "SAL")
    ]
    
    # Números de vuelo
    flight_numbers = [f"AV{random.randint(100, 103)}" for _ in range(20)]
    
    # Generar datos
    test_data = []
    
    # 1. Vuelos normales durante el día (10 vuelos)
    for i in range(10):
        # Hora base entre 8:00 y 18:00
        base_hour = random.randint(8, 18)
        base_minute = random.randint(0, 59)
        
        # Seleccionar ruta y fecha aleatorias
        origin, destination = random.choice(routes)
        flight_date = random.choice(test_dates)
        flight_number = random.choice(flight_numbers)
        
        # Generar tiempos secuenciales
        times = generate_sequential_times(base_hour, base_minute)
        
        # Datos adicionales
        pax_ob_total = str(random.randint(80, 200))
        delay = str(random.randint(0, 30))
        gate = f"G{random.randint(1, 20)}"
        carrousel = str(random.randint(1, 8))
        delay_codes = ["CREW", "WEATHER", "TECHNICAL", "ATC", "SECURITY", "NONE"]
        delay_code = random.choice(delay_codes) if int(delay) > 0 else "NONE"
        wchr = str(random.randint(0, 5))
        
        flight_data = {
            "flight_date": flight_date,
            "origin": origin,
            "destination": destination,
            "flight_number": flight_number,
            "std": times["std"],
            "atd": times["atd"],
            "groomers_in": times["groomers_in"],
            "groomers_out": times["groomers_out"],
            "crew_at_gate": times["crew_at_gate"],
            "ok_to_board": times["ok_to_board"],
            "flight_secure": times["flight_secure"],
            "cierre_de_puerta": times["cierre_de_puerta"],
            "push_back": times["push_back"],
            "pax_ob_total": pax_ob_total,
            "customs_in": "N/A",
            "delay": delay,
            "gate": gate,
            "carrousel": carrousel,
            "delay_code": delay_code,
            "WCHR": wchr,
            "comments": "Vuelo normal durante el día"
        }
        
        test_data.append(flight_data)
    
    # 2. Vuelos nocturnos que cruzan la medianoche (5 vuelos)
    for i in range(5):
        # Hora base entre 22:00 y 23:59
        base_hour = random.randint(22, 23)
        base_minute = random.randint(0, 59)
        
        # Seleccionar ruta y fecha aleatorias
        origin, destination = random.choice(routes)
        flight_date = random.choice(test_dates)
        flight_number = random.choice(flight_numbers)
        
        # Generar tiempos secuenciales
        times = generate_sequential_times(base_hour, base_minute)
        
        # Datos adicionales
        pax_ob_total = str(random.randint(80, 200))
        delay = str(random.randint(0, 30))
        gate = f"G{random.randint(1, 20)}"
        carrousel = str(random.randint(1, 8))
        delay_codes = ["CREW", "WEATHER", "TECHNICAL", "ATC", "SECURITY", "NONE"]
        delay_code = random.choice(delay_codes) if int(delay) > 0 else "NONE"
        wchr = str(random.randint(0, 5))
        
        flight_data = {
            "flight_date": flight_date,
            "origin": origin,
            "destination": destination,
            "flight_number": flight_number,
            "std": times["std"],
            "atd": times["atd"],
            "groomers_in": times["groomers_in"],
            "groomers_out": times["groomers_out"],
            "crew_at_gate": times["crew_at_gate"],
            "ok_to_board": times["ok_to_board"],
            "flight_secure": times["flight_secure"],
            "cierre_de_puerta": times["cierre_de_puerta"],
            "push_back": times["push_back"],
            "pax_ob_total": pax_ob_total,
            "customs_in": "N/A",
            "delay": delay,
            "gate": gate,
            "carrousel": carrousel,
            "delay_code": delay_code,
            "WCHR": wchr,
            "comments": "Vuelo nocturno que cruza la medianoche"
        }
        
        test_data.append(flight_data)
    
    # 3. Vuelos con datos incompletos (3 vuelos)
    for i in range(3):
        # Hora base entre 10:00 y 20:00
        base_hour = random.randint(10, 20)
        base_minute = random.randint(0, 59)
        
        # Seleccionar ruta y fecha aleatorias
        origin, destination = random.choice(routes)
        flight_date = random.choice(test_dates)
        flight_number = random.choice(flight_numbers)
        
        # Generar tiempos secuenciales
        times = generate_sequential_times(base_hour, base_minute)
        
        # Omitir algunos datos intencionalmente
        if random.random() < 0.5:
            times["groomers_out"] = ""
        if random.random() < 0.5:
            times["ok_to_board"] = ""
        if random.random() < 0.5:
            times["cierre_de_puerta"] = ""
        
        # Datos adicionales
        pax_ob_total = str(random.randint(80, 200))
        delay = str(random.randint(0, 30))
        gate = f"G{random.randint(1, 20)}"
        carrousel = str(random.randint(1, 8))
        delay_codes = ["CREW", "WEATHER", "TECHNICAL", "ATC", "SECURITY", "NONE"]
        delay_code = random.choice(delay_codes) if int(delay) > 0 else "NONE"
        wchr = str(random.randint(0, 5))
        
        flight_data = {
            "flight_date": flight_date,
            "origin": origin,
            "destination": destination,
            "flight_number": flight_number,
            "std": times["std"],
            "atd": times["atd"],
            "groomers_in": times["groomers_in"],
            "groomers_out": times["groomers_out"],
            "crew_at_gate": times["crew_at_gate"],
            "ok_to_board": times["ok_to_board"],
            "flight_secure": times["flight_secure"],
            "cierre_de_puerta": times["cierre_de_puerta"],
            "push_back": times["push_back"],
            "pax_ob_total": pax_ob_total,
            "customs_in": "N/A",
            "delay": delay,
            "gate": gate,
            "carrousel": carrousel,
            "delay_code": delay_code,
            "WCHR": wchr,
            "comments": "Vuelo con datos incompletos"
        }
        
        test_data.append(flight_data)
    
    return test_data

def main():
    st.title("Insertar Datos de Prueba en Supabase")
    
    # Inicializar cliente de Supabase
    client, project_ref, error = initialize_supabase_client()
    
    if error:
        st.error(f"Error al conectar con Supabase: {error}")
        return
    
    st.success("Conexiu00f3n a Supabase establecida correctamente")
    st.write(f"Proyecto: {project_ref}")
    
    # Opciones de generaciu00f3n de datos
    st.subheader("Opciones de Generaciu00f3n de Datos")
    
    # Seleccionar tipo de datos a generar
    data_type = st.radio(
        "Tipo de datos a generar:",
        ["Datos predefinidos (2 vuelos)", "Datos aleatorios (20 vuelos variados)"],
        index=1
    )
    
    # Datos de prueba para insertar
    if data_type == "Datos predefinidos (2 vuelos)":
        test_data = [
            {
                "flight_date": "2025-03-19",
                "origin": "BOG",
                "destination": "MDE",
                "flight_number": "AV205",
                "std": "08:30:00",
                "atd": "08:45:00",
                "groomers_in": "07:15:00",
                "groomers_out": "07:45:00",
                "crew_at_gate": "08:00:00",
                "ok_to_board": "08:15:00",
                "flight_secure": "08:35:00",
                "cierre_de_puerta": "08:40:00",
                "push_back": "08:45:00",
                "pax_ob_total": "120",
                "customs_in": "N/A",
                "delay": "15",
                "gate": "G12",
                "carrousel": "3",
                "delay_code": "CREW",
                "WCHR": "0",
                "comments": "Vuelo de prueba"
            },
            {
                "flight_date": "2025-03-18",
                "origin": "MDE",
                "destination": "BOG",
                "flight_number": "AV255",
                "std": "14:30:00",
                "atd": "14:40:00",
                "groomers_in": "13:15:00",
                "groomers_out": "13:45:00",
                "crew_at_gate": "14:00:00",
                "ok_to_board": "14:15:00",
                "flight_secure": "14:35:00",
                "cierre_de_puerta": "14:38:00",
                "push_back": "14:40:00",
                "pax_ob_total": "150",
                "customs_in": "N/A",
                "delay": "10",
                "gate": "G5",
                "carrousel": "2",
                "delay_code": "WEATHER",
                "WCHR": "2",
                "comments": "Retraso por lluvia"
            }
        ]
    else:
        # Generar datos aleatorios
        test_data = generate_test_data()
        
        # Mostrar resumen de los datos generados
        st.write(f"Se generaron {len(test_data)} vuelos de prueba:")
        st.write("- 10 vuelos normales durante el día")
        st.write("- 5 vuelos nocturnos que cruzan la medianoche")
        st.write("- 3 vuelos con datos incompletos")
    
    # Botu00f3n para insertar datos
    if st.button("Insertar Datos de Prueba"):
        with st.spinner("Insertando datos..."):
            success_count = 0
            for data in test_data:
                try:
                    response = client.table(DEFAULT_TABLE_NAME).insert(data).execute()
                    
                    if hasattr(response, 'error') and response.error is not None:
                        st.error(f"Error al insertar datos: {response.error}")
                        logger.error(f"Error al insertar datos: {response.error}")
                    else:
                        success_count += 1
                        logger.info(f"Datos insertados correctamente: {data['flight_number']}")
                except Exception as e:
                    st.error(f"Error al insertar datos: {str(e)}")
                    logger.exception(f"Error al insertar datos: {e}")
            
            if success_count > 0:
                st.success(f"Se insertaron {success_count} registros correctamente")
            else:
                st.warning("No se pudo insertar ningún registro")
    
    # Verificar datos existentes
    st.subheader("Datos Existentes en la Tabla")
    try:
        response = client.table(DEFAULT_TABLE_NAME).select("*").execute()
        
        if hasattr(response, 'error') and response.error is not None:
            st.error(f"Error al consultar datos: {response.error}")
        else:
            st.write(f"Registros encontrados: {len(response.data)}")
            if len(response.data) > 0:
                st.write("Registros:")
                for i, record in enumerate(response.data):
                    with st.expander(f"Vuelo {i+1}: {record.get('flight_number')} - {record.get('flight_date')}"):
                        st.json(record)
            else:
                st.warning("No hay registros en la tabla")
    except Exception as e:
        st.error(f"Error al consultar datos: {str(e)}")

if __name__ == "__main__":
    main()
