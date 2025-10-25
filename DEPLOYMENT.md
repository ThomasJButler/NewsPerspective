# NewsPerspective Deployment Guide

## Azure Functions Deployment

### Prerequisites

- Azure subscription
- Azure CLI installed (`az --version` to verify)
- Python 3.10 or 3.11
- Azure Functions Core Tools v4

### Initial Setup

1. **Create Azure Function App**

```bash
# Login to Azure
az login

# Create resource group
az group create --name news-perspective-rg --location uksouth

# Create storage account for function app
az storage account create \
  --name newsperspectivesa \
  --location uksouth \
  --resource-group news-perspective-rg \
  --sku Standard_LRS

# Create Function App (Linux, Python 3.11)
az functionapp create \
  --resource-group news-perspective-rg \
  --consumption-plan-location uksouth \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name news-perspective-func \
  --storage-account newsperspectivesa \
  --os-type Linux
```

2. **Configure Application Settings**

```bash
# Set all environment variables as application settings
az functionapp config appsettings set \
  --name news-perspective-func \
  --resource-group news-perspective-rg \
  --settings \
    NEWS_API_KEY="your_key" \
    AZURE_OPENAI_KEY="your_key" \
    AZURE_OPENAI_ENDPOINT="your_endpoint" \
    AZURE_SEARCH_KEY="your_key" \
    AZURE_SEARCH_ENDPOINT="your_endpoint" \
    ARTICLE_SOURCE_MODE="mixed" \
    BATCH_TOTAL_ARTICLES="500"
```

3. **Deploy Function App**

```bash
# Deploy using Azure Functions Core Tools
func azure functionapp publish news-perspective-func
```

### GitHub Actions Deployment

1. **Get Publish Profile**

```bash
az functionapp deployment list-publishing-profiles \
  --name news-perspective-func \
  --resource-group news-perspective-rg \
  --xml
```

2. **Add to GitHub Secrets**

- Go to repository Settings → Secrets and variables → Actions
- Create new secret named `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
- Paste the XML publish profile from step 1

3. **Push to trigger deployment**

```bash
git push origin main
```

Deployment will run automatically on pushes to `main` or `master` branches.

### Manual Trigger

Trigger batch processing manually via HTTP:

```bash
# Get function key
FUNCTION_KEY=$(az functionapp function keys list \
  --name news-perspective-func \
  --resource-group news-perspective-rg \
  --function-name ManualBatchProcessor \
  --query "default" -o tsv)

# Trigger processing
curl -X POST "https://news-perspective-func.azurewebsites.net/api/process?code=$FUNCTION_KEY"

# Trigger with custom article count
curl -X POST "https://news-perspective-func.azurewebsites.net/api/process?articles=100&code=$FUNCTION_KEY"
```

### Monitoring

View logs in Azure Portal:
- Navigate to Function App → Functions → scheduled_batch_processor → Monitor
- Or use Application Insights if configured

View logs via CLI:

```bash
az functionapp logs tail \
  --name news-perspective-func \
  --resource-group news-perspective-rg
```

### Schedule Configuration

Default schedule: Daily at 6 AM UTC

To change the schedule, modify `function_app.py`:

```python
@app.timer_trigger(
    schedule="0 0 6 * * *",  # Cron format: sec min hour day month dayOfWeek
    ...
)
```

Common schedules:
- Every 6 hours: `0 0 */6 * * *`
- Twice daily (6 AM & 6 PM): `0 0 6,18 * * *`
- Every hour: `0 0 * * * *`

### Cost Optimisation

Consumption Plan (pay-per-execution):
- First 1 million executions free per month
- £0.000014 per execution after free tier
- £0.000012 per GB-second of execution time

Estimated monthly cost for daily execution: < £1

### Troubleshooting

**Function fails to import modules:**
- Verify all dependencies in requirements.txt
- Check function app Python version matches local development

**Timeout errors:**
- Increase `functionTimeout` in host.json (max 10 min on Consumption plan)
- Consider Premium plan for longer timeouts

**Environment variables not found:**
- Verify application settings in Azure Portal
- Check `.env` file is not deployed (should be in .funcignore)

### Local Development

Test function locally before deploying:

```bash
# Install Azure Functions Core Tools
# macOS: brew install azure-functions-core-tools@4
# Windows: npm install -g azure-functions-core-tools@4

# Copy settings template
cp local.settings.json.template local.settings.json

# Edit local.settings.json with your credentials

# Run locally
func start
```

Test endpoints:
- Health check: http://localhost:7071/api/health
- Manual trigger: http://localhost:7071/api/process
- Timer trigger: Runs on schedule or manually via Azure Portal

## Alternative: Docker Deployment

Build and run in Docker:

```bash
docker build -t news-perspective .
docker run -d --env-file .env news-perspective python batch_processor.py
```

## Alternative: VM/Server Deployment

Set up cron job on Linux server:

```bash
# Edit crontab
crontab -e

# Add daily execution at 6 AM
0 6 * * * cd /path/to/NewsPerspective && /path/to/python batch_processor.py >> /var/log/news-perspective.log 2>&1
```
