import os
import json
from ..utils.logging import log, error

def validate_record(rec):
    """Валидация записи с подробными сообщениями об ошибках"""
    required = ["id", "title", "abstract", "text_for_embedding"]
    for k in required:
        if not rec.get(k):
            raise ValueError(f"Missing or empty field: {k} - {rec.get('pmid', 'N/A')}")

def atomic_save(path, records):
    """Атомарное сохранение данных"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            for rec in records:
                json.dump(rec, f, ensure_ascii=False)
                f.write("\n")
        os.replace(tmp_path, path)
        log(f"Successfully saved {len(records)} records to {path}")
    except Exception as e:
        error(f"Failed to save records: {str(e)}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

def load_existing(path):
    """Загрузка существующих данных с обработкой ошибок"""
    if not os.path.exists(path):
        return {}

    existing = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    if "id" in rec:
                        existing[rec["id"]] = rec
        log(f"Loaded {len(existing)} existing records from {path}")
    except Exception as e:
        error(f"Error loading existing data: {str(e)}")
    return existing
