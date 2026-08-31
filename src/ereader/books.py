from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree


@dataclass(frozen=True)
class Book:
    title: str
    author: str
    text: str


SAMPLE_BOOKS = [
    Book(
        title="The Quiet Circuit",
        author="P. Vale",
        text=(
            "The first prototype did not look alive until the page turned. "
            "For a moment the display went black, then white, then settled "
            "into a field of small steady letters. Mira smiled. It was not "
            "fast, but it was calm.\n\n"
            "Every screen in the reader was drawn as a complete page. The "
            "library, the settings panel, the book itself: each one became a "
            "single grayscale image before the device decided how to refresh "
            "the panel. That decision mattered. A full refresh was clean but "
            "dramatic. A partial refresh was quiet but left a pale memory of "
            "what came before.\n\n"
            "By afternoon the simulator was good enough to teach the team "
            "where the real device would be picky. Thin gray text disappeared. "
            "Tiny icons became smudges. Animations felt silly. Page turns, "
            "careful spacing, and confident contrast won every argument."
        ),
    ),
    Book(
        title="Notes On Paper Machines",
        author="A. Ren",
        text=(
            "An e-ink reader is not a small tablet with fewer colors. It is a "
            "machine that rewards patience and punishes visual noise.\n\n"
            "Menus should be direct. Controls should be large enough to survive "
            "dithering. Screens should change because the reader asked them to "
            "change, not because a spinner wanted attention.\n\n"
            "The best interface feels almost printed. The computer is still "
            "there, of course, but it has learned to keep its voice down."
        ),
    ),
]


def load_uploaded_books(directory: Path) -> list[Book]:
    if not directory.exists():
        return []

    books: list[Book] = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in {".txt", ".epub"}:
            continue

        text, title, author = _read_book_file(path)

        if not text:
            continue

        books.append(Book(title=title or _title_from_text_or_path(text, path), author=author, text=text))

    return books


def save_uploaded_book(directory: Path, filename: str, content: bytes) -> Book:
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_book_filename(filename)
    path = _available_path(directory / safe_name)
    path.write_bytes(content)
    text, title, author = _read_book_file(path)
    return Book(title=title or _title_from_text_or_path(text, path), author=author, text=text)


def _read_book_file(path: Path) -> tuple[str, str, str]:
    if path.suffix.lower() == ".epub":
        return _read_epub(path)

    try:
        text = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text, _title_from_text_or_path(text, path), "Uploaded text file"


def _title_from_text_or_path(text: str, path: Path) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first_line[:80] if first_line else path.stem.replace("_", " ").replace("-", " ").title()


def _safe_book_filename(filename: str) -> str:
    source = Path(filename)
    stem = source.stem or "uploaded-book"
    suffix = source.suffix.lower()
    if suffix not in {".txt", ".epub"}:
        suffix = ".txt"
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in stem)
    safe = "-".join(part for part in safe.split("-") if part) or "uploaded-book"
    return f"{safe[:80]}{suffix}"


def _available_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate

    raise FileExistsError(f"Too many uploaded books named like {path.name}")


def _read_epub(path: Path) -> tuple[str, str, str]:
    with zipfile.ZipFile(path) as epub:
        opf_path = _opf_path(epub)
        opf_root = ElementTree.fromstring(epub.read(opf_path))
        opf_dir = Path(opf_path).parent
        manifest = _manifest_items(opf_root)
        spine = _spine_ids(opf_root)
        title = _metadata_value(opf_root, "title") or path.stem.replace("_", " ").replace("-", " ").title()
        author = _metadata_value(opf_root, "creator") or "Uploaded EPUB"

        chapters: list[str] = []
        for item_id in spine:
            href = manifest.get(item_id)
            if not href:
                continue

            chapter_path = (opf_dir / href).as_posix() if opf_dir.as_posix() != "." else href
            if chapter_path not in epub.namelist():
                continue

            raw_html = epub.read(chapter_path).decode("utf-8", errors="replace")
            chapter_text = _html_to_text(raw_html)
            if chapter_text:
                chapters.append(chapter_text)

    return "\n\n".join(chapters).strip(), title, author


def _opf_path(epub: zipfile.ZipFile) -> str:
    container = ElementTree.fromstring(epub.read("META-INF/container.xml"))
    for element in container.iter():
        if element.tag.endswith("rootfile"):
            path = element.attrib.get("full-path")
            if path:
                return path

    raise ValueError("EPUB is missing META-INF/container.xml rootfile path")


def _manifest_items(opf_root: ElementTree.Element) -> dict[str, str]:
    items: dict[str, str] = {}
    for element in opf_root.iter():
        if not element.tag.endswith("item"):
            continue

        item_id = element.attrib.get("id")
        href = element.attrib.get("href")
        media_type = element.attrib.get("media-type", "")
        if item_id and href and media_type in {"application/xhtml+xml", "text/html"}:
            items[item_id] = href
    return items


def _spine_ids(opf_root: ElementTree.Element) -> list[str]:
    ids: list[str] = []
    for element in opf_root.iter():
        if element.tag.endswith("itemref"):
            item_id = element.attrib.get("idref")
            if item_id:
                ids.append(item_id)
    return ids


def _metadata_value(opf_root: ElementTree.Element, name: str) -> str:
    for element in opf_root.iter():
        if element.tag.endswith(name) and element.text:
            return element.text.strip()
    return ""


def _html_to_text(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", raw_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|blockquote|section|chapter|article)>", "\n\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = unescape(text)

    lines = [line.strip() for line in text.splitlines()]
    compacted: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank and compacted:
                compacted.append("")
            blank = True
            continue

        compacted.append(re.sub(r"\s+", " ", line))
        blank = False

    return "\n".join(compacted).strip()
