"""Main desktop workspace for GeloTech AI."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gelotech_ai.agent import ReadOnlyAgent, make_inspect_tool, make_read_tool, make_search_tool
from gelotech_ai.core.context import build_project_context
from gelotech_ai.core.project import ProjectFile, discover_files, read_text_file
from gelotech_ai.models.ollama import OllamaProvider
from gelotech_ai.models.openai_compat import DEFAULT_BASE_URL, OpenAICompatProvider
from gelotech_ai.ui.workers import AgentChatWorker, OllamaChatWorker, OllamaModelsWorker

PROVIDER_OLLAMA = "Ollama (local)"
PROVIDER_CLOUD = "Cloud API (OpenAI-compatible)"

_AGENT_SYSTEM_PROMPT = (
    "You are GeloTech AI, a read-only coding agent for the opened project. "
    "Use the available tools to inspect the project before answering. "
    "Cite file paths and line numbers when useful. "
    "If a tool finds nothing or reports an error, say so. "
    "Never invent file contents. Be precise and concise."
)


class MainWindow(QMainWindow):
    """Windows-first project browser and local-model chat workspace."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GeloTech AI")
        self.resize(1500, 900)
        self.project_root: Path | None = None
        self._files: dict[str, ProjectFile] = {}
        self._messages: list[dict[str, str]] = []
        self._current_response = ""
        self._chat_worker: OllamaChatWorker | None = None
        self._models_worker: OllamaModelsWorker | None = None
        self._build_ui()
        self._refresh_models()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        project_button = QPushButton("Open Project")
        project_button.clicked.connect(self._open_project)
        self.project_label = QLabel("No project opened")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([PROVIDER_OLLAMA, PROVIDER_CLOUD])
        self.provider_combo.currentTextChanged.connect(self._provider_changed)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API key (or set GELOTECH_API_KEY)")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMinimumWidth(180)
        self.base_url_input = QLineEdit(DEFAULT_BASE_URL)
        self.base_url_input.setMinimumWidth(200)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setMinimumWidth(260)
        refresh_models = QPushButton("Refresh Models")
        refresh_models.clicked.connect(self._refresh_models)
        toolbar.addWidget(project_button)
        toolbar.addWidget(self.project_label, 1)
        toolbar.addWidget(self.provider_combo)
        toolbar.addWidget(self.api_key_input)
        toolbar.addWidget(self.base_url_input)
        toolbar.addWidget(QLabel("Model:"))
        toolbar.addWidget(self.model_combo)
        toolbar.addWidget(refresh_models)
        root_layout.addLayout(toolbar)
        self._provider_changed(self.provider_combo.currentText())

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("PROJECT")
        self.project_tree.itemClicked.connect(self._preview_item)
        splitter.addWidget(self.project_tree)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Select a text file to preview it here.")
        splitter.addWidget(self.preview)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("Your local AI conversation will appear here...")
        splitter.addWidget(self.chat)
        splitter.setSizes([300, 500, 700])
        root_layout.addWidget(splitter, 1)

        prompt_row = QHBoxLayout()
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Ask GeloTech AI about your project...")
        self.prompt.returnPressed.connect(self._send_prompt)
        self.send_button = QPushButton("Send")
        self.send_button.setDefault(True)
        self.send_button.clicked.connect(self._send_prompt)
        prompt_row.addWidget(self.prompt, 1)
        prompt_row.addWidget(self.send_button)
        root_layout.addLayout(prompt_row)

        self.statusBar().showMessage("Ready. Install/start Ollama to use local AI.")
        self.setCentralWidget(root)

    def _open_project(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Open Project")
        if not selected:
            return
        self.project_root = Path(selected).resolve()
        self.project_label.setText(str(self.project_root))
        self._load_project_tree()
        self.chat.append(f"<b>Project opened:</b> {self.project_root}")
        self.statusBar().showMessage("Project loaded. Files are inspected locally.")

    def _load_project_tree(self) -> None:
        assert self.project_root is not None
        self.project_tree.clear()
        self._files.clear()
        root_item = QTreeWidgetItem([self.project_root.name or str(self.project_root)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self.project_tree.addTopLevelItem(root_item)

        for item in discover_files(self.project_root):
            key = item.path.as_posix()
            self._files[key] = item
            parts = item.path.parts
            parent = root_item
            for part in parts[:-1]:
                child = next(
                    (
                        parent.child(i)
                        for i in range(parent.childCount())
                        if parent.child(i).text(0) == part
                    ),
                    None,
                )
                if child is None:
                    child = QTreeWidgetItem([part])
                    parent.addChild(child)
                parent = child
            leaf = QTreeWidgetItem([parts[-1]])
            leaf.setData(0, Qt.ItemDataRole.UserRole, key)
            parent.addChild(leaf)
        root_item.setExpanded(True)

    def _preview_item(self, item: QTreeWidgetItem, _column: int) -> None:
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if not key or self.project_root is None:
            return
        try:
            text = read_text_file(self.project_root, Path(key))
        except (OSError, ValueError) as exc:
            self.preview.setPlainText(f"Cannot preview file: {exc}")
            return
        self.preview.setPlainText(text)

    def _provider_changed(self, provider: str) -> None:
        is_cloud = provider == PROVIDER_CLOUD
        self.api_key_input.setVisible(is_cloud)
        self.base_url_input.setVisible(is_cloud)

    def _make_provider(self, model: str) -> OllamaProvider | OpenAICompatProvider:
        if self.provider_combo.currentText() == PROVIDER_CLOUD:
            return OpenAICompatProvider(
                base_url=self.base_url_input.text().strip() or DEFAULT_BASE_URL,
                api_key=self.api_key_input.text().strip(),
                model=model,
            )
        return OllamaProvider(model=model)

    def _refresh_models(self) -> None:
        if self._models_worker and self._models_worker.isRunning():
            return
        self.statusBar().showMessage("Checking available models...")
        provider = self._make_provider("")
        self._models_worker = OllamaModelsWorker(provider)
        self._models_worker.models_ready.connect(self._models_loaded)
        self._models_worker.error.connect(self._ollama_error)
        self._models_worker.finished.connect(self._models_worker.deleteLater)
        self._models_worker.start()

    def _models_loaded(self, models: list[str]) -> None:
        current = self.model_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if current:
            index = self.model_combo.findText(current)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
            else:
                self.model_combo.setEditText(current)
        if models:
            self.statusBar().showMessage(f"Provider ready: {len(models)} model(s).")
        else:
            self.statusBar().showMessage(
                "Provider is running but no models are available."
            )

    def _ollama_error(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _send_prompt(self) -> None:
        prompt = self.prompt.text().strip()
        model = self.model_combo.currentText().strip()
        if not prompt:
            return
        if not model:
            QMessageBox.warning(
                self, "No model selected", "Select or enter an Ollama model first."
            )
            return
        if self._chat_worker and self._chat_worker.isRunning():
            return

        self._messages.append({"role": "user", "content": prompt})
        if self.project_root is not None:
            system = _AGENT_SYSTEM_PROMPT + "\n\n" + build_project_context(self.project_root)
            tools = [
                make_search_tool(self.project_root),
                make_read_tool(self.project_root),
                make_inspect_tool(self.project_root),
            ]
            agent = ReadOnlyAgent(self._make_provider(model), tools)
            worker = AgentChatWorker(agent, self._agent_messages(system))
            worker.tool_used.connect(self._handle_tool_used)
        else:
            system = "You are GeloTech AI, a local coding assistant. Be precise and concise."
            worker = OllamaChatWorker(
                self._make_provider(model), self._agent_messages(system)
            )
        self.chat.append(f"<b>You:</b> {prompt}")
        self.chat.append("<b>GeloTech AI:</b> ")
        self.prompt.clear()
        self.send_button.setEnabled(False)
        self._current_response = ""
        self._chat_worker = worker
        self._chat_worker.chunk.connect(self._handle_chat_chunk)
        self._chat_worker.finished_ok.connect(self._chat_finished)
        self._chat_worker.error.connect(self._chat_error)
        self._chat_worker.finished.connect(self._chat_worker.deleteLater)
        self._chat_worker.start()

    def _agent_messages(self, system: str) -> list[dict[str, object]]:
        return [{"role": "system", "content": system}, *self._messages]

    def _handle_tool_used(self, name: str) -> None:
        self.chat.append(f'<i style="color:#888">→ {name}</i>')

    def _handle_chat_chunk(self, text: str) -> None:
        self._current_response += text
        self.chat.insertPlainText(text)
        self.chat.ensureCursorVisible()

    def _chat_finished(self) -> None:
        if self._current_response:
            self._messages.append({"role": "assistant", "content": self._current_response})
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Response complete.")

    def _chat_error(self, message: str) -> None:
        self.chat.append(f"\n<b>Error:</b> {message}")
        self.send_button.setEnabled(True)
        self.statusBar().showMessage("Ollama request failed.")
