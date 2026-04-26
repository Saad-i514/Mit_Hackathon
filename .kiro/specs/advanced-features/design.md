# Design Document — Advanced Features for AI Scientist Platform

## Overview

This document describes the technical design for implementing 12 advanced features across the AI Scientist Platform. The features extend the core pipeline (hypothesis validation → literature QC → plan generation) with richer data sources, statistical rigour, interactive visualisation, and real-time collaboration.

The design is organised by layer: Backend Services, API Contracts, Database Schema, Frontend Components, and Data Flow.

---

## 1. Backend Architecture

### 1.1 New Services

#### `backend/app/services/clinical_trials.py`
**Purpose**: Query ClinicalTrials.gov API v2 for overlapping clinical trials.

**Key Functions**:
- `extract_key_terms(hypothesis: str) -> List[str]` — Use GPT-4o to extract 3–5 key terms from hypothesis
- `check_clinical_trials(hypothesis: str) -> Dict` — Query ClinicalTrials.gov API v2 with key terms, filter by status (RECRUITING, ACTIVE_NOT_RECRUITING, NOT_YET_RECRUITING, COMPLETED)
- Returns: `{ total_found: int, studies: List[{ nct_id, title, status, phase, url }] }`

**API Endpoint**: `https://clinicaltrials.gov/api/v2/studies`
**Rate Limit**: No stated limit; no API key required
**Timeout**: 10 seconds
**Caching**: Cache results per experiment_id in `clinical_trial_results` table

---

#### `backend/app/services/safety_assessor.py`
**Purpose**: Generate risk and safety assessment using GPT-4o and PubChem GHS data.

**Key Functions**:
- `assess_safety(plan: ExperimentPlan) -> SafetyAssessment` — Call GPT-4o with plan data to determine BSL level, IACUC/IRB flags, PPE requirements, waste disposal categories
- `extract_ghs_codes(reagent_name: str) -> List[str]` — Query PubChem for GHS hazard codes (H300–H310 for acute toxicity, etc.)
- Returns: `SafetyAssessment` object with BSL level, flags, PPE list, hazardous reagents, waste categories, emergency contacts

**Output Schema**:
```python
class SafetyAssessment(BaseModel):
    bsl_level: int  # 1–4
    bsl_rationale: str
    requires_iacuc: bool
    requires_irb: bool
    requires_biosafety_committee: bool
    ppe_required: List[str]
    hazardous_reagents: List[Dict]  # {name, ghs_codes, hazard, ppe_addition, disposal}
    waste_disposal: Dict  # {biological, chemical, sharps}
    emergency_contacts: List[str]
```

---

#### `backend/app/services/grant_methods.py`
**Purpose**: Rewrite protocol as formal grant Methods section.

**Key Functions**:
- `generate_grant_methods(plan: ExperimentPlan, grant_body: str = 'NIH') -> str` — Call GPT-4o with structured prompt to rewrite protocol in past tense, third person, 400–600 words, with all reagents cited with source and catalog number
- Supported grant bodies: NIH, NSF, ERC
- Returns: Plain text Methods section

**Prompt Template**:
```
You are an experienced grant writer with a track record of NIH R01 and NSF awards.
Rewrite the following experiment plan as a formal Methods section suitable for submission to {grant_body}.

Requirements:
- Past tense, third person
- All reagents must include source and catalog number on first mention
- Statistical analysis paragraph at the end specifying test, alpha, power, software
- Include institutional approval sentence if IACUC/IRB required
- Target length: 400–600 words
- Use passive voice throughout

Output only the Methods section text — no preamble, no headers.
```

---

#### `backend/app/services/notebook_generator.py`
**Purpose**: Generate pre-filled electronic lab notebook template.

**Key Functions**:
- `generate_notebook(plan: ExperimentPlan) -> NotebookTemplate` — Call GPT-4o to produce structured notebook JSON with sections: header, objective, materials receipt log, protocol checklist, raw data tables, statistical analysis, conclusions, deviations log
- Returns: `NotebookTemplate` object with all sections pre-populated from plan

**Output Schema**:
```python
class NotebookTemplate(BaseModel):
    header: Dict  # {hypothesis, pi_name, date, experiment_id, start_date, lab_location}
    objective: str
    materials_receipt: List[Dict]  # {name, catalog_no, supplier, lot_number, expiry_date, actual_supplier}
    protocol_steps: List[Dict]  # {step_number, title, observation_field}
    raw_data_tables: List[Dict]  # {table_name, columns, rows}
    statistical_analysis: Dict  # {test_name, alpha, n, p_value_field, ci_field}
    conclusions: Dict  # {expected_outcome, actual_outcome}
    deviations_log: str  # Free text field
```

---

### 1.2 Modified Services

#### `backend/app/services/plan_generator.py`
**Changes**:
1. Add `three_variants()` method to generate Budget, Standard, Premium variants in single GPT-4o call
2. Add `power_analysis` field to output schema with GPT-4o-suggested effect size, alpha, power, calculated n
3. Add `equipment_required` field to output schema with list of equipment items
4. Add `safety_assessment` field to output schema (call `safety_assessor.assess_safety()`)
5. Add `is_decision`, `decision_branches`, `materials_used`, `safety_notes`, `expected_output` fields to each protocol step
6. Add ISO date strings (`start_date`, `end_date`) to each timeline phase
7. Inject top 2 protocols.io matches into GPT-4o prompt as methodological context

**New Output Fields**:
```python
class ExperimentPlan(BaseModel):
    # ... existing fields ...
    variants: Optional[Dict[str, ProtocolVariant]]  # {budget, standard, premium}
    power_analysis: Optional[PowerAnalysis]
    equipment_required: Optional[List[EquipmentItem]]
    safety_assessment: Optional[SafetyAssessment]
    clinical_trials_check: Optional[ClinicalTrialResult]
```

---

#### `backend/app/services/literature_qc.py`
**Changes**:
1. Verify OpenAlex, PubMed, Europe PMC, bioRxiv are all wired in parallel (they should be based on codebase review)
2. Ensure deduplication by DOI and title normalisation
3. Ensure composite ranking: citations × 0.6 + recency × 0.4
4. Add source badge to each paper result (SemanticScholar | Serper | OpenAlex | PubMed | EuropePMC | bioRxiv)
5. Flag bioRxiv results with `is_preprint: true`

---

#### `backend/app/services/protocols_io.py`
**Changes**:
1. Verify protocol matches are cached in `protocol_matches` table
2. Inject top 2 matches into `plan_generator.py` GPT-4o prompt as methodological context
3. Include protocol title, DOI, citation count, step count in injection

---

### 1.3 New API Endpoints

#### `POST /api/v1/plans/{plan_id}/grant-methods`
**Request**:
```json
{
  "grant_body": "NIH"  // or "NSF", "ERC"
}
```

**Response**:
```json
{
  "grant_body": "NIH",
  "methods_section": "Cells were seeded at 5x10^4 per well...",
  "generated_at": "2026-04-26T12:34:56Z"
}
```

---

#### `POST /api/v1/plans/{plan_id}/notebook`
**Request**: Empty body

**Response**:
```json
{
  "notebook": {
    "header": {...},
    "objective": "...",
    "materials_receipt": [...],
    "protocol_steps": [...],
    "raw_data_tables": [...],
    "statistical_analysis": {...},
    "conclusions": {...},
    "deviations_log": ""
  }
}
```

---

#### `GET /api/v1/plans/{plan_id}/versions`
**Response**:
```json
{
  "versions": [
    {
      "version_number": 1,
      "created_at": "2026-04-26T10:00:00Z",
      "triggered_by": "initial_generation",
      "change_summary": "Initial plan generated"
    },
    {
      "version_number": 2,
      "created_at": "2026-04-26T11:30:00Z",
      "triggered_by": "scientist_correction",
      "change_summary": "Updated protocol steps based on PI feedback"
    }
  ]
}
```

---

#### `POST /api/v1/plans/{plan_id}/restore/{version_id}`
**Request**: Empty body

**Response**:
```json
{
  "plan_id": "uuid",
  "version_number": 2,
  "restored_at": "2026-04-26T12:00:00Z"
}
```

---

#### `PUT /api/v1/equipment/{equipment_name}`
**Request**:
```json
{
  "has_item": true,
  "notes": "Available in core facility"
}
```

**Response**:
```json
{
  "equipment": "Flow cytometer",
  "has_item": true,
  "notes": "Available in core facility",
  "saved_at": "2026-04-26T12:00:00Z"
}
```

---

### 1.4 LangGraph Pipeline Modifications

**New Node**: `_assess_clinical_trials_node`
- Calls `clinical_trials.check_clinical_trials(hypothesis)`
- Stores result in state as `clinical_trials_check`
- Emits progress event

**Modified Node**: `_generate_plan_node`
- After plan generation, call `safety_assessor.assess_safety(plan)`
- Inject clinical trials check into plan metadata
- Generate three variants if requested
- Add power analysis field
- Add equipment list
- Store plan version in `plan_versions` table

---

## 2. Database Schema

### New Tables

```sql
-- Plan version history
CREATE TABLE plan_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  plan_snapshot JSONB NOT NULL,
  change_summary TEXT,
  triggered_by TEXT CHECK (triggered_by IN ('initial_generation', 'scientist_correction', 'hypothesis_edit', 'manual_regen')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX plan_versions_unique ON plan_versions(experiment_id, version_number);
ALTER TABLE plan_versions ENABLE ROW LEVEL SECURITY;

-- Real-time annotations for collaborative review
CREATE TABLE plan_annotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  section TEXT NOT NULL,
  content TEXT NOT NULL,
  position_pct FLOAT,
  author_id TEXT,
  author_role TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE plan_annotations ENABLE ROW LEVEL SECURITY;

-- Per-lab equipment inventory
CREATE TABLE lab_equipment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  equipment TEXT NOT NULL,
  has_item BOOLEAN DEFAULT TRUE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE lab_equipment ENABLE ROW LEVEL SECURITY;

-- Clinical trials cache
CREATE TABLE clinical_trial_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  total_found INTEGER,
  studies JSONB,
  queried_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE clinical_trial_results ENABLE ROW LEVEL SECURITY;

-- Protocol similarity cache
CREATE TABLE protocol_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  matches JSONB,
  queried_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE protocol_matches ENABLE ROW LEVEL SECURITY;

-- Enable Realtime for collaborative features
ALTER TABLE plan_annotations ENABLE ROW LEVEL SECURITY;
-- (In Supabase Dashboard: Table Editor → plan_annotations → Enable Realtime for INSERT, UPDATE)
-- (In Supabase Dashboard: Table Editor → scientist_reviews → Enable Realtime for INSERT, UPDATE)
```

---

## 3. Frontend Architecture

### 3.1 New Components

#### `frontend/components/plan-viewer/power-calculator.tsx`
**Purpose**: Interactive sample-size calculator for statistical power analysis.

**Props**:
```typescript
interface PowerCalculatorProps {
  initialPowerAnalysis?: PowerAnalysis;
  onUpdate?: (analysis: PowerAnalysis) => void;
}
```

**Features**:
- Sliders for effect size, alpha, power
- Dropdown for test type (t-test, ANOVA, chi-squared, log-rank)
- Real-time calculation of sample size per group and total
- Plain-language interpretation

**Implementation**: Pure TypeScript, no external API calls. Uses normal CDF approximation for z-scores.

---

#### `frontend/components/plan-viewer/protocol-flowchart.tsx`
**Purpose**: Interactive directed graph of protocol steps using React Flow.

**Props**:
```typescript
interface ProtocolFlowchartProps {
  protocol: ProtocolStep[];
  onNodeClick?: (step: ProtocolStep) => void;
}
```

**Features**:
- Rectangular nodes for regular steps, diamond nodes for decision points
- Animated edges showing flow
- Click to expand step detail panel
- Background, Controls (zoom/pan), MiniMap
- Fit all nodes in viewport on load

**Dependencies**: `@xyflow/react`

---

#### `frontend/components/plan-viewer/gantt-timeline.tsx`
**Purpose**: Interactive Gantt chart for timeline phases using Frappe Gantt.

**Props**:
```typescript
interface GanttTimelineProps {
  timeline: TimelinePhase[];
  onTaskChange?: (taskId: string, startDate: Date, endDate: Date) => void;
}
```

**Features**:
- Drag to reschedule task bars
- Dependency arrows between phases
- Week/Month view toggle
- Click task to show detail panel
- Fit all tasks in viewport

**Dependencies**: `frappe-gantt`

---

#### `frontend/components/plan-viewer/export-suite.tsx`
**Purpose**: One-click export buttons for PDF, CSV, iCal, DOCX.

**Props**:
```typescript
interface ExportSuiteProps {
  plan: ExperimentPlan;
  grantMethodsText?: string;
}
```

**Features**:
- PDF export (jsPDF + jsPDF-AutoTable)
- CSV export (Papa Parse)
- iCal export (ics.js)
- DOCX export (docx.js)
- All client-side, no server call

**Dependencies**: `jspdf`, `jspdf-autotable`, `file-saver`, `ics`, `docx`

---

#### `frontend/components/plan-viewer/grant-methods.tsx`
**Purpose**: Tab for generating and displaying grant Methods section.

**Props**:
```typescript
interface GrantMethodsProps {
  plan: ExperimentPlan;
  planId: string;
}
```

**Features**:
- Dropdown to select grant body (NIH, NSF, ERC)
- "Generate" button calls API
- Display generated Methods section
- Copy-to-clipboard button
- Include in DOCX export

---

#### `frontend/components/plan-viewer/equipment-checklist.tsx`
**Purpose**: Equipment list with per-lab availability tracking.

**Props**:
```typescript
interface EquipmentChecklistProps {
  equipment: EquipmentItem[];
  planId: string;
}
```

**Features**:
- Checkbox for each item: "Have it", "Need to acquire", "Using core facility"
- Persist selection to Supabase `lab_equipment` table
- Pre-populate from previous experiments
- Summary showing total cost for items to acquire
- List of core facility bookings needed

---

#### `frontend/components/plan-viewer/safety-tab.tsx`
**Purpose**: Dedicated Safety tab displaying risk and safety assessment.

**Props**:
```typescript
interface SafetyTabProps {
  safety: SafetyAssessment;
}
```

**Features**:
- BSL level badge at top
- Red banners for IACUC/IRB requirements
- GHS pictogram icons for hazardous reagents
- PPE requirements list
- Waste disposal categories
- Emergency contact guidance

---

#### `frontend/components/plan-viewer/version-history.tsx`
**Purpose**: Version history rail and diff view.

**Props**:
```typescript
interface VersionHistoryProps {
  planId: string;
  currentVersion: number;
}
```

**Features**:
- Horizontal version rail at top showing all versions
- Click version to load it
- Select two versions to enter diff mode
- Diff display with green (additions) and red (removals) highlights
- "Restore this version" button

**Dependencies**: `fast-diff`

---

#### `frontend/components/plan-viewer/collaborative-review.tsx`
**Purpose**: Real-time presence, annotations, and review feed.

**Props**:
```typescript
interface CollaborativeReviewProps {
  planId: string;
  userId: string;
  userRole: string;
}
```

**Features**:
- Supabase Realtime presence tracking
- Active reviewer avatars in top-right corner
- Tab indicators showing which reviewer is viewing which tab
- Floating comment bubbles for annotations
- Live review feed sidebar
- Broadcast annotations via Realtime

**Dependencies**: `@supabase/supabase-js` (Realtime)

---

#### `frontend/components/plan-viewer/variant-selector.tsx`
**Purpose**: Budget/Standard/Premium variant selection cards.

**Props**:
```typescript
interface VariantSelectorProps {
  variants: ProtocolVariants;
  onSelect: (variant: 'budget' | 'standard' | 'premium') => void;
}
```

**Features**:
- Three cards showing variant name, cost, timeline
- Click to select variant
- Update plan view below
- Side-by-side comparison table

---

#### `frontend/components/plan-viewer/clinical-trials-badge.tsx`
**Purpose**: Clinical trials radar badge.

**Props**:
```typescript
interface ClinicalTrialsBadgeProps {
  clinicalTrials: ClinicalTrialResult;
}
```

**Features**:
- Green badge: "No overlapping clinical trials found"
- Amber badge: "Active clinical trials detected" (expandable list)
- Red badge: "High clinical trial overlap"
- Links to ClinicalTrials.gov

---

#### `frontend/components/plan-viewer/notebook-export.tsx`
**Purpose**: Lab notebook export button and preview.

**Props**:
```typescript
interface NotebookExportProps {
  plan: ExperimentPlan;
  planId: string;
}
```

**Features**:
- "Generate Lab Notebook" button
- Preview of notebook structure
- Export as PDF with fillable fields
- Pre-populated with plan data

---

### 3.2 Modified Pages

#### `frontend/app/(dashboard)/plans/[id]/page.tsx`
**Changes**:
1. Add new tabs: Safety, Grant Language, Equipment, Notebook
2. Add version history rail at top
3. Add collaborative review sidebar
4. Add variant selector at top of Plan tab
5. Add export suite buttons
6. Add clinical trials badge in header
7. Add power calculator to Validation tab
8. Restructure tab layout to accommodate new tabs

**New Tab Order**:
1. Protocol (with flowchart)
2. Materials
3. Timeline (with Gantt)
4. Validation (with power calculator)
5. Safety (new)
6. Grant Language (new)
7. Equipment (new)
8. Notebook (new)

---

### 3.3 New Types

Add to `frontend/lib/types.ts`:

```typescript
interface SafetyAssessment {
  bsl_level: number;
  bsl_rationale: string;
  requires_iacuc: boolean;
  requires_irb: boolean;
  requires_biosafety_committee: boolean;
  ppe_required: string[];
  hazardous_reagents: Array<{
    name: string;
    ghs_codes: string[];
    hazard: string;
    ppe_addition: string;
    disposal: string;
  }>;
  waste_disposal: Record<string, string>;
  emergency_contacts: string[];
}

interface ProtocolVariant {
  total_cost_usd: number;
  timeline_weeks: number;
  key_tradeoffs?: string;
  key_advantages?: string;
  protocol: ProtocolStep[];
  materials: Material[];
}

interface ProtocolVariants {
  budget: ProtocolVariant;
  standard: ProtocolVariant;
  premium: ProtocolVariant;
}

interface PowerAnalysis {
  recommended_test: string;
  suggested_effect_size: number;
  effect_size_rationale: string;
  suggested_alpha: number;
  suggested_power: number;
  calculated_n_per_group: number;
  total_sample_size: number;
}

interface EquipmentItem {
  name: string;
  category: string;
  model_suggestion: string;
  est_purchase_usd: number;
  is_commonly_available: boolean;
  core_facility_alternative?: string;
  rental_available: boolean;
}

interface PlanVersion {
  version_number: number;
  created_at: string;
  triggered_by: string;
  change_summary: string;
}

interface PlanAnnotation {
  id: string;
  section: string;
  content: string;
  position_pct: number;
  author_id: string;
  author_role: string;
  created_at: string;
}

interface ClinicalTrialResult {
  total_found: number;
  studies: Array<{
    nct_id: string;
    title: string;
    status: string;
    phase?: string;
    url: string;
  }>;
}

interface GrantMethodsResult {
  grant_body: string;
  methods_section: string;
  generated_at: string;
}

interface NotebookTemplate {
  header: Record<string, any>;
  objective: string;
  materials_receipt: Array<Record<string, any>>;
  protocol_steps: Array<Record<string, any>>;
  raw_data_tables: Array<Record<string, any>>;
  statistical_analysis: Record<string, any>;
  conclusions: Record<string, any>;
  deviations_log: string;
}
```

---

## 4. Data Flow

### Feature F-01: Multi-Source Literature
1. User submits hypothesis
2. `literature_qc_node` queries 6 sources in parallel (Semantic Scholar, Serper, OpenAlex, PubMed, Europe PMC, bioRxiv)
3. Results deduplicated by DOI, ranked by composite score
4. Frontend displays coverage summary and source badges

### Feature F-04: Clinical Trials Radar
1. After hypothesis validation, `_assess_clinical_trials_node` extracts key terms
2. Queries ClinicalTrials.gov API v2
3. Results cached in `clinical_trial_results` table
4. Frontend displays badge (green/amber/red) based on trial count

### Feature F-05: Statistical Power Calculator
1. `plan_generator` includes `power_analysis` field with GPT-4o-suggested values
2. Frontend loads power calculator with suggested values
3. User adjusts sliders, calculator updates sample size in real-time
4. No API calls required

### Feature F-07: Risk & Safety Assessment
1. After plan generation, `safety_assessor` calls GPT-4o with plan data
2. Queries PubChem for GHS codes on each reagent
3. Returns `SafetyAssessment` object
4. Frontend displays Safety tab with BSL badge, IACUC/IRB banners, GHS pictograms

### Feature F-08: Three Protocol Variants
1. `plan_generator` calls GPT-4o with structured output schema requiring three variants
2. Returns `variants` object with budget/standard/premium
3. Frontend displays variant selector cards
4. User clicks variant to update plan view

### Feature F-09: Interactive Protocol Flowchart
1. `plan_generator` includes `is_decision`, `decision_branches`, `materials_used`, `safety_notes` on each step
2. Frontend renders React Flow flowchart with rectangular and diamond nodes
3. User clicks node to expand detail panel

### Feature F-10: Real-Time Gantt Timeline
1. `plan_generator` provides ISO date strings on each timeline phase
2. Frontend renders Frappe Gantt with task bars and dependency arrows
3. User drags to reschedule, changes persist in local state

### Feature F-11: Export Suite
1. User clicks export button
2. Frontend generates PDF/CSV/iCal/DOCX entirely client-side
3. Browser downloads file

### Feature F-12: Grant Methods Generator
1. User selects grant body and clicks "Generate"
2. Frontend calls `POST /api/v1/plans/{id}/grant-methods`
3. Backend calls GPT-4o with grant-specific prompt
4. Frontend displays Methods section with copy button

### Feature F-13: Equipment Checklist
1. `plan_generator` includes `equipment_required` field
2. Frontend displays checklist with availability toggles
3. User marks items, frontend persists to `lab_equipment` table
4. On next plan, frontend pre-populates from saved equipment

### Feature F-15: Live Collaborative Review
1. Multiple users open same plan
2. Frontend joins Supabase Realtime channel for that plan
3. Presence tracked, avatars displayed
4. Annotations broadcast via Realtime
5. Reviews displayed in live feed via Postgres Changes

### Feature F-16: Plan Version History
1. Each plan generation creates entry in `plan_versions` table
2. Frontend displays version rail at top
3. User clicks version to load it
4. User selects two versions to enter diff mode
5. Diff computed client-side using fast-diff library

### Feature F-17: Lab Notebook Template
1. User clicks "Generate Lab Notebook"
2. Frontend calls `POST /api/v1/plans/{id}/notebook`
3. Backend calls GPT-4o to generate notebook JSON
4. Frontend exports as PDF with fillable fields

---

## 5. Dependencies

### Backend (requirements.txt additions)
```
lxml==5.3.0
xmltodict==0.14.2
tenacity==9.0.0
cachetools==5.5.0
python-docx==1.2.0
reportlab==4.2.5
icalendar==6.0.1
```

### Frontend (package.json additions)
```json
{
  "@xyflow/react": "^12.3.0",
  "frappe-gantt": "^0.6.1",
  "jspdf": "^2.5.1",
  "jspdf-autotable": "^3.8.2",
  "file-saver": "^2.0.5",
  "ics": "^3.7.2",
  "fast-diff": "^1.3.0",
  "docx": "^8.5.0"
}
```

---

## 6. Implementation Notes

### Parallelisation
- Literature search: All 6 sources queried in parallel with `asyncio.gather()`
- Clinical trials check: Runs in parallel with plan generation
- Safety assessment: Runs after plan generation (depends on plan data)

### Error Handling
- If any literature source fails, continue with remaining sources
- If clinical trials API unavailable, display neutral badge
- If safety assessment fails, return plan without safety field
- If grant methods generation fails, display retry button

### Caching
- Protocol matches cached per experiment_id
- Clinical trial results cached per experiment_id
- Equipment availability cached per user_id

### Rate Limiting
- Plan generation: 10 req/min per user
- Grant methods: 10 req/min per user
- Notebook generation: 10 req/min per user

### Testing Strategy
- Unit tests for each new service (clinical_trials, safety_assessor, grant_methods, notebook_generator)
- Integration tests for new API endpoints
- Frontend component tests for power calculator, flowchart, Gantt, export suite
- E2E tests for full feature workflows
