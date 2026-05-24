import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from rox_filer.main import main


def test_main_import():
    """Test that the main module can be imported."""
    from rox_filer import main
    assert main is not None


def test_main_function_exists():
    """Test that the main function exists."""
    from rox_filer.main import main
    assert callable(main)


@patch('rox_filer.main.Gtk.Application')
@patch('sys.exit')
def test_main_execution(mock_exit, mock_app):
    """Test the main application entry point."""
    mock_exit.side_effect = SystemExit
    mock_app_instance = MagicMock()
    mock_app.return_value = mock_app_instance

    with patch('rox_filer.main.RoxFilerWindow'):
        # This will raise SystemExit normally, so we catch it
        with pytest.raises(SystemExit):
            main()

    mock_app.assert_called_once()
    mock_app_instance.connect.assert_called_with("activate", mock_app_instance.connect.call_args[0][1])


def test_window_import():
    """Test that the window module can be imported."""
    from rox_filer.window import RoxFilerWindow
    assert RoxFilerWindow is not None