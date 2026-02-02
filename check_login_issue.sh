#!/bin/bash
# Quick check script

echo "🔍 Checking Cloud Run environment variables..."
echo ""

gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(spec.template.spec.containers[0].env)" | grep -E "SUPABASE"

echo ""
echo "✅ If SUPABASE_URL and SUPABASE_KEY are empty or missing, that's the problem!"
echo ""
echo "🔧 Fix: Set them in GitHub Secrets and re-deploy"
