"""
Response models for API endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NoveltyClassification(str, Enum):
    """Novelty classification for literature QC"""
    NOT_FOUND = "not_found"
    SIMILAR_EXISTS = "similar_exists"
    EXACT_MATCH = "exact_match"


class ValidationStatus(str, Enum):
    """Validation status for hypotheses"""
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_CLARIFICATION = "needs_clarification"


class PlanStatus(str, Enum):
    """Status of experiment plan"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ValidationResult(BaseModel):
    """Result of hypothesis validation"""
    is_valid: bool
    domain: Optional[str] = None
    testable_claim: Optional[str] = None
    clarification_questions: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    reasoning: Optional[str] = None


class Paper(BaseModel):
    """Scientific paper from literature search"""
    title: str
    authors: Optional[List[str]] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    citation_count: Optional[int] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    venue: Optional[str] = None
    source: Optional[str] = None


class NoveltyAssessment(BaseModel):
    """Result of literature quality control"""
    classification: NoveltyClassification
    similar_papers: List[Paper] = Field(default_factory=list)
    search_duration: float
    error: Optional[str] = None


class ProgressEvent(BaseModel):
    """Progress event for SSE streaming"""
    stage: str
    status: str
    completion_percentage: int
    message: str
    timestamp: str


class Reference(BaseModel):
    """Reference to a protocol or publication"""
    title: str
    doi: Optional[str] = None
    url: Optional[str] = None
    year: Optional[int] = None


class ProtocolStep(BaseModel):
    """Single step in experiment protocol"""
    step_number: int
    description: str
    duration: str
    critical_parameters: Dict[str, str] = Field(default_factory=dict)
    source: Optional[Reference] = None


class Material(BaseModel):
    """Material/reagent for experiment"""
    name: str
    catalog_number: str
    supplier: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    product_url: Optional[str] = None
    verification_status: str = "verified"
    pubchem_found: Optional[bool] = None
    cid: Optional[int] = None
    cas_number: Optional[str] = None
    molecular_weight: Optional[float] = None
    molecular_formula: Optional[str] = None
    ghs_codes: List[str] = Field(default_factory=list)
    pubchem_url: Optional[str] = None
    alternatives: List[Any] = Field(default_factory=list)


class Phase(BaseModel):
    """Phase in experiment timeline"""
    phase_number: int
    name: str
    duration_days: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    dependencies: List[Any] = Field(default_factory=list)
    description: str


class Criterion(BaseModel):
    """Success or failure criterion"""
    description: str
    threshold: str
    measurement_technique: str
    expected_range: Optional[str] = None
    literature_precedent: Optional[Reference] = None


class Protocol(BaseModel):
    """Complete protocol section"""
    steps: List[ProtocolStep]
    references: List[Reference] = Field(default_factory=list)
    safety_considerations: List[str] = Field(default_factory=list)
    troubleshooting: List[Dict[str, str]] = Field(default_factory=list)


class Materials(BaseModel):
    """Complete materials section"""
    items: List[Material]
    total_budget: float
    currency: str = "USD"


class Timeline(BaseModel):
    """Complete timeline section"""
    phases: List[Phase]
    total_duration_days: int
    gantt_data: Optional[Dict[str, Any]] = None


class ValidationCriteria(BaseModel):
    """Complete validation criteria section"""
    success_criteria: List[Criterion]
    failure_criteria: List[Criterion]
    validation_methods: List[str] = Field(default_factory=list)


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int
    
    @property
    def has_next(self) -> bool:
        """Check if there are more items"""
        return self.offset + self.limit < self.total
    
    @property
    def has_previous(self) -> bool:
        """Check if there are previous items"""
        return self.offset > 0


class ExperimentPlanMetadata(BaseModel):
    """Metadata for experiment plan"""
    model_config = ConfigDict(protected_namespaces=())

    generated_at: str
    model_version: str = "gpt-4o"
    few_shot_examples_used: int = 0
    requires_expert_review: List[str] = Field(default_factory=list)
    hypothesis_quality_score: Optional[int] = None
    hypothesis_refined: bool = False
    protocols_io_matches: List[Dict[str, Any]] = Field(default_factory=list)
    reproducibility_assessment: Optional[Dict[str, Any]] = None
    average_rating: Optional[float] = None


class ExperimentPlan(BaseModel):
    """Complete experiment plan"""
    hypothesis: str
    domain: str
    novelty_classification: NoveltyClassification
    protocol: Protocol
    materials: Materials
    timeline: Timeline
    validation_criteria: ValidationCriteria
    power_analysis: Optional[Dict[str, Any]] = None
    safety_assessment: Optional[Dict[str, Any]] = None
    variants: Optional[Dict[str, Any]] = None
    equipment_required: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: ExperimentPlanMetadata


class ExperimentPlanResponse(BaseModel):
    """Response for experiment plan retrieval"""
    model_config = ConfigDict(protected_namespaces=())

    id: str
    user_id: str
    hypothesis_id: str
    plan_data: ExperimentPlan
    novelty_classification: NoveltyClassification
    model_version: str
    few_shot_examples_used: int
    requires_expert_review: List[str]
    status: PlanStatus
    generated_at: str
    average_rating: Optional[float] = None


class ReviewResponse(BaseModel):
    """Response for review submission"""
    review_id: str
    plan_id: str
    overall_rating: float
    submitted_at: str
    embeddings_generated: int


class ErrorResponse(BaseModel):
    """Structured error response"""
    error_code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    request_id: Optional[str] = None
