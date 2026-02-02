#!/bin/bash
echo "🔍 Debugging Login Issue..."
echo ""

echo "1. Checking Cloud Run Environment Variables:"
echo "=============================================="
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="yaml(spec.template.spec.containers[0].env)" | grep -E "SUPABASE|BIGQUERY"

echo ""
echo "2. Checking Recent Logs:"
echo "=============================================="
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 30 | grep -i "supabase\|login\|auth\|error" | tail -20

echo ""
echo "3. Testing Health Endpoint:"
echo "=============================================="
SERVICE_URL=$(gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
curl -s "$SERVICE_URL/health" | head -20
