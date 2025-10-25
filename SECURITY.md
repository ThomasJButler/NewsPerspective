## NewsPerspective Security Guide

Comprehensive security best practices and Azure Key Vault integration for secret management.

## Table of Contents

1. [Azure Key Vault Integration](#azure-key-vault-integration)
2. [Secret Management](#secret-management)
3. [Authentication Methods](#authentication-methods)
4. [Secret Rotation](#secret-rotation)
5. [Security Best Practices](#security-best-practices)
6. [Incident Response](#incident-response)

---

## Azure Key Vault Integration

### Why Use Key Vault?

- ✅ Centralised secret management
- ✅ Encryption at rest and in transit
- ✅ Access logging and auditing
- ✅ Secret versioning and rotation
- ✅ Eliminates secrets in code/config files
- ✅ RBAC (Role-Based Access Control)

### Setup Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name news-perspective-kv \
  --resource-group news-perspective-rg \
  --location uksouth \
  --enable-rbac-authorization false

# Grant yourself access
USER_PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv)

az keyvault set-policy \
  --name news-perspective-kv \
  --object-id $USER_PRINCIPAL_ID \
  --secret-permissions get list set delete
```

### Store Secrets in Key Vault

```bash
# News API key
az keyvault secret set \
  --vault-name news-perspective-kv \
  --name NEWS-API-KEY \
  --value "your_actual_key_here"

# Azure OpenAI key
az keyvault secret set \
  --vault-name news-perspective-kv \
  --name AZURE-OPENAI-KEY \
  --value "your_actual_key_here"

# Azure Search key
az keyvault secret set \
  --vault-name news-perspective-kv \
  --name AZURE-SEARCH-KEY \
  --value "your_actual_key_here"

# Azure AI Language key
az keyvault secret set \
  --vault-name news-perspective-kv \
  --name AZURE-AI-LANGUAGE-KEY \
  --value "your_actual_key_here"

# Azure Document Intelligence key
az keyvault secret set \
  --vault-name news-perspective-kv \
  --name AZURE-DOCUMENT-INTELLIGENCE-KEY \
  --value "your_actual_key_here"
```

### Enable Key Vault in Application

Update `.env`:

```bash
KEYVAULT_ENABLED=true
KEYVAULT_URL=https://news-perspective-kv.vault.azure.net/

# Service Principal authentication (recommended for production)
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
```

### Usage in Code

```python
from azure_key_vault import get_config_value

# Retrieves from Key Vault if enabled, otherwise from environment variable
news_api_key = get_config_value("NEWS-API-KEY", "NEWS_API_KEY")
openai_key = get_config_value("AZURE-OPENAI-KEY", "AZURE_OPENAI_KEY")
```

---

## Secret Management

### Secret Naming Convention

Key Vault secret names use hyphens instead of underscores:

| Environment Variable | Key Vault Secret Name |
|---------------------|----------------------|
| NEWS_API_KEY | NEWS-API-KEY |
| AZURE_OPENAI_KEY | AZURE-OPENAI-KEY |
| AZURE_SEARCH_KEY | AZURE-SEARCH-KEY |
| AZURE_AI_LANGUAGE_KEY | AZURE-AI-LANGUAGE-KEY |

### Secret Lifecycle

1. **Creation**: Store secrets in Key Vault during initial setup
2. **Retrieval**: Application retrieves secrets at runtime
3. **Rotation**: Regular rotation of API keys (quarterly recommended)
4. **Audit**: Review access logs monthly
5. **Retirement**: Disable old secret versions when rotating

---

## Authentication Methods

### 1. Managed Identity (Recommended for Azure Resources)

Best for Azure Functions, App Services, VMs running on Azure.

```bash
# Enable system-assigned managed identity for Function App
az functionapp identity assign \
  --name news-perspective-func \
  --resource-group news-perspective-rg

# Grant Key Vault access to managed identity
FUNC_PRINCIPAL_ID=$(az functionapp identity show \
  --name news-perspective-func \
  --resource-group news-perspective-rg \
  --query principalId -o tsv)

az keyvault set-policy \
  --name news-perspective-kv \
  --object-id $FUNC_PRINCIPAL_ID \
  --secret-permissions get list
```

No credentials needed in code - Azure handles authentication automatically.

### 2. Service Principal (Recommended for Development/CI)

Create service principal:

```bash
# Create service principal
SP_INFO=$(az ad sp create-for-rbac \
  --name news-perspective-sp \
  --role Reader \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID)

# Extract credentials
CLIENT_ID=$(echo $SP_INFO | jq -r .appId)
CLIENT_SECRET=$(echo $SP_INFO | jq -r .password)
TENANT_ID=$(echo $SP_INFO | jq -r .tenant)

# Grant Key Vault access
az keyvault set-policy \
  --name news-perspective-kv \
  --spn $CLIENT_ID \
  --secret-permissions get list
```

Add to `.env`:

```bash
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
```

### 3. Azure CLI Credential (Local Development)

Login once:

```bash
az login
```

Application uses your logged-in Azure CLI identity automatically.

---

## Secret Rotation

### Quarterly Rotation Schedule

Rotate all API keys every 3 months to maintain security.

**Step 1: Generate New Keys**

```bash
# Example: Rotate Azure OpenAI key
# 1. Generate new key in Azure Portal (Key 2)
# 2. Store new key in Key Vault
az keyvault secret set \
  --vault-name news-perspective-kv \
  --name AZURE-OPENAI-KEY \
  --value "new_key_here"

# Old version automatically archived with version ID
```

**Step 2: Verify Application**

```bash
# Test with new key
python run.py  # Should succeed

# If issues, rollback to previous version
az keyvault secret show \
  --vault-name news-perspective-kv \
  --name AZURE-OPENAI-KEY \
  --version previous_version_id
```

**Step 3: Disable Old Key**

After confirming new key works (48 hours):

```bash
# Disable old key in Azure Portal
# Or regenerate Key 1 in Azure OpenAI resource
```

### Automated Rotation (Advanced)

Use Azure Key Vault rotation policies:

```bash
# Set rotation policy (90 days)
az keyvault secret set-policy \
  --vault-name news-perspective-kv \
  --name NEWS-API-KEY \
  --policy '{"lifetimeActions": [{"action": {"type": "Rotate"}, "trigger": {"timeBeforeExpiry": "P30D"}}]}'
```

---

## Security Best Practices

### 1. Never Commit Secrets

**What to avoid:**
- ❌ API keys in `.env` checked into Git
- ❌ Secrets in GitHub Actions workflow files
- ❌ Credentials in Docker images
- ❌ Keys in screenshots or documentation

**Proper approach:**
- ✅ Use `.gitignore` for `.env` files
- ✅ Use GitHub Secrets for CI/CD
- ✅ Use Key Vault for production secrets
- ✅ Redact credentials in logs

### 2. Principle of Least Privilege

Grant minimum permissions needed:

```bash
# Good: Only secret 'get' permission
az keyvault set-policy \
  --name news-perspective-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get

# Bad: All permissions
az keyvault set-policy \
  --name news-perspective-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions all
```

### 3. Enable Audit Logging

Monitor Key Vault access:

```bash
# Enable diagnostic logging
az monitor diagnostic-settings create \
  --name kv-audit-logs \
  --resource /subscriptions/SUB_ID/resourceGroups/news-perspective-rg/providers/Microsoft.KeyVault/vaults/news-perspective-kv \
  --logs '[{"category": "AuditEvent", "enabled": true}]' \
  --workspace /subscriptions/SUB_ID/resourceGroups/news-perspective-rg/providers/Microsoft.OperationalInsights/workspaces/news-perspective-logs
```

Review logs monthly for suspicious access.

### 4. Network Security

Restrict Key Vault access to specific networks:

```bash
# Allow only Azure services
az keyvault network-rule add \
  --name news-perspective-kv \
  --resource-group news-perspective-rg \
  --subnet /subscriptions/SUB_ID/resourceGroups/news-perspective-rg/providers/Microsoft.Network/virtualNetworks/news-vnet/subnets/default

# Deny all other traffic
az keyvault update \
  --name news-perspective-kv \
  --resource-group news-perspective-rg \
  --default-action Deny
```

### 5. Secret Expiry

Set expiration dates for secrets:

```bash
# Set secret with 90-day expiry
EXPIRY_DATE=$(date -u -d "+90 days" +%Y-%m-%dT%H:%M:%SZ)

az keyvault secret set \
  --vault-name news-perspective-kv \
  --name TEMP-API-KEY \
  --value "temporary_key" \
  --expires $EXPIRY_DATE
```

---

## Incident Response

### If Secrets Are Compromised

**Immediate Actions (within 1 hour):**

1. **Revoke compromised keys**
   ```bash
   # Disable secret in Key Vault
   az keyvault secret set-attributes \
     --vault-name news-perspective-kv \
     --name COMPROMISED-KEY \
     --enabled false
   ```

2. **Regenerate API keys**
   - Azure OpenAI: Regenerate keys in Azure Portal
   - NewsAPI: Generate new key in NewsAPI dashboard
   - Azure Search: Regenerate admin keys

3. **Update Key Vault with new keys**
   ```bash
   az keyvault secret set \
     --vault-name news-perspective-kv \
     --name API-KEY-NAME \
     --value "new_regenerated_key"
   ```

4. **Restart applications**
   ```bash
   # Restart Function App to pick up new secrets
   az functionapp restart \
     --name news-perspective-func \
     --resource-group news-perspective-rg
   ```

**Follow-up Actions (within 24 hours):**

1. Review Key Vault audit logs for unauthorized access
2. Change service principal credentials if compromised
3. Enable additional security controls (network restrictions)
4. Document incident and remediation steps

### Monitoring for Breaches

Set up alerts for suspicious activity:

```bash
# Alert on failed Key Vault access attempts
az monitor metrics alert create \
  --name kv-failed-access \
  --resource-group news-perspective-rg \
  --scopes /subscriptions/SUB_ID/resourceGroups/news-perspective-rg/providers/Microsoft.KeyVault/vaults/news-perspective-kv \
  --condition "count ServiceApiResult where Result = 'Unauthorized' > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group email-admins
```

---

## Compliance Checklist

- [ ] All production secrets stored in Key Vault
- [ ] No secrets in Git repository
- [ ] Managed identity enabled for Azure resources
- [ ] Audit logging enabled on Key Vault
- [ ] Network restrictions configured
- [ ] Secret rotation schedule established
- [ ] Incident response plan documented
- [ ] Access reviewed quarterly
- [ ] Backup of Key Vault configuration
- [ ] Disaster recovery plan in place

---

## Cost Optimisation

Azure Key Vault pricing (UK South):

- Standard tier: £0.025 per 10,000 operations
- Secrets: Free (unlimited)
- Typical monthly cost for this project: < £0.50

Use caching to minimise Key Vault calls:

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def get_cached_secret(secret_name):
    return key_vault_manager.get_secret(secret_name)
```

---

## Additional Resources

- [Azure Key Vault Documentation](https://docs.microsoft.com/azure/key-vault/)
- [Best Practices for Secrets Management](https://docs.microsoft.com/azure/key-vault/general/best-practices)
- [Managed Identities Overview](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [Secret Rotation Tutorial](https://docs.microsoft.com/azure/key-vault/secrets/tutorial-rotation-dual)
