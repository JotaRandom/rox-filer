import pytest
from unittest.mock import patch
from pathlib import Path
from rox_filer.options import OptionsManager, DEFAULT_OPTIONS

def test_options_manager_defaults(tmp_path):
    test_file = tmp_path / "Options"
    with patch.object(OptionsManager, '_resolve_options_path', return_value=test_file):
        manager = OptionsManager()
        
        # Verify defaults
        assert manager.get("bind_single_click") == "0"
        assert manager.get_int("display_icon_size") == 0
        assert manager.get_bool("display_dirs_first") is True
        assert manager.get_bool("display_show_hidden") is False
        assert manager.get("non_existent_option") == ""

def test_options_manager_set_and_save(tmp_path):
    test_file = tmp_path / "Options"
    with patch.object(OptionsManager, '_resolve_options_path', return_value=test_file):
        manager = OptionsManager()
        
        # Update settings
        manager.set("display_icon_size", "2")
        manager.set("display_show_hidden", "1")
        manager.set_bool("bind_single_click", True)
        manager.set_int("filer_view_type", 1)
        
        assert test_file.exists()
        
        # Load from new instance
        manager2 = OptionsManager()
        assert manager2.get_int("display_icon_size") == 2
        assert manager2.get_bool("display_show_hidden") is True
        assert manager2.get_bool("bind_single_click") is True
        assert manager2.get_int("filer_view_type") == 1

def test_options_manager_invalid_xml(tmp_path):
    test_file = tmp_path / "Options"
    test_file.write_text("invalid xml data")
    
    with patch.object(OptionsManager, '_resolve_options_path', return_value=test_file):
        manager = OptionsManager()
        # Should fall back to default values gracefully
        assert manager.get("bind_single_click") == "0"
