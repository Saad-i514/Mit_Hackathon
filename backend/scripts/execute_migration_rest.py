"""
Execute Supabase migration using REST API with proper authentication
This uses the Supabase PostgREST API to execute SQL
"""
import os
import sys
from pathlib import Path
import requests
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def parse_sql_statements(sql_content: str) -> list[str]:
    """Parse SQL file into individual statements"""
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        stripped = line.strip()
        
        if not stripped or stripped.startswith('--'):
            continue
        
        current_statement.append(line)
        
        if stripped.endswith(';'):
            statement = '\n'.join(current_statement).strip()
            if statement and not statement.startswith('--'):
                statements.append(statement)
            current_statement = []
    
    return statements


def execute_migration():
    """Execute migration using Supabase REST API"""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION - REST API EXECUTION")
    print("="*80 + "\n")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("✗ Missing Supabase credentials in .env file")
        return False
    
    print(f"Supabase URL: {SUPABASE_URL}\n")
    
    # Read migration file
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    
    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration file: {migration_file.name}")
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Parse statements
    statements = parse_sql_statements(sql_content)
    print(f"Found {len(statements)} SQL statements\n")
    
    print("="*80)
    print("IMPORTANT: Supabase REST API Limitation")
    print("="*80)
    print("\nThe Supabase REST API (PostgREST) does not support executing")
    print("arbitrary DDL statements (CREATE TABLE, ALTER TABLE, etc.) for")
    print("security reasons. This is by design.\n")
    
    print("The only way to execute migrations programmatically is:")
    print("1. Direct PostgreSQL connection (requires network access)")
    print("2. Supabase CLI (requires installation)")
    print("3. Manual execution via SQL Editor (most reliable)\n")
    
    return False


def provide_supabase_cli_instructions():
    """Provide instructions for using Supabase CLI"""
    print("="*80)
    print("OPTION 1: Use Supabase CLI (Recommended for automation)")
    print("="*80 + "\n")
    
    print("1. Install Supabase CLI:")
    print("   npm install -g supabase")
    print("   OR")
    print("   scoop install supabase\n")
    
    print("2. Link to your project:")
    print("   supabase link --project-ref kdzzyxihfxxcsnifcnpi\n")
    
    print("3. Run migration:")
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    print(f"   supabase db execute --file {migration_file}\n")


def provide_manual_instructions():
    """Provide manual execution instructions"""
    print("="*80)
    print("OPTION 2: Manual Execution (Fastest for one-time setup)")
    print("="*80 + "\n")
    
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    
    print("1. Open Supabase SQL Editor:")
    print("   https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql\n")
    
    print("2. Open migration file:")
    print(f"   {migration_file.absolute()}\n")
    
    print("3. Copy entire contents and paste into SQL Editor\n")
    
    print("4. Click 'Run' button\n")
    
    print("5. Verify tables created:")
    print("   https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/editor")
    print("   - plan_versions")
    print("   - plan_annotations")
    print("   - lab_equipment")
    print("   - clinical_trial_results")
    print("   - protocol_matches\n")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION EXECUTOR")
    print("="*80 + "\n")
    
    # Try REST API (will explain limitations)
    execute_migration()
    
    # Provide both options
    provide_supabase_cli_instructions()
    print()
    provide_manual_instructions()
    
    print("="*80)
    print("\nRecommendation: Use OPTION 2 (Manual) for quickest setup")
    print("It takes less than 1 minute and is the most reliable method.\n")


if __name__ == "__main__":
    main()
