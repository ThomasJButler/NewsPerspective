"""
@author Tom Butler
@date 2025-10-25
@description Azure Key Vault integration for secure secret management.
             Retrieves API keys and credentials from Azure Key Vault instead of .env files.
"""

import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from logger_config import setup_logger

logger = setup_logger("NewsPerspective.KeyVault")


class KeyVaultManager:
    """Manages secrets retrieval from Azure Key Vault."""

    def __init__(self):
        """Initialise Key Vault manager with credentials."""
        self.enabled = os.getenv("KEYVAULT_ENABLED", "false").lower() == "true"
        self.vault_url = os.getenv("KEYVAULT_URL", "")

        if not self.enabled:
            logger.info("Azure Key Vault disabled, using environment variables")
            self.client = None
            return

        if not self.vault_url:
            logger.warning("KEYVAULT_URL not set, falling back to environment variables")
            self.enabled = False
            self.client = None
            return

        try:
            # Try service principal authentication first
            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")

            if tenant_id and client_id and client_secret:
                credential = ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret
                )
                logger.info("Using service principal authentication for Key Vault")
            else:
                # Fall back to default credential chain
                credential = DefaultAzureCredential()
                logger.info("Using default Azure credential for Key Vault")

            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            logger.info(f"Successfully connected to Azure Key Vault: {self.vault_url}")

        except Exception as e:
            logger.error(f"Failed to initialise Key Vault client: {str(e)}")
            logger.warning("Falling back to environment variables")
            self.enabled = False
            self.client = None

    def get_secret(self, secret_name, fallback_env_var=None):
        """
        Retrieve a secret from Key Vault or fall back to environment variable.
        @param {str} secret_name - Name of secret in Key Vault
        @param {str} fallback_env_var - Environment variable name to use if Key Vault unavailable
        @return {str} Secret value or None
        """
        # If Key Vault disabled, use environment variable
        if not self.enabled or not self.client:
            if fallback_env_var:
                value = os.getenv(fallback_env_var)
                if value:
                    logger.debug(f"Retrieved {fallback_env_var} from environment")
                return value
            return None

        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
            return secret.value

        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{secret_name}' from Key Vault: {str(e)}")

            # Fall back to environment variable
            if fallback_env_var:
                value = os.getenv(fallback_env_var)
                if value:
                    logger.debug(f"Retrieved {fallback_env_var} from environment (fallback)")
                return value

            return None

    def get_all_secrets(self):
        """
        Retrieve all secrets from Key Vault.
        @return {dict} Dictionary mapping secret names to values
        """
        if not self.enabled or not self.client:
            logger.info("Key Vault disabled, cannot retrieve all secrets")
            return {}

        secrets = {}

        try:
            for secret_properties in self.client.list_properties_of_secrets():
                secret_name = secret_properties.name

                try:
                    secret = self.client.get_secret(secret_name)
                    secrets[secret_name] = secret.value
                except Exception as e:
                    logger.error(f"Failed to retrieve secret '{secret_name}': {str(e)}")

            logger.info(f"Retrieved {len(secrets)} secrets from Key Vault")
            return secrets

        except Exception as e:
            logger.error(f"Failed to list secrets from Key Vault: {str(e)}")
            return {}

    def set_secret(self, secret_name, secret_value):
        """
        Store a secret in Key Vault.
        @param {str} secret_name - Name of secret
        @param {str} secret_value - Value to store
        @return {bool} Success status
        """
        if not self.enabled or not self.client:
            logger.warning("Key Vault disabled, cannot set secret")
            return False

        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"Successfully stored secret '{secret_name}' in Key Vault")
            return True

        except Exception as e:
            logger.error(f"Failed to store secret '{secret_name}': {str(e)}")
            return False

    def delete_secret(self, secret_name):
        """
        Delete a secret from Key Vault.
        @param {str} secret_name - Name of secret to delete
        @return {bool} Success status
        """
        if not self.enabled or not self.client:
            logger.warning("Key Vault disabled, cannot delete secret")
            return False

        try:
            poller = self.client.begin_delete_secret(secret_name)
            poller.wait()
            logger.info(f"Successfully deleted secret '{secret_name}' from Key Vault")
            return True

        except Exception as e:
            logger.error(f"Failed to delete secret '{secret_name}': {str(e)}")
            return False


# Global instance
key_vault_manager = KeyVaultManager()


def get_config_value(secret_name, env_var_name):
    """
    Helper function to get configuration value from Key Vault or environment.
    @param {str} secret_name - Key Vault secret name
    @param {str} env_var_name - Environment variable name (fallback)
    @return {str} Configuration value
    """
    return key_vault_manager.get_secret(secret_name, env_var_name)
