"""
Script to run database migrations and enable Realtime on Supabase
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def get_supabase_client() -> Client:
    """Create Supabase client with service role key"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def run_migration(client: Client, migration_file: str):
    """
    Run a SQL migration file
    
    Args:
        client: Supabase client
        migration_file: Path to migration SQL file
    """
    print(f"\n{'='*80}")
    print(f"Running migration: {migration_file}")
    print(f"{'='*80}\n")
    
    # Read migration file
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Split by statement (simple approach - split by semicolon followed by newline)
    statements = [s.strip() for s in sql_content.split(';\n') if s.strip() and not s.strip().startswith('--')]
    
    print(f"Found {len(statements)} SQL statements to execute\n")
    
    # Execute each statement
    for idx, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if not statement or statement.startswith('--'):
            continue
        
        # Clean up the statement
        clean_statement = statement.strip()
        if not clean_statement:
            continue
        
        # Add semicolon back if not present
        if not clean_statement.endswith(';'):
            clean_statement += ';'
        
        # Get first line for logging
        first_line = clean_statement.split('\n')[0][:80]
        print(f"[{idx}/{len(statements)}] Executing: {first_line}...")
        
        try:
            # Execute via RPC call to execute raw SQL
            result = client.rpc('exec_sql', {'sql': clean_statement}).execute()
            print(f"  ✓ Success")
        except Exception as e:
            error_msg = str(e)
            # Check if it's a "already exists" error (which we can ignore)
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"  ⚠ Already exists (skipping)")
            else:
                print(f"  ✗ Error: {error_msg}")
                # Don't stop on error, continue with next statement
    
    print(f"\n{'='*80}")
    print(f"Migration completed: {migration_file}")
    print(f"{'='*80}\n")


def enable_realtime_on_table(client: Client, table_name: str):
    """
    Enable Realtime on a table
    
    Args:
        client: Supabase client
        table_name: Name of the table
    """
    print(f"\nEnabling Realtime on table: {table_name}")
    
    try:
        # Enable Realtime via SQL
        sql = f"""
        ALTER PUBLICATION supabase_realtime ADD TABLE {table_name};
        """
        result = client.rpc('exec_sql', {'sql': sql}).execute()
        print(f"  ✓ Realtime enabled on {table_name}")
    except Exception as e:
        error_msg = str(e)
        if 'already' in error_msg.lower() or 'duplicate' in error_msg.lower():
            print(f"  ⚠ Realtime already enabled on {table_name}")
        else:
            print(f"  ✗ Error enabling Realtime on {table_name}: {error_msg}")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("AI Scientist Platform - Database Migration Script")
    print("="*80 + "\n")
    
    # Create Supabase client
    print("Connecting to Supabase...")
    client = get_supabase_client()
    print("✓ Connected to Supabase\n")
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    # Run migration 003 (advanced features)
    migration_file = migrations_dir / "003_advanced_features_schema.sql"
    
    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return
    
    # Note: Supabase doesn't have a direct RPC for executing arbitrary SQL
    # We need to execute statements individually or use the Supabase SQL editor
    print("⚠ Note: Supabase requires migrations to be run via the SQL Editor in the Dashboard")
    print("   or by executing statements individually via the REST API.\n")
    
    print("Reading migration file...")
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    print(f"\n{'='*80}")
    print("Migration SQL Content:")
    print(f"{'='*80}\n")
    print(sql_content[:500] + "...\n")
    
    print(f"{'='*80}")
    print("To run this migration:")
    print(f"{'='*80}\n")
    print("1. Go to: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql")
    print("2. Copy the contents of: backend/migrations/003_advanced_features_schema.sql")
    print("3. Paste into the SQL Editor")
    print("4. Click 'Run' to execute\n")
    
    print("Alternatively, I'll try to execute via the PostgREST API...\n")
    
    # Try to execute via direct SQL
    try:
        # Split into individual statements
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        print(f"Found {len(statements)} statements to execute\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for idx, statement in enumerate(statements, 1):
            if not statement or len(statement) < 10:
                continue
            
            # Get first line for logging
            first_line = statement.split('\n')[0][:80]
            print(f"[{idx}/{len(statements)}] {first_line}...")
            
            try:
                # Try to execute via query
                # Note: This may not work for all DDL statements
                result = client.postgrest.rpc('query', {'query': statement + ';'}).execute()
                print(f"  ✓ Success")
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                    print(f"  ⚠ Already exists (skipping)")
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
        
    except Exception as e:
        print(f"✗ Error executing migration: {e}\n")
        print("Please run the migration manually via the Supabase Dashboard SQL Editor.\n")
    
    # Enable Realtime on tables
    print("\n" + "="*80)
    print("Enabling Realtime on tables")
    print("="*80 + "\n")
    
    tables_to_enable = [
        "plan_annotations",
        "scientist_reviews",
        "experiment_plans"
    ]
    
    print("⚠ Note: Realtime must be enabled via the Supabase Dashboard:\n")
    print("1. Go to: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/database/publications")
    print("2. Click on 'supabase_realtime' publication")
    print("3. Add the following tables:")
    for table in tables_to_enable:
        print(f"   - {table}")
    print("\nOr use the Table Editor:")
    print("1. Go to: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/editor")
    print("2. For each table, click the table name → 'Enable Realtime'")
    print("3. Select INSERT, UPDATE events\n")
    
    print("="*80)
    print("Migration script completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
