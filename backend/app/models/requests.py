"""
Request models for API endpoints
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class GeneratePlanRequest(BaseModel):
    """Request model for generating an experiment plan"""
    hypothesis: str = Field(
        ...,
        description="Scientific hypothesis to generate experiment plan for",
        min_length=20,
        max_length=5000
    )

    @field_validator('hypothesis')
    @classmethod
    def validate_hypothesis(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Hypothesis cannot be empty or whitespace only")
        if len(v.strip()) < 20:
            raise ValueError("Hypothesis must be at least 20 characters long")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "hypothesis": "DMSO at 10% v/v will provide superior cryoprotection compared to glycerol for HeLa cells, resulting in ≥85% post-thaw viability measured by trypan blue exclusion."
            }
        }
    }


class ReviewSubmission(BaseModel):
    """Request model for submitting a plan review"""
    protocol_rating: int = Field(..., ge=1, le=5, description="Protocol rating 1-5")
    materials_rating: int = Field(..., ge=1, le=5, description="Materials rating 1-5")
    timeline_rating: int = Field(..., ge=1, le=5, description="Timeline rating 1-5")
    validation_rating: int = Field(..., ge=1, le=5, description="Validation rating 1-5")
    protocol_corrections: Optional[str] = Field(None, description="Protocol corrections text")
    materials_corrections: Optional[str] = Field(None, description="Materials corrections text")
    timeline_corrections: Optional[str] = Field(None, description="Timeline corrections text")
    validation_corrections: Optional[str] = Field(None, description="Validation corrections text")

    model_config = {
        "json_schema_extra": {
            "example": {
                "protocol_rating": 4,
                "materials_rating": 5,
                "timeline_rating": 4,
                "validation_rating": 5,
                "protocol_corrections": "Step 3 should specify pH 7.4 buffer",
                "materials_corrections": None,
                "timeline_corrections": None,
                "validation_corrections": None
            }
        }
    }
