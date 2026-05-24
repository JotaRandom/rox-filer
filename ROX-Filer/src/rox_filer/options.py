import os
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_OPTIONS = {
    'bind_single_click': '0',
    'display_dirs_first': '1',
    'display_show_hidden': '0',
    'display_icon_size': '0',      # 0 = Large, 1 = Small, 2 = Huge, 3 = Auto
    'filer_view_type': '0',        # 0 = Grid, 1 = List
    'display_sort_by': '0',        # 0 = Name, 1 = Type, 2 = Date, 3 = Size
}

class OptionsManager:
    def __init__(self):
        self.options = DEFAULT_OPTIONS.copy()
        self.path = self._resolve_options_path()
        self.load()

    def _resolve_options_path(self) -> Path:
        # Check XDG_CONFIG_HOME
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            p = Path(xdg_config_home) / "rox.sourceforge.net" / "ROX-Filer" / "Options"
            if p.exists():
                return p
        else:
            p = Path.home() / ".config" / "rox.sourceforge.net" / "ROX-Filer" / "Options"
            if p.exists():
                return p

        # Check legacy Choices path
        legacy_path = Path.home() / "Choices" / "ROX-Filer" / "Options"
        if legacy_path.exists():
            return legacy_path

        # Default path to create new settings
        if xdg_config_home:
            return Path(xdg_config_home) / "rox.sourceforge.net" / "ROX-Filer" / "Options"
        return Path.home() / ".config" / "rox.sourceforge.net" / "ROX-Filer" / "Options"

    def load(self):
        if not self.path.exists():
            return

        try:
            tree = ET.parse(self.path)
            root = tree.getroot()
            if root.tag == "Options":
                for child in root:
                    if child.tag == "Option":
                        name = child.attrib.get("name")
                        if name:
                            # Strip whitespace like the original C parser
                            self.options[name] = (child.text or "").strip()
        except Exception as e:
            print(f"[ROX-Filer] Error cargando opciones: {e}")

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            root = ET.Element("Options")
            
            # Sort keys for consistent XML output
            for name in sorted(self.options.keys()):
                opt_elem = ET.SubElement(root, "Option", name=name)
                opt_elem.text = str(self.options[name])

            # Write XML with pretty printing representation
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(self.path, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            print(f"[ROX-Filer] Error guardando opciones: {e}")

    def get(self, name: str) -> str:
        return self.options.get(name, DEFAULT_OPTIONS.get(name, ""))

    def get_int(self, name: str) -> int:
        val = self.get(name)
        try:
            return int(val)
        except ValueError:
            default_val = DEFAULT_OPTIONS.get(name, "0")
            try:
                return int(default_val)
            except ValueError:
                return 0

    def get_bool(self, name: str) -> bool:
        val = self.get(name)
        return val in ('1', 'true', 'True', 'yes', 'Yes')

    def set(self, name: str, value: str):
        self.options[name] = str(value)
        self.save()

    def set_int(self, name: str, value: int):
        self.set(name, str(value))

    def set_bool(self, name: str, value: bool):
        self.set(name, '1' if value else '0')

# Global options manager instance
options_manager = OptionsManager()
