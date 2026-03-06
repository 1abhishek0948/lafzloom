from __future__ import annotations

from dataclasses import dataclass, field

from django.contrib.auth import get_user_model

from .models import Category, Shayari


LANGUAGE_ALIASES = {
    'hi': Shayari.LANG_HI,
    'hindi': Shayari.LANG_HI,
    'en': Shayari.LANG_EN,
    'english': Shayari.LANG_EN,
    'ur': Shayari.LANG_UR,
    'urdu': Shayari.LANG_UR,
}

EXPECTED_COLUMNS = {'title', 'text', 'language', 'category', 'author'}
REQUIRED_COLUMNS = {'title', 'text', 'language', 'category'}


@dataclass
class ImportResult:
    created: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)


def _clean(value):
    if value is None:
        return ''
    return str(value).strip()


def _header_key(value):
    return _clean(value).lower().replace(' ', '').replace('_', '')


def _resolve_language(raw_language: str):
    return LANGUAGE_ALIASES.get(raw_language.strip().lower())


def _resolve_author(raw_author: str, default_author, result: ImportResult, row_num: int):
    raw_author = raw_author.strip()
    if not raw_author:
        return default_author

    User = get_user_model()
    user = User.objects.filter(username__iexact=raw_author).first()
    if user:
        return user

    user = User.objects.filter(email__iexact=raw_author).first()
    if user:
        return user

    result.warnings.append(
        f"Row {row_num}: author '{raw_author}' not found, used '{default_author.username}'."
    )
    return default_author


def import_shayari_xlsx(file_obj, default_author, approve=False):
    try:
        from openpyxl import load_workbook
    except Exception as exc:
        raise ValueError('openpyxl is required to import .xlsx files.') from exc

    workbook = load_workbook(filename=file_obj, read_only=True, data_only=True)
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    header_row = next(rows, None)
    if not header_row:
        raise ValueError('The Excel file is empty.')

    column_indices = {}
    for idx, header in enumerate(header_row):
        key = _header_key(header)
        for column in EXPECTED_COLUMNS:
            if key == column:
                column_indices[column] = idx
                break

    missing = REQUIRED_COLUMNS - set(column_indices.keys())
    if missing:
        missing_str = ', '.join(sorted(missing))
        raise ValueError(f'Missing required columns: {missing_str}.')

    result = ImportResult()

    for row_num, row in enumerate(rows, start=2):
        if row is None:
            continue

        title = _clean(row[column_indices['title']]) if column_indices['title'] < len(row) else ''
        text = _clean(row[column_indices['text']]) if column_indices['text'] < len(row) else ''
        language_raw = (
            _clean(row[column_indices['language']]) if column_indices['language'] < len(row) else ''
        )
        category_name = (
            _clean(row[column_indices['category']]) if column_indices['category'] < len(row) else ''
        )
        author_raw = (
            _clean(row[column_indices['author']])
            if 'author' in column_indices and column_indices['author'] < len(row)
            else ''
        )

        if not any([title, text, language_raw, category_name, author_raw]):
            continue

        if not title or not text or not language_raw or not category_name:
            result.skipped += 1
            result.warnings.append(f'Row {row_num}: missing required field(s).')
            continue

        if len(title) > 200:
            result.skipped += 1
            result.warnings.append(f'Row {row_num}: title exceeds 200 characters.')
            continue

        language = _resolve_language(language_raw)
        if not language:
            result.skipped += 1
            result.warnings.append(
                f"Row {row_num}: invalid language '{language_raw}' (use Hindi/English/Urdu)."
            )
            continue

        category = Category.objects.filter(name__iexact=category_name).first()
        if not category:
            category = Category.objects.create(name=category_name)
        author = _resolve_author(author_raw, default_author, result, row_num)

        Shayari.objects.create(
            title=title,
            text=text,
            language=language,
            category=category,
            author=author,
            approved=approve,
        )
        result.created += 1

    return result
