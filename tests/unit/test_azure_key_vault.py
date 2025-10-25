"""
@author Tom Butler
@date 2025-10-25
@description Unit tests for Azure Key Vault integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from azure_key_vault import KeyVaultManager, get_config_value


class TestKeyVaultManager:
    """Test Azure Key Vault manager functionality."""

    def test_manager_disabled_by_default(self, monkeypatch):
        """Test manager is disabled when KEYVAULT_ENABLED is false."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "false")
        manager = KeyVaultManager()
        assert manager.enabled is False
        assert manager.client is None

    def test_manager_disabled_without_vault_url(self, monkeypatch):
        """Test manager is disabled when vault URL not set."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.delenv("KEYVAULT_URL", raising=False)

        manager = KeyVaultManager()
        assert manager.enabled is False

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.DefaultAzureCredential')
    def test_manager_uses_default_credential(self, mock_cred, mock_client, monkeypatch):
        """Test manager uses DefaultAzureCredential when service principal not configured."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")
        monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)

        manager = KeyVaultManager()
        mock_cred.assert_called_once()

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.ClientSecretCredential')
    def test_manager_uses_service_principal(self, mock_cred, mock_client, monkeypatch):
        """Test manager uses service principal when configured."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")
        monkeypatch.setenv("AZURE_TENANT_ID", "tenant-id")
        monkeypatch.setenv("AZURE_CLIENT_ID", "client-id")
        monkeypatch.setenv("AZURE_CLIENT_SECRET", "client-secret")

        manager = KeyVaultManager()
        mock_cred.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            client_secret="client-secret"
        )

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.DefaultAzureCredential')
    def test_get_secret_from_vault(self, mock_cred, mock_client_class, monkeypatch):
        """Test retrieving secret from Key Vault."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")

        # Mock the secret client
        mock_client = Mock()
        mock_secret = Mock()
        mock_secret.value = "secret_value_from_vault"
        mock_client.get_secret.return_value = mock_secret
        mock_client_class.return_value = mock_client

        manager = KeyVaultManager()
        value = manager.get_secret("TEST-SECRET")

        assert value == "secret_value_from_vault"
        mock_client.get_secret.assert_called_once_with("TEST-SECRET")

    def test_get_secret_falls_back_to_env(self, monkeypatch):
        """Test fallback to environment variable when vault disabled."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "false")
        monkeypatch.setenv("TEST_ENV_VAR", "env_value")

        manager = KeyVaultManager()
        value = manager.get_secret("TEST-SECRET", fallback_env_var="TEST_ENV_VAR")

        assert value == "env_value"

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.DefaultAzureCredential')
    def test_get_secret_fallback_on_vault_error(self, mock_cred, mock_client_class, monkeypatch):
        """Test fallback to env var when vault retrieval fails."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")
        monkeypatch.setenv("TEST_ENV_VAR", "env_fallback_value")

        # Mock vault error
        mock_client = Mock()
        mock_client.get_secret.side_effect = Exception("Vault error")
        mock_client_class.return_value = mock_client

        manager = KeyVaultManager()
        value = manager.get_secret("TEST-SECRET", fallback_env_var="TEST_ENV_VAR")

        assert value == "env_fallback_value"

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.DefaultAzureCredential')
    def test_get_all_secrets(self, mock_cred, mock_client_class, monkeypatch):
        """Test retrieving all secrets from vault."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")

        # Mock the client
        mock_client = Mock()

        # Mock secret properties
        mock_props_1 = Mock()
        mock_props_1.name = "SECRET-1"
        mock_props_2 = Mock()
        mock_props_2.name = "SECRET-2"

        # Mock secret values
        mock_secret_1 = Mock()
        mock_secret_1.value = "value1"
        mock_secret_2 = Mock()
        mock_secret_2.value = "value2"

        mock_client.list_properties_of_secrets.return_value = [mock_props_1, mock_props_2]
        mock_client.get_secret.side_effect = [mock_secret_1, mock_secret_2]
        mock_client_class.return_value = mock_client

        manager = KeyVaultManager()
        secrets = manager.get_all_secrets()

        assert len(secrets) == 2
        assert secrets["SECRET-1"] == "value1"
        assert secrets["SECRET-2"] == "value2"

    def test_get_all_secrets_when_disabled(self, monkeypatch):
        """Test get_all_secrets returns empty dict when disabled."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "false")

        manager = KeyVaultManager()
        secrets = manager.get_all_secrets()

        assert secrets == {}

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.DefaultAzureCredential')
    def test_set_secret(self, mock_cred, mock_client_class, monkeypatch):
        """Test setting a secret in vault."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        manager = KeyVaultManager()
        result = manager.set_secret("TEST-SECRET", "test_value")

        assert result is True
        mock_client.set_secret.assert_called_once_with("TEST-SECRET", "test_value")

    def test_set_secret_when_disabled(self, monkeypatch):
        """Test set_secret returns False when disabled."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "false")

        manager = KeyVaultManager()
        result = manager.set_secret("TEST-SECRET", "test_value")

        assert result is False

    @patch('azure_key_vault.SecretClient')
    @patch('azure_key_vault.DefaultAzureCredential')
    def test_delete_secret(self, mock_cred, mock_client_class, monkeypatch):
        """Test deleting a secret from vault."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "true")
        monkeypatch.setenv("KEYVAULT_URL", "https://test.vault.azure.net/")

        mock_client = Mock()
        mock_poller = Mock()
        mock_poller.wait.return_value = None
        mock_client.begin_delete_secret.return_value = mock_poller
        mock_client_class.return_value = mock_client

        manager = KeyVaultManager()
        result = manager.delete_secret("TEST-SECRET")

        assert result is True
        mock_client.begin_delete_secret.assert_called_once_with("TEST-SECRET")

    def test_delete_secret_when_disabled(self, monkeypatch):
        """Test delete_secret returns False when disabled."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "false")

        manager = KeyVaultManager()
        result = manager.delete_secret("TEST-SECRET")

        assert result is False

    @patch('azure_key_vault.KeyVaultManager')
    def test_get_config_value_helper(self, mock_manager_class, monkeypatch):
        """Test get_config_value helper function."""
        mock_manager = Mock()
        mock_manager.get_secret.return_value = "vault_value"
        mock_manager_class.return_value = mock_manager

        # Note: This test would need to import fresh or mock the module-level instance
        # For simplicity, we'll test the function directly
        with patch('azure_key_vault.key_vault_manager', mock_manager):
            value = get_config_value("TEST-SECRET", "TEST_ENV_VAR")
            mock_manager.get_secret.assert_called_once_with("TEST-SECRET", "TEST_ENV_VAR")

    def test_get_secret_returns_none_when_not_found(self, monkeypatch):
        """Test get_secret returns None when secret not found."""
        monkeypatch.setenv("KEYVAULT_ENABLED", "false")

        manager = KeyVaultManager()
        value = manager.get_secret("NONEXISTENT-SECRET")

        assert value is None
