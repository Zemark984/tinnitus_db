import requests
import xml.etree.ElementTree as ET
from datetime import datetime

from ..utils.logging import error
from ..utils.config import args, SCHEMA_VERSION
from ..utils.hashing import hash_id
from ..processing.normalization import normalize_year

def fetch_atom(atom_url):
    """Получение данных из Atom/RSS ленты"""
    entries = []
    try:
        r = requests.get(atom_url, timeout=15, headers={'User-Agent': f'TinnitusDB/1.0 ({args.email})'})
        r.raise_for_status()

        root = ET.fromstring(r.content)
        ns = {'a': 'http://www.w3.org/2005/Atom'}

        for entry in root.findall('a:entry', ns):
            link = entry.find('a:link', ns).get('href', "")
            title = entry.find('a:title', ns).text or ""
            pubdate = entry.find('a:published', ns).text or ""

            # Нормализуем дату
            year = normalize_year(pubdate)

            entries.append({
                "id": hash_id("atom", link + pubdate),
                "title": title,
                "abstract": "",
                "authors": [],
                "year": year,
                "journal": None,
                "source": "PubMed Atom",
                "pmid": None,
                "doi": None,
                "evidence_type": "update",
                "study_level": [],
                "sample_size": 0,
                "findings": "",
                "results": {},
                "mesh_terms": [],
                "limitations": None,
                "provenance": {
                    "schema_version": SCHEMA_VERSION,
                    "collected_by": "TinnitusDB",
                    "collected_at": datetime.now().isoformat(),
                    "original_url": link,
                },
                "text_for_embedding": title.strip(),
                "updated": datetime.now().date().isoformat(),
                "confidence": 0.3,
                "confidence_reason": "Atom update",
                "ethics_risk": None
            })
    except Exception as e:
        error(f"Error fetching Atom feed: {str(e)}")

    return entries
