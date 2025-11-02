import re

def normalize_year(year_raw):
    """Нормализация года публикации"""
    if not year_raw:
        return None
    m = re.search(r'(19|20)\d{2}', str(year_raw))
    return m.group(0) if m else None

def normalize_pubtypes(pubtypes):
    """Нормализация типов публикаций"""
    if isinstance(pubtypes, list):
        return [p.strip() for p in pubtypes if p.strip()]
    return [pubtypes] if pubtypes else []
