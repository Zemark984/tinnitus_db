import requests
import xml.etree.ElementTree as ET
import time
import re
from datetime import datetime

from ..utils.logging import log, error
from ..utils.decorators import retry_on_fail
from ..utils.config import args, SCHEMA_VERSION
from ..utils.hashing import hash_id
from ..processing.normalization import normalize_year, normalize_pubtypes
from ..processing.nlp import extract_sample_size, extract_findings
from ..processing.evidence import calc_confidence
from ..storage.jsonl import validate_record
from ..utils.exceptions import NCBIAPITemporaryBlock

def handle_ncbi_block(response):
    """Проверяет, не заблокирован ли доступ к NCBI"""
    if "blocked" in response.text.lower() or response.status_code == 429:
        # Пытаемся извлечь информацию о блокировке
        block_info = "No specific block information"
        if "your access to the ncbi website" in response.text.lower():
            block_info = "Temporary block due to possible misuse/abuse"
        elif "429 too many requests" in response.text.lower():
            block_info = "Rate limit exceeded"

        raise NCBIAPITemporaryBlock(block_info)

    return False

@retry_on_fail()
def fetch_pubmed_ids(query, retmax):
    """Получение ID статей из PubMed с обработкой блокировок"""
    # Проверяем email на валидность
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', args.email):
        raise ValueError("Invalid email format. Please provide a valid email address.")

    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={requests.utils.quote(query)}"
        f"&retmax={retmax}&retmode=json"
        f"&tool=TinnitusDB&email={args.email}"
    )
    if args.api_key:
        url += f"&api_key={args.api_key}"
    headers = {'User-Agent': f'TinnitusDB/1.0 ({args.email})'}

    try:
        r = requests.get(url, headers=headers, timeout=25)
        r.raise_for_status()

        # Проверяем на блокировку
        handle_ncbi_block(r)

        # Добавляем небольшую задержку между запросами
        time.sleep(0.34)

        return r.json()["esearchresult"]["idlist"]
    except requests.exceptions.RequestException as e:
        error(f"PubMed ID fetch error: {str(e)}")
        raise

@retry_on_fail()
def fetch_pubmed_meta(ids):
    """Получение метаданных статей из PubMed"""
    BATCH = 15
    results = []
    headers = {'User-Agent': f'TinnitusDB/1.0 ({args.email})'}

    for i in range(0, len(ids), BATCH):
        group = ids[i:i+BATCH]
        url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={','.join(group)}&retmode=xml"
            f"&tool=TinnitusDB&email={args.email}"
        )
        if args.api_key:
            url += f"&api_key={args.api_key}"

        try:
            r = requests.get(url, headers=headers, timeout=25)
            r.raise_for_status()

            # Проверяем на блокировку
            handle_ncbi_block(r)

            # Добавляем небольшую задержку между запросами
            time.sleep(0.34)

            tree = ET.fromstring(r.content)
            for article in tree.findall(".//PubmedArticle"):
                try:
                    # Извлекаем данные
                    pmid = article.findtext(".//PMID", "")
                    if not pmid:
                        continue

                    art = article.find(".//Article")
                    if art is None:
                        continue

                    title = art.findtext("ArticleTitle", "")
                    abstract_el = art.find(".//Abstract")
                    abstract = " ".join([el.text.strip() for el in abstract_el.findall(".//AbstractText") if el.text]) if abstract_el else ""

                    # Нормализуем год
                    year = normalize_year(article.findtext(".//PubDate/Year", ""))
                    if not year:
                        year = article.findtext(".//PubDate/MedlineDate", "")[:4] if article.findtext(".//PubDate/MedlineDate") else ""

                    # Извлекаем MeSH термины
                    mesh_terms = [m.text for m in article.findall(".//MeshHeading/DescriptorName") if m.text]

                    # Извлекаем авторов
                    auths = [f"{a.findtext('LastName', '')} {a.findtext('Initials', '')}".strip()
                             for a in art.findall(".//Author")
                             if a.findtext("LastName")]

                    # Извлекаем информацию о журнале
                    journal = art.findtext(".//Journal/Title", "")
                    pubtypes = normalize_pubtypes([t.text for t in art.findall(".//PublicationType") if t.text])

                    # Извлекаем DOI
                    doi = None
                    for aid in art.findall(".//ArticleId"):
                        if aid.get("IdType") == "doi":
                            doi = aid.text

                    # Определяем тип доказательств
                    evidence_type = "update"
                    for pt in pubtypes:
                        pt_lower = pt.lower()
                        if "meta-analysis" in pt_lower:
                            evidence_type = "meta-analysis"
                            break
                        elif "systematic review" in pt_lower:
                            evidence_type = "systematic review"
                            break
                        elif "randomized controlled trial" in pt_lower or "rct" in pt_lower:
                            evidence_type = "rct"
                            break

                    # Извлекаем размер выборки и выводы
                    sample_size = extract_sample_size(abstract)
                    findings = extract_findings(abstract)

                    # Рассчитываем уверенность
                    conf, conf_reason = calc_confidence(
                        evidence_type, sample_size, year, pubtypes, journal=journal
                    )

                    # Формируем запись
                    rec = {
                        "id": hash_id("pmid", pmid),
                        "title": title,
                        "abstract": abstract,
                        "authors": [a for a in auths if a],
                        "year": year,
                        "journal": journal,
                        "source": "PubMed",
                        "pmid": pmid,
                        "doi": doi,
                        "evidence_type": evidence_type,
                        "study_level": pubtypes,
                        "sample_size": sample_size,
                        "findings": findings,
                        "results": {},  # Для ML анализа/Fact extraction отдельно
                        "mesh_terms": mesh_terms,
                        "limitations": None,
                        "provenance": {
                            "schema_version": SCHEMA_VERSION,
                            "collected_by": "TinnitusDB",
                            "collected_at": datetime.now().isoformat(),
                            "original_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        },
                        "text_for_embedding": " ".join(filter(None, [
                            title, abstract, " ".join(mesh_terms)
                        ])).strip(),
                        "updated": datetime.now().date().isoformat(),
                        "confidence": conf,
                        "confidence_reason": conf_reason,
                        "ethics_risk": "[ВНИМАНИЕ] Не одобрено FDA/EMA" if "pharmacological" in evidence_type.lower() else None
                    }

                    # Валидируем запись
                    validate_record(rec)
                    results.append(rec)
                except Exception as e:
                    error(f"Error parsing article {pmid}: {str(e)}")
        except Exception as e:
            error(f"Error fetching batch {i//BATCH + 1}: {str(e)}")
            raise

    return results
