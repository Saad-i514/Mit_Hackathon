"""
Execute Supabase migration using Supabase Management API
This script uses the Supabase client to execute SQL statements
"""
import os
import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def parse_sql_statements(sql_content: str) -> list[str]:
    """
    Parse SQL file into individual statements
    
    Args:
        sql_content: Raw SQL file content
        
    Returns:
        List of SQL statements
    """
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Skip single-line comments
        if stripped.startswith('--'):
            continue
        
        # Add line to current statement
        current_statement.append(line)
        
        # Check if statement is complete (ends with semicolon)
        if stripped.endswith(';'):
            statement = '\n'.join(current_statement).strip()
            if statement and not statement.startswith('--'):
                statements.append(statement)
            current_statement = []
    
    return statements


async def execute_via_supabase_client():
    """Execute migration using Supabase Python client"""
    print("\n" + "="*80)
    print("AI SCIENTIST PLATFORM - SUPABASE CLIENT MIGRATION")
    print("="*80 + "\n")
    
    try:
        from supabase import create_client, Client
    except ImportError:
        print("Installing supabase...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
        from supabase import create_client, Client
    
    print(f"Connecting to Supabase...")
    print(f"  URL: {SUPABASE_URL}\n")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print("✓ Connected to Supabase\n")
        
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
        print(f"Found {len(statements)} SQL statements to execute\n")
        
        # Execute statements using RPC
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for idx, statement in enumerate(statements, 1):
            # Get first line for display
            first_line = statement.split('\n')[0][:70]
            print(f"[{idx}/{len(statements)}] {first_line}...")
            
            try:
                # Use the postgrest client to execute SQL
                # Note: This requires a custom RPC function in Supabase
                result = supabase.rpc('exec_sql', {'query': statement}).execute()
                print(f"  ✓ Success")
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg.lower():
                    print(f"  ⚠ Already exists (skipping)")
                    skip_count += 1
                elif 'function exec_sql' in error_msg.lower():
                    print(f"  ⚠ RPC function not available")
                    print(f"     This requires manual execution")
                    skip_count += 1
                else:
                    print(f"  ✗ Error: {error_msg[:100]}")
                    error_count += 1
        
        print(f"\n{'='*80}")
        print(f"Execution Summary:")
        print(f"  ✓ Success: {success_count}")
        print(f"  ⚠ Skipped: {skip_count}")
        print(f"  ✗ Errors: {error_count}")
        print(f"{'='*80}\n")
        
        if skip_count > 0:
            print("⚠ Some statements require manual execution.")
            print("   The Supabase Python client doesn't support direct SQL execution.")
            print("   Please use the SQL Editor in Supabase Dashboard.\n")
            return False
        
        return error_count == 0
        
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False


def execute_via_sql_editor():
    """Provide instructions for manual execution"""
    print("\n" + "="*80)
    print("MANUAL EXECUTION REQUIRED")
    print("="*80 + "\n")
    
    print("The Supabase Python client and direct PostgreSQL connections")
    print("don't support executing DDL statements programmatically.\n")
    
    print("Please execute the migration manually using these steps:\n")
    
    print("1. Open Supabase SQL Editor:")
    print("   https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql\n")
    
    print("2. Copy the migration file:")
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    print(f"   File: {migration_file}\n")
    
    print("3. Paste the entire contents into the SQL Editor\n")
    
    print("4. Click 'Run' to execute\n")
    
    print("5. Verify the following tables were created:")
    print("   - plan_versions")
    print("   - plan_annotations")
    print("   - lab_equipment")
    print("   - clinical_trial_results")
    print("   - protocol_matches\n")
    
    print("6. Verify Realtime is enabled on:")
    print("   - plan_annotations")
    print("   - scientist_reviews")
    print("   - experiment_plans\n")
    
    return False


async def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION - AUTOMATED EXECUTION")
    print("="*80 + "\n")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("✗ Missing Supabase credentials in .env file")
        return
    
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Service Key: {SUPABASE_SERVICE_KEY[:20]}...\n")
    
    # Try Supabase client
    print("Attempting execution via Supabase client...\n")
    success = await execute_via_supabase_client()
    
    if not success:
        # Provide manual instructions
        execute_via_sql_editor()
    else:
        print("\n" + "="*80)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
        print("Next steps:")
        print("1. Verify tables in Supabase Dashboard")
        print("2. Realtime has been enabled on required tables")
        print("3. Continue with Phase 5 implementation\n")


if __name__ == "__main__":
    asyncio.run(main())
