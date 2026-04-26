"""
Helper script to make manual migration easier
Opens browser and copies SQL to clipboard
"""
import os
import sys
from pathlib import Path
import webbrowser

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("SUPABASE MIGRATION HELPER")
    print("="*80 + "\n")
    
    # Read migration file
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    
    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return
    
    print(f"Migration file: {migration_file}\n")
    
    # Try to copy to clipboard
    try:
        import pyperclip
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        pyperclip.copy(sql_content)
        print("✓ SQL copied to clipboard!\n")
        clipboard_success = True
    except ImportError:
        print("⚠ pyperclip not installed - cannot copy to clipboard")
        print("  Install with: pip install pyperclip\n")
        clipboard_success = False
    except Exception as e:
        print(f"⚠ Could not copy to clipboard: {e}\n")
        clipboard_success = False
    
    # Open browser
    sql_editor_url = "https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql"
    
    print("Opening Supabase SQL Editor in browser...\n")
    try:
        webbrowser.open(sql_editor_url)
        print("✓ Browser opened\n")
    except Exception as e:
        print(f"⚠ Could not open browser: {e}")
        print(f"  Please open manually: {sql_editor_url}\n")
    
    # Provide instructions
    print("="*80)
    print("NEXT STEPS")
    print("="*80 + "\n")
    
    if clipboard_success:
        print("1. The SQL Editor should now be open in your browser")
        print("2. The migration SQL is already copied to your clipboard")
        print("3. Paste (Ctrl+V) into the SQL Editor")
        print("4. Click the 'Run' button")
    else:
        print("1. The SQL Editor should now be open in your browser")
        print(f"2. Open the migration file: {migration_file}")
        print("3. Copy the entire contents")
        print("4. Paste into the SQL Editor")
        print("5. Click the 'Run' button")
    
    print("\n5. Verify these tables were created:")
    print("   - plan_versions")
    print("   - plan_annotations")
    print("   - lab_equipment")
    print("   - clinical_trial_results")
    print("   - protocol_matches")
    
    print("\n6. Verify Realtime is enabled (automatic)")
    print("   - plan_annotations")
    print("   - scientist_reviews")
    print("   - experiment_plans")
    
    print("\n" + "="*80)
    print("After completing these steps, the migration will be complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
