import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from src.config.supabase_config import DEFAULT_TABLE_NAME
from src.services.supabase_service import fetch_data_from_supabase, SupabaseReadError
from src.config.logging_config import setup_logger # Import logger

logger = setup_logger() # Initialize logger

def render_wheelchair_tab(client):
    """
    Renders the Wheelchairs tab with information about wheelchair services.
    
    Args:
        client: Initialized Supabase client
    """
    try:
        st.header("📊 Wheelchair Services Report")
        
        # Date filters
        st.subheader("Filters")
        col1, col2 = st.columns(2)
        
        current_date = datetime.now().date()
        default_start_date = current_date - timedelta(days=7)
        
        with col1:
            start_date = st.date_input("Start Date", value=default_start_date)
        with col2:
            end_date = st.date_input("End Date", value=current_date)
        
        if start_date > end_date:
            st.error("End date must be after start date.")
            return
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Fetch flight numbers for the filter dropdown within the selected date range
        # This is inefficient as it fetches all data for the date range.
        # A dedicated function in supabase_service to fetch distinct values would be better.
        flight_numbers = []
        try:
            # This will fetch ALL columns for the date range.
            # We are only interested in 'flight_number' and 'flight_date' for filtering.
            # fetch_data_from_supabase does not currently support selecting specific columns or date range filtering directly.
            # This needs to be handled by query_params or by enhancing fetch_data_from_supabase.
            # For now, we fetch all and filter locally.
            # This is a known limitation for this refactoring step.
            
            # Corrected approach: fetch_data_from_supabase takes query_params.
            # However, it doesn't directly support gte/lte for dates in the current simplified form.
            # This is a limitation. We'll fetch all and filter, or assume for now this part might not work as intended
            # without further supabase_service modification.
            # For the purpose of this task, let's assume we fetch all data and filter client-side for the dropdown.
            # This is highly inefficient for large datasets.
            
            all_data_for_filters = fetch_data_from_supabase(client, DEFAULT_TABLE_NAME) # Fetches all data
            
            if all_data_for_filters:
                # Filter by date client-side (inefficient)
                filtered_by_date = [
                    item for item in all_data_for_filters 
                    if item and 'flight_date' in item and start_date_str <= item['flight_date'] <= end_date_str
                ]
                flight_numbers = sorted(list(set([item['flight_number'] for item in filtered_by_date if 'flight_number' in item])))
            
            if not flight_numbers:
                st.warning("No flights found in the selected date range for filter population.")
                # Don't return yet, allow user to click "Search Data" which might have more specific query
        
        except SupabaseReadError as e:
            st.error(f"Error fetching flight numbers for filters: {str(e)}")
            logger.error(f"Error fetching flight numbers for wheelchair tab filters: {e}", exc_info=True)
            return # Stop if filter data can't be loaded

        selected_flights = st.multiselect(
            "Select Flight Number(s)",
            options=flight_numbers,
            default=None,
            help="You can select one or more flights. Leave empty to see all."
        )
        
        if st.button("Search Data"):
            try:
                # Base query_params for date range
                # This assumes fetch_data_from_supabase can be enhanced or already handles date range.
                # For now, this won't filter by date range in fetch_data_from_supabase
                # We will filter client-side after fetching.
                query_params = {
                    # "flight_date_gte": start_date_str, # Hypothetical, not supported by current fetch_data_from_supabase
                    # "flight_date_lte": end_date_str,   # Hypothetical
                }
                if selected_flights:
                    # This assumes fetch_data_from_supabase can handle a list for 'in_' style filtering.
                    # The current implementation of fetch_data_from_supabase only handles .eq()
                    # This is another limitation. We will filter client-side.
                    # query_params["flight_number_in"] = selected_flights # Hypothetical
                    pass


                # Fetch all data and filter client-side due to current limitations of fetch_data_from_supabase
                all_data = fetch_data_from_supabase(client, DEFAULT_TABLE_NAME, None) # Fetch all
                
                # Client-side filtering
                filtered_data = all_data
                if filtered_data:
                    # Date filtering
                    filtered_data = [
                        d for d in filtered_data if d and 'flight_date' in d and start_date_str <= d['flight_date'] <= end_date_str
                    ]
                    # Flight number filtering
                    if selected_flights:
                        filtered_data = [
                            d for d in filtered_data if d and 'flight_number' in d and d['flight_number'] in selected_flights
                        ]

                if not filtered_data:
                    st.warning("No data found with the selected filters.")
                    return
                
                df = pd.DataFrame(filtered_data)
                
                # Select and rename columns as in the original code
                # Ensure all keys are present or use .get()
                df = df[[
                    "created_at", "flight_date", "flight_number", "gate", "comments",
                    "wchr_previous_flight", "agents_previous_flight", 
                    "wchr_current_flight", "agents_current_flight",
                    "std", "atd", "cierre_de_puerta", "push_back",
                    "groomers_in", "groomers_out"
                ]]

                df['created_at'] = pd.to_datetime(df.get('created_at'))
                df = df.sort_values(by='created_at')
                df = df.drop_duplicates(subset=['std', 'cierre_de_puerta','push_back','groomers_in','groomers_out'], keep='last')
                
                column_mapping = {
                    "created_at": "Creation Date",
                    "flight_date": "Flight Date",
                    "flight_number": "Flight Number",
                    "gate": "Gate",
                    "comments": "Comments",
                    "wchr_previous_flight": "WCHR Arrival Flight",
                    "agents_previous_flight": "Agents Arrival Flight",
                    "wchr_current_flight": "WCHR Departure Flight",
                    "agents_current_flight": "Agents Departure Flight",
                    "std": "STD",
                    "atd": "ATD",
                    "cierre_de_puerta": "Door Closure",
                    "push_back": "Push Back",
                    "groomers_in": "Groomers In",
                    "groomers_out": "Groomers Out"
                }
                df = df.rename(columns=column_mapping).sort_values(by="Flight Date")
                
                st.subheader("Results")
                st.dataframe(df, use_container_width=True)
                
                if not df.empty:
                    csv = df.to_csv(index=False)
                    buffer = io.BytesIO()
                    buffer.write(csv.encode())
                    buffer.seek(0)
                    
                    st.download_button(
                        label="Download as CSV",
                        data=buffer,
                        file_name=f"wheelchair_report_{start_date_str}_to_{end_date_str}.csv",
                        mime="text/csv"
                    )
            except SupabaseReadError as e:
                st.error(f"Error fetching wheelchair data: {str(e)}")
                logger.error(f"SupabaseReadError in wheelchair_tab when searching data: {e}", exc_info=True)
            except Exception as e: # Catch any other unexpected errors during data processing
                st.error(f"An unexpected error occurred while processing data: {str(e)}")
                logger.error(f"Unexpected error in wheelchair_tab search data block: {e}", exc_info=True)

    except SupabaseReadError as e: # Catch errors during initial filter population
        st.error(f"Error loading initial filter data: {str(e)}")
        logger.error(f"SupabaseReadError populating filters in wheelchair_tab: {e}", exc_info=True)
    except Exception as e: # General error catch for the tab
        st.error(f"Error loading wheelchair services data: {str(e)}")
        logger.error(f"Generic error in render_wheelchair_tab: {e}", exc_info=True)