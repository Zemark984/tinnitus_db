from datetime import datetime
from ..utils.config import CONFIDENCE_WEIGHTS

def calc_confidence(evidence_type, sample_size, year, pubtypes=None, journal=None):
    """Улучшенный расчет уверенности с настраиваемыми весами"""
    base = CONFIDENCE_WEIGHTS["evidence_types"]
    ev = (evidence_type or "update").lower()
    c = base.get(ev, 0.3)

    n = sample_size or 0
    year_i = int(year) if (year and year.isdigit()) else 2020

    # Веса на основе размера выборки
    if n >= 5000:
        c += 0.02
    elif n >= 1000:
        c += 0.01
    elif n == 0:
        c -= 0.07

    # Веса на основе типа публикации
    if pubtypes and "systematic review" in " ".join(pubtypes).lower():
        c += 0.02

    # Веса на основе возраста
    if datetime.now().year - year_i > 8:
        c -= 0.03

    # Веса на основе журнала
    journal_impact = CONFIDENCE_WEIGHTS["journal_impact"]
    if journal and any(key in journal.lower() for key in journal_impact):
        for key, weight in journal_impact.items():
            if key in journal.lower():
                c += weight
                break

    # Обработка крайних значений
    confidence = round(max(0.0, min(1.0, c)), 3)

    # Формируем причину для отладки
    reason = f"type={ev}; n={n}; year={year_i}; pubtypes={pubtypes}; journal={journal}; confidence={confidence}"
    return confidence, reason
