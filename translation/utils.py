def _contains_devanagari(text):
    for ch in text:
        if '\u0900' <= ch <= '\u097F':
            return True
    return False


def _contains_arabic(text):
    for ch in text:
        if '\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u077F' or '\u08A0' <= ch <= '\u08FF':
            return True
    return False


def _mostly_ascii(text):
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    ascii_letters = [ch for ch in letters if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z']
    return len(ascii_letters) / len(letters) > 0.7


def _transliterate(text, target_script):
    if not target_script:
        return text
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
    except Exception:
        return text
    try:
        return transliterate(text, sanscript.ITRANS, target_script)
    except Exception:
        return text


def ensure_script(text, target_lang):
    if target_lang == 'hi':
        # Keep Hindi in the original script (often romanized Hindi).
        # Do not force Devanagari, per UI requirement.
        return text
    if target_lang == 'ur':
        if _contains_arabic(text) or not _mostly_ascii(text):
            return text
        try:
            from indic_transliteration import sanscript
            target_script = getattr(sanscript, 'URDU', None) or getattr(sanscript, 'ARABIC', None)
        except Exception:
            target_script = None
        return _transliterate(text, target_script)
    return text
