import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from src.config.supabase_config import DEFAULT_TABLE_NAME

def render_wheelchair_tab(client):
    """
    Renderiza la pestaña de Wheelchairs con información sobre servicios de sillas de ruedas.
    
    Args:
        client: Cliente de Supabase inicializado
    """
    try:
        st.header("📊 Informe de Servicios de Sillas de Ruedas")
        
        # Filtros de fecha
        st.subheader("Filtros")
        col1, col2 = st.columns(2)
        
        # Fecha actual y rango predeterminado (7 días atrás hasta hoy)
        current_date = datetime.now().date()
        default_start_date = current_date - timedelta(days=7)
        
        with col1:
            start_date = st.date_input("Fecha Inicial", value=default_start_date)
        with col2:
            end_date = st.date_input("Fecha Final", value=current_date)
        
        # Validar que la fecha final sea posterior a la inicial
        if start_date > end_date:
            st.error("La fecha final debe ser posterior a la fecha inicial")
            return
        
        # Convertir fechas a formato de cadena para la consulta
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Obtener todos los números de vuelo disponibles en el rango de fechas
        flight_numbers_query = client.table(DEFAULT_TABLE_NAME).select("flight_number").gte("flight_date", start_date_str).lte("flight_date", end_date_str).execute()
        
        if not flight_numbers_query.data:
            st.warning("No se encontraron vuelos en el rango de fechas seleccionado")
            return
            
        # Extraer números de vuelo únicos
        flight_numbers = sorted(list(set([item['flight_number'] for item in flight_numbers_query.data if 'flight_number' in item])))
        
        # Filtro de número de vuelo (multiselect para permitir seleccionar varios)
        selected_flights = st.multiselect(
            "Seleccionar Número(s) de Vuelo",
            options=flight_numbers,
            default=None,
            help="Puede seleccionar uno o varios vuelos. Deje vacío para ver todos."
        )
        
        # Botón para ejecutar la consulta
        if st.button("Buscar Datos"):
            # Construir la consulta base
            query = client.table(DEFAULT_TABLE_NAME).select(
                "flight_date", 
                "flight_number", 
                "gate",
                "comments",
                "wchr_previous_flight", 
                "agents_previous_flight", 
                "wchr_current_flight", 
                "agents_current_flight"
            ).gte("flight_date", start_date_str).lte("flight_date", end_date_str)
            
            # Añadir filtro de número de vuelo si se seleccionaron
            if selected_flights:
                query = query.in_("flight_number", selected_flights)
                
            # Ejecutar la consulta
            result = query.execute()
            
            if not result.data:
                st.warning("No se encontraron datos con los filtros seleccionados")
                return
                
            # Convertir a DataFrame para mostrar
            df = pd.DataFrame(result.data)
            
            # Renombrar columnas para mejor visualización
            column_mapping = {
                "flight_date": "Fecha de Vuelo",
                "flight_number": "Número de Vuelo",
                "gate": "Puerta",
                "comments": "Comentarios",
                "wchr_previous_flight": "WCHR Vuelo Llegada",
                "agents_previous_flight": "Agentes Vuelo Llegada",
                "wchr_current_flight": "WCHR Vuelo Salida",
                "agents_current_flight": "Agentes Vuelo Salida"
            }
            
            df = df.rename(columns=column_mapping)
            
            # Mostrar el DataFrame en una tabla
            st.subheader("Resultados")
            st.dataframe(df, use_container_width=True)
            
            # Botón para descargar como CSV
            if not df.empty:
                csv = df.to_csv(index=False)
                
                # Crear un buffer para el CSV
                buffer = io.BytesIO()
                buffer.write(csv.encode())
                buffer.seek(0)
                
                # Botón de descarga
                st.download_button(
                    label="Descargar como CSV",
                    data=buffer,
                    file_name=f"wheelchair_report_{start_date_str}_to_{end_date_str}.csv",
                    mime="text/csv"
                )
                
    except Exception as e:
        st.error(f"Error al cargar los datos de sillas de ruedas: {str(e)}")
        import traceback
        print(f"Error en render_wheelchair_tab: {traceback.format_exc()}")