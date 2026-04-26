"""
Seeds a minimal test plan directly into Supabase for the test user,
so plan-specific endpoint tests can run without a full pipeline execution.
"""
import os, sys, json, uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TEST_USER_ID = "1ce1244b-e0c7-4548-b09a-91fe7de24b01"  # created earlier

PLAN_ID = str(uuid.uuid4())

SAMPLE_PLAN = {
    "hypothesis": "CRISPR-Cas9 knockout of BRCA1 in MCF-7 cells will increase sensitivity to PARP inhibitor olaparib",
    "domain": "Molecular Biology",
    "novelty_classification": "not_found",
    "protocol": {
        "steps": [
            {
                "step_number": 1,
                "description": "Culture MCF-7 cells in DMEM + 10% FBS at 37°C, 5% CO2",
                "duration": "2 days",
                "critical_parameters": {"temperature": "37°C", "CO2": "5%"},
                "source": {"title": "Standard cell culture protocol", "doi": None, "url": None}
            },
            {
                "step_number": 2,
                "description": "Transfect cells with BRCA1-targeting sgRNA + Cas9 plasmid",
                "duration": "1 day",
                "critical_parameters": {"reagent": "Lipofectamine 3000", "ratio": "1:2"},
                "source": {"title": "Lipofectamine 3000 protocol", "doi": None, "url": None}
            }
        ],
        "references": [{"title": "CRISPR-Cas9 genome editing", "doi": "10.1126/science.1225829", "url": None, "year": 2012}],
        "safety_considerations": ["BSL-2 containment required", "Wear PPE when handling lentiviral vectors"],
        "troubleshooting": [{"issue": "Low transfection efficiency", "solution": "Optimize lipid:DNA ratio"}]
    },
    "materials": {
        "items": [
            {
                "name": "MCF-7 cells",
                "catalog_number": "HTB-22",
                "supplier": "ATCC",
                "quantity": 1,
                "unit": "vial",
                "unit_price": 450.0,
                "total_price": 450.0,
                "product_url": "https://www.atcc.org/products/htb-22",
                "verification_status": "verified",
                "alternatives": []
            },
            {
                "name": "Olaparib",
                "catalog_number": "S1060",
                "supplier": "Selleckchem",
                "quantity": 10,
                "unit": "mg",
                "unit_price": 85.0,
                "total_price": 850.0,
                "product_url": None,
                "verification_status": "verified",
                "alternatives": ["Niraparib", "Rucaparib"]
            }
        ],
        "total_budget": 1300.0,
        "currency": "USD"
    },
    "timeline": {
        "phases": [
            {
                "phase_number": 1,
                "name": "Cell preparation",
                "duration_days": 7,
                "start_date": "2026-05-01",
                "end_date": "2026-05-07",
                "dependencies": [],
                "description": "Culture and expand MCF-7 cells"
            },
            {
                "phase_number": 2,
                "name": "CRISPR transfection",
                "duration_days": 14,
                "start_date": "2026-05-08",
                "end_date": "2026-05-21",
                "dependencies": [1],
                "description": "Transfect and select BRCA1 knockout clones"
            }
        ],
        "total_duration_days": 21,
        "gantt_data": {}
    },
    "validation_criteria": {
        "success_criteria": [
            {
                "description": "≥80% reduction in BRCA1 protein by Western blot",
                "threshold": "≥80%",
                "measurement_technique": "Western blot",
                "expected_range": "0-20% residual expression"
            }
        ],
        "failure_criteria": [
            {
                "description": "<50% reduction in BRCA1 protein",
                "threshold": "<50%",
                "measurement_technique": "Western blot"
            }
        ],
        "validation_methods": ["Western blot", "Sanger sequencing", "Cell viability assay"]
    },
    "metadata": {
        "generated_at": datetime.utcnow().isoformat(),
        "model_version": "gpt-4o",
        "few_shot_examples_used": 2,
        "requires_expert_review": ["BSL-2 safety review"],
        "average_rating": None
    }
}

def seed():
    db = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Insert hypothesis
    try:
        db.table("hypotheses").insert({
            "id": PLAN_ID,
            "user_id": TEST_USER_ID,
            "hypothesis_text": SAMPLE_PLAN["hypothesis"],
            "domain": SAMPLE_PLAN["domain"],
            "validation_status": "valid",
        }).execute()
        print(f"✅ Inserted hypothesis {PLAN_ID}")
    except Exception as e:
        print(f"⚠  Hypothesis insert: {e}")

    # Insert plan
    result = db.table("experiment_plans").insert({
        "id": PLAN_ID,
        "hypothesis_id": PLAN_ID,
        "user_id": TEST_USER_ID,
        "plan_data": SAMPLE_PLAN,
        "novelty_classification": "not_found",
        "model_version": "gpt-4o",
        "few_shot_examples_used": 2,
        "requires_expert_review": ["BSL-2 safety review"],
        "status": "draft",
    }).execute()

    if result.data:
        print(f"✅ Inserted plan {PLAN_ID}")
    else:
        print(f"❌ Failed to insert plan: {result}")
        return

    # Insert a version
    db.table("plan_versions").insert({
        "experiment_id": PLAN_ID,
        "version_number": 1,
        "plan_snapshot": SAMPLE_PLAN,
        "change_summary": "Initial generation",
        "triggered_by": "initial_generation"
    }).execute()
    print(f"✅ Inserted version 1 for plan {PLAN_ID}")

    print(f"\nPLAN_ID={PLAN_ID}")
    # Write plan_id to a temp file so the test script can pick it up
    with open("tests/.test_plan_id", "w") as f:
        f.write(PLAN_ID)

if __name__ == "__main__":
    seed()
