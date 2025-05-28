def generate_flight_report_text(display_data):
    """Generates the flight report text from display_data."""
    
    flight_number = display_data.get('flight_number', '')
    # Mapeo de vuelos para determinar el vuelo anterior
    previous_flight_mapping = {
        "AV205": "AV204",
        "AV627": "AV626",
        "AV255": "AV254"
    }
    previous_flight = previous_flight_mapping.get(flight_number, "")
    
    report_text = f"""
🚀 *Datos Básicos*:
*Fecha de vuelo:* {display_data.get('flight_date', '')}
*Origen:* {display_data.get('origin', '')}
*Destino:* {display_data.get('destination', '')}
*Número de vuelo:* {display_data.get('flight_number', '')}

⏰ *Tiempos:*
*STD:* {display_data.get('std', '')}
*ATD:* {display_data.get('atd', '')}
*Groomers In:* {display_data.get('groomers_in', '')}
*Groomers Out:* {display_data.get('groomers_out', '')}
*Crew at Gate:* {display_data.get('crew_at_gate', '')}
*OK to Board:* {display_data.get('ok_to_board', '')}
*Flight Secure:* {display_data.get('flight_secure', '')}
*Cierre de Puerta:* {display_data.get('cierre_de_puerta', '')}
*Push Back:* {display_data.get('push_back', '')}

📋 *Información de Customs:*
*Customs In:* {display_data.get('customs_in', '')}
*Customs Out:* {display_data.get('customs_out', '')}

👥 *Información de Pasajeros:*
*Total Pax:* {display_data.get('pax_ob_total', '')}
*PAX C:* {display_data.get('pax_c', '')}
*PAX Y:* {display_data.get('pax_y', '')}
*Infantes:* {display_data.get('infants', '')}

⏳ *Información por Demoras:*
*Delay:* {display_data.get('delay', '')}
*Delay Code:* {display_data.get('delay_code', '')}

♿ *Silla de ruedas:*
*Sillas Vuelo Llegada ({previous_flight}):* {display_data.get('wchr_previous_flight', '')}
*Agentes Vuelo Llegada ({previous_flight}):* {display_data.get('agents_previous_flight', '')}
*Sillas Vuelo Salida ({flight_number}):* {display_data.get('wchr_current_flight', '')}
*Agentes Vuelo Salida ({flight_number}):* {display_data.get('agents_current_flight', '')}

📍 *Información de Gate y Carrusel:*
*Gate:* {display_data.get('gate', '')}
*Carrousel:* {display_data.get('carrousel', '')}

🧳 *Información de Gate Bag:*
*Gate Bag:* {display_data.get('gate_bag', '')}

💬 *Comentarios:*
{display_data.get('comments', '')}
"""
    return report_text.strip()
