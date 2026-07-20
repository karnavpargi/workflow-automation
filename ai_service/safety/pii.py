"""PII detection and redaction via Microsoft Presidio (MIT, free).

Both the analyzer and anonymizer engines are module-level singletons.
The spacy ``en_core_web_lg`` model is auto-downloaded on first import.
"""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

_analyzer = AnalyzerEngine()
_anonymizer = AnonymizerEngine()


def redact_pii(text: str) -> str:
    """Redact PII entities from text.

    Args:
        text: Input text.

    Returns:
        Text with PII replaced by placeholders.
    """
    results = _analyzer.analyze(text=text, language="en")
    return _anonymizer.anonymize(text=text, analyzer_results=results).text


def contains_pii(text: str) -> bool:
    """Return True if PII entities are detected.

    Args:
        text: Input text.

    Returns:
        Detection flag.
    """
    return bool(_analyzer.analyze(text=text, language="en"))
