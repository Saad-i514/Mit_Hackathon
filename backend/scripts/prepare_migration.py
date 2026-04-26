"""
Prepare migration SQL for easy copy-paste to Supabase Dashboard
"""
import os
from pathlib import Path

def main():
    """Generate migration instructions"""
    print("\n" + "="*80)
    print("AI SCIENTIST PLATFORM - MIGRATION PREPARATION")
    print("="*80 + "\n")
    
    # Read migration file
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_file = migrations_dir / "003_advanced_features_schema.sql"
    
    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return
    
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    # Output file path
    output_file = migrations_dir / "APPLY_IN_SUPABASE.sql"
    
    # Create a clean version for Supabase
    with open(output_file, 'w') as f:
        f.write("-- ============================================================================\n")
        f.write("-- AI Scientist Platform - Advanced Features Migration\n")
        f.write("-- INSTRUCTIONS: Copy this entire file and paste into Supabase SQL Editor\n")
        f.write("-- URL: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql\n")
        f.write("-- ============================================================================\n\n")
        f.write(sql_content)
        f.write("\n\n-- ============================================================================\n")
        f.write("-- ENABLE REALTIME ON TABLES\n")
        f.write("-- ============================================================================\n\n")
        f.write("-- Enable Realtime for collaborative features\n")
        f.write("ALTER PUBLICATION supabase_realtime ADD TABLE plan_annotations;\n")
        f.write("ALTER PUBLICATION supabase_realtime ADD TABLE scientist_reviews;\n")
        f.write("ALTER PUBLICATION supabase_realtime ADD TABLE experiment_plans;\n\n")
        f.write("-- ============================================================================\n")
        f.write("-- MIGRATION COMPLETE\n")
        f.write("-- ============================================================================\n")
    
    print(f"✓ Created migration file: {output_file}\n")
    print("="*80)
    print("NEXT STEPS:")
    print("="*80 + "\n")
    print("1. Open Supabase SQL Editor:")
    print("   https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql\n")
    print(f"2. Open the file: {output_file}")
    print("   (or copy from below)\n")
    print("3. Copy ALL contents and paste into SQL Editor\n")
    print("4. Click 'Run' button\n")
    print("5. Verify tables created in Table Editor:\n")
    print("   - plan_versions")
    print("   - plan_annotations")
    print("   - lab_equipment")
    print("   - clinical_trial_results")
    print("   - protocol_matches\n")
    print("="*80)
    print("SQL CONTENT (copy from here if needed):")
    print("="*80 + "\n")
    
    # Print the content
    with open(output_file, 'r') as f:
        print(f.read())
    
    print("\n" + "="*80)
    print("✓ Migration preparation complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
