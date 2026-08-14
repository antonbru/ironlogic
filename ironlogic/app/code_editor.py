"""Редактор .py с подсветкой синтаксиса Python (PySide6)."""

from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit


class PythonHighlighter(QSyntaxHighlighter):
    """Подсветка ключевых слов Python, строк, комментариев."""

    KEYWORDS = {
        "if", "else", "elif", "while", "for", "def", "return", "import", "from",
        "class", "not", "and", "or", "in", "is", "None", "True", "False", "global",
        "pass", "break", "continue", "lambda", "with", "as", "try", "except",
    }

    def __init__(self, document) -> None:
        super().__init__(document)
        self._formats: dict[str, QTextCharFormat] = {}

        kw = QTextCharFormat()
        kw.setForeground(QColor("#ff79c6"))
        kw.setFontWeight(QFont.Weight.Bold)
        self._formats["keyword"] = kw

        comment = QTextCharFormat()
        comment.setForeground(QColor("#6272a4"))
        comment.setFontItalic(True)
        self._formats["comment"] = comment

        string = QTextCharFormat()
        string.setForeground(QColor("#f1fa8c"))
        self._formats["string"] = string

        self._rules = [
            (QRegularExpression(r"#[^\n]*"), self._formats["comment"]),
            (QRegularExpression(r"\".*?\"|'.*?'"), self._formats["string"]),
            (QRegularExpression(r"\b(" + "|".join(self.KEYWORDS) + r")\b"), self._formats["keyword"]),
        ]

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class CodeEditor(QPlainTextEdit):
    """Простой редактор Python с подсветкой синтаксиса."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        font = QFont("Menlo", 12)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.setStyleSheet(
            "QPlainTextEdit { background: #0d1117; color: #c9d1d9;"
            "border: 1px solid #30363d; border-radius: 8px; padding: 8px; }"
        )
        self.highlighter = PythonHighlighter(self.document())