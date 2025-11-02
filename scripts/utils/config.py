import argparse

# Конфигурация
parser = argparse.ArgumentParser(description="ETL PubMed for tinnitus/hearing loss knowledge base")
parser.add_argument('--query', default='(tinnitus[Title/Abstract] AND ("hearing loss"[Title/Abstract] OR deafness OR "тугоухость")) AND (humans[MeSH]) NOT (animals[MeSH])', help='PubMed query')
parser.add_argument('--retmax', type=int, default=50, help='max articles')
parser.add_argument('--email', required=True, help='NCBI API email')
parser.add_argument('--atom', default='', help='Atom/RSS feed for update (optional)')
parser.add_argument('--out', default='data/tinnitus_db.jsonl', help='Output JSONL path')
parser.add_argument('--log', default='logs/db_update.log', help='Log file path')
parser.add_argument('--ncbi_max_retries', type=int, default=5, help='Max retries for NCBI API')
parser.add_argument('--ncbi_retry_delay', type=int, default=60, help='Base delay for NCBI retries (seconds)')
args = parser.parse_args()

SCHEMA_VERSION = "1.0.1"

# Настройки для метрики уверенности
CONFIDENCE_WEIGHTS = {
    "evidence_types": {
        "meta-analysis": 0.95,
        "systematic review": 0.92,
        "rct": 0.90,
        "cohort": 0.71,
        "case-control": 0.62,
        "case series": 0.43,
        "case report": 0.18,
        "review": 0.65,
        "update": 0.3
    },
    "journal_impact": {
        "jama": 0.05,
        "nejm": 0.05,
        "lancet": 0.05,
        "nature": 0.05,
        "science": 0.05
    }
}
