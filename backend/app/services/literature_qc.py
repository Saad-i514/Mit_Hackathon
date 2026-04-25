"""
Literature Quality Control Engine
Searches scientific literature and assesses novelty
"""
import json
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.services.semantic_scholar import SemanticScholarClient
from app.services.serper import SerperClient
from app.services.openai_client import OpenAIClient
from app.models.responses import NoveltyAssessment, Paper, NoveltyClassification


logger = logging.getLogger(__name__)


class LiteratureQCEngine:
    """Assesses novelty of hypotheses against scientific literature"""
    
    def __init__(
        self,
        semantic_scholar_client: SemanticScholarClient,
        serper_client: SerperClient,
        openai_client: OpenAIClient
    ):
        """
        Initialize LiteratureQCEngine
        
        Args:
            semantic_scholar_client: Semantic Scholar API client
            serper_client: Serper web search client
            openai_client: OpenAI client for novelty classification
        """
        self.ss_client = semantic_scholar_client
        self.serper_client = serper_client
        self.openai_client = openai_client
        self.timeout = 30.0  # 30 second timeout
    
    async def assess_novelty(
        self,
        hypothesis: str,
        domain: str
    ) -> NoveltyAssessment:
        """
        Assess hypothesis novelty against literature
        
        Args:
            hypothesis: Scientific hypothesis text
            domain: Scientific domain
        
        Returns:
            NoveltyAssessment with classification and similar papers
        """
        start_time = time.time()
        
        try:
            # Run searches concurrently with timeout
            async with asyncio.timeout(self.timeout):
                ss_results, serper_results = await asyncio.gather(
                    self._search_semantic_scholar(hypothesis, domain),
                    self._search_serper(hypothesis, domain),
                    return_exceptions=True
                )
        
        except asyncio.TimeoutError:
            logger.warning(f"Literature search timeout after {self.timeout}s")
            return NoveltyAssessment(
                classification=NoveltyClassification.NOT_FOUND,
                similar_papers=[],
                search_duration=self.timeout,
                error="Search timeout exceeded - proceeding with plan generation"
            )
        
        # Handle exceptions from concurrent searches
        if isinstance(ss_results, Exception):
            logger.warning(f"Semantic Scholar search failed: {ss_results}")
            ss_results = []
        
        if isinstance(serper_results, Exception):
            logger.warning(f"Serper search failed: {serper_results}")
            serper_results = []
        
        # Merge and deduplicate results
        all_papers = self._merge_results(ss_results, serper_results)
        
        # Classify novelty using GPT-4o
        classification = await self._classify_novelty(hypothesis, all_papers)
        
        duration = time.time() - start_time
        
        return NoveltyAssessment(
            classification=classification,
            similar_papers=all_papers[:10],  # Top 10 most relevant
            search_duration=duration,
            error=None
        )
    
    async def _search_semantic_scholar(
        self,
        hypothesis: str,
        domain: str
    ) -> List[Paper]:
        """
        Search Semantic Scholar for relevant papers
        
        Args:
            hypothesis: Scientific hypothesis
            domain: Scientific domain
        
        Returns:
            List[Paper]: List of relevant papers
        """
        try:
            # Create search query from hypothesis
            query = f"{domain} {hypothesis[:150]}"
            
            results = await self.ss_client.search_papers(
                query=query,
                limit=20
            )
            
            papers = []
            for paper in results:
                papers.append(Paper(
                    title=paper.get("title", ""),
                    doi=paper.get("externalIds", {}).get("DOI"),
                    year=paper.get("year"),
                    citation_count=paper.get("citationCount"),
                    abstract=paper.get("abstract", ""),
                    url=paper.get("url")
                ))
            
            logger.info(f"Found {len(papers)} papers from Semantic Scholar")
            return papers
        
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []
    
    async def _search_serper(
        self,
        hypothesis: str,
        domain: str
    ) -> List[Paper]:
        """
        Search web for scientific content using Serper
        
        Args:
            hypothesis: Scientific hypothesis
            domain: Scientific domain
        
        Returns:
            List[Paper]: List of relevant papers from web search
        """
        try:
            query = f"{domain} {hypothesis[:150]} research paper"
            
            results = await self.serper_client.search_scientific(
                query=query,
                num_results=20
            )
            
            papers = []
            for result in results:
                # Extract paper information from search result
                papers.append(Paper(
                    title=result.get("title", ""),
                    doi=None,  # DOI not available from web search
                    year=None,  # Year not reliably available
                    citation_count=None,
                    abstract=result.get("snippet", ""),
                    url=result.get("link")
                ))
            
            logger.info(f"Found {len(papers)} results from Serper")
            return papers
        
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []
    
    def _merge_results(
        self,
        ss_papers: List[Paper],
        serper_papers: List[Paper]
    ) -> List[Paper]:
        """
        Merge and deduplicate papers from different sources
        
        Args:
            ss_papers: Papers from Semantic Scholar
            serper_papers: Papers from Serper
        
        Returns:
            List[Paper]: Merged and deduplicated papers
        """
        # Prioritize Semantic Scholar results (more structured)
        merged = list(ss_papers)
        
        # Add Serper results that don't duplicate SS results
        seen_titles = {p.title.lower() for p in ss_papers if p.title}
        
        for paper in serper_papers:
            if paper.title and paper.title.lower() not in seen_titles:
                merged.append(paper)
                seen_titles.add(paper.title.lower())
        
        # Sort by citation count (if available), then by year
        merged.sort(
            key=lambda p: (
                p.citation_count if p.citation_count else 0,
                p.year if p.year else 0
            ),
            reverse=True
        )
        
        return merged
    
    async def _classify_novelty(
        self,
        hypothesis: str,
        papers: List[Paper]
    ) -> NoveltyClassification:
        """
        Classify novelty using GPT-4o
        
        Args:
            hypothesis: Scientific hypothesis
            papers: List of similar papers found
        
        Returns:
            NoveltyClassification: not_found, similar_exists, or exact_match
        """
        if not papers:
            return NoveltyClassification.NOT_FOUND
        
        # Build summary of top papers
        papers_summary = "\n".join([
            f"- {p.title} ({p.year if p.year else 'N/A'}): {p.abstract[:200] if p.abstract else 'No abstract'}..."
            for p in papers[:5]
        ])
        
        prompt = f"""Analyze the novelty of this scientific hypothesis against existing literature.

Hypothesis: "{hypothesis}"

Similar papers found:
{papers_summary}

Classify the novelty:
- "exact_match": This exact hypothesis has already been tested in the literature
- "similar_exists": Similar research exists, but this hypothesis has novel aspects
- "not_found": No similar research found, hypothesis appears novel

Return JSON:
{{
  "classification": "exact_match" | "similar_exists" | "not_found",
  "reasoning": "brief explanation of your classification"
}}"""
        
        try:
            response = await self.openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            classification_str = result.get("classification", "not_found")
            
            # Map string to enum
            classification_map = {
                "exact_match": NoveltyClassification.EXACT_MATCH,
                "similar_exists": NoveltyClassification.SIMILAR_EXISTS,
                "not_found": NoveltyClassification.NOT_FOUND
            }
            
            return classification_map.get(classification_str, NoveltyClassification.NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Novelty classification failed: {e}")
            # Default to similar_exists if we have papers but classification failed
            return NoveltyClassification.SIMILAR_EXISTS if papers else NoveltyClassification.NOT_FOUND


def get_literature_qc_engine(
    semantic_scholar_client: SemanticScholarClient,
    serper_client: SerperClient,
    openai_client: OpenAIClient
) -> LiteratureQCEngine:
    """
    Factory function to create LiteratureQCEngine instance
    
    Args:
        semantic_scholar_client: Semantic Scholar client
        serper_client: Serper client
        openai_client: OpenAI client
    
    Returns:
        LiteratureQCEngine: Configured engine instance
    """
    return LiteratureQCEngine(semantic_scholar_client, serper_client, openai_client)
