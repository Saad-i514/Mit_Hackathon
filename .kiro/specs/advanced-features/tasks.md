# Implementation Tasks — Advanced Features

## Phase 1: Database & Backend Infrastructure

- [x] 1.1 Create migration file `backend/migrations/003_advanced_features_schema.sql` with all new tables (plan_versions, plan_annotations, lab_equipment, clinical_trial_results, protocol_matches)
- [x] 1.2 Run migration in Supabase to create tables and enable RLS
- [x] 1.3 Enable Realtime on `plan_annotations` and `scientist_reviews` tables in Supabase Dashboard
- [x] 1.4 Add new dependencies to `backend/requirements.txt`: lxml, xmltodict, tenacity, cachetools, python-docx, reportlab, icalendar
- [ ] 1.5 Update `backend/app/config.py` to validate new environment variables (if any)

## Phase 2: Backend Services — New Services

- [x] 2.1 Create `backend/app/services/clinical_trials.py` with:
  - `extract_key_terms(hypothesis: str) -> List[str]` using GPT-4o
  - `check_clinical_trials(hypothesis: str) -> Dict` querying ClinicalTrials.gov API v2
  - Caching logic to `clinical_trial_results` table
  - Error handling for API failures

- [x] 2.2 Create `backend/app/services/safety_assessor.py` with:
  - `assess_safety(plan: ExperimentPlan) -> SafetyAssessment` calling GPT-4o
  - `extract_ghs_codes(reagent_name: str) -> List[str]` querying PubChem
  - BSL level determination logic
  - IACUC/IRB flag logic
  - PPE and waste disposal categorisation

- [x] 2.3 Create `backend/app/services/grant_methods.py` with:
  - `generate_grant_methods(plan: ExperimentPlan, grant_body: str) -> str` calling GPT-4o
  - Support for NIH, NSF, ERC grant bodies
  - Prompt template with past tense, third person, reagent citations

- [x] 2.4 Create `backend/app/services/notebook_generator.py` with:
  - `generate_notebook(plan: ExperimentPlan) -> NotebookTemplate` calling GPT-4o
  - Structured notebook JSON with all sections pre-populated
  - Materials receipt log with lot number fields
  - Protocol step checklist with observation fields
  - Raw data tables with pre-defined columns
  - Statistical analysis section
  - Conclusions and deviations log

## Phase 3: Backend Services — Modifications

- [x] 3.1 Modify `backend/app/services/literature_qc.py`:
  - Verify OpenAlex, PubMed, Europe PMC, bioRxiv are all wired in parallel
  - Add source badge to each paper result
  - Flag bioRxiv results with `is_preprint: true`
  - Ensure deduplication by DOI and title
  - Ensure composite ranking: citations × 0.6 + recency × 0.4

- [x] 3.2 Modify `backend/app/services/plan_generator.py`:
  - Add `three_variants()` method to generate Budget, Standard, Premium in single GPT-4o call
  - Add `power_analysis` field to output with GPT-4o-suggested values
  - Add `equipment_required` field to output
  - Call `safety_assessor.assess_safety()` and add `safety_assessment` field
  - Add `is_decision`, `decision_branches`, `materials_used`, `safety_notes`, `expected_output` to protocol steps
  - Add ISO date strings (`start_date`, `end_date`) to timeline phases
  - Inject top 2 protocols.io matches into GPT-4o prompt

- [x] 3.3 Modify `backend/app/services/protocols_io.py`:
  - Verify protocol matches are cached in `protocol_matches` table
  - Ensure matches are injected into plan_generator GPT-4o prompt

## Phase 4: Backend API Endpoints

- [x] 4.1 Add new endpoint `POST /api/v1/plans/{plan_id}/grant-methods` in `backend/app/api/v1/plans.py`:
  - Accept `grant_body` parameter (NIH, NSF, ERC)
  - Call `grant_methods.generate_grant_methods()`
  - Return Methods section text

- [x] 4.2 Add new endpoint `POST /api/v1/plans/{plan_id}/notebook` in `backend/app/api/v1/plans.py`:
  - Call `notebook_generator.generate_notebook()`
  - Return NotebookTemplate JSON

- [x] 4.3 Add new endpoint `GET /api/v1/plans/{plan_id}/versions` in `backend/app/api/v1/plans.py`:
  - Query `plan_versions` table for experiment_id
  - Return list of versions with metadata

- [x] 4.4 Add new endpoint `POST /api/v1/plans/{plan_id}/restore/{version_id}` in `backend/app/api/v1/plans.py`:
  - Load plan snapshot from `plan_versions` table
  - Create new version entry with trigger type `manual_regen`
  - Return restored plan

- [x] 4.5 Add new endpoint `PUT /api/v1/equipment/{equipment_name}` in `backend/app/api/v1/plans.py`:
  - Accept `has_item` and `notes` parameters
  - Persist to `lab_equipment` table
  - Return confirmation

## Phase 5: Backend Pipeline Integration

- [x] 5.1 Modify `backend/app/graph/ai_pipeline.py`:
  - Add new node `_assess_clinical_trials_node` that calls `clinical_trials.check_clinical_trials()`
  - Insert node into graph after `_validate_hypothesis_node`
  - Emit progress events for clinical trials check

- [x] 5.2 Modify `_generate_plan_node` in `backend/app/graph/ai_pipeline.py`:
  - After plan generation, call `safety_assessor.assess_safety()`
  - Add clinical trials check to plan metadata
  - Store plan version in `plan_versions` table with trigger type `initial_generation`
  - Emit progress events for safety assessment

- [x] 5.3 Update `backend/app/graph/pipeline_state.py`:
  - Add `clinical_trials_check` field to PipelineState
  - Add `safety_assessment` field to PipelineState

## Phase 6: Frontend Dependencies & Types

- [x] 6.1 Add new npm packages to `frontend/package.json`:
  - `@xyflow/react@^12.3.0`
  - `frappe-gantt@^0.6.1`
  - `jspdf@^2.5.1`
  - `jspdf-autotable@^3.8.2`
  - `file-saver@^2.0.5`
  - `ics@^3.7.2`
  - `fast-diff@^1.3.0`
  - `docx@^8.5.0`

- [x] 6.2 Run `npm install` in frontend directory

- [x] 6.3 Add new TypeScript types to `frontend/lib/types.ts`:
  - SafetyAssessment
  - ProtocolVariant, ProtocolVariants
  - PowerAnalysis
  - EquipmentItem
  - PlanVersion
  - PlanAnnotation
  - ClinicalTrialResult
  - GrantMethodsResult
  - NotebookTemplate

## Phase 7: Frontend Components — Power Calculator & Flowchart

- [x] 7.1 Create `frontend/components/plan-viewer/power-calculator.tsx`:
  - Sliders for effect size, alpha, power
  - Dropdown for test type (t-test, ANOVA, chi-squared, log-rank)
  - Real-time sample size calculation
  - Plain-language interpretation
  - Pre-populate from `power_analysis` field in plan

- [x] 7.2 Create `frontend/components/plan-viewer/protocol-flowchart.tsx`:
  - React Flow setup with nodes and edges
  - Rectangular nodes for regular steps, diamond for decision points
  - Click node to expand detail panel
  - Background, Controls, MiniMap
  - Fit all nodes in viewport on load

## Phase 8: Frontend Components — Timeline & Export

- [x] 8.1 Create `frontend/components/plan-viewer/gantt-timeline.tsx`:
  - Frappe Gantt setup with task bars
  - Dependency arrows between phases
  - Week/Month view toggle
  - Drag to reschedule
  - Click task to show detail panel

- [x] 8.2 Create `frontend/components/plan-viewer/export-suite.tsx`:
  - PDF export using jsPDF + jsPDF-AutoTable
  - CSV export using Papa Parse
  - iCal export using ics.js
  - DOCX export using docx.js
  - All client-side, no server call

## Phase 9: Frontend Components — Grant, Equipment, Safety

- [x] 9.1 Create `frontend/components/plan-viewer/grant-methods.tsx`:
  - Dropdown to select grant body (NIH, NSF, ERC)
  - "Generate" button calls `POST /api/v1/plans/{id}/grant-methods`
  - Display generated Methods section
  - Copy-to-clipboard button

- [x] 9.2 Create `frontend/components/plan-viewer/equipment-checklist.tsx`:
  - Checkbox for each item: "Have it", "Need to acquire", "Using core facility"
  - Persist selection to `lab_equipment` table via `PUT /api/v1/equipment/{name}`
  - Pre-populate from previous experiments
  - Summary showing total cost and core facility bookings

- [x] 9.3 Create `frontend/components/plan-viewer/safety-tab.tsx`:
  - BSL level badge at top
  - Red banners for IACUC/IRB requirements
  - GHS pictogram icons for hazardous reagents
  - PPE requirements list
  - Waste disposal categories
  - Emergency contact guidance

## Phase 10: Frontend Components — Collaboration & Versioning

- [x] 10.1 Create `frontend/components/plan-viewer/collaborative-review.tsx`:
  - Supabase Realtime presence tracking
  - Active reviewer avatars in top-right corner
  - Tab indicators showing which reviewer is viewing which tab
  - Floating comment bubbles for annotations
  - Live review feed sidebar
  - Broadcast annotations via Realtime

- [x] 10.2 Create `frontend/components/plan-viewer/version-history.tsx`:
  - Horizontal version rail at top
  - Click version to load it
  - Select two versions to enter diff mode
  - Diff display with green (additions) and red (removals) highlights
  - "Restore this version" button calls `POST /api/v1/plans/{id}/restore/{version_id}`

## Phase 11: Frontend Components — Variants & Clinical Trials

- [x] 11.1 Create `frontend/components/plan-viewer/variant-selector.tsx`:
  - Three cards showing variant name, cost, timeline
  - Click to select variant
  - Update plan view below
  - Side-by-side comparison table

- [x] 11.2 Create `frontend/components/plan-viewer/clinical-trials-badge.tsx`:
  - Green badge: "No overlapping clinical trials found"
  - Amber badge: "Active clinical trials detected" (expandable list)
  - Red badge: "High clinical trial overlap"
  - Links to ClinicalTrials.gov

## Phase 12: Frontend Components — Notebook

- [x] 12.1 Create `frontend/components/plan-viewer/notebook-export.tsx`:
  - "Generate Lab Notebook" button calls `POST /api/v1/plans/{id}/notebook`
  - Preview of notebook structure
  - Export as PDF with fillable fields
  - Pre-populated with plan data

## Phase 13: Frontend Page Restructuring

- [x] 13.1 Modify `frontend/app/(dashboard)/plans/[id]/page.tsx`:
  - Add new tabs: Safety, Grant Language, Equipment, Notebook
  - Add version history rail at top
  - Add collaborative review sidebar
  - Add variant selector at top of Plan tab
  - Add export suite buttons
  - Add clinical trials badge in header
  - Add power calculator to Validation tab
  - Restructure tab layout to accommodate new tabs
  - Update tab order: Protocol, Materials, Timeline, Validation, Safety, Grant Language, Equipment, Notebook

## Phase 14: Testing — Backend Services

- [ ] 14.1 Write unit tests for `clinical_trials.py`:
  - Test `extract_key_terms()` with various hypotheses
  - Test `check_clinical_trials()` with mock API responses
  - Test caching logic

- [ ] 14.2 Write unit tests for `safety_assessor.py`:
  - Test `assess_safety()` with various plans
  - Test `extract_ghs_codes()` with various reagents
  - Test BSL level determination

- [ ] 14.3 Write unit tests for `grant_methods.py`:
  - Test `generate_grant_methods()` for NIH, NSF, ERC
  - Test output format (past tense, third person, reagent citations)

- [ ] 14.4 Write unit tests for `notebook_generator.py`:
  - Test `generate_notebook()` with various plans
  - Test notebook structure and pre-population

## Phase 15: Testing — API Endpoints

- [ ] 15.1 Write integration tests for new endpoints:
  - `POST /api/v1/plans/{id}/grant-methods`
  - `POST /api/v1/plans/{id}/notebook`
  - `GET /api/v1/plans/{id}/versions`
  - `POST /api/v1/plans/{id}/restore/{version_id}`
  - `PUT /api/v1/equipment/{equipment_name}`

- [ ] 15.2 Test error handling for all endpoints (API failures, timeouts, invalid inputs)

## Phase 16: Testing — Frontend Components

- [ ] 16.1 Write component tests for power calculator:
  - Test slider interactions
  - Test sample size calculation
  - Test pre-population from plan data

- [ ] 16.2 Write component tests for protocol flowchart:
  - Test node rendering
  - Test edge rendering
  - Test node click interactions

- [ ] 16.3 Write component tests for Gantt timeline:
  - Test task bar rendering
  - Test dependency arrows
  - Test drag to reschedule

- [ ] 16.4 Write component tests for export suite:
  - Test PDF export
  - Test CSV export
  - Test iCal export
  - Test DOCX export

## Phase 17: Testing — E2E Workflows

- [ ] 17.1 E2E test: Generate plan with all features
  - Submit hypothesis
  - Verify clinical trials check appears
  - Verify safety assessment appears
  - Verify three variants appear
  - Verify power calculator pre-populated
  - Verify equipment checklist appears

- [ ] 17.2 E2E test: Export plan in all formats
  - Generate plan
  - Export as PDF
  - Export as CSV
  - Export as iCal
  - Export as DOCX
  - Verify all files download correctly

- [ ] 17.3 E2E test: Collaborative review
  - Open plan in two browser windows
  - Verify presence tracking
  - Add annotation in one window
  - Verify annotation appears in other window
  - Submit review in one window
  - Verify review appears in other window

- [ ] 17.4 E2E test: Version history
  - Generate plan (v1)
  - Modify and regenerate (v2)
  - View version history
  - Compare v1 and v2
  - Restore v1
  - Verify v1 is now current

## Phase 18: Documentation & Deployment

- [ ] 18.1 Update `backend/README.md` with new services and endpoints
- [ ] 18.2 Update `frontend/README.md` with new components and features
- [ ] 18.3 Update API documentation with new endpoints
- [ ] 18.4 Create migration guide for existing users
- [ ] 18.5 Deploy to staging environment
- [ ] 18.6 Run full regression test suite
- [ ] 18.7 Deploy to production

---

## Notes

- All tasks should be completed in order within each phase
- Each task should be tested individually before moving to the next
- Backend services should be tested with unit tests before integration
- Frontend components should be tested with component tests before integration
- E2E tests should be run after all components are integrated
- Use the venv for backend development
- Use npm for frontend development
- All new code should follow existing code style and conventions
