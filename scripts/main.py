import os
import time
from .utils.config import args, SCHEMA_VERSION
from .utils.logging import log, error
from .api.ncbi import fetch_pubmed_ids, fetch_pubmed_meta
from .api.atom import fetch_atom
from .storage.jsonl import load_existing, atomic_save

def main():
    """Основная функция"""
    start_time = time.time()
    try:
        log(f"Starting database update with query: {args.query}")
        os.makedirs(os.path.dirname(args.out), exist_ok=True)

        # Получаем ID статей
        ids = fetch_pubmed_ids(args.query, args.retmax)
        log(f"Found {len(ids)} PubMed IDs")

        # Получаем метаданные
        entries = fetch_pubmed_meta(ids)
        log(f"Retrieved {len(entries)} records from PubMed")

        # Получаем обновления из Atom (если указано)
        atom_entries = fetch_atom(args.atom) if args.atom else []
        log(f"Retrieved {len(atom_entries)} entries from Atom feed")

        # Загружаем существующие данные
        existing = load_existing(args.out)
        n_before = len(existing)

        # Обрабатываем новые записи
        newrecs = []
        for rec in entries + atom_entries:
            if rec["id"] not in existing:
                newrecs.append(rec)
                existing[rec["id"]] = rec

        # Сохраняем данные
        all_records = list(existing.values())
        atomic_save(args.out, all_records)

        log(f"Database update completed: {len(newrecs)} new records added, total {len(all_records)}. Schema version {SCHEMA_VERSION}.")
        log(f"Confidence metrics: average={sum(r['confidence'] for r in all_records)/len(all_records):.3f}, min={min(r['confidence'] for r in all_records):.3f}, max={max(r['confidence'] for r in all_records):.3f}")

    except Exception as e:
        error(f"Critical error during database update: {str(e)}")
        raise
    finally:
        end_time = time.time()
        duration = end_time - start_time
        log(f"Total execution time: {duration:.2f} seconds.")
