"""
Execute Supabase migration via direct PostgreSQL connection
This script runs the migration directly without needing the dashboard
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
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")


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


async def execute_via_postgres():
    """Execute migration via direct PostgreSQL connection"""
    print("\n" + "="*80)
    print("AI SCIENTIST PLATFORM - DIRECT POSTGRESQL MIGRATION")
    print("="*80 + "\n")
    
    # Check for asyncpg
    try:
        import asyncpg
    except ImportError:
        print("Installing asyncpg...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "asyncpg"])
        import asyncpg
    
    # Extract connection details from Supabase URL
    project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
    db_host = f"db.{project_ref}.supabase.co"
    db_name = "postgres"
    db_user = "postgres"
    
    print(f"Connection details:")
    print(f"  Host: {db_host}")
    print(f"  Database: {db_name}")
    print(f"  User: {db_user}\n")
    
    # Check if password is in environment
    if not SUPABASE_DB_PASSWORD:
        print("✗ SUPABASE_DB_PASSWORD not set in .env file")
        print("\nTo enable direct execution:")
        print("1. Get your database password from Supabase Dashboard")
        print("   URL: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/settings/database")
        print("2. Add to backend/.env file: SUPABASE_DB_PASSWORD=your_password")
        print("3. Run this script again\n")
        return False
    
    try:
        print("Connecting to PostgreSQL...")
        conn = await asyncpg.connect(
            host=db_host,
            port=5432,
            database=db_name,
            user=db_user,
            password=SUPABASE_DB_PASSWORD,
            ssl='require'
        )
        
        print("✓ Connected to PostgreSQL\n")
        
        # Read migration file
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
        
        if not migration_file.exists():
            print(f"✗ Migration file not found: {migration_file}")
            await conn.close()
            return False
        
        print(f"Reading migration file: {migration_file.name}")
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Parse statements
        statements = parse_sql_statements(sql_content)
        print(f"Found {len(statements)} SQL statements to execute\n")
        
        # Execute statements one by one
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for idx, statement in enumerate(statements, 1):
            # Get first line for display
            first_line = statement.split('\n')[0][:70]
            print(f"[{idx}/{len(statements)}] {first_line}...")
            
            try:
                await conn.execute(statement)
                print(f"  ✓ Success")
                success_count += 1
            except asyncpg.exceptions.DuplicateTableError:
                print(f"  ⚠ Table already exists (skipping)")
                skip_count += 1
            except asyncpg.exceptions.DuplicateObjectError:
                print(f"  ⚠ Object already exists (skipping)")
                skip_count += 1
            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg.lower():
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
        
        await conn.close()
        
        return error_count == 0
        
    except asyncpg.exceptions.InvalidPasswordError:
        print(f"✗ Invalid database password\n")
        print("Please check your SUPABASE_DB_PASSWORD in .env file")
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}\n")
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
    
    # Execute via direct PostgreSQL connection
    success = await execute_via_postgres()
    
    if success:
        print("\n" + "="*80)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
        print("Next steps:")
        print("1. Verify tables in Supabase Dashboard")
        print("2. Realtime has been enabled on required tables")
        print("3. Continue with Phase 5 implementation\n")
    else:
        print("\n" + "="*80)
        print("⚠ AUTOMATIC MIGRATION FAILED")
        print("="*80 + "\n")
        
        print("Please run the migration manually:")
        print("1. Open: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql")
        print("2. Copy contents of: backend/migrations/APPLY_IN_SUPABASE.sql")
        print("3. Paste and click 'Run'\n")


if __name__ == "__main__":
    asyncio.run(main())
