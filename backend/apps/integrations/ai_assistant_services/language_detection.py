# -*- coding: utf-8 -*-
"""
Language Detection & Capability Configuration for ProofVoice (English & Hindi only).
"""
import re

SUPPORTED_LANGUAGES = {
    'en-IN': {'name': 'English', 'native': 'English', 'script': 'Latin', 'bcp47': 'en-IN', 'voice_support': True, 'gnani_voice': 'Paul'},
    'hi-IN': {'name': 'Hindi', 'native': 'हिन्दी', 'script': 'Devanagari', 'bcp47': 'hi-IN', 'voice_support': True, 'gnani_voice': 'Nalini'},
}

SCRIPT_PATTERNS = {
    'devanagari': re.compile(r'[ऀ-ॿ]')   # Hindi
}

def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    t = re.sub(r'([a-z])\1{2,}', r'\1', t)
    return t

def normalize_lang_code(code: str) -> str:
    """Converts language identifiers to canonical BCP-47 tag ('en-IN' or 'hi-IN')."""
    if not code:
        return 'en-IN'
    c = str(code).strip().lower()
    if c.startswith('hi') or 'hindi' in c:
        return 'hi-IN'
    return 'en-IN'

def detect_language(query: str, preferred: str = 'en-IN') -> str:
    """
    Detects language (English or Hindi only), falling back to preferred.
    """
    norm_preferred = normalize_lang_code(preferred)
    if not query or not query.strip():
        return norm_preferred

    # 1. Check Native Devanagari Block for Hindi
    if SCRIPT_PATTERNS['devanagari'].search(query):
        return 'hi-IN'

    # 2. Check Romanized / Transliterated Hindi Keywords
    norm = normalize_text(query)
    hindi_pattern = r'\b(namaste|kaise|kya|karein|shikayat|dhanyawad|batao|chal\s*raha|karo|kaun|aapka|kripya|madad|madat|samiksha)\b'
    if re.search(hindi_pattern, norm):
        return 'hi-IN'

    if norm_preferred == 'hi-IN':
        return 'hi-IN'

    return 'en-IN'
