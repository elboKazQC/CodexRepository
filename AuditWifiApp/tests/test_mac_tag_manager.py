import tkinter.messagebox  # ensure attribute for patched fixture
from mac_tag_manager import MacTagManager


def test_validate_mac():
    manager = MacTagManager()
    assert manager.validate_mac("AA:BB:CC:DD:EE:FF")
    assert not manager.validate_mac("ZZ:BB:CC:DD:EE:FF")
    assert not manager.validate_mac("AABBCCDDEEFF")


def test_add_and_get_tag(tmp_path, monkeypatch):
    temp_file = tmp_path / "tags.json"
    manager = MacTagManager(file_path=str(temp_file))
    manager.set_tag("AA:BB:CC:DD:EE:FF", "Warehouse")
    manager.save_tags()

    new_manager = MacTagManager(file_path=str(temp_file))
    assert new_manager.get_tag("AA:BB:CC:DD:EE:FF") == "Warehouse"
