"""
Learning Engine Component (RAG)
Handles feedback embeddings and similarity search for continuous improvement
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import Client
from app.services.openai_client import OpenAIClient


logger = logging.getLogger(__name__)


class FeedbackEmbedding:
    """Represents a feedback embedding with metadata"""
    
    def __init__(
        self,
        id: str,
        correction_text: str,
        hypothesis_domain: str,
        similarity: float,
        rating: int,
        created_at: str,
        original_issue: Optional[str] = None
    ):
        self.id = id
        self.correction_text = correction_text
        self.hypothesis_domain = hypothesis_domain
        self.similarity = similarity
        self.rating = rating
        self.created_at = created_at
        self.original_issue = original_issue


class LearningEngine:
    """RAG-based learning engine for continuous improvement"""
    
    def __init__(
        self,
        openai_client: OpenAIClient,
        supabase_client: Client
    ):
        """
        Initialize LearningEngine
        
        Args:
            openai_client: OpenAI client for embeddings
            supabase_client: Supabase client for vector storage
        """
        self.openai_client = openai_client
        self.supabase = supabase_client
        self.embedding_dimensions = 1536  # text-embedding-3-small
    
    async def embed_correction(
        self,
        correction_text: str,
        hypothesis_domain: str,
        scientist_id: str,
        plan_id: str,
        rating: int,
        original_issue: Optional[str] = None,
        review_id: Optional[str] = None
    ) -> str:
        """
        Generate embedding for correction and store in vector database
        
        Args:
            correction_text: The correction text to embed
            hypothesis_domain: Scientific domain
            scientist_id: ID of the scientist who provided correction
            plan_id: ID of the experiment plan
            rating: Rating given to the section (1-5)
            original_issue: Optional description of the original issue
            review_id: Optional review ID
        
        Returns:
            str: ID of the stored embedding
        
        Raises:
            Exception: If embedding generation or storage fails
        """
        try:
            # Generate embedding with retry logic
            embedding_vector = await self.openai_client.generate_embedding(
                text=correction_text,
                max_retries=2
            )
            
            # Verify dimensionality
            if len(embedding_vector) != self.embedding_dimensions:
                raise ValueError(
                    f"Expected {self.embedding_dimensions} dimensions, "
                    f"got {len(embedding_vector)}"
                )
            
            # Store in Supabase
            result = self.supabase.table("feedback_embeddings").insert({
                "review_id": review_id,
                "plan_id": plan_id,
                "scientist_id": scientist_id,
                "correction_text": correction_text,
                "original_issue": original_issue,
                "embedding": embedding_vector,
                "hypothesis_domain": hypothesis_domain,
                "rating": rating,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            embedding_id = result.data[0]["id"]
            logger.info(f"Stored feedback embedding {embedding_id} for domain {hypothesis_domain}")
            
            return embedding_id
        
        except Exception as e:
            logger.error(f"Failed to embed and store correction: {e}")
            raise Exception(f"Embedding generation failed: {e}")
    
    async def query_corrections(
        self,
        hypothesis: str,
        domain: str,
        top_k: int = 5,
        similarity_threshold: float = 0.75
    ) -> List[FeedbackEmbedding]:
        """
        Query similar corrections using cosine similarity
        
        Args:
            hypothesis: Scientific hypothesis text
            domain: Scientific domain
            top_k: Number of similar corrections to return
            similarity_threshold: Minimum cosine similarity (0-1)
        
        Returns:
            List[FeedbackEmbedding]: List of similar corrections sorted by similarity
        """
        try:
            # Generate query embedding
            query_text = f"{domain}: {hypothesis}"
            query_vector = await self.openai_client.generate_embedding(
                text=query_text,
                max_retries=2
            )
            
            # Convert similarity threshold to distance threshold
            # Cosine distance = 1 - cosine similarity
            distance_threshold = 1 - similarity_threshold
            
            # Perform similarity search using RPC function
            result = self.supabase.rpc(
                "match_feedback_embeddings",
                {
                    "query_embedding": query_vector,
                    "match_threshold": distance_threshold,
                    "match_count": top_k,
                    "filter_domain": domain
                }
            ).execute()
            
            # Parse results into FeedbackEmbedding objects
            corrections = []
            for row in result.data:
                # Convert distance back to similarity
                similarity = 1 - row["distance"]
                
                corrections.append(FeedbackEmbedding(
                    id=row["id"],
                    correction_text=row["correction_text"],
                    hypothesis_domain=row["hypothesis_domain"],
                    similarity=similarity,
                    rating=row["rating"],
                    created_at=row["created_at"],
                    original_issue=row.get("original_issue")
                ))
            
            logger.info(
                f"Found {len(corrections)} similar corrections for domain {domain} "
                f"(threshold: {similarity_threshold})"
            )
            
            return corrections
        
        except Exception as e:
            logger.error(f"Failed to query corrections: {e}")
            # Return empty list on failure - plan generation can proceed without corrections
            return []
    
    def build_few_shot_context(
        self,
        corrections: List[FeedbackEmbedding]
    ) -> str:
        """
        Build few-shot context string from corrections
        
        Args:
            corrections: List of feedback embeddings
        
        Returns:
            str: Formatted few-shot context for GPT-4o prompt
        """
        if not corrections:
            return ""
        
        context_parts = ["\n\nRELEVANT EXPERT CORRECTIONS FROM PRIOR PLANS:"]
        
        for i, correction in enumerate(corrections, 1):
            context_parts.append(f"\nExample {i} (Similarity: {correction.similarity:.2f}, Rating: {correction.rating}/5):")
            
            if correction.original_issue:
                context_parts.append(f"Original Issue: {correction.original_issue}")
            
            context_parts.append(f"Correction: {correction.correction_text}")
            context_parts.append("---")
        
        context_parts.append("\nApply these learnings to avoid similar issues in your plan generation.")
        
        return "\n".join(context_parts)


def get_learning_engine(
    openai_client: OpenAIClient,
    supabase_client: Client
) -> LearningEngine:
    """
    Factory function to create LearningEngine instance
    
    Args:
        openai_client: OpenAI client
        supabase_client: Supabase client
    
    Returns:
        LearningEngine: Configured engine instance
    """
    return LearningEngine(openai_client, supabase_client)
