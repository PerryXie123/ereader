from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
    for path in sorted(directory.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace").strip()

        if not text:
            continue

        title = _title_from_text_or_path(text, path)
        books.append(Book(title=title, author="Uploaded text file", text=text))

    return books


def save_uploaded_book(directory: Path, filename: str, content: bytes) -> Book:
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_txt_filename(filename)
    path = _available_path(directory / safe_name)
    text = content.decode("utf-8", errors="replace").strip()
    path.write_text(text, encoding="utf-8")
    return Book(title=_title_from_text_or_path(text, path), author="Uploaded text file", text=text)


def _title_from_text_or_path(text: str, path: Path) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first_line[:80] if first_line else path.stem.replace("_", " ").replace("-", " ").title()


def _safe_txt_filename(filename: str) -> str:
    stem = Path(filename).stem or "uploaded-book"
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in stem)
    safe = "-".join(part for part in safe.split("-") if part) or "uploaded-book"
    return f"{safe[:80]}.txt"


def _available_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate

    raise FileExistsError(f"Too many uploaded books named like {path.name}")
