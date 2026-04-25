#!/bin/bash
"""
Database Setup Script
Sets up the AI Scientist Platform database with all required extensions and functions
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
check_env_vars() {
    log_info "Checking environment variables..."
    
    if [ -z "$SUPABASE_URL" ]; then
        log_error "SUPABASE_URL environment variable is not set"
        exit 1
    fi
    
    if [ -z "$SUPABASE_SERVICE_KEY" ]; then
        log_error "SUPABASE_SERVICE_KEY environment variable is not set"
        exit 1
    fi
    
    log_success "Environment variables are set"
}

# Check if Python dependencies are installed
check_dependencies() {
    log_info "Checking Python dependencies..."
    
    if ! python3 -c "import supabase" 2>/dev/null; then
        log_error "Supabase Python client not installed. Run: pip install supabase"
        exit 1
    fi
    
    if ! python3 -c "import dotenv" 2>/dev/null; then
        log_error "python-dotenv not installed. Run: pip install python-dotenv"
        exit 1
    fi
    
    log_success "Dependencies are installed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$(dirname "$0")"  # Change to script directory
    
    if python3 migrate.py migrate; then
        log_success "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Check migration status
check_status() {
    log_info "Checking migration status..."
    
    cd "$(dirname "$0")"  # Change to script directory
    python3 migrate.py status
}

# Setup database with sample data
setup_sample_data() {
    log_info "Setting up sample data..."
    
    cd "$(dirname "$0")"  # Change to script directory
    
    # Check if sample data migration exists
    if [ -f "../migrations/002_sample_data.sql" ]; then
        log_info "Sample data migration found, it will be applied with regular migrations"
    else
        log_warning "Sample data migration not found, skipping sample data setup"
    fi
}

# Verify database setup
verify_setup() {
    log_info "Verifying database setup..."
    
    cd "$(dirname "$0")"  # Change to script directory
    
    # Create a simple verification script
    cat > verify_db.py << 'EOF'
import os
import sys
from supabase import create_client

def verify_database():
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        client = create_client(supabase_url, supabase_key)
        
        # Test basic connection
        result = client.table('_migrations').select('*').limit(1).execute()
        print("✓ Database connection successful")
        
        # Check if required tables exist
        tables_to_check = ['users', 'hypotheses', 'experiment_plans', 'reviews', 'feedback_embeddings']
        
        for table in tables_to_check:
            try:
                result = client.table(table).select('*').limit(1).execute()
                print(f"✓ Table '{table}' exists and is accessible")
            except Exception as e:
                print(f"✗ Table '{table}' check failed: {e}")
                return False
        
        # Check if required functions exist
        try:
            result = client.rpc('match_feedback_embeddings', {
                'query_embedding': [0.0] * 1536,
                'similarity_threshold': 0.5,
                'match_count': 1
            }).execute()
            print("✓ Function 'match_feedback_embeddings' exists and is callable")
        except Exception as e:
            print(f"✗ Function 'match_feedback_embeddings' check failed: {e}")
            return False
        
        try:
            result = client.rpc('get_average_plan_rating', {
                'plan_id_param': 'test-id'
            }).execute()
            print("✓ Function 'get_average_plan_rating' exists and is callable")
        except Exception as e:
            print(f"✗ Function 'get_average_plan_rating' check failed: {e}")
            return False
        
        print("\n✓ Database setup verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
EOF
    
    if python3 verify_db.py; then
        log_success "Database setup verification passed"
        rm verify_db.py
    else
        log_error "Database setup verification failed"
        rm verify_db.py
        exit 1
    fi
}

# Main setup function
main() {
    log_info "Starting AI Scientist Platform database setup..."
    echo
    
    # Check prerequisites
    check_env_vars
    check_dependencies
    echo
    
    # Run setup steps
    run_migrations
    echo
    
    setup_sample_data
    echo
    
    verify_setup
    echo
    
    log_success "Database setup completed successfully!"
    echo
    log_info "You can now start the AI Scientist Platform backend server"
    log_info "Run: python -m uvicorn app.main:app --reload"
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "migrate")
        check_env_vars
        check_dependencies
        run_migrations
        ;;
    "status")
        check_env_vars
        check_dependencies
        check_status
        ;;
    "verify")
        check_env_vars
        check_dependencies
        verify_setup
        ;;
    "help"|"-h"|"--help")
        echo "AI Scientist Platform Database Setup"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  setup     Run complete database setup (default)"
        echo "  migrate   Run migrations only"
        echo "  status    Check migration status"
        echo "  verify    Verify database setup"
        echo "  help      Show this help message"
        echo
        echo "Environment variables required:"
        echo "  SUPABASE_URL          - Your Supabase project URL"
        echo "  SUPABASE_SERVICE_KEY  - Your Supabase service role key"
        echo
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac