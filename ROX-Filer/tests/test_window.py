import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from gi.repository import Gtk
from rox_filer.window import RoxFilerWindow


@pytest.fixture
def app():
    app = Gtk.Application(application_id="org.rox.filer.test")
    return app


@patch('gi.repository.Gtk.ApplicationWindow.__init__')
def test_window_initialization(mock_super_init, app):
    """Test RoxFilerWindow initialization."""
    window = RoxFilerWindow(app)
    
    assert window.get_title() == "ROX-Filer"
    assert window.get_default_size() == (900, 600)
    mock_super_init.assert_called_once()


def test_current_path(app):
    """Test that current_path is set to home."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = None
        window.__init__(app)
        assert window.current_path == Path.home()


def test_load_directory(app):
    """Test load_directory method."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = None
        window.address_entry = MagicMock()
        window.fileview = MagicMock()
        
        test_path = Path('/tmp')
        window.load_directory(test_path)
        
        assert window.current_path == test_path
        window.address_entry.set_text.assert_called_once_with(str(test_path))


def test_go_up(app):
    """Test go_up functionality."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = Path('/home/user/documents')
        window.load_directory = MagicMock()
        
        window.go_up()
        
        window.load_directory.assert_called_once()
        # parent should be /home/user
        assert window.load_directory.call_args[0][0] == Path('/home/user')


def test_go_home(app):
    """Test go_home functionality."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.load_directory = MagicMock()
        
        window.go_home()
        
        window.load_directory.assert_called_once_with(Path.home())