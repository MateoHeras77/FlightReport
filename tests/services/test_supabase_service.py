import pytest
from unittest.mock import MagicMock, patch
from src.services.supabase_service import send_data_to_supabase, SupabaseWriteError

@patch('src.services.supabase_service.logger') # Mock logger to avoid actual logging
def test_send_data_supabase_success(mock_logger):
    """Test successful data sending to Supabase."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.error = None
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_response

    table_name = "FlightReport"
    data = {"key": "value"}

    try:
        send_data_to_supabase(mock_client, table_name, data)
    except SupabaseWriteError:
        pytest.fail("SupabaseWriteError raised unexpectedly on success.")

    mock_client.table.assert_called_once_with(table_name)
    mock_client.table(table_name).insert.assert_called_once_with(data)
    mock_client.table(table_name).insert(data).execute.assert_called_once()

@patch('src.services.supabase_service.logger')
def test_send_data_supabase_failure_raises_exception(mock_logger):
    """Test that SupabaseWriteError is raised when Supabase client returns an error."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.error = "Simulated database error"
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_response

    table_name = "FlightReport"
    data = {"key": "value"}

    with pytest.raises(SupabaseWriteError) as excinfo:
        send_data_to_supabase(mock_client, table_name, data)
    
    assert "Simulated database error" in str(excinfo.value)
    mock_client.table.assert_called_once_with(table_name)
    mock_client.table(table_name).insert.assert_called_once_with(data)
