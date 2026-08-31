from __future__ import annotations

from dataclasses import dataclass


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

