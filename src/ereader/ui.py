from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

from .books import Book, SAMPLE_BOOKS
from .framebuffer import DisplaySize


class Screen(str, Enum):
    LIBRARY = "library"
    READER = "reader"


@dataclass
class ReaderState:
    screen: Screen = Screen.LIBRARY
    selected_book: int = 0
    active_book: int = 0
    page: int = 0


class ReaderUI:
    def __init__(self, size: DisplaySize, books: list[Book] | None = None) -> None:
        self.size = size
        self.books = books or SAMPLE_BOOKS
        self.state = ReaderState()
        self._font_regular = _load_font(24)
        self._font_small = _load_font(18)
        self._font_title = _load_font(34)
        self._font_mono = _load_font(16)

    def render(self) -> Image.Image:
        image = Image.new("L", (self.size.width, self.size.height), 236)
        draw = ImageDraw.Draw(image)

        if self.state.screen == Screen.LIBRARY:
            self._render_library(draw)
        else:
            self._render_reader(draw)

        return image

    def home(self) -> None:
        self.state.screen = Screen.LIBRARY

    def select_next(self) -> None:
        if self.state.screen == Screen.LIBRARY:
            self.state.selected_book = min(len(self.books) - 1, self.state.selected_book + 1)
        else:
            self.next_page()

    def select_previous(self) -> None:
        if self.state.screen == Screen.LIBRARY:
            self.state.selected_book = max(0, self.state.selected_book - 1)
        else:
            self.previous_page()

    def open_selected(self) -> None:
        self.state.active_book = self.state.selected_book
        self.state.page = 0
        self.state.screen = Screen.READER

    def next_page(self) -> None:
        pages = self._book_pages(self.books[self.state.active_book])
        self.state.page = min(len(pages) - 1, self.state.page + 1)

    def previous_page(self) -> None:
        self.state.page = max(0, self.state.page - 1)

    def _render_library(self, draw: ImageDraw.ImageDraw) -> None:
        margin = 54
        draw.text((margin, 52), "Library", fill=16, font=self._font_title)
        draw.line((margin, 106, self.size.width - margin, 106), fill=70, width=2)

        y = 148
        for index, book in enumerate(self.books):
            selected = index == self.state.selected_book
            if selected:
                draw.rounded_rectangle(
                    (margin - 14, y - 16, self.size.width - margin + 14, y + 86),
                    radius=6,
                    fill=24,
                )
                title_fill = 245
                meta_fill = 205
            else:
                title_fill = 28
                meta_fill = 92

            draw.text((margin, y), book.title, fill=title_fill, font=self._font_regular)
            draw.text((margin, y + 36), book.author, fill=meta_fill, font=self._font_small)
            y += 126

        footer = "Enter opens  |  arrows select  |  Home returns"
        draw.text((margin, self.size.height - 58), footer, fill=90, font=self._font_mono)

    def _render_reader(self, draw: ImageDraw.ImageDraw) -> None:
        book = self.books[self.state.active_book]
        pages = self._book_pages(book)
        page = pages[self.state.page]
        margin = 58

        draw.text((margin, 36), book.title, fill=45, font=self._font_small)
        draw.line((margin, 72, self.size.width - margin, 72), fill=165, width=1)

        y = 112
        line_height = 34
        for line in page:
            draw.text((margin, y), line, fill=18, font=self._font_regular)
            y += line_height

        progress_width = self.size.width - margin * 2
        progress = (self.state.page + 1) / max(1, len(pages))
        bar_y = self.size.height - 70
        draw.rectangle((margin, bar_y, margin + progress_width, bar_y + 4), fill=190)
        draw.rectangle((margin, bar_y, margin + int(progress_width * progress), bar_y + 4), fill=35)
        draw.text(
            (margin, self.size.height - 50),
            f"Page {self.state.page + 1} of {len(pages)}",
            fill=80,
            font=self._font_mono,
        )

    def _book_pages(self, book: Book) -> list[list[str]]:
        text_width = max(28, (self.size.width - 116) // 14)
        lines: list[str] = []
        for paragraph in book.text.split("\n\n"):
            lines.extend(wrap(paragraph, width=text_width))
            lines.append("")

        lines_per_page = max(8, (self.size.height - 220) // 34)
        pages = [lines[i : i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
        return pages or [[]]


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

