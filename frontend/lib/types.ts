/**
 * TypeScript type definitions for the AI Scientist Platform
 * Matches backend Pydantic models for type safety
 */

// Enums
export enum NoveltyClassification {
  NOT_FOUND = "not_found",
  SIMILAR_EXISTS = "similar_exists",
  EXACT_MATCH = "exact_match"
}

export enum EventType {
  PROGRESS = "progress",
  ERROR = "error",
  COMPLETE = "complete",
  STAGE_START = "stage_start",
  STAGE_COMPLETE = "stage_complete"
}

// Base interfaces
export interface ValidationResult {
  is_valid: boolean;
  domain: string;
  testable_claim: string;
  clarification_questions: string[];
}

export interface Paper {
  title: string;
  authors?: string[];
  year?: number;
  abstract?: string;
  doi?: string;
  url?: string;
  venue?: string;
  source?: string;
  citation_count?: number;
}

export interface NoveltyAssessment {
  classification: NoveltyClassification;
  similar_papers: Paper[];
  search_duration: number;
}

// Protocol interfaces
export interface ProtocolStep {
  step_number: number;
  description: string;
  duration: string;
  critical_parameters: Record<string, string>;
  source: {
    title: string;
    doi?: string;
    url?: string;
  };
}

export interface ProtocolReference {
  title: string;
  doi?: string;
  url?: string;
  year: number;
}

export interface TroubleshootingItem {
  issue: string;
  solution: string;
}

export interface Protocol {
  steps: ProtocolStep[];
  references: ProtocolReference[];
  safety_considerations: string[];
  troubleshooting: TroubleshootingItem[];
}

// Materials interfaces
export interface Material {
  name: string;
  catalog_number: string;
  supplier: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  product_url?: string;
  verification_status: "verified" | "pending_verification";
  alternatives: string[];
  // PubChem enrichment fields
  pubchem_found?: boolean;
  cid?: number;
  cas_number?: string;
  molecular_weight?: number;
  molecular_formula?: string;
  ghs_codes?: string[];
  pubchem_url?: string;
}

export interface Materials {
  items: Material[];
  total_budget: number;
  currency: string;
}

// Timeline interfaces
export interface Phase {
  phase_number: number;
  name: string;
  duration_days: number;
  start_date: string;
  end_date: string;
  dependencies: number[];
  description: string;
}

export interface Timeline {
  phases: Phase[];
  total_duration_days: number;
  gantt_data: Record<string, any>;
}

// Validation interfaces
export interface Criterion {
  description: string;
  threshold: string;
  measurement_technique: string;
  expected_range?: string;
}

export interface ValidationCriteria {
  success_criteria: Criterion[];
  failure_criteria: Criterion[];
  validation_methods: string[];
}

// Metadata interface
export interface ExperimentPlanMetadata {
  generated_at: string;
  model_version: string;
  few_shot_examples_used: number;
  requires_expert_review: string[];
  hypothesis_quality_score?: number;
  hypothesis_refined?: boolean;
  protocols_io_matches?: Array<Record<string, any>>;
  reproducibility_assessment?: Record<string, any>;
  average_rating?: number;
}

// Main experiment plan interface
export interface ExperimentPlan {
  hypothesis: string;
  domain: string;
  novelty_classification: NoveltyClassification;
  protocol: Protocol;
  materials: Materials;
  timeline: Timeline;
  validation_criteria: ValidationCriteria;
  power_analysis?: PowerAnalysis;
  safety_assessment?: SafetyAssessment;
  variants?: ProtocolVariants;
  equipment_required?: Array<Record<string, any>>;
  metadata: ExperimentPlanMetadata;
}

// SSE Event interfaces
export interface SSEEventData {
  stage?: string;
  progress_percent?: number;
  message?: string;
  details?: Record<string, any>;
  description?: string;
  estimated_duration?: number;
  duration?: number;
  result_summary?: Record<string, any>;
  error_code?: string;
  plan_id?: string;
  total_duration?: number;
  summary?: Record<string, any>;
}

export interface SSEEvent {
  event_type: EventType;
  timestamp: string;
  data: SSEEventData;
}

// Pipeline state interface
export interface PipelineState {
  hypothesis: string;
  user_id: string;
  validation_result?: ValidationResult;
  domain?: string;
  novelty_assessment?: NoveltyAssessment;
  experiment_plan?: ExperimentPlan;
  error?: string;
  error_code?: string;
  error_stage?: string;
  current_stage: string;
  progress_events: Record<string, any>[];
  pipeline_start_time?: number;
  stage_durations: Record<string, number>;
  few_shot_examples_used: number;
  langsmith_run_id?: string;
}

// API Request interfaces
export interface GeneratePlanRequest {
  hypothesis: string;
}

export interface ReviewSubmission {
  protocol_rating: number;
  materials_rating: number;
  timeline_rating: number;
  validation_rating: number;
  protocol_corrections?: string;
  materials_corrections?: string;
  timeline_corrections?: string;
  validation_corrections?: string;
}

// API Response interfaces
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PlanSummary {
  id: string;
  status: string;
  domain?: string;
  total_budget?: number;
  created_at: string;
}

export interface ReviewResult {
  review_id: string;
  overall_rating: number;
  embeddings_generated: string;
}

// App State interfaces
export interface AppState {
  user: User | null;
  currentPlan: ExperimentPlan | null;
  pipelineState: PipelineState | null;
  progressEvents: SSEEvent[];
  isGenerating: boolean;
  error: string | null;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
}

// Component Props interfaces
export interface HypothesisInputProps {
  onSubmit: (hypothesis: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export interface PipelineProgressProps {
  events: SSEEvent[];
  currentStage: string;
}

export interface ExperimentPlanViewerProps {
  plan: ExperimentPlan;
  readonly?: boolean;
}

export interface MaterialListProps {
  materials: Materials;
}

export interface TimelineGanttProps {
  timeline: Timeline;
}

export interface ReviewPanelProps {
  plan: ExperimentPlan;
  onSubmit: (review: ReviewSubmission) => void;
  isSubmitting: boolean;
}

// SSE Hook interfaces
export interface SSEConnection {
  connect: (url: string, onMessage: (event: SSEEvent) => void) => void;
  disconnect: () => void;
  isConnected: boolean;
}

export interface UseSSEResult {
  connect: (url: string, onMessage: (event: SSEEvent) => void) => void;
  disconnect: () => void;
  isConnected: boolean;
  error: string | null;
}

// API Client interfaces
export interface APIClientConfig {
  baseURL: string;
  timeout?: number;
}

export interface APIError {
  error_code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  request_id?: string;
}

// Environment configuration
export interface Config {
  apiUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
}

// Form interfaces
export interface HypothesisFormData {
  hypothesis: string;
}

export interface LoginFormData {
  email: string;
  password: string;
}

export interface SignupFormData {
  email: string;
  password: string;
  confirmPassword: string;
  name?: string;
}

// Navigation interfaces
export interface NavItem {
  title: string;
  href: string;
  icon?: React.ComponentType;
  description?: string;
}

export interface BreadcrumbItem {
  title: string;
  href?: string;
}

// Loading and error states
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  error?: APIError | Error;
  retry?: () => void;
}

// Utility types
export type PlanStatus = "draft" | "generating" | "completed" | "failed";
export type StageType = "validation" | "literature_qc" | "plan_generation";
export type RatingValue = 1 | 2 | 3 | 4 | 5;

// ============================================================================
// Advanced Features Types (Phase 6)
// ============================================================================

// Safety Assessment Types
export interface HazardousReagent {
  name: string;
  ghs_codes: string[];
  hazard: string;
  ppe_addition: string;
  disposal: string;
}

export interface SafetyAssessment {
  bsl_level: number; // 1-4
  bsl_rationale: string;
  requires_iacuc: boolean;
  requires_irb: boolean;
  requires_biosafety_committee: boolean;
  ppe_required: string[];
  hazardous_reagents: HazardousReagent[];
  waste_disposal: Record<string, string>;
  emergency_contacts: string[];
}

// Protocol Variants Types
export interface ProtocolVariant {
  name: string; // "Budget", "Standard", "Premium"
  total_budget: number;
  timeline_days: number;
  description: string;
  materials: Materials;
  protocol_modifications: string[];
}

export interface ProtocolVariants {
  budget: ProtocolVariant;
  standard: ProtocolVariant;
  premium: ProtocolVariant;
}

// Power Analysis Types
export interface PowerAnalysis {
  test_type: string; // "t-test", "ANOVA", "chi-squared", "log-rank"
  effect_size: number;
  alpha: number;
  power: number;
  sample_size: number;
  interpretation: string;
}

// Equipment Types
export interface EquipmentItem {
  equipment: string;
  has_item: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Plan Version Types
export interface PlanVersion {
  version_number: number;
  plan_snapshot?: ExperimentPlan;
  change_summary?: string;
  triggered_by: "initial_generation" | "scientist_correction" | "hypothesis_edit" | "manual_regen";
  created_at: string;
}

// Plan Annotation Types
export interface PlanAnnotation {
  id: string;
  plan_id: string;
  section: string;
  content: string;
  position_pct?: number;
  author_id?: string;
  author_role?: string;
  created_at: string;
}

// Clinical Trial Types
export interface ClinicalTrialStudy {
  nct_id: string;
  title: string;
  status: string;
  phase: string;
  url: string;
}

export interface ClinicalTrialResult {
  total_found: number;
  studies: ClinicalTrialStudy[];
  error?: string;
}

// Grant Methods Types
export interface GrantMethodsResult {
  grant_body: "NIH" | "NSF" | "ERC";
  methods_text: string;
  generated_at: string;
}

// Notebook Template Types
export interface NotebookSection {
  title: string;
  content: string;
  fields?: Record<string, string>;
}

export interface NotebookTemplate {
  title: string;
  hypothesis: string;
  date: string;
  sections: NotebookSection[];
  materials_log: Array<{
    material: string;
    lot_number: string;
    received_date: string;
    expiry_date: string;
  }>;
  protocol_checklist: Array<{
    step: string;
    completed: boolean;
    observations: string;
    timestamp: string;
  }>;
  data_tables: Array<{
    table_name: string;
    columns: string[];
    rows: Array<Record<string, any>>;
  }>;
  statistical_analysis: {
    test_type: string;
    results: string;
    interpretation: string;
  };
  conclusions: string;
  deviations: string[];
}

// Component Props for Advanced Features
export interface PowerCalculatorProps {
  initialValues?: PowerAnalysis;
  onCalculate: (analysis: PowerAnalysis) => void;
}

export interface ProtocolFlowchartProps {
  protocol: Protocol;
  onNodeClick?: (stepNumber: number) => void;
}

export interface GanttTimelineProps {
  timeline: Timeline;
  onTaskClick?: (phaseNumber: number) => void;
  onReschedule?: (phaseNumber: number, newStartDate: string) => void;
}

export interface ExportSuiteProps {
  plan: ExperimentPlan;
  onExport: (format: "pdf" | "csv" | "ical" | "docx") => void;
}

export interface GrantMethodsProps {
  planId: string;
  onGenerate: (grantBody: "NIH" | "NSF" | "ERC") => void;
}

export interface EquipmentChecklistProps {
  planId: string;
  equipment: string[];
  onUpdate: (equipment: string, hasItem: boolean, notes?: string) => void;
}

export interface SafetyTabProps {
  safetyAssessment: SafetyAssessment;
}

export interface CollaborativeReviewProps {
  planId: string;
  onAnnotate: (annotation: Omit<PlanAnnotation, "id" | "created_at">) => void;
}

export interface VersionHistoryProps {
  planId: string;
  versions: PlanVersion[];
  onRestore: (versionNumber: number) => void;
  onCompare: (version1: number, version2: number) => void;
}

export interface VariantSelectorProps {
  variants: ProtocolVariants;
  selectedVariant: "budget" | "standard" | "premium";
  onSelect: (variant: "budget" | "standard" | "premium") => void;
}

export interface ClinicalTrialsBadgeProps {
  clinicalTrials: ClinicalTrialResult;
}

export interface NotebookExportProps {
  planId: string;
  onGenerate: () => void;
  onExport: (format: "pdf") => void;
}