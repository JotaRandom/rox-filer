import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from gi.repository import Gtk
from rox_filer.window import RoxFilerWindow


@pytest.fixture
def app():
    app = Gtk.Application(application_id="org.rox.filer.test")
    return app


def test_window_initialization(app):
    """Test RoxFilerWindow initialization."""
    with patch.object(Gtk.ApplicationWindow, '__init__', return_value=None) as mock_super_init, \
         patch.object(Gtk.ApplicationWindow, 'set_title') as mock_set_title, \
         patch.object(Gtk.ApplicationWindow, 'set_default_size') as mock_set_default_size, \
         patch.object(Gtk.ApplicationWindow, 'set_child'), \
         patch.object(Gtk.Widget, 'add_controller'):
        
        window = RoxFilerWindow(app)
        
        mock_super_init.assert_called_once_with(application=app)
        assert mock_set_title.call_count == 2
        mock_set_title.assert_any_call("ROX-Filer")
        mock_set_default_size.assert_called_once_with(480, 320)


def test_current_path(app):
    """Test that current_path is set to home."""
    with patch.object(Gtk.ApplicationWindow, '__init__', return_value=None), \
         patch.object(Gtk.ApplicationWindow, 'set_title'), \
         patch.object(Gtk.ApplicationWindow, 'set_default_size'), \
         patch.object(Gtk.ApplicationWindow, 'set_child'), \
         patch.object(Gtk.Widget, 'add_controller'):
         
        window = RoxFilerWindow(app)
        assert window.current_path == Path.home()


def test_load_directory(app):
    """Test load_directory method."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None), \
         patch.object(Gtk.ApplicationWindow, 'set_title') as mock_set_title:
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = None
        window.history = []
        window.view_mode = "grid"
        window.icon_size = 32
        window.address_entry = MagicMock()
        window.fileview = MagicMock()
        
        test_path = Path('/tmp')
        window.load_directory(test_path)
        
        assert window.current_path == test_path
        window.address_entry.set_text.assert_called_once_with(str(test_path))
        mock_set_title.assert_called_once()


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


def test_zoom_in_out(app):
    """Test that zooming in and out cycles through discrete sizes and sets manual_zoom."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = Path.home()
        window.load_directory = MagicMock()
        
        # Start at 24
        window.icon_size = 24
        window.manual_zoom = False
        
        # Zoom in
        window.zoom_in()
        assert window.icon_size == 36
        assert window.manual_zoom is True
        
        # Zoom in again
        window.zoom_in()
        assert window.icon_size == 48
        
        # Zoom out
        window.zoom_out()
        assert window.icon_size == 36
        
        # Zoom out all the way to 16
        window.zoom_out() # to 24
        window.zoom_out() # to 16
        assert window.icon_size == 16
        
        # Try zooming out past minimum (stays at 16)
        window.zoom_out()
        assert window.icon_size == 16


def test_load_directory_respects_manual_zoom(app):
    """Test that load_directory does not overwrite icon_size if manual_zoom is set."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None), \
         patch.object(Gtk.ApplicationWindow, 'set_title'), \
         patch('rox_filer.window.options_manager') as mock_options:
        
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = None
        window.history = []
        window.view_mode = "grid"
        window.icon_size = 36  # Manually zoomed to 36
        window.manual_zoom = True
        window.address_entry = MagicMock()
        window.fileview = MagicMock()
        
        # Mock options to return Auto size (3)
        mock_options.get_int.return_value = 3
        
        # Load directory (should mock iterdir to avoid reading home or temp)
        with patch.object(Path, 'iterdir', return_value=[]):
            window.load_directory(Path('/tmp'))
            
            # Since manual_zoom is True, icon_size must remain 36, not reset to 48 (since file count < 50)
            assert window.icon_size == 36


def test_classic_icon_path():
    """Test get_classic_icon_path returns expected png paths for directories and files."""
    from rox_filer.window import get_classic_icon_path
    
    with patch.object(Path, 'is_dir', return_value=True):
        # Normal directory
        path_dir = Path('/tmp/some_dir')
        icon_path = get_classic_icon_path(path_dir)
        assert 'inode-directory.png' in icon_path
        
    with patch.object(Path, 'is_dir', return_value=False):
        # File (mock content type)
        with patch('gi.repository.Gio.File.new_for_path') as mock_new:
            mock_file = MagicMock()
            mock_new.return_value = mock_file
            mock_info = MagicMock()
            mock_file.query_info.return_value = mock_info
            mock_info.get_content_type.return_value = 'text/plain'
            
            path_file = Path('/tmp/some_file.txt')
            icon_path = get_classic_icon_path(path_file)
            assert 'text-x-generic.png' in icon_path or 'text-plain.png' in icon_path


def test_toggle_show_hidden(app):
    """Test toggle_show_hidden toggles configuration and reloads directory."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None), \
         patch('rox_filer.window.options_manager') as mock_options:
         
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = Path('/tmp')
        window.load_directory = MagicMock()
        
        mock_options.get_bool.return_value = False
        
        window.toggle_show_hidden()
        
        mock_options.set_bool.assert_called_once_with('display_show_hidden', True)
        mock_options.save.assert_called_once()
        window.load_directory.assert_called_once_with(Path('/tmp'), push_history=False)


def test_action_copy(app):
    """Test action_copy sets state and clipboard."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        test_path = Path('/tmp/some_file')
        
        with patch('gi.repository.Gdk.Display.get_default') as mock_get_default:
            mock_display = MagicMock()
            mock_clipboard = MagicMock()
            mock_get_default.return_value = mock_display
            mock_display.get_clipboard.return_value = mock_clipboard
            
            window.action_copy(test_path)
            
            assert window.copied_path == test_path
            mock_clipboard.set.assert_called_once()


def test_action_paste(app, tmp_path):
    """Test action_paste copies file and resolves naming conflicts."""
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.rescan = MagicMock()
        
        # Create temp source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "test.txt"
        src_file.write_text("hello")
        
        # Set copied path
        window.copied_path = src_file
        
        # Paste into a dst directory where it does not exist
        dst_dir = tmp_path / "dst"
        dst_dir.mkdir()
        
        window.action_paste(dst_dir)
        
        pasted_file = dst_dir / "test.txt"
        assert pasted_file.exists()
        assert pasted_file.read_text() == "hello"
        window.rescan.assert_called_once()
        
        # Paste again (conflict resolution)
        window.action_paste(dst_dir)
        conflict_file = dst_dir / "test_copy1.txt"
        assert conflict_file.exists()
        assert conflict_file.read_text() == "hello"


def test_action_decompress_zip(app, tmp_path):
    """Test action_decompress for a zip file."""
    import zipfile
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = tmp_path
        window.rescan = MagicMock()
        
        # Create a mock zip
        zip_path = tmp_path / "test.zip"
        
        # Let's write dummy data to extract
        file_to_zip = tmp_path / "dummy.txt"
        file_to_zip.write_text("zipped content")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(file_to_zip, "dummy.txt")
            
        # Delete original file to verify extraction
        file_to_zip.unlink()
            
        # Decompress
        window.action_decompress(zip_path)
        
        extracted_file = tmp_path / "dummy.txt"
        assert extracted_file.exists()
        window.rescan.assert_called_once()


def test_action_decompress_tar(app, tmp_path):
    """Test action_decompress for a tar.gz file."""
    import tarfile
    with patch.object(RoxFilerWindow, '__init__', return_value=None):
        window = RoxFilerWindow.__new__(RoxFilerWindow)
        window.current_path = tmp_path
        window.rescan = MagicMock()
        
        # Create a mock tar
        tar_path = tmp_path / "test.tar.gz"
        
        file_to_tar = tmp_path / "dummy_tar.txt"
        file_to_tar.write_text("tar content")
        
        with tarfile.open(tar_path, 'w:gz') as tarf:
            tarf.add(file_to_tar, arcname="dummy_tar.txt")
            
        # Delete original file to verify extraction
        file_to_tar.unlink()
            
        # Decompress
        window.action_decompress(tar_path)
        
        extracted_file = tmp_path / "dummy_tar.txt"
        assert extracted_file.exists()
        window.rescan.assert_called_once()