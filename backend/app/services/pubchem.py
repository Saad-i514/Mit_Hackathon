"""
PubChem reagent enrichment service.
"""
import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class PubChemClient:
    """Fetches chemical metadata for reagent names."""

    def __init__(self) -> None:
        self.timeout = 10.0

    async def enrich_reagent(self, name: str) -> Dict[str, Any]:
        """Enrich reagent with CID, MW, CAS and hazard hints."""
        cleaned = (name or "").strip()
        if not cleaned:
            return {"name": name, "pubchem_found": False}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                cid_resp = await client.get(f"{PUBCHEM_BASE}/compound/name/{cleaned}/cids/JSON")
                if cid_resp.status_code != 200:
                    return {"name": cleaned, "pubchem_found": False}
                cid_list = (cid_resp.json().get("IdentifierList") or {}).get("CID") or []
                if not cid_list:
                    return {"name": cleaned, "pubchem_found": False}
                cid = cid_list[0]

                props = "MolecularWeight,MolecularFormula,IUPACName"
                props_resp = await client.get(
                    f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{props}/JSON"
                )
                props_data = ((props_resp.json().get("PropertyTable") or {}).get("Properties") or [{}])[0]

                cas_resp = await client.get(f"{PUBCHEM_BASE}/compound/cid/{cid}/xrefs/RN/JSON")
                cas_info = ((cas_resp.json().get("InformationList") or {}).get("Information") or [{}])[0]
                cas_numbers = cas_info.get("RN") or []

                # Classification endpoint shape varies; keep best-effort extraction.
                cls_resp = await client.get(f"{PUBCHEM_BASE}/compound/cid/{cid}/classification/JSON")
                ghs_codes = self._extract_ghs_codes(cls_resp.json() if cls_resp.status_code == 200 else {})

            return {
                "name": cleaned,
                "cid": cid,
                "pubchem_found": True,
                "molecular_weight": props_data.get("MolecularWeight"),
                "molecular_formula": props_data.get("MolecularFormula"),
                "cas_number": cas_numbers[0] if cas_numbers else None,
                "ghs_codes": ghs_codes,
                "pubchem_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            }
        except Exception as exc:
            logger.warning("PubChem enrichment failed for %s: %s", cleaned, exc)
            return {"name": cleaned, "pubchem_found": False}

    def _extract_ghs_codes(self, payload: Dict[str, Any]) -> List[str]:
        """Extract H-codes from variable PubChem classification payload."""
        text = str(payload)
        codes: List[str] = []
        for token in text.replace('"', " ").replace("'", " ").split():
            if len(token) == 4 and token.startswith("H") and token[1:].isdigit():
                codes.append(token)
        # preserve order, dedupe
        seen = set()
        out = []
        for c in codes:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out[:10]


_pubchem_client = PubChemClient()


def get_pubchem_client() -> PubChemClient:
    """Dependency accessor for PubChem client."""
    return _pubchem_client

