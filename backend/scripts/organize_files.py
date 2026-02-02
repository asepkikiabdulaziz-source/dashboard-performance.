"""
Script to organize backend files into appropriate folders
Run this once to reorganize the file structure
"""
import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# File mappings: source -> destination folder
FILE_MAPPINGS = {
    # Migrations
    "migration_*.sql": "scripts/migrations",
    "schema_migration.sql": "scripts/migrations",
    "cleanup_legacy_tables.sql": "scripts/migrations",
    "fix_pma_duplicates.sql": "scripts/migrations",
    "sync_price_zones.sql": "scripts/migrations",
    
    # Imports
    "import_*.py": "scripts/imports",
    
    # Seeds
    "seed_*.py": "scripts/seeds",
    
    # Utils - Analysis
    "analyze_*.py": "scripts/utils",
    "audit_*.py": "scripts/utils",
    "check_*.py": "scripts/utils",
    "verify_*.py": "scripts/utils",
    "explore_*.py": "scripts/utils",
    "investigate_*.py": "scripts/utils",
    "list_*.py": "scripts/utils",
    "show_*.py": "scripts/utils",
    "get_*.py": "scripts/utils",
    "find_*.py": "scripts/utils",
    "compare_*.py": "scripts/utils",
    "clarify_*.py": "scripts/utils",
    "save_columns.py": "scripts/utils",
    "extract_*.py": "scripts/utils",
    "fetch_*.py": "scripts/utils",
    "read_*.py": "scripts/utils",
    "detailed_analyze.py": "scripts/utils",
    "broad_probe.py": "scripts/utils",
    "diagnose_import.py": "scripts/utils",
    "validation_probe.py": "scripts/utils",
    
    # Utils - Fix/Apply
    "fix_*.py": "scripts/utils",
    "apply_*.py": "scripts/utils",
    "force_*.py": "scripts/utils",
    "populate_*.py": "scripts/utils",
    "deduplicate_*.py": "scripts/utils",
    "cleanup_*.py": "scripts/utils",
    "run_*.py": "scripts/utils",
    "test_*.py": "scripts/utils",
    "bq_*.py": "scripts/utils",
    
    # Backup
    "main_git.py": "scripts/backup",
    
    # Temporary/Log files
    "*.txt": "scripts/backup",  # probe_log.txt, test_results.txt, final_probe.txt
    "*.csv": "scripts/backup",  # region_summary.csv
}

def move_files():
    """Move files according to mappings"""
    moved = []
    skipped = []
    errors = []
    
    for pattern, dest_folder in FILE_MAPPINGS.items():
        dest_path = BASE_DIR / dest_folder
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Handle wildcard patterns
        if "*" in pattern:
            import glob
            files = glob.glob(str(BASE_DIR / pattern))
        else:
            files = [str(BASE_DIR / pattern)] if (BASE_DIR / pattern).exists() else []
        
        for file_path in files:
            src = Path(file_path)
            if not src.exists() or src.is_dir():
                continue
                
            # Skip if already in destination
            if str(dest_path) in str(src.parent):
                skipped.append(str(src))
                continue
            
            try:
                dest_file = dest_path / src.name
                # Handle name conflicts
                if dest_file.exists():
                    counter = 1
                    while dest_file.exists():
                        stem = src.stem
                        suffix = src.suffix
                        dest_file = dest_path / f"{stem}_{counter}{suffix}"
                        counter += 1
                
                shutil.move(str(src), str(dest_file))
                moved.append((str(src), str(dest_file)))
                print(f"[OK] Moved: {src.name} -> {dest_file}")
            except Exception as e:
                errors.append((str(src), str(e)))
                print(f"[ERROR] Error moving {src.name}: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Moved: {len(moved)} files")
    print(f"Skipped: {len(skipped)} files")
    print(f"Errors: {len(errors)} files")
    
    if errors:
        print("\nErrors:")
        for src, error in errors:
            print(f"  {src}: {error}")

if __name__ == "__main__":
    print("Organizing backend files...")
    move_files()
    print("\nDone! Files have been organized.")
