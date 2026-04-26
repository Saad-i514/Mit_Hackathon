"""
Execute Supabase migration - tries multiple methods
"""
import os
import sys
from pathlib import Path
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")


def try_psql_execution():
    """Try to execute migration using psql command-line tool"""
    print("\n" + "="*80)
    print("ATTEMPTING PSQL EXECUTION")
    print("="*80 + "\n")
    
    # Check if psql is available
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("✗ psql not found in PATH")
            return False
        print(f"✓ Found: {result.stdout.strip()}\n")
    except FileNotFoundError:
        print("✗ psql not found in PATH")
        print("   Install PostgreSQL client tools to use this method\n")
        return False
    
    if not SUPABASE_DB_PASSWORD:
        print("✗ SUPABASE_DB_PASSWORD not set in .env file")
        return False
    
    # Extract connection details
    project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
    db_host = f"db.{project_ref}.supabase.co"
    db_name = "postgres"
    db_user = "postgres"
    db_port = "5432"
    
    # Read migration file
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    
    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return False
    
    print(f"Executing migration via psql...")
    print(f"  Host: {db_host}")
    print(f"  Database: {db_name}")
    print(f"  User: {db_user}\n")
    
    # Set password in environment
    env = os.environ.copy()
    env['PGPASSWORD'] = SUPABASE_DB_PASSWORD
    
    # Execute psql
    try:
        with open(migration_file, 'r') as f:
            result = subprocess.run(
                [
                    'psql',
                    f'postgresql://{db_user}@{db_host}:{db_port}/{db_name}?sslmode=require'
                ],
                stdin=f,
                capture_output=True,
                text=True,
                env=env
            )
        
        if result.returncode == 0:
            print("✓ Migration executed successfully\n")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True
        else:
            print(f"✗ psql execution failed")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def provide_manual_instructions():
    """Provide clear manual execution instructions"""
    print("\n" + "="*80)
    print("MANUAL EXECUTION INSTRUCTIONS")
    print("="*80 + "\n")
    
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    
    print("Since automated execution is not available, please follow these steps:\n")
    
    print("STEP 1: Open Supabase SQL Editor")
    print("  URL: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql\n")
    
    print("STEP 2: Open the migration file")
    print(f"  File: {migration_file.absolute()}\n")
    
    print("STEP 3: Copy the entire file contents\n")
    
    print("STEP 4: Paste into the SQL Editor and click 'Run'\n")
    
    print("STEP 5: Verify tables were created")
    print("  Go to: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/editor")
    print("  Check for these new tables:")
    print("    ✓ plan_versions")
    print("    ✓ plan_annotations")
    print("    ✓ lab_equipment")
    print("    ✓ clinical_trial_results")
    print("    ✓ protocol_matches\n")
    
    print("STEP 6: Verify Realtime is enabled")
    print("  The migration script automatically enables Realtime on:")
    print("    ✓ plan_annotations")
    print("    ✓ scientist_reviews")
    print("    ✓ experiment_plans\n")
    
    print("="*80 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION EXECUTOR")
    print("="*80 + "\n")
    
    if not SUPABASE_URL:
        print("✗ SUPABASE_URL not set in .env file")
        return
    
    print(f"Supabase URL: {SUPABASE_URL}\n")
    
    # Try psql first
    success = try_psql_execution()
    
    if success:
        print("\n" + "="*80)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
        print("Next steps:")
        print("1. Verify tables in Supabase Dashboard")
        print("2. Continue with Phase 5 implementation\n")
    else:
        # Provide manual instructions
        provide_manual_instructions()
        
        print("After completing the manual steps, you can continue with:")
        print("  Phase 5: Backend Pipeline Integration\n")


if __name__ == "__main__":
    main()
