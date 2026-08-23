"""
ui/dialogs/update_dialog.py
Модальное окно обновления WaterMetrics в стиле Apple Frosted Glass.
Отображает список изменений с GitHub, размер обновления, прогресс скачивания
и запускает безопасную установку.
"""

import os
import sys
import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextBrowser, QFrame, QApplication, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Slot, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from services.updater_service import (
    GitHubReleaseInfo, GitHubAssetDownloader, WindowsUpdateDeployer
)
from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard
from ui.components.toast import ToastNotification
from config import APP_VERSION


class UpdateDialog(QDialog):
    """
    Элегантный диалог проверки и установки обновлений WaterMetrics.
    """

    def __init__(self, release_info: GitHubReleaseInfo, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.downloader: GitHubAssetDownloader = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(620, 500)

        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        self.card = HoverGlassCard()
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ─── Шапка ───
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_icon("update", color=accent, size=QSize(26, 26)).pixmap(26, 26))
        header_row.addWidget(icon_lbl)

        title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if is_light else "#F8FAFC")
        lbl_title = QLabel("Доступно обновление WaterMetrics", objectName="PageTitle")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {title_col};")
        header_row.addWidget(lbl_title, 1)

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        close_bg = "rgba(0, 0, 0, 0.05)" if is_light else "rgba(255, 255, 255, 0.07)"
        close_col = "#475569" if is_light else "#94A3B8"
        btn_x.setStyleSheet(f"""
            QPushButton {{
                background: {close_bg};
                color: {close_col};
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.45);
                color: #FFFFFF;
            }}
        """)
        btn_x.clicked.connect(self._on_close_clicked)
        header_row.addWidget(btn_x)

        layout.addLayout(header_row)

        # ─── Бейджи версий ───
        ver_row = QHBoxLayout()
        ver_row.setSpacing(10)

        lbl_curr_ver = QLabel(f"Установлена: v{APP_VERSION}")
        lbl_curr_ver.setStyleSheet("background: rgba(148, 163, 184, 0.15); border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; color: #94A3B8;")

        lbl_arrow = QLabel("➔")
        lbl_arrow.setStyleSheet(f"color: {accent}; font-weight: bold;")

        lbl_new_ver = QLabel(f"Новая: v{self.release_info.version}")
        lbl_new_ver.setStyleSheet(f"background: rgba(0, 216, 144, 0.18); border: 1px solid {accent}; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: bold; color: {accent};")

        ver_row.addWidget(lbl_curr_ver)
        ver_row.addWidget(lbl_arrow)
        ver_row.addWidget(lbl_new_ver)
        ver_row.addStretch()

        if self.release_info.asset_size > 0:
            size_mb = self.release_info.asset_size / (1024 * 1024)
            lbl_size = QLabel(f"Размер: {size_mb:.1f} МБ")
            lbl_size.setStyleSheet("font-size: 12px; color: #64748B;")
            ver_row.addWidget(lbl_size)

        layout.addLayout(ver_row)

        # ─── Список изменений (Changelog) ───
        lbl_notes_title = QLabel("Что нового в этой версии:")
        lbl_notes_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {title_col};")
        layout.addWidget(lbl_notes_title)

        self.txt_notes = QTextBrowser()
        self.txt_notes.setOpenExternalLinks(True)
        notes_bg = "rgba(255, 255, 255, 0.7)" if is_light else "rgba(15, 23, 42, 0.6)"
        notes_col = "#0F172A" if is_light else "#E2E8F0"
        self.txt_notes.setStyleSheet(f"""
            QTextBrowser {{
                background: {notes_bg};
                color: {notes_col};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.4;
            }}
        """)
        
        # Преобразование Markdown в HTML
        raw_body = self.release_info.body or "Описание релиза не предоставлено разработчиком."
        formatted_html = self._format_markdown_to_html(raw_body)
        self.txt_notes.setHtml(formatted_html)
        layout.addWidget(self.txt_notes, 1)

        # ─── Секция прогресса загрузки ───
        self.progress_container = QWidget()
        self.progress_lay = QVBoxLayout(self.progress_container)
        self.progress_lay.setContentsMargins(0, 4, 0, 4)
        self.progress_lay.setSpacing(4)

        self.lbl_progress_status = QLabel("Подготовка к загрузке...")
        self.lbl_progress_status.setStyleSheet("font-size: 12px; color: #94A3B8;")
        self.progress_lay.addWidget(self.lbl_progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: 5px;
            }}
        """)
        self.progress_lay.addWidget(self.progress_bar)

        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)

        # ─── Кнопки управления ───
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_gh = QPushButton("Открыть на GitHub", objectName="SecondaryButton")
        self.btn_gh.setIcon(get_svg_icon("github"))
        self.btn_gh.setMinimumHeight(36)
        self.btn_gh.clicked.connect(self._open_github_page)

        self.btn_install = QPushButton("⚡ Скачать и установить", objectName="PrimaryButton")
        self.btn_install.setIcon(get_svg_icon("download", color="#020617" if not is_light else "#FFFFFF"))
        self.btn_install.setMinimumHeight(36)
        self.btn_install.clicked.connect(self._start_download_and_install)

        self.btn_later = QPushButton("Напомнить позже", objectName="SecondaryButton")
        self.btn_later.setMinimumHeight(36)
        self.btn_later.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_gh)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_later)
        btn_box.addWidget(self.btn_install)

        layout.addLayout(btn_box)
        root_lay.addWidget(self.card)

    def _format_markdown_to_html(self, md_text: str) -> str:
        """Простой конвертер базового Markdown в чистый HTML для QTextBrowser."""
        import html
        escaped = html.escape(md_text)
        # Жирный текст **текст**
        escaped = escaped.replace("**", "<b>", 1)
        while "**" in escaped:
            escaped = escaped.replace("**", "</b>", 1)
            if "**" in escaped:
                escaped = escaped.replace("**", "<b>", 1)
        # Переводы строк
        lines = escaped.split("\n")
        html_lines = []
        for l in lines:
            l_strip = l.strip()
            if l_strip.startswith("### "):
                html_lines.append(f"<h4 style='margin: 4px 0; color: #00d890;'>{l_strip[4:]}</h4>")
            elif l_strip.startswith("## "):
                html_lines.append(f"<h3 style='margin: 6px 0; color: #00d890;'>{l_strip[3:]}</h3>")
            elif l_strip.startswith("# "):
                html_lines.append(f"<h2 style='margin: 8px 0; color: #00d890;'>{l_strip[2:]}</h2>")
            elif l_strip.startswith("- ") or l_strip.startswith("* "):
                html_lines.append(f"<div style='margin-left: 10px;'>• {l_strip[2:]}</div>")
            else:
                html_lines.append(f"<p style='margin: 2px 0;'>{l}</p>")
        return "".join(html_lines)

    def _open_github_page(self):
        url = self.release_info.html_url
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _start_download_and_install(self):
        download_url = self.release_info.asset_download_url
        if not download_url:
            # Если прямой бинарный ассет отсутствует, открываем страницу релиза
            ToastNotification.show_toast(self, "Прямой файл установки не найден. Открываем GitHub...", "INFO")
            self._open_github_page()
            self.accept()
            return

        self.btn_install.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress_container.setVisible(True)
        self.lbl_progress_status.setText("Подключение к серверу загрузки...")

        filename = self.release_info.asset_name or f"WaterMetrics_v{self.release_info.version}.exe"
        self.downloader = GitHubAssetDownloader(download_url, filename, self)
        self.downloader.progress.connect(self._on_download_progress)
        self.downloader.finished.connect(self._on_download_finished)
        self.downloader.failed.connect(self._on_download_failed)
        self.downloader.start()

    @Slot(int, int, int)
    def _on_download_progress(self, percent: int, bytes_read: int, total_bytes: int):
        self.progress_bar.setValue(percent)
        mb_read = bytes_read / (1024 * 1024)
        mb_total = total_bytes / (1024 * 1024) if total_bytes > 0 else 0
        if mb_total > 0:
            self.lbl_progress_status.setText(f"Загрузка: {mb_read:.1f} / {mb_total:.1f} МБ ({percent}%)")
        else:
            self.lbl_progress_status.setText(f"Загрузка: {mb_read:.1f} МБ")

    @Slot(str)
    def _on_download_finished(self, temp_file_path: str):
        self.lbl_progress_status.setText("✅ Загрузка завершена! Применение обновления...")
        self.progress_bar.setValue(100)

        # Вызов WindowsUpdateDeployer
        ok = WindowsUpdateDeployer.apply_update(temp_file_path)
        if ok:
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                ToastNotification.show_toast(self.parent() or self, "Перезапуск для применения обновления...", "SUCCESS")
                QTimer.singleShot(1000, QApplication.quit)
            else:
                ToastNotification.show_toast(self.parent() or self, f"Обновление сохранено: {os.path.basename(temp_file_path)}", "SUCCESS")
                self.accept()
        else:
            ToastNotification.show_toast(self, "Не удалось запустить скрипт обновления", "ERROR")
            self.btn_install.setEnabled(True)
            self.btn_later.setEnabled(True)

    @Slot(str)
    def _on_download_failed(self, error_msg: str):
        self.lbl_progress_status.setText(f"❌ {error_msg}")
        ToastNotification.show_toast(self, error_msg, "ERROR")
        self.btn_install.setEnabled(True)
        self.btn_later.setEnabled(True)

    def _on_close_clicked(self):
        if self.downloader and self.downloader.isRunning():
            self.downloader.cancel()
            self.downloader.wait(500)
        self.reject()
