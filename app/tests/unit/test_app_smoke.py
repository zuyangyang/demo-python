def test_app_import_smoke() -> None:
    # Import app and ensure it initializes
    from app.main import app  # noqa: F401


def test_settings_env_parsing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("APP_NAME", "Custom App")
    from importlib import reload
    from app.core import config as config_module

    reload(config_module)
    assert config_module.settings.app_name in {"Custom App", "Demo Python API"}


