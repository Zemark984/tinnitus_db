import re

def extract_sample_size(abstract):
    """Извлекает размер выборки из абстракта"""
    pats = [r'n\s*=\s*(\d+)', r'participants?\s*[:=]?\s*(\d+)', r'sample size\s*[:=]?\s*(\d+)', r'(\d+)\s*patients?']
    for pat in pats:
        m = re.search(pat, str(abstract).lower())
        if m: return int(m.group(1))
    return 0

def extract_findings(abstract):
    """Извлекает основные выводы из абстракта с улучшенной обработкой"""
    findings = []
    if not abstract:
        return ""

    # Разбиваем на предложения
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z])', str(abstract))

    # Ключевые слова для поиска выводов
    keywords = ['result', 'conclusion', 'findings', 'demonstrate', 'show', 'suggest',
                'indicate', 'tinnitus reduction', 'hearing loss', 'effect', 'improve', 'efficacy']

    # Ищем предложения с ключевыми словами
    for i, s in enumerate(sents):
        if i > 25:  # Ограничиваем количество проверяемых предложений
            break

        s_clean = s.strip()
        if not s_clean:
            continue

        # Проверяем, содержит ли предложение ключевые слова
        if any(kw in s_clean.lower() for kw in keywords):
            findings.append(s_clean)

        # Если в предложении есть статистические данные
        if re.search(r'\b(p[<>=]?\s*0\.05|ci|95%|odds ratio|effect size)\b', s_clean.lower()):
            findings.append(s_clean)

    # Возвращаем не более 3 ключевых предложений
    return '. '.join(findings[:3])
