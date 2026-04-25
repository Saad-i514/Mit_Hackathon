"""
Request models for API endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict


class GeneratePlanRequest(BaseModel):
    """Request model for generating an experiment plan"""
    hypothesis: str = Field(
        ...,
        description="Scientific hypothesis to generate experiment plan for",
        min_length=20,
        max_length=5000
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID (optional, will be extracted from JWT if not provided)"
    )
    
    @validator('hypothesis')
    def validate_hypothesis(cls, v):
        """Validate hypothesis is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Hypothesis cannot be empty or whitespace only")
        if len(v.strip()) < 20:
            raise ValueError("Hypothesis must be at least 20 characters long")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "hypothesis": "Paper-based electrochemical biosensors can detect glucose at concentrations below 1 mM with 95% accuracy"
            }
        }


class ReviewSubmission(BaseModel):
    """Request model for submitting a review"""
    ratings: Dict[str, int] = Field(
        ...,
        description="Ratings for each section (1-5 scale)"
    )
    corrections: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Corrections for specific sections"
    )
    
    @validator('ratings')
    def validate_ratings(cls, v):
        """Validate ratings are between 1 and 5"""
        required_sections = ['protocol', 'materials', 'budget', 'timeline', 'validation']
        
        for section in required_sections:
            if section not in v:
                raise ValueError(f"Missing rating for section: {section}")
            
            rating = v[section]
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                raise ValueError(f"Rating for {section} must be an integer between 1 and 5")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "ratings": {
                    "protocol": 5,
                    "materials": 4,
                    "budget": 4,
                    "timeline": 5,
                    "validation": 4
                },
                "corrections": {
                    "materials": {
                        "original_issue": "Catalog number ABC123 not found",
                        "correction": "Use catalog number XYZ789 from Thermo Fisher instead",
                        "section": "materials",
                        "item_index": "3"
                    }
                }
            }
        }
