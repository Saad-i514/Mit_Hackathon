"""
Clinical Trials Radar Service
Checks for overlapping clinical trials using ClinicalTrials.gov API v2
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

CT_BASE = "https://clinicaltrials.gov/api/v2/studies"
ACTIVE_STATUSES = "RECRUITING,ACTIVE_NOT_RECRUITING,NOT_YET_RECRUITING,COMPLETED"


class ClinicalTrialsClient:
    """Client for ClinicalTrials.gov API v2"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize ClinicalTrials client
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def check_clinical_trials(self, hypothesis: str) -> Dict[str, Any]:
        """
        Check for overlapping clinical trials
        
        Args:
            hypothesis: Scientific hypothesis text
            
        Returns:
            Dict with total_found and studies list
        """
        try:
            # Extract key terms from hypothesis
            key_terms = self._extract_key_terms(hypothesis)
            
            if not key_terms:
                logger.warning("No key terms extracted from hypothesis")
                return {"total_found": 0, "studies": []}
            
            # Query ClinicalTrials.gov API v2
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                query_term = " AND ".join(key_terms)
                
                response = await client.get(
                    CT_BASE,
                    params={
                        "query.term": query_term,
                        "filter.overallStatus": ACTIVE_STATUSES,
                        "pageSize": 5,
                        "fields": "NCTId,BriefTitle,OverallStatus,Phase,StartDate,Condition"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"ClinicalTrials.gov API error: {response.status_code}")
                    return {"total_found": 0, "studies": []}
                
                data = response.json()
                studies = data.get("studies", [])
                total_found = data.get("totalCount", 0)
                
                # Parse and format studies
                formatted_studies = []
                for study in studies[:3]:  # Return top 3
                    try:
                        protocol_section = study.get("protocolSection", {})
                        identification = protocol_section.get("identificationModule", {})
                        status_module = protocol_section.get("statusModule", {})
                        
                        nct_id = identification.get("nctId", "")
                        formatted_studies.append({
                            "nct_id": nct_id,
                            "title": identification.get("briefTitle", ""),
                            "status": status_module.get("overallStatus", ""),
                            "phase": status_module.get("phase", ""),
                            "url": f"https://clinicaltrials.gov/study/{nct_id}"
                        })
                    except (KeyError, TypeError) as e:
                        logger.warning(f"Error parsing study: {e}")
                        continue
                
                return {
                    "total_found": total_found,
                    "studies": formatted_studies
                }
                
        except httpx.TimeoutException:
            logger.error("ClinicalTrials.gov API timeout")
            return {"total_found": 0, "studies": [], "error": "API timeout"}
        except httpx.RequestError as e:
            logger.error(f"ClinicalTrials.gov API request error: {e}")
            return {"total_found": 0, "studies": [], "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error checking clinical trials: {e}")
            return {"total_found": 0, "studies": [], "error": str(e)}
    
    def _extract_key_terms(self, hypothesis: str) -> List[str]:
        """
        Extract key terms from hypothesis
        Simple implementation: split by spaces and filter common words
        
        Args:
            hypothesis: Scientific hypothesis text
            
        Returns:
            List of key terms
        """
        # Common words to exclude
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "be", "been",
            "will", "would", "could", "should", "may", "might", "must", "can",
            "that", "this", "these", "those", "which", "who", "what", "when",
            "where", "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "same",
            "so", "than", "too", "very", "just", "if", "then", "else", "do", "does"
        }
        
        # Split hypothesis into words and filter
        words = hypothesis.lower().split()
        key_terms = [
            word.strip(".,;:!?()[]{}\"'")
            for word in words
            if word.lower().strip(".,;:!?()[]{}\"'") not in stop_words
            and len(word.strip(".,;:!?()[]{}\"'")) > 3
        ]
        
        # Return top 5 key terms
        return key_terms[:5]


# Singleton instance
_clinical_trials_client: Optional[ClinicalTrialsClient] = None


def get_clinical_trials_client() -> ClinicalTrialsClient:
    """Get or create ClinicalTrials client singleton"""
    global _clinical_trials_client
    if _clinical_trials_client is None:
        _clinical_trials_client = ClinicalTrialsClient()
    return _clinical_trials_client
