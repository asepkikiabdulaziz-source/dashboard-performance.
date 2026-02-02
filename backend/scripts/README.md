# Backend Scripts

This directory contains organized utility scripts for the dashboard performance application.

## Directory Structure

```
scripts/
├── migrations/     # SQL migration files
├── imports/        # Data import scripts
├── seeds/          # Database seeding scripts
├── utils/          # Utility and analysis scripts
└── backup/         # Backup and temporary files
```

## Usage

### Migrations
SQL migration files for database schema changes. Run these in Supabase SQL Editor.

### Imports
Scripts to import data from external sources (Excel, CSV, etc.)

### Seeds
Scripts to populate reference data (lookups, roles, etc.)

### Utils
Various utility scripts for:
- Analysis (`analyze_*.py`)
- Verification (`verify_*.py`, `check_*.py`)
- Fixes (`fix_*.py`, `apply_*.py`)
- Exploration (`explore_*.py`, `investigate_*.py`)

## Running Scripts

Most scripts can be run directly:
```bash
python scripts/utils/analyze_products.py
python scripts/seeds/seed_roles.py
```

Some scripts may require environment variables or database connections.

## Notes

- Scripts in `backup/` are archived and may not be actively used
- Always backup your database before running migration scripts
- Check script documentation before running utility scripts
