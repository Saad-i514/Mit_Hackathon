"""
OpenAI API client with retry logic and error handling
"""
from openai import AsyncOpenAI, RateLimitError, APIError
from typing import List, Dict, Any, Optional
import asyncio
import logging
from app.config import settings


logger = logging.getLogger(__name__)


class OpenAIClient:
    """Async OpenAI client with retry logic"""
    
    def __init__(self):
        """Initialize AsyncOpenAI client"""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=60.0,
            max_retries=2
        )
        self.model = settings.openai_model
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a chat completion with retry logic
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            response_format: Optional response format (e.g., {"type": "json_object"})
        
        Returns:
            str: Response content from the model
        
        Raises:
            RateLimitError: If rate limit is exceeded after retries
            APIError: If API call fails after retries
        """
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = await self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts")
                    raise
            
            except APIError as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"API error after {max_retries} attempts: {e}")
                    raise
            
            except Exception as e:
                logger.error(f"Unexpected error in chat completion: {e}")
                raise
    
    async def generate_embedding(
        self,
        text: str,
        max_retries: int = 2
    ) -> List[float]:
        """
        Generate embedding for text with retry logic
        
        Args:
            text: Text to embed
            max_retries: Maximum number of retry attempts
        
        Returns:
            List[float]: Embedding vector (1536 dimensions)
        
        Raises:
            Exception: If embedding generation fails after retries
        """
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text,
                    encoding_format="float"
                )
                
                embedding = response.data[0].embedding
                
                # Verify dimensionality
                if len(embedding) != self.embedding_dimensions:
                    raise ValueError(
                        f"Expected {self.embedding_dimensions} dimensions, got {len(embedding)}"
                    )
                
                return embedding
            
            except Exception as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Embedding error, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Embedding generation failed after {max_retries + 1} attempts: {e}")
                    raise Exception(f"Embedding generation failed: {e}")


# Global OpenAI client instance
openai_client = OpenAIClient()


def get_openai_client() -> OpenAIClient:
    """Get the global OpenAI client instance"""
    return openai_client
