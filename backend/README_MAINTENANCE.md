# Maintenance Notes

## Duplicate Files

### `main_git.py`
- **Status**: Duplicate of `main.py`
- **Action**: Can be safely removed or moved to `scripts/backup/` folder
- **Note**: No references found in codebase. Appears to be a backup/version control file.

## Logging

### Log Files Location
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Log rotation: 10MB per file, 5 backups

### Environment Variables
- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO
- `ENVIRONMENT`: Set to "production" to disable debug endpoints. Default: "development"

## CORS Configuration

### Environment Variables
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for production
- Default (development): localhost:5173, localhost:3000

Example:
```bash
ALLOWED_ORIGINS=https://dashboard.example.com,https://app.example.com
```

## Debug Endpoints

Debug endpoints are automatically:
- Hidden from Swagger documentation (`include_in_schema=False`)
- Disabled in production mode (when `ENVIRONMENT=production`)
- Protected by super_admin role check

Endpoints:
- `/api/debug/bq` - BigQuery diagnostic
- `/api/debug/assignments` - Assignments check
