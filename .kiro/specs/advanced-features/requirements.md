# Requirements Document

## Introduction

This document specifies 12 advanced features for the AI Scientist Platform. The platform already has a working core pipeline (hypothesis validation → literature QC → plan generation) backed by Semantic Scholar, Serper, PubChem, protocols.io, and GPT-4o. These features extend the platform across four categories: Intelligence Layer (richer data sources), Plan Quality (statistical rigour and safety), Scientist-Grade UI (interactive visualisation and export), and Collaboration (real-time teamwork and history). All external services used are free-tier or keyless.

## Glossary

- **Platform**: The complete AI Scientist Platform (Next.js frontend + FastAPI backend + Supabase)
- **Literature_QC_Engine**: Existing backend component that searches literature and classifies novelty
- **Plan_Generator**: Existing GPT-4o component that produces structured `ExperimentPlan` JSON
- **Web_Client**: Next.js 14 frontend application
- **API_Gateway**: FastAPI backend service
- **Vector_Store**: Supabase PostgreSQL + pgvector database
- **Realtime_Channel**: Supabase Realtime WebSocket channel
- **ExperimentPlan**: Structured JSON output containing protocol, materials, timeline, and validation criteria
- **Principal_Investigator**: Primary user role — a working scientist who will act on the generated plan
- **PubChem**: NCBI's free chemical compound database (REST API, no key required)
- **ClinicalTrials_API**: ClinicalTrials.gov REST API v2 (no key required)
- **Power_Calculator**: Client-side TypeScript statistical power and sample-size calculator
- **Safety_Assessor**: Backend component that generates risk and safety briefings using GPT-4o and PubChem GHS data
- **Protocol_Flowchart**: React Flow interactive directed-graph visualisation of protocol steps
- **Gantt_Timeline**: Frappe Gantt interactive timeline component
- **Export_Suite**: Client-side export utilities (PDF, CSV, iCal, DOCX)
- **Grant_Generator**: GPT-4o component that rewrites the protocol as a formal grant Methods section
- **Equipment_Checklist**: GPT-4o-generated equipment list with per-lab availability tracking in Supabase
- **Collaborative_Review**: Supabase Realtime presence, broadcast, and Postgres Changes layer for multi-user plan review
- **Version_History**: Supabase-persisted snapshots of every plan revision with client-side diff rendering
- **Notebook_Generator**: GPT-4o component that produces a pre-filled electronic lab notebook template

---

## Requirements

### Requirement F-01: Multi-Source Literature Engine

**User Story:** As a Principal_Investigator, I want the Platform to search multiple literature databases in parallel, so that I get a comprehensive novelty assessment that does not miss relevant prior work.

#### Acceptance Criteria

1. WHEN a validated hypothesis is received, THE Literature_QC_Engine SHALL query OpenAlex, PubMed (NCBI eutils), Europe PMC, and bioRxiv in parallel alongside the existing Semantic Scholar and Serper searches
2. THE Literature_QC_Engine SHALL deduplicate results across all six sources using DOI as the primary key and normalised title as the fallback key
3. WHEN results from multiple sources are merged, THE Literature_QC_Engine SHALL rank papers by a composite score weighting citation count (60%) and recency (40%)
4. THE Literature_QC_Engine SHALL complete the six-source parallel search within 30 seconds
5. IF any individual source search fails or times out, THEN THE Literature_QC_Engine SHALL continue with results from the remaining sources and log the failure
6. WHEN bioRxiv results are included, THE Web_Client SHALL display an amber "PREPRINT — not peer-reviewed" badge on those references
7. THE Web_Client SHALL display a coverage summary showing the number of databases searched, total papers found, papers after deduplication, and papers shown

---

### Requirement F-02: Reagent Intelligence Engine

**User Story:** As a Principal_Investigator, I want each reagent in the materials list to show chemical identity, hazard codes, and cheaper alternatives, so that I can make informed procurement and safety decisions.

#### Acceptance Criteria

1. FOR ALL reagents in a generated ExperimentPlan, THE Plan_Generator SHALL enrich each reagent with PubChem data including: CID, CAS number, molecular weight, molecular formula, GHS hazard codes, and PubChem URL
2. WHEN a reagent name cannot be resolved by PubChem, THE Plan_Generator SHALL mark that reagent as `pubchem_found: false` and continue without blocking plan generation
3. THE Web_Client SHALL render GHS hazard codes as colour-coded badges: red for acute toxicity (H300–H310 range), amber for health hazard, blue for environmental hazard
4. THE Web_Client SHALL display GHS pictogram icons (skull, flame, exclamation, etc.) inline with each hazardous reagent row in the Materials tab
5. THE Web_Client SHALL display a "Cheaper alternatives" section for each reagent showing at least one lower-cost substitute where available
6. THE Web_Client SHALL display a total safety summary at the top of the Materials tab showing the highest biosafety level required by any reagent in the list
7. WHEN a user expands a reagent row, THE Web_Client SHALL show the full PubChem detail drawer including CAS number, molecular weight, GHS codes, and a link to the PubChem compound page

---

### Requirement F-03: Protocol Similarity Search

**User Story:** As a Principal_Investigator, I want the Platform to find similar published protocols before generating a plan, so that the generated protocol steps are grounded in validated real-world methodology.

#### Acceptance Criteria

1. WHEN a hypothesis is validated, THE API_Gateway SHALL query the protocols.io public API for the five most-cited protocols matching the hypothesis keywords
2. THE Plan_Generator SHALL inject the top two matching protocols as methodological context into the GPT-4o prompt, including protocol title, DOI, citation count, and step count
3. THE Web_Client SHALL display matched protocols in the Protocol tab with title, citation count, step count, and a direct link to protocols.io
4. IF the protocols.io API is unavailable or returns no results, THEN THE Plan_Generator SHALL proceed with plan generation without protocol context and log the failure
5. THE API_Gateway SHALL cache protocol similarity results per experiment to avoid redundant API calls on plan re-generation

---

### Requirement F-04: Clinical Trials Radar

**User Story:** As a Principal_Investigator, I want to know whether active clinical trials are already testing my hypothesis, so that I can avoid duplicating ongoing human studies.

#### Acceptance Criteria

1. WHEN an experiment plan is generated, THE API_Gateway SHALL query the ClinicalTrials.gov API v2 using key terms extracted from the hypothesis, filtering for RECRUITING, ACTIVE_NOT_RECRUITING, NOT_YET_RECRUITING, and COMPLETED statuses
2. THE Web_Client SHALL display a green badge "No overlapping clinical trials found" when zero matching trials are returned
3. THE Web_Client SHALL display an amber badge "Active clinical trials detected" with an expandable list of up to three trials (NCT ID, title, status, phase, link) when one to three matching trials are found
4. THE Web_Client SHALL display a red badge "High clinical trial overlap — consider refining hypothesis scope" when more than three matching trials are found
5. THE API_Gateway SHALL cache clinical trial query results per experiment to avoid redundant API calls
6. IF the ClinicalTrials.gov API is unavailable, THEN THE Web_Client SHALL display a neutral "Clinical trial check unavailable" indicator without blocking plan display

---

### Requirement F-05: Statistical Power Calculator

**User Story:** As a Principal_Investigator, I want an interactive sample-size calculator embedded in the Validation tab, so that I can confirm my experiment is adequately powered before ordering materials.

#### Acceptance Criteria

1. THE Web_Client SHALL include a Power_Calculator component in the Validation tab that computes required sample size for two-sample t-test, one-way ANOVA, chi-squared, and survival log-rank test designs
2. THE Power_Calculator SHALL accept effect size, alpha level, and desired power as inputs and display the calculated sample size per group in real time as the user adjusts sliders
3. THE Plan_Generator SHALL include a `power_analysis` field in the ExperimentPlan JSON with GPT-4o-suggested values for: recommended test, suggested effect size with rationale, alpha, power, calculated n per group, and total sample size
4. WHEN an ExperimentPlan is loaded, THE Web_Client SHALL pre-populate the Power_Calculator sliders with the GPT-4o-suggested values from the `power_analysis` field
5. THE Power_Calculator SHALL operate entirely client-side with no external API calls
6. THE Power_Calculator SHALL display the calculated total sample size and a plain-language interpretation (e.g. "26 animals per group, 52 total") alongside the numeric result

---

### Requirement F-07: Risk & Safety Assessment

**User Story:** As a Principal_Investigator, I want an automatically generated safety briefing for my experiment, so that I can meet legal and institutional requirements before starting bench work.

#### Acceptance Criteria

1. WHEN an ExperimentPlan is generated, THE Safety_Assessor SHALL produce a `safety_assessment` object containing: BSL level (1–4) with rationale, IACUC required flag, IRB required flag, biosafety committee required flag, required PPE list, per-reagent GHS hazard details, waste disposal categories, and emergency contact guidance
2. THE Web_Client SHALL display the Safety Assessment as a dedicated "Safety" tab (sixth tab) in the plan viewer, with the BSL level badge prominently at the top
3. WHEN `requires_iacuc` is true, THE Web_Client SHALL display a prominent red banner: "This experiment requires IACUC approval before starting"
4. WHEN `requires_irb` is true, THE Web_Client SHALL display a prominent red banner: "This experiment requires IRB approval before starting"
5. THE Web_Client SHALL render GHS pictogram icons for each hazardous reagent listed in the safety assessment
6. IF the Safety_Assessor call fails, THEN THE API_Gateway SHALL return the ExperimentPlan without a safety assessment and set a `safety_assessment_error` flag, which THE Web_Client SHALL display as a warning

---

### Requirement F-08: Three Protocol Variants

**User Story:** As a Principal_Investigator, I want to choose between budget, standard, and premium protocol variants, so that I can match the experiment to my available resources.

#### Acceptance Criteria

1. THE Plan_Generator SHALL generate three protocol variants in a single GPT-4o call: Budget (minimise cost), Standard (balance cost and quality), and Premium (maximum sensitivity and quality)
2. EACH variant SHALL include: total cost in USD, estimated timeline in weeks, key trade-offs or advantages, a complete protocol step list, and a complete materials list
3. THE Web_Client SHALL display three variant selection cards at the top of the Plan tab, each showing variant name, total cost, and timeline
4. WHEN a scientist selects a variant card, THE Web_Client SHALL update the full plan view below to show that variant's protocol steps and materials
5. THE Web_Client SHALL display a side-by-side comparison table showing key differences between variants: total cost, timeline, key reagent substitutions, and sensitivity impact
6. THE Web_Client SHALL default to the Standard variant on initial plan load

---

### Requirement F-09: Interactive Protocol Flowchart

**User Story:** As a Principal_Investigator, I want to see the protocol as an interactive flowchart, so that I can understand the experimental flow and decision points at a glance.

#### Acceptance Criteria

1. THE Web_Client SHALL render the Protocol tab with a Protocol_Flowchart component using React Flow (`@xyflow/react`) that displays each protocol step as a node and each step transition as a directed edge
2. THE Protocol_Flowchart SHALL render decision-point steps (where `is_decision` is true) as diamond-shaped nodes with branching edges to alternative next steps
3. WHEN a scientist clicks a node, THE Web_Client SHALL display a detail panel showing: full step description, duration, materials used, safety notes, and source citation
4. THE Protocol_Flowchart SHALL include React Flow Background, Controls (zoom/pan), and MiniMap components
5. THE Plan_Generator SHALL include `is_decision`, `decision_branches`, `materials_used`, `safety_notes`, and `expected_output` fields on each protocol step in the ExperimentPlan JSON
6. THE Protocol_Flowchart SHALL fit all nodes within the visible viewport on initial render

---

### Requirement F-10: Real-Time Gantt Timeline

**User Story:** As a Principal_Investigator, I want an interactive Gantt chart for the experiment timeline, so that I can visualise phase dependencies and reschedule tasks.

#### Acceptance Criteria

1. THE Web_Client SHALL render the Timeline tab with a Gantt_Timeline component using Frappe Gantt (`frappe-gantt`) that displays each timeline phase as a task bar
2. THE Gantt_Timeline SHALL display dependency arrows between phases that have declared dependencies
3. WHEN a scientist drags a task bar, THE Web_Client SHALL update the phase start and end dates in the local plan state
4. THE Gantt_Timeline SHALL support Week and Month view modes, defaulting to Week view
5. WHEN a scientist clicks a task bar, THE Web_Client SHALL display a detail panel showing phase name, duration, description, and dependencies
6. THE Plan_Generator SHALL provide timeline phase data with ISO date strings for `start_date` and `end_date` on each phase to support direct Gantt rendering

---

### Requirement F-11: Export Suite

**User Story:** As a Principal_Investigator, I want to export the experiment plan in multiple formats, so that I can share it with collaborators, submit it for procurement, and add it to my calendar.

#### Acceptance Criteria

1. THE Web_Client SHALL provide a PDF export that generates a formatted lab report including: hypothesis, QC results, all plan sections, safety assessment, and references using jsPDF and jsPDF-AutoTable, saved as `experiment_plan.pdf`
2. THE Web_Client SHALL provide a CSV export of the materials list with columns: name, catalog number, supplier, unit, quantity, unit cost (USD), total cost (USD), saved as `materials_list.csv`
3. THE Web_Client SHALL provide an iCal export that creates one calendar event per timeline phase with the phase description in the event body, saved as `experiment_timeline.ics`
4. THE Web_Client SHALL provide a DOCX export of the GPT-4o-generated grant Methods section saved as `methods_section.docx`
5. ALL four export formats SHALL be generated entirely client-side with no server call required
6. THE Web_Client SHALL display export buttons in a clearly labelled "Export" section accessible from the plan detail page

---

### Requirement F-12: Grant Methods Generator

**User Story:** As a Principal_Investigator, I want the Platform to rewrite my protocol as a formal grant Methods section, so that I can use it directly in NIH, NSF, or ERC funding applications.

#### Acceptance Criteria

1. THE Web_Client SHALL include a "Grant Language" tab in the plan viewer with a selector for grant body: NIH, NSF, or ERC
2. WHEN a scientist selects a grant body and clicks "Generate", THE API_Gateway SHALL call GPT-4o to rewrite the protocol as a formal Methods section in past tense, third person, 400–600 words, with all reagents cited with source and catalog number on first mention
3. THE generated Methods section SHALL include a statistical analysis paragraph specifying the test used, alpha level, power, and analysis software
4. WHEN `requires_iacuc` or `requires_irb` is true in the safety assessment, THE Grant_Generator SHALL include an institutional approval sentence in the Methods section
5. THE Web_Client SHALL display the generated Methods section as formatted text with a one-click copy-to-clipboard button
6. THE Web_Client SHALL include the Methods section text in the DOCX export produced by the Export Suite (F-11)

---

### Requirement F-13: Equipment Checklist

**User Story:** As a Principal_Investigator, I want a complete equipment checklist with availability tracking, so that I know what I need to acquire or book before starting the experiment.

#### Acceptance Criteria

1. THE Plan_Generator SHALL include an `equipment_required` array in the ExperimentPlan JSON, where each item contains: name, category, suggested model, estimated purchase cost in USD, `is_commonly_available` flag, core facility alternative (if applicable), and rental availability flag
2. THE Web_Client SHALL display the equipment list as a checklist where scientists can mark each item as "Have it", "Need to acquire", or "Using core facility"
3. WHEN a scientist marks an item's availability status, THE API_Gateway SHALL persist that status to the `lab_equipment` Supabase table keyed by lab identifier
4. WHEN the same scientist generates a new experiment plan, THE Web_Client SHALL pre-populate equipment availability based on previously saved `lab_equipment` records
5. THE Web_Client SHALL display a summary showing total equipment cost for items marked "Need to acquire" and a list of items requiring core facility booking
6. IF the equipment checklist cannot be persisted due to a Vector_Store error, THEN THE Web_Client SHALL display the checklist in read-only mode with a warning that availability status will not be saved

---

### Requirement F-15: Live Collaborative Review

**User Story:** As a Principal_Investigator, I want multiple team members to review the same experiment plan simultaneously, so that we can collaborate in real time without emailing plan versions back and forth.

#### Acceptance Criteria

1. WHEN a scientist opens a plan detail page, THE Web_Client SHALL join a Supabase Realtime_Channel for that plan and broadcast the user's presence (user ID, role, joined timestamp)
2. THE Web_Client SHALL display active reviewers as avatar initials in the top-right corner of the plan page, colour-coded by role (PI: purple, Postdoc: teal, Technician: green)
3. WHEN a reviewer is viewing a specific tab, THE Web_Client SHALL show a small coloured dot next to that tab's label indicating which reviewer is currently viewing it
4. WHEN a scientist submits a section annotation, THE Web_Client SHALL broadcast it via the Realtime_Channel so all other viewers see the floating comment bubble appear without page refresh
5. WHEN a review is submitted and inserted into the `scientist_reviews` table, THE Web_Client SHALL display the new review card in a live feed sidebar for all active viewers via Supabase Postgres Changes subscription
6. THE Vector_Store SHALL include a `plan_annotations` table with columns: id, plan_id, section, content, position_pct, author_id, author_role, created_at; with RLS enabled and Realtime enabled for INSERT events

---

### Requirement F-16: Plan Version History

**User Story:** As a Principal_Investigator, I want to see a history of all plan versions and compare them, so that I can track how the plan evolved and restore a previous version if needed.

#### Acceptance Criteria

1. WHEN an ExperimentPlan is first generated or regenerated, THE API_Gateway SHALL save a versioned snapshot to the `plan_versions` Supabase table with: experiment ID, auto-incremented version number, full plan JSON snapshot, change summary, and trigger type (`initial_generation`, `scientist_correction`, `hypothesis_edit`, or `manual_regen`)
2. WHEN two or more versions exist, THE Web_Client SHALL display a horizontal version rail at the top of the plan page showing each version node with version number, date, and trigger label
3. WHEN a scientist clicks a version node, THE Web_Client SHALL load and display that version's plan data
4. WHEN a scientist selects two version nodes, THE Web_Client SHALL enter diff mode and display section-by-section differences with additions highlighted green and removals highlighted red
5. WHEN a scientist clicks "Restore this version", THE API_Gateway SHALL save a new version snapshot with trigger type `manual_regen` and set it as the current plan
6. THE Vector_Store SHALL enforce a unique constraint on (experiment_id, version_number) in the `plan_versions` table and enable RLS

---

### Requirement F-17: Lab Notebook Template

**User Story:** As a Principal_Investigator, I want a pre-filled electronic lab notebook generated from my experiment plan, so that I can walk into the lab with a structured document ready for recording observations.

#### Acceptance Criteria

1. WHEN a scientist requests a lab notebook, THE Notebook_Generator SHALL call GPT-4o to produce a structured notebook JSON containing sections: header, objective, materials receipt log, protocol step checklist, raw data tables, statistical analysis, conclusions, and deviations log
2. THE materials receipt log section SHALL include a row for each reagent from the ExperimentPlan with pre-filled name, catalog number, and supplier, plus blank fields for lot number, expiry date, and actual supplier used
3. THE protocol step checklist section SHALL include each protocol step as a numbered checklist item with a blank observation field after each step
4. THE raw data tables section SHALL include pre-defined column headers derived from the ExperimentPlan validation criteria
5. THE Web_Client SHALL export the completed notebook template as a PDF using jsPDF, with blank underline fields for scientist handwriting or digital completion, saved as `lab_notebook.pdf`
6. IF the Notebook_Generator GPT-4o call fails, THEN THE API_Gateway SHALL return a structured error and THE Web_Client SHALL display a retry button without losing the current plan view
