# Backend Structure

## Core Application Files

These files are the main application code and should remain in the backend root:

- `main.py` - FastAPI application entry point
- `auth.py` - Authentication and authorization
- `rbac.py` - Role-Based Access Control
- `logger.py` - Logging configuration
- `models.py` - Pydantic models
- `supabase_client.py` - Supabase client wrapper
- `bigquery_service.py` - BigQuery service layer
- `bigquery_client.py` - BigQuery client (if separate)
- `cache_manager.py` - Caching system
- `mock_data.py` - Mock data generator (for development)
- `competition_config.py` - Competition configuration
- `database.py` - Database utilities
- `csv_validator.py` - CSV validation utilities

## Admin Routes

- `admin_routes.py` - Product management routes
- `admin_employees.py` - Employee management routes
- `admin_master.py` - Master data management routes
- `admin_slots.py` - Slot management routes

## Scripts Organization

All utility scripts are organized in the `scripts/` directory:

- `scripts/migrations/` - SQL migration files
- `scripts/imports/` - Data import scripts
- `scripts/seeds/` - Database seeding scripts
- `scripts/utils/` - Utility and analysis scripts
- `scripts/backup/` - Backup and archived files

See `scripts/README.md` for more details.

## Configuration Files

- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not in repo)
- `README_MAINTENANCE.md` - Maintenance notes

## Logs

- `logs/app.log` - Application logs
- `logs/error.log` - Error logs only

Logs are automatically rotated (10MB per file, 5 backups).
