from typing import Dict, Any, List, Optional

from src.config.logging_config import setup_logger

# Configure logger
logger = setup_logger()

# Custom Exceptions
class SupabaseError(Exception):
    """Base class for Supabase related errors."""
    pass

class SupabaseWriteError(SupabaseError):
    """Error during Supabase write operation."""
    pass

class SupabaseReadError(SupabaseError):
    """Error during Supabase read operation."""
    pass

def send_data_to_supabase(client, table_name: str, data: Dict[str, Any]) -> None:
    """
    Sends data to Supabase.
    
    Args:
        client: Initialized Supabase client
        table_name (str): Name of the Supabase table
        data (Dict[str, Any]): Data to send
        
    Raises:
        SupabaseWriteError: If the Supabase client is not initialized or if an error occurs during the write operation.
    """
    if client is None:
        error_msg = "Cannot send data: Supabase client is not initialized"
        logger.error(error_msg)
        raise SupabaseWriteError(error_msg)
        
    try:
        logger.info(f"Sending data to Supabase table: {table_name}")
        logger.debug(f"Data to send: {data}") # Changed to debug for potentially large data
        
        # Insert data into the Supabase table
        response = client.table(table_name).insert(data).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error is not None:
            error_msg = f"Error inserting into Supabase: {response.error}"  
            logger.error(error_msg)
            raise SupabaseWriteError(error_msg)
        else:
            logger.info("Data sent successfully to Supabase")
            # No return needed on success, absence of exception implies success
            
    except Exception as e:
        # Catch any other exception during the process, including network errors etc.
        # and wrap it in SupabaseWriteError for consistent error handling by the caller.
        error_msg = f"Error sending data to Supabase: {str(e)}"
        logger.exception(error_msg) # Log the full traceback
        raise SupabaseWriteError(error_msg)

def fetch_data_from_supabase(client, table_name: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Fetches data from Supabase with optional filters.
    
    Args:
        client: Initialized Supabase client
        table_name (str): Name of the Supabase table
        query_params (Optional[Dict[str, Any]]): Optional query parameters (e.g., for filtering)
        
    Returns:
        List[Dict[str, Any]]: Data fetched from Supabase.
        
    Raises:
        SupabaseReadError: If the Supabase client is not initialized or if an error occurs during the read operation.
    """
    if client is None:
        error_msg = "Cannot fetch data: Supabase client is not initialized"
        logger.error(error_msg)
        raise SupabaseReadError(error_msg)
    
    try:
        logger.info(f"Fetching data from Supabase table: {table_name}")
        
        # Start the query
        query = client.table(table_name).select("*")
        
        # Apply filters if they exist
        if query_params:
            logger.debug(f"Applying query parameters: {query_params}")
            for key, value in query_params.items():
                if value is not None: # Ensure value is not None before applying filter
                    query = query.eq(key, value)
        
        # Execute the query
        response = query.execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error is not None:
            error_msg = f"Error querying Supabase: {response.error}"
            logger.error(error_msg)
            raise SupabaseReadError(error_msg)
        else:
            data: List[Dict[str, Any]] = response.data
            logger.info(f"Data fetched successfully from Supabase: {len(data)} records")
            return data
            
    except Exception as e:
        # Catch any other exception and wrap it
        error_msg = f"Error fetching data from Supabase: {str(e)}"
        logger.exception(error_msg) # Log the full traceback
        raise SupabaseReadError(error_msg)