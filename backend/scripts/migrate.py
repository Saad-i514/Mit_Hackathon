#!/usr/bin/env python3
"""
Database Migration Runner
Applies database migrations to Supabase PostgreSQL
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Database migration runner for Supabase"""
    
    def __init__(self):
        """Initialize migration runner"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_service_key)
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        
        logger.info(f"Migration runner initialized")
        logger.info(f"Migrations directory: {self.migrations_dir}")
    
    def get_migration_files(self) -> List[Path]:
        """Get all migration files in order"""
        if not self.migrations_dir.exists():
            logger.error(f"Migrations directory not found: {self.migrations_dir}")
            return []
        
        # Get all .sql files that start with numbers
        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            if file_path.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                migration_files.append(file_path)
        
        # Sort by filename to ensure correct order
        migration_files.sort(key=lambda x: x.name)
        
        logger.info(f"Found {len(migration_files)} migration files")
        for file_path in migration_files:
            logger.info(f"  - {file_path.name}")
        
        return migration_files
    
    def create_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        sql = """
        CREATE TABLE IF NOT EXISTS _migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            checksum VARCHAR(64)
        );
        """
        
        try:
            result = self.client.rpc('exec_sql', {'sql': sql}).execute()
            logger.info("Migrations table created/verified")
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            result = self.client.table('_migrations').select('filename').execute()
            applied = [row['filename'] for row in result.data]
            logger.info(f"Found {len(applied)} applied migrations")
            return applied
        except Exception as e:
            logger.warning(f"Could not fetch applied migrations (table may not exist): {e}")
            return []
    
    def calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of migration content"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def execute_migration(self, file_path: Path) -> bool:
        """Execute a single migration file"""
        try:
            # Read migration content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Migration file {file_path.name} is empty, skipping")
                return True
            
            # Calculate checksum
            checksum = self.calculate_checksum(content)
            
            logger.info(f"Executing migration: {file_path.name}")
            
            # Split content by semicolons and execute each statement
            statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        # Use RPC to execute raw SQL
                        result = self.client.rpc('exec_sql', {'sql': statement}).execute()
                        logger.debug(f"  Statement {i+1}/{len(statements)} executed successfully")
                    except Exception as e:
                        logger.error(f"  Failed to execute statement {i+1}: {statement[:100]}...")
                        logger.error(f"  Error: {e}")
                        raise
            
            # Record migration as applied
            self.client.table('_migrations').insert({
                'filename': file_path.name,
                'checksum': checksum
            }).execute()
            
            logger.info(f"Migration {file_path.name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute migration {file_path.name}: {e}")
            return False
    
    def run_migrations(self, target_migration: str = None) -> bool:
        """Run all pending migrations"""
        try:
            # Create migrations table
            self.create_migrations_table()
            
            # Get migration files and applied migrations
            migration_files = self.get_migration_files()
            applied_migrations = self.get_applied_migrations()
            
            if not migration_files:
                logger.info("No migration files found")
                return True
            
            # Filter to pending migrations
            pending_migrations = []
            for file_path in migration_files:
                if file_path.name not in applied_migrations:
                    pending_migrations.append(file_path)
                    
                # Stop at target migration if specified
                if target_migration and file_path.name == target_migration:
                    break
            
            if not pending_migrations:
                logger.info("No pending migrations")
                return True
            
            logger.info(f"Running {len(pending_migrations)} pending migrations")
            
            # Execute pending migrations
            for file_path in pending_migrations:
                if not self.execute_migration(file_path):
                    logger.error(f"Migration failed: {file_path.name}")
                    return False
            
            logger.info("All migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration run failed: {e}")
            return False
    
    def rollback_migration(self, migration_name: str) -> bool:
        """Rollback a specific migration"""
        rollback_file = self.migrations_dir / f"rollback_{migration_name}"
        
        if not rollback_file.exists():
            logger.error(f"Rollback file not found: {rollback_file}")
            return False
        
        try:
            logger.info(f"Rolling back migration: {migration_name}")
            
            # Execute rollback
            if self.execute_migration(rollback_file):
                # Remove from migrations table
                self.client.table('_migrations').delete().eq('filename', migration_name).execute()
                logger.info(f"Rollback completed: {migration_name}")
                return True
            else:
                logger.error(f"Rollback failed: {migration_name}")
                return False
                
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False
    
    def status(self):
        """Show migration status"""
        try:
            migration_files = self.get_migration_files()
            applied_migrations = self.get_applied_migrations()
            
            print("\nMigration Status:")
            print("=" * 50)
            
            for file_path in migration_files:
                status = "✓ Applied" if file_path.name in applied_migrations else "✗ Pending"
                print(f"{file_path.name:<30} {status}")
            
            print(f"\nTotal migrations: {len(migration_files)}")
            print(f"Applied: {len(applied_migrations)}")
            print(f"Pending: {len(migration_files) - len(applied_migrations)}")
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Runner")
    parser.add_argument('command', choices=['migrate', 'rollback', 'status'], 
                       help='Migration command')
    parser.add_argument('--target', help='Target migration file')
    parser.add_argument('--migration', help='Migration name for rollback')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        runner = MigrationRunner()
        
        if args.command == 'migrate':
            success = runner.run_migrations(args.target)
            sys.exit(0 if success else 1)
            
        elif args.command == 'rollback':
            if not args.migration:
                logger.error("--migration required for rollback")
                sys.exit(1)
            success = runner.rollback_migration(args.migration)
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            runner.status()
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()