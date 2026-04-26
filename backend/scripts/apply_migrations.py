"""
Direct migration script using Supabase client
Executes SQL statements directly via the database connection
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio
import asyncpg

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Extract database connection details from Supabase URL
# Format: https://PROJECT_REF.supabase.co
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0] if SUPABASE_URL else None
DB_HOST = f"db.{PROJECT_REF}.supabase.co" if PROJECT_REF else None
DB_NAME = "postgres"
DB_USER = "postgres"
# Note: DB password needs to be obtained from Supabase dashboard


async def execute_migration_async():
    """Execute migration using asyncpg for direct PostgreSQL access"""
    print("\n" + "="*80)
    print("AI Scientist Platform - Direct Migration Execution")
    print("="*80 + "\n")
    
    # Read migration file
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "003_advanced_features_schema.sql"
    
    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return
    
    print(f"Reading migration file: {migration_file.name}")
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Split into statements
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # Skip comment-only lines
        if line.strip().startswith('--') and not current_statement:
            continue
        
        current_statement.append(line)
        
        # Check if line ends with semicolon (end of statement)
        if line.strip().endswith(';'):
            statement = '\n'.join(current_statement).strip()
            if statement and not statement.startswith('--'):
                statements.append(statement)
            current_statement = []
    
    print(f"Found {len(statements)} SQL statements\n")
    
    # Try to connect via Supabase client
    print("Attempting to execute via Supabase client...")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for idx, statement in enumerate(statements, 1):
        # Get first line for display
        first_line = statement.split('\n')[0][:80]
        print(f"\n[{idx}/{len(statements)}] {first_line}...")
        
        try:
            # Execute via Supabase query
            # Note: Supabase Python client doesn't directly support raw SQL execution
            # We need to use the REST API or PostgREST
            
            # For now, just print the statement
            print(f"  Statement length: {len(statement)} characters")
            
            # Check if it's a CREATE TABLE statement
            if 'CREATE TABLE' in statement.upper():
                table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                print(f"  → Creating table: {table_name}")
            elif 'CREATE INDEX' in statement.upper():
                print(f"  → Creating index")
            elif 'CREATE POLICY' in statement.upper():
                print(f"  → Creating RLS policy")
            elif 'ALTER TABLE' in statement.upper():
                print(f"  → Altering table")
            
            # Mark as pending manual execution
            print(f"  ⚠ Requires manual execution via Supabase Dashboard")
            skip_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            error_count += 1
    
    print(f"\n{'='*80}")
    print(f"Execution Summary:")
    print(f"  ✓ Success: {success_count}")
    print(f"  ⚠ Pending: {skip_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"{'='*80}\n")
    
    # Provide instructions
    print("\n" + "="*80)
    print("MANUAL MIGRATION REQUIRED")
    print("="*80 + "\n")
    
    print("Supabase Python client doesn't support direct SQL execution.")
    print("Please run the migration manually:\n")
    
    print("Option 1: Via Supabase Dashboard (RECOMMENDED)")
    print("-" * 80)
    print(f"1. Go to: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}/sql")
    print(f"2. Open file: {migration_file}")
    print("3. Copy all contents")
    print("4. Paste into SQL Editor")
    print("5. Click 'Run'\n")
    
    print("Option 2: Via psql command line")
    print("-" * 80)
    print(f"psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} -f {migration_file}\n")
    
    print("Option 3: Copy SQL to clipboard")
    print("-" * 80)
    print("The migration SQL is ready to copy:\n")
    print(sql_content[:500] + "...\n")
    
    # Enable Realtime instructions
    print("\n" + "="*80)
    print("ENABLE REALTIME ON TABLES")
    print("="*80 + "\n")
    
    print("After running the migration, enable Realtime on these tables:\n")
    print("1. Go to: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/database/publications")
    print("2. Click 'supabase_realtime' publication")
    print("3. Add these tables:")
    print("   - plan_annotations")
    print("   - scientist_reviews")
    print("   - experiment_plans\n")
    
    print("Or via SQL Editor:")
    print("-" * 80)
    print("ALTER PUBLICATION supabase_realtime ADD TABLE plan_annotations;")
    print("ALTER PUBLICATION supabase_realtime ADD TABLE scientist_reviews;")
    print("ALTER PUBLICATION supabase_realtime ADD TABLE experiment_plans;\n")
    
    print("="*80)
    print("Script completed!")
    print("="*80 + "\n")


def main():
    """Main entry point"""
    try:
        asyncio.run(execute_migration_async())
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
