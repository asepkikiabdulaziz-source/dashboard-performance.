# Dashboard Performance

Professional analytics dashboard with **Supabase Authentication** and **Row-Level Security** - a modern alternative to Power BI.

## 🎯 Features

- ✅ **Row-Level Security** - Users only see data for their assigned region
- ✅ **Easy Authentication** - Simple login with demo accounts
- ✅ **Interactive Charts** - Professional visualizations with drill-down capabilities
- ✅ **Modern UI** - Clean, responsive design with Ant Design
- ✅ **Real-time Data** - Fast API with automatic filtering
- ✅ **Mobile Friendly** - Fully responsive design

## 🚀 Quick Start

### Demo Credentials

```
Admin (All Regions):
Email: admin@company.com
Password: admin123

Region A User:
Email: user-a@company.com
Password: password123

Region B User:
Email: user-b@company.com
Password: password123

Region C User:
Email: user-c@company.com
Password: password123
```

### Installation

#### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Running Locally

#### Start Backend API

```bash
cd backend
python main.py
```

Backend API will run on `http://localhost:8000`

#### Start Frontend Dev Server

```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:5173`

Open your browser and navigate to `http://localhost:5173`

## 📊 Dashboard Features

### For Regional Users
- **KPI Cards**: Revenue, Achievement Rate, Growth Rate, Forecast
- **Sales Trend Chart**: Weekly revenue visualization
- **Target vs Actual**: Performance tracking
- **13-Week Forecast**: Predictive analytics

### For Admin Users
All regional features PLUS:
- **Region Comparison**: Compare performance across all regions
- **Access to all regional data**: Switch between regions

## 🔒 Row-Level Security

The application implements Row-Level Security at the API level:

1. **Authentication**: JWT tokens contain user region metadata
2. **Middleware**: Every API request validates the token
3. **Data Filtering**: Queries automatically filter by user region
4. **Admin Access**: Users with `region: "ALL"` can see all data

### Security Flow

```
User Login → JWT with region metadata → 
API Request with JWT → Backend validates token → 
Extract user region → Filter data by region → 
Return filtered data
```

## 🏗️ Architecture

### Backend (FastAPI)
- `main.py` - Main API application with endpoints
- `auth.py` - Authentication & JWT handling
- `mock_data.py` - Mock data generator (replace with BigQuery)
- `requirements.txt` - Python dependencies

### Frontend (React + Vite)
- `src/pages/` - Login & Dashboard pages
- `src/components/Charts/` - ECharts components
- `src/contexts/` - Authentication context
- `src/api.js` - Axios API client with interceptors

## 🔄 Connecting to Real Data

### Replace Mock Data with BigQuery

1. Install BigQuery client:
```bash
pip install google-cloud-bigquery
```

2. Update `backend/mock_data.py` to query BigQuery:
```python
from google.cloud import bigquery

def get_sales_data(region):
    client = bigquery.Client()
    query = f"""
        SELECT * FROM sales_table
        WHERE region = '{region}'
    """
    return client.query(query).to_dataframe()
```

3. Add BigQuery credentials to `.env`

### Setup Real Supabase Auth

1. Create Supabase project at https://supabase.com
2. Enable Email authentication
3. Add user metadata (region) in Supabase dashboard
4. Update `backend/auth.py` to use Supabase

## 📦 Deployment

### Deploy to Google Cloud Run

1. Build Docker image:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
COPY frontend/dist /app/static
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. Deploy:
```bash
gcloud run deploy dashboard-performance \
  --source . \
  --platform managed \
  --region asia-southeast2 \
  --allow-unauthenticated
```

## 🎨 Customization

### Change Theme Colors

Edit `frontend/src/main.jsx`:
```javascript
const theme = {
  token: {
    colorPrimary: '#1890ff', // Change to your brand color
    borderRadius: 8,
  },
}
```

### Add More Charts

1. Create new chart component in `src/components/Charts/`
2. Add API endpoint in `backend/main.py`
3. Import and use in `Dashboard.jsx`

## 📈 Tech Stack

- **Frontend**: React 18, Vite, Ant Design, Apache ECharts
- **Backend**: FastAPI, Python 3.11
- **Auth**: JWT (ready for Supabase)
- **Data**: Mock data (ready for BigQuery)

## 🤝 Support

This is a **production-ready prototype** with mock data. To adapt for your use case:

1. Replace mock data with your BigQuery tables
2. Setup Supabase project and update auth config
3. Customize charts and KPIs based on your metrics
4. Deploy to Cloud Run or your preferred platform

## 📄 License

MIT

---

**Built with ❤️ for professional data analytics**
