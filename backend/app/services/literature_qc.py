"""
Literature Quality Control Engine
Searches scientific literature and assesses novelty
"""
import json
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
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
        self.http_timeout = 12.0
    
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
                (
                    ss_results,
                    serper_results,
                    openalex_results,
                    pubmed_results,
                    europe_pmc_results,
                    biorxiv_results,
                ) = await asyncio.gather(
                    self._search_semantic_scholar(hypothesis, domain),
                    self._search_serper(hypothesis, domain),
                    self._search_openalex(hypothesis, domain),
                    self._search_pubmed(hypothesis, domain),
                    self._search_europe_pmc(hypothesis, domain),
                    self._search_biorxiv(hypothesis, domain),
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
        
        for name, result in (
            ("OpenAlex", openalex_results),
            ("PubMed", pubmed_results),
            ("EuropePMC", europe_pmc_results),
            ("bioRxiv", biorxiv_results),
        ):
            if isinstance(result, Exception):
                logger.warning("%s search failed: %s", name, result)

        # Merge and deduplicate results from all sources.
        all_papers = self._merge_results(
            ss_papers=ss_results if isinstance(ss_results, list) else [],
            serper_papers=serper_results if isinstance(serper_results, list) else [],
            openalex_papers=openalex_results if isinstance(openalex_results, list) else [],
            pubmed_papers=pubmed_results if isinstance(pubmed_results, list) else [],
            europe_pmc_papers=europe_pmc_results if isinstance(europe_pmc_results, list) else [],
            biorxiv_papers=biorxiv_results if isinstance(biorxiv_results, list) else [],
        )
        
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
                # Extract author names from the authors list of objects
                raw_authors = paper.get("authors") or []
                author_names = [a.get("name", "") for a in raw_authors if a.get("name")]
                papers.append(Paper(
                    title=paper.get("title", ""),
                    authors=author_names if author_names else None,
                    doi=paper.get("externalIds", {}).get("DOI"),
                    year=paper.get("year"),
                    citation_count=paper.get("citationCount"),
                    abstract=paper.get("abstract", ""),
                    url=paper.get("url"),
                    source="SemanticScholar"
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
                    url=result.get("link"),
                    source="Serper"
                ))
            
            logger.info(f"Found {len(papers)} results from Serper")
            return papers
        
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []
    
    async def _search_openalex(self, hypothesis: str, domain: str) -> List[Paper]:
        """Search OpenAlex public works API."""
        query = f"{domain} {hypothesis[:150]}".strip()
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                response = await client.get(
                    "https://api.openalex.org/works",
                    params={
                        "search": query,
                        "per-page": 10,
                        "sort": "cited_by_count:desc",
                    },
                )
            if response.status_code != 200:
                return []
            works = response.json().get("results", [])
            papers: List[Paper] = []
            for w in works:
                papers.append(
                    Paper(
                        title=w.get("display_name", ""),
                        doi=(w.get("doi") or "").replace("https://doi.org/", "") or None,
                        year=w.get("publication_year"),
                        citation_count=w.get("cited_by_count"),
                        abstract=self._openalex_abstract(w),
                        url=w.get("id"),
                        source="OpenAlex",
                    )
                )
            return papers
        except Exception as exc:
            logger.warning("OpenAlex search failed: %s", exc)
            return []

    async def _search_pubmed(self, hypothesis: str, domain: str) -> List[Paper]:
        """Search PubMed via eutils (esearch + esummary)."""
        query = f"{domain} {hypothesis[:120]}".strip()
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                search = await client.get(
                    f"{base}/esearch.fcgi",
                    params={"db": "pubmed", "term": query, "retmax": 10, "retmode": "json"},
                )
                ids = ((search.json().get("esearchresult") or {}).get("idlist")) or []
                if not ids:
                    return []
                summary = await client.get(
                    f"{base}/esummary.fcgi",
                    params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                )
            payload = summary.json()
            result = payload.get("result") or {}
            papers: List[Paper] = []
            for pid in ids:
                item = result.get(pid) or {}
                papers.append(
                    Paper(
                        title=item.get("title", ""),
                        doi=self._extract_pubmed_doi(item),
                        year=self._extract_year(item.get("pubdate")),
                        citation_count=None,
                        abstract=None,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
                        source="PubMed",
                    )
                )
            return papers
        except Exception as exc:
            logger.warning("PubMed search failed: %s", exc)
            return []

    async def _search_europe_pmc(self, hypothesis: str, domain: str) -> List[Paper]:
        """Search Europe PMC REST API."""
        query = f"{domain} {hypothesis[:120]}".strip()
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                response = await client.get(
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                    params={"query": query, "format": "json", "pageSize": 10},
                )
            if response.status_code != 200:
                return []
            items = ((response.json().get("resultList") or {}).get("result")) or []
            papers: List[Paper] = []
            for it in items:
                doi = it.get("doi")
                papers.append(
                    Paper(
                        title=it.get("title", ""),
                        doi=doi,
                        year=self._extract_year(it.get("pubYear")),
                        citation_count=self._to_int(it.get("citedByCount")),
                        abstract=it.get("abstractText"),
                        url=it.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url")
                        if isinstance(it.get("fullTextUrlList"), dict)
                        else None,
                        source="EuropePMC",
                    )
                )
            return papers
        except Exception as exc:
            logger.warning("Europe PMC search failed: %s", exc)
            return []

    async def _search_biorxiv(self, hypothesis: str, domain: str) -> List[Paper]:
        """Search bioRxiv preprints (best effort)."""
        query_terms = [t for t in f"{domain} {hypothesis}".lower().split() if len(t) > 3][:5]
        url = "https://api.biorxiv.org/details/biorxiv/2024-01-01/2030-01-01/0"
        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                response = await client.get(url)
            if response.status_code != 200:
                return []
            collection = response.json().get("collection", [])
            papers: List[Paper] = []
            for item in collection:
                title = (item.get("title") or "").lower()
                if not any(term in title for term in query_terms):
                    continue
                papers.append(
                    Paper(
                        title=item.get("title", ""),
                        doi=item.get("doi"),
                        year=self._extract_year(item.get("date")),
                        citation_count=None,
                        abstract=item.get("abstract"),
                        url=f"https://www.biorxiv.org/content/{item.get('doi')}",
                        source="bioRxiv",
                    )
                )
                if len(papers) >= 10:
                    break
            return papers
        except Exception as exc:
            logger.warning("bioRxiv search failed: %s", exc)
            return []

    def _merge_results(
        self,
        ss_papers: List[Paper],
        serper_papers: List[Paper],
        openalex_papers: List[Paper],
        pubmed_papers: List[Paper],
        europe_pmc_papers: List[Paper],
        biorxiv_papers: List[Paper],
    ) -> List[Paper]:
        """
        Merge and deduplicate papers from different sources
        
        Args:
            ss_papers: Papers from Semantic Scholar
            serper_papers: Papers from Serper
        
        Returns:
            List[Paper]: Merged and deduplicated papers
        """
        merged: List[Paper] = []
        seen_doi = set()
        seen_titles = set()

        all_sources = (
            ss_papers + openalex_papers + pubmed_papers + europe_pmc_papers + biorxiv_papers + serper_papers
        )

        for paper in all_sources:
            title_key = (paper.title or "").strip().lower()
            doi_key = (paper.doi or "").strip().lower()
            if doi_key and doi_key in seen_doi:
                continue
            if title_key and title_key in seen_titles:
                continue
            if doi_key:
                seen_doi.add(doi_key)
            if title_key:
                seen_titles.add(title_key)
            merged.append(paper)
        
        # Sort by citation count (if available), then by year
        merged.sort(
            key=lambda p: (
                p.citation_count if p.citation_count else 0,
                p.year if p.year else 0
            ),
            reverse=True
        )
        
        return merged

    def _openalex_abstract(self, work: Dict[str, Any]) -> Optional[str]:
        inverted = work.get("abstract_inverted_index")
        if not isinstance(inverted, dict):
            return None
        words: Dict[int, str] = {}
        for token, positions in inverted.items():
            for pos in positions:
                words[int(pos)] = token
        if not words:
            return None
        return " ".join(words[i] for i in sorted(words.keys()))

    def _extract_pubmed_doi(self, item: Dict[str, Any]) -> Optional[str]:
        ids = item.get("articleids") or []
        for entry in ids:
            if entry.get("idtype") == "doi":
                return entry.get("value")
        return None

    def _extract_year(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        text = str(value)
        for chunk in text.replace("/", "-").split("-"):
            if len(chunk) == 4 and chunk.isdigit():
                year = int(chunk)
                if 1800 <= year <= datetime.now(timezone.utc).year + 1:
                    return year
        return None

    def _to_int(self, value: Any) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except Exception:
            return None
    
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
