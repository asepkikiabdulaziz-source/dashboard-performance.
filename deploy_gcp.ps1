# Helper Script: Deploy to Google Cloud Run
# Simpan sebagai deploy_gcp.ps1

# 1. Konfigurasi (Ubah PROJECT_ID sesuai ID di GCP Console Anda)
$PROJECT_ID = "myproject-482315" # Berdasarkan file JSON Anda
$IMAGE_NAME = "dashboard-performance"
$REGION = "asia-southeast2"
$REPOSITORY = "dashboard-repo"

Write-Host "🚀 Memulai proses deployment ke Google Cloud Run..." -ForegroundColor Cyan

# 2. Login (Hanya jika belum login)
# gcloud auth login

# 3. Set Project
Write-Host "Set Project ke: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 4. Build dan Push menggunakan Google Cloud Build
Write-Host "🏗️ Membangun Container di Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$IMAGE_NAME"

# 5. Deploy ke Cloud Run
Write-Host "🚢 Mendeploy ke Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $IMAGE_NAME `
    --image "gcr.io/$PROJECT_ID/$IMAGE_NAME" `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 5 `
    --port 8080

Write-Host "✅ Selesai! Aplikasi Anda sekarang online." -ForegroundColor Green
