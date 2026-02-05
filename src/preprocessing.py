import re
import unicodedata

AZ_LETTERS = r"a-zA-ZəğıöşçüİƏĞÖŞÇÜ"

def unicode_normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)

def remove_punctuation_noise(text):
    # 1. Remove long strings of the same character (e.g., "----------")
    # This keeps "..." (3 dots) but removes 4 or more
    text = re.sub(r'([!\"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~])\1{3,}', '', text)

    # 2. Remove mixed "divider" characters (e.g., "-.-.-" or "* * *")
    text = re.sub(r'[\-\._\*~=\+]{3,}', '', text)

    # 3. Clean up "ghost" punctuation left between words
    # Removes things like "Söz . söz" but keeps "Söz. Söz" (proper sentence)
    text = re.sub(r'\s[^\w\s]\s', ' ', text)

    # 4. Final pass: collapse multiple spaces left behind
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def clean_az_text(text: str) -> str:
    text = unicode_normalize(text)

    # Remove page numbers
    text = re.sub(r'(?m)^[-–—]*\s*\d+\s*[-–—]*$', '', text)

    # 1. Remove page headers/footers (often digits alone on a line)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # Fix hyphenated words across lines
    text = re.sub(
        rf'([{AZ_LETTERS}]+)-\n([{AZ_LETTERS}]+)',
        r'\1\2',
        text
    )

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    text = remove_punctuation_noise(text)

    # Fix spaces before common Azerbaijani suffixes or apostrophes
    text = re.sub(r"(['’])\s+", r"\1", text) # Bakı ' nın -> Bakı'nın

    # Normalize punctuation spacing
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(?=[^\s])', r'\1 ', text)

    # Remove OCR garbage, keep Azerbaijani
    text = re.sub(
        rf'[^{AZ_LETTERS}0-9\s.,;:!?()"\'\-–—]',
        '',
        text
    )

    text = text.lower()

    return text.strip()
