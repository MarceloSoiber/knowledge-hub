from backend.app.core.settings import Settings
from backend.app.services.config import ConfigurationError, _decrypt_api_key, _fernet


def test_api_key_is_encrypted_and_decrypted_with_backend_master_key() -> None:
    settings = Settings(config_encryption_key="3XvZcV6NmcsPPvSLsS8eR0_wOuwL77JyxD7Eey8uS0Y=")
    encrypted = _fernet(settings).encrypt(b"secret-api-key").decode()

    assert encrypted != "secret-api-key"
    assert _decrypt_api_key(encrypted, settings) == "secret-api-key"


def test_api_key_encryption_requires_master_key() -> None:
    try:
        _fernet(Settings(config_encryption_key=""))
    except ConfigurationError as error:
        assert "CONFIG_ENCRYPTION_KEY" in str(error)
    else:
        raise AssertionError("expected configuration error")
