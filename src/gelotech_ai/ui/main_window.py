"""Main desktop window for GeloTech AI."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Initial shell of the GeloTech AI workspace."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GeloTech AI")
        self.resize(1400, 850)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        project_button = QPushButton("Open Project")
        model_label = QLabel("Model:")
        model_input = QLineEdit("ollama")
        model_input.setMaximumWidth(220)
        toolbar.addWidget(project_button)
        toolbar.addStretch()
        toolbar.addWidget(model_label)
        toolbar.addWidget(model_input)
        root_layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        project_tree = QTreeWidget()
        project_tree.setHeaderLabel("PROJECT")
        project_tree.addTopLevelItem(QTreeWidgetItem(["Open a project to begin"]))
        splitter.addWidget(project_tree)

        chat = QTextEdit()
        chat.setReadOnly(True)
        chat.setPlaceholderText("AI conversation will appear here...")
        splitter.addWidget(chat)

        root_layout.addWidget(splitter, 1)

        prompt_row = QHBoxLayout()
        prompt = QLineEdit()
        prompt.setPlaceholderText("Ask GeloTech AI to inspect, explain, or modify your project...")
        send = QPushButton("Send")
        send.setDefault(True)
        prompt_row.addWidget(prompt, 1)
        prompt_row.addWidget(send)
        root_layout.addLayout(prompt_row)

        self.setCentralWidget(root)
