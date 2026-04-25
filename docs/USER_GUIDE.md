# User Guide

## Overview

The AI Scientist Platform transforms natural-language scientific hypotheses into fully operational experiment plans. Each plan includes a grounded protocol, materials list with real catalog numbers, budget breakdown, timeline, and validation criteria.

---

## Getting Started

### 1. Create an account

Navigate to the platform and click **Sign Up**. You can register with:
- Email and password
- Google OAuth
- GitHub OAuth

### 2. Submit your first hypothesis

Click **New Plan** in the navigation. You'll see the hypothesis input form.

---

## Writing Effective Hypotheses

A good hypothesis for the platform should:

- **Be specific and testable** — state a measurable prediction
- **Identify the system** — specify the organism, cell type, or model system
- **State the intervention** — what you're changing or testing
- **Predict the outcome** — what you expect to observe

### Example hypotheses by domain

**Molecular Biology**
> "Overexpression of CRISPR-Cas9 with sgRNA targeting the PCSK9 gene in HepG2 cells will reduce LDL receptor degradation by at least 60% compared to scrambled sgRNA controls, as measured by flow cytometry and Western blot."

**Cell Biology**
> "Treatment of MCF-7 breast cancer cells with 10 µM tamoxifen for 48 hours will induce G1 cell cycle arrest and increase apoptosis by 30% compared to DMSO vehicle controls, measured by propidium iodide staining and Annexin V assay."

**Neuroscience**
> "Chronic administration of 10 mg/kg fluoxetine for 28 days in C57BL/6 mice will increase hippocampal neurogenesis by 40% compared to saline controls, as measured by BrdU incorporation and doublecortin immunostaining."

**Immunology**
> "Co-culture of CD8+ T cells with PD-L1-overexpressing tumor cells will reduce IFN-γ secretion by 50% compared to PD-L1-negative controls, reversible by anti-PD-1 checkpoint blockade at 10 µg/mL."

**Biochemistry**
> "Substitution of Asp189 with Ala in trypsin will reduce catalytic efficiency (kcat/Km) for Arg-containing substrates by at least 10-fold compared to wild-type, as measured by fluorogenic substrate assay."

### Character limit

Hypotheses are limited to **5,000 characters**. The input form shows a live character count.

---

## Understanding the Pipeline

After submitting, you'll see real-time progress through three stages:

### Stage 1: Hypothesis Validation (0–33%)

The system:
- Extracts the scientific domain from 20 supported domains
- Identifies the testable claim
- Checks for ambiguity and generates clarification questions if needed

If your hypothesis is flagged as ambiguous, you'll see clarification questions. You can revise and resubmit.

### Stage 2: Literature QC (33–66%)

The system:
- Searches Semantic Scholar for related publications
- Supplements with web search via Serper
- Classifies novelty as one of:
  - **Not found** — no closely related work found
  - **Similar exists** — related work exists but your hypothesis is distinct
  - **Exact match** — very similar work already published

The novelty classification is informational — the platform generates a plan regardless of classification.

### Stage 3: Plan Generation (66–100%)

The system generates a structured experiment plan using GPT-4o, incorporating:
- Few-shot examples from similar expert-reviewed plans (if available)
- Protocol grounding in published sources
- Real catalog numbers from Thermo Fisher Scientific and Sigma-Aldrich

---

## Reading Your Experiment Plan

The generated plan has five sections:

### Protocol

Step-by-step experimental procedure with:
- Numbered steps with detailed instructions
- Critical parameters (temperature, concentration, pH, duration)
- Source references (protocols.io, bio-protocol.org, or publications with DOI)
- Safety considerations
- Troubleshooting guidance

### Materials

Complete materials list with:
- Catalog numbers from Thermo Fisher Scientific or Sigma-Aldrich
- 2024-2025 pricing
- Supplier links
- Verification status (verified or pending_verification)
- Alternative suppliers where available

### Budget

Line-item budget breakdown with:
- Unit prices and quantities
- Total per item
- Grand total
- Budget notes

### Timeline

Phased timeline with:
- Phase names and durations
- Start and end dates
- Dependencies between phases
- Gantt-style visualization

### Validation Criteria

Quantitative success and failure criteria with:
- Measurable thresholds (e.g., "≥ 60% reduction in protein expression")
- Statistical methods (t-test, ANOVA, etc.)
- Expected result ranges from literature
- Failure criteria indicating when to stop the experiment

---

## Expert Review Flags

Plans may include expert review flags in the header:

- **Unverified catalog numbers** — catalog numbers marked `pending_verification` should be confirmed with the supplier before ordering
- **Missing critical parameters** — protocol steps where temperature, concentration, or timing was not specified
- **Vague validation criteria** — success criteria that lack quantitative thresholds

These flags are advisory. Review flagged items before proceeding with the experiment.

---

## Submitting a Review

After reviewing a plan, click **Review This Plan** to submit expert feedback.

Rate each section 1–5:
- **1** — Major issues, not usable
- **2** — Significant problems
- **3** — Acceptable with revisions
- **4** — Good, minor issues
- **5** — Excellent, ready to use

For each section, you can provide text corrections. These corrections are embedded and used to improve future plans for similar hypotheses (RAG learning loop).

---

## Supported Scientific Domains

| Domain | Example Hypothesis Topics |
|--------|--------------------------|
| Molecular Biology | Gene expression, PCR, cloning, CRISPR |
| Cell Biology | Cell culture, microscopy, flow cytometry |
| Biochemistry | Enzyme kinetics, protein purification, assays |
| Genetics | Inheritance, mutation analysis, genome editing |
| Neuroscience | Behavior, electrophysiology, neuroimaging |
| Immunology | Immune cell function, cytokines, antibodies |
| Microbiology | Bacterial growth, infection, antimicrobials |
| Pharmacology | Drug efficacy, dose-response, toxicity |
| Biophysics | Protein structure, membrane dynamics |
| Structural Biology | Crystallography, cryo-EM, NMR |
| Genomics | Sequencing, variant analysis, epigenomics |
| Proteomics | Mass spectrometry, protein identification |
| Metabolomics | Metabolite profiling, pathway analysis |
| Ecology | Population dynamics, species interactions |
| Evolutionary Biology | Phylogenetics, selection, adaptation |
| Developmental Biology | Embryogenesis, differentiation, organoids |
| Physiology | Organ function, homeostasis, signaling |
| Pathology | Disease mechanisms, biomarkers, histology |
| Bioinformatics | Sequence analysis, computational modeling |
| Synthetic Biology | Genetic circuits, metabolic engineering |

---

## Performance Expectations

| Stage | Expected Duration |
|-------|------------------|
| Hypothesis validation | < 5 seconds |
| Literature QC | < 30 seconds |
| Plan generation | < 60 seconds |
| **Total end-to-end** | **< 90 seconds (P95)** |

---

## Tips for Best Results

1. **Be specific about quantities** — include concentrations, cell counts, and timepoints
2. **Name your model system** — specify the organism, cell line, or in vitro system
3. **State your measurement method** — mention the assay or technique you plan to use
4. **Include a comparison** — specify your control condition
5. **Review the protocol sources** — click through to the referenced protocols to verify they match your lab's capabilities
6. **Check catalog numbers** — always verify catalog numbers on the supplier website before ordering, especially those marked `pending_verification`
