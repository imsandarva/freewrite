"""The writing papers."""

from papers.catalog import ORDER, next_paper, paper_for, remember_paper, saved_paper
from papers.cycle import PaperCycle
from papers.style import chrome_qss

__all__ = [
    "ORDER", "PaperCycle", "chrome_qss", "next_paper", "paper_for", "remember_paper", "saved_paper",
]
