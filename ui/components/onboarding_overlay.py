"""
ui/components/onboarding_overlay.py
Минималистичный интерактивный оверлей обучения (Мастер первой проводки).
Реализует эстетичный Spotlight (вырез с мягкой подсветкой) вокруг активного элемента,
плавающую карточку в стиле Apple Frosted Glass и мгновенную загрузку демо-данных.
"""

from typing import List, Callable, Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QFrame
)
from PySide6.QtCore import (
    Qt, QPoint, QRect, QSize, QSettings, Signal,
    QPropertyAnimation, QEasingCurve, QTimer
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPen, QBrush, QKeyEvent, QResizeEvent
)

from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard


class OnboardingStep:
    """Модель одного шага обучения."""
    def __init__(
        self,
        title: str,
        description: str,
        target_getter: Callable[[], Optional[QWidget]],
        show_demo_btn: bool = False,
        page_index: int = 0
    ):
        self.title = title
        self.description = description
        self.target_getter = target_getter
        self.show_demo_btn = show_demo_btn
        self.page_index = page_index


class OnboardingOverlay(QWidget):
    """
    Полноэкранный прозрачный оверлей с динамическим вырезом (Spotlight)
    и плавающей карточкой подсказок.
    """
    finished = Signal()
    demo_requested = Signal()

    def __init__(self, parent: QWidget, steps: List[OnboardingStep]):
        super().__init__(parent)
        self.steps = steps
        self.current_step_idx = 0

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._init_card()
        self.update_geometry_to_parent()

    def update_geometry_to_parent(self):
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())

    def _init_card(self):
        self.card = HoverGlassCard(self)
        self.card.setFixedWidth(400)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 16, 20, 16)
        self.card_layout.setSpacing(10)

        # ─── Верхняя строка: Бейдж шага + Кнопка закрытия ───
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.lbl_step_badge = QLabel("Шаг 1 из 5")

        self.btn_skip = QPushButton("✕")
        self.btn_skip.setFixedSize(26, 26)
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.setToolTip("Пропустить обучение (Esc)")
        self.btn_skip.clicked.connect(self.skip_tour)

        top_row.addWidget(self.lbl_step_badge)
        top_row.addStretch()
        top_row.addWidget(self.btn_skip)
        self.card_layout.addLayout(top_row)

        # ─── Заголовок и Описание ───
        self.lbl_title = QLabel("Заголовок шага")
        self.lbl_title.setWordWrap(True)
        self.card_layout.addWidget(self.lbl_title)

        self.lbl_desc = QLabel("Описание шага...")
        self.lbl_desc.setWordWrap(True)
        self.card_layout.addWidget(self.lbl_desc)

        # ─── Кнопка демо-данных (на шаге 1) ───
        self.btn_demo = QPushButton("✨ Загрузить демо-данные для теста", objectName="AccentButton")
        self.btn_demo.setMinimumHeight(34)
        self.btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_demo.clicked.connect(self._on_demo_clicked)
        self.card_layout.addWidget(self.btn_demo)

        # ─── Нижняя панель навигации: [Назад] [Далее] ───
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_prev = QPushButton("‹ Назад", objectName="SecondaryButton")
        self.btn_prev.setMinimumHeight(32)
        self.btn_prev.clicked.connect(self.prev_step)

        self.btn_next = QPushButton("Далее ›", objectName="PrimaryButton")
        self.btn_next.setMinimumHeight(32)
        self.btn_next.clicked.connect(self.next_step)

        btn_box.addWidget(self.btn_prev)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_next)
        self.card_layout.addLayout(btn_box)
        self._update_theme_styles()

    def _update_theme_styles(self):
        """Применение стилей выбранной темы оформления ко всем элементам оверлея."""
        t_name = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color(t_name)
        is_light = t_name in ("Pearl Light", "Как дома")

        if t_name == "Как дома":
            self.lbl_step_badge.setStyleSheet("""
                background: #0A246A;
                color: #FFFFFF;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 3px;
            """)
            self.lbl_title.setStyleSheet("font-size: 14.5px; font-weight: bold; color: #0A246A; background: transparent;")
            self.lbl_desc.setStyleSheet("font-size: 12px; line-height: 1.4; color: #000000; background: transparent;")
            self.btn_skip.setStyleSheet("""
                QPushButton {
                    background: #ECE9D8;
                    color: #000000;
                    border: 1px solid #7F9DB9;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #EF4444;
                    color: #FFFFFF;
                }
            """)
            self.btn_demo.setStyleSheet("""
                QPushButton {
                    background: #0A246A;
                    color: #FFFFFF;
                    border: 1px solid #000000;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background: #005A9E;
                }
            """)
            self.btn_prev.setStyleSheet("""
                QPushButton {
                    background: #ECE9D8;
                    color: #000000;
                    border: 1px solid #7F9DB9;
                    border-radius: 3px;
                    font-weight: 600;
                    padding: 5px 12px;
                }
                QPushButton:hover {
                    background: #DFDBC8;
                }
            """)
            self.btn_next.setStyleSheet("""
                QPushButton {
                    background: #0A246A;
                    color: #FFFFFF;
                    border: 1px solid #000000;
                    border-radius: 3px;
                    font-weight: bold;
                    padding: 5px 16px;
                }
                QPushButton:hover {
                    background: #005A9E;
                }
            """)
        elif is_light:
            self.lbl_step_badge.setStyleSheet(f"""
                background: rgba(2, 128, 144, 0.15);
                color: #028090;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 6px;
            """)
            self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A; background: transparent;")
            self.lbl_desc.setStyleSheet("font-size: 12px; line-height: 1.4; color: #334155; background: transparent;")
            self.btn_skip.setStyleSheet("""
                QPushButton {
                    background: #E2E8F0;
                    color: #64748B;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.3);
                    color: #EF4444;
                }
            """)
            self.btn_demo.setStyleSheet(f"""
                QPushButton {{
                    background: #028090;
                    color: #FFFFFF;
                    border: 1px solid #028090;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background: #00A896;
                }}
            """)
            self.btn_prev.setStyleSheet("""
                QPushButton {
                    background: #E2E8F0;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    font-weight: 600;
                    padding: 5px 12px;
                }
                QPushButton:hover {
                    background: #CBD5E1;
                }
            """)
            self.btn_next.setStyleSheet(f"""
                QPushButton {{
                    background: #028090;
                    color: #FFFFFF;
                    border: 1px solid #028090;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 5px 16px;
                }}
                QPushButton:hover {{
                    background: #00A896;
                }}
            """)
        else:
            self.lbl_step_badge.setStyleSheet(f"""
                background: rgba(0, 216, 144, 0.15);
                color: {accent};
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 6px;
            """)
            self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF; background: transparent;")
            self.lbl_desc.setStyleSheet("font-size: 12px; line-height: 1.4; color: #CBD5E1; background: transparent;")
            self.btn_skip.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    color: #94A3B8;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.4);
                    color: #FFFFFF;
                }
            """)
            self.btn_demo.setStyleSheet(f"""
                QPushButton {{
                    background: {accent};
                    color: #020617;
                    border: 1px solid {accent};
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background: #FFFFFF;
                }}
            """)
            self.btn_prev.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.10);
                    color: #FFFFFF;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    font-weight: 600;
                    padding: 5px 12px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.18);
                }
            """)
            self.btn_next.setStyleSheet(f"""
                QPushButton {{
                    background: {accent};
                    color: #020617;
                    border: 1px solid {accent};
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 5px 16px;
                }}
                QPushButton:hover {{
                    background: #FFFFFF;
                }}
            """)

        self.btn_demo.setIcon(get_svg_icon("sparkles", color="#FFFFFF" if is_light else "#020617"))

    def start(self):
        """Запуск показа онбординга."""
        self.current_step_idx = 0
        self.update_geometry_to_parent()
        self._update_theme_styles()
        self.show()
        self.raise_()
        self.setFocus()
        QTimer.singleShot(50, self._show_current_step)

    def _show_current_step(self):
        if not self.steps or self.current_step_idx >= len(self.steps):
            self.finish_tour()
            return

        step = self.steps[self.current_step_idx]

        # Если шаг требует определенной страницы в главном окне
        if hasattr(self.parent(), 'switch_page') and hasattr(step, 'page_index'):
            self.parent().switch_page(step.page_index)

        # Обновление текстов
        total = len(self.steps)
        self.lbl_step_badge.setText(f"Шаг {self.current_step_idx + 1} из {total}")
        self.lbl_title.setText(step.title)
        self.lbl_desc.setText(step.description)

        # Кнопка демо-данных
        self.btn_demo.setVisible(step.show_demo_btn)

        # Состояние кнопок Назад / Далее
        self.btn_prev.setEnabled(self.current_step_idx > 0)
        if self.current_step_idx == total - 1:
            self.btn_next.setText("Завершить 🎉")
        else:
            self.btn_next.setText("Далее ›")

        self._update_theme_styles()
        # Перемещение карточки и перерисовка
        self._position_card()
        self.update()

    def _get_target_rect(self) -> Optional[QRect]:
        if not self.steps or self.current_step_idx >= len(self.steps):
            return None
        step = self.steps[self.current_step_idx]
        target = step.target_getter()
        if not target or not target.isVisible():
            return None

        # Маппинг абсолютных глобальных координат в локальные координаты оверлея
        try:
            g_pos = target.mapToGlobal(QPoint(0, 0))
            local_pos = self.mapFromGlobal(g_pos)
            return QRect(local_pos, target.size())
        except Exception:
            return None

    def _position_card(self):
        target_rect = self._get_target_rect()
        card_w = self.card.width()
        card_h = self.card.sizeHint().height()
        self.card.setFixedHeight(card_h)

        if not target_rect:
            # Центрируем карточку, если цель не найдена
            x = (self.width() - card_w) // 2
            y = (self.height() - card_h) // 2
            self.card.move(max(10, x), max(10, y))
            return

        # Пытаемся разместить снизу от цели
        margin = 14
        x = target_rect.center().x() - (card_w // 2)
        y = target_rect.bottom() + margin

        # Если снизу не влезает, размещаем сверху
        if y + card_h > self.height() - 20:
            y = target_rect.top() - card_h - margin

        # Если и сверху не влезает, размещаем сбоку (справа или слева)
        if y < 20:
            y = max(20, min(self.height() - card_h - 20, target_rect.center().y() - (card_h // 2)))
            if target_rect.right() + card_w + margin < self.width():
                x = target_rect.right() + margin
            else:
                x = max(10, target_rect.left() - card_w - margin)

        # Ограничиваем границами окна
        x = max(16, min(self.width() - card_w - 16, x))
        y = max(16, min(self.height() - card_h - 16, y))

        self.card.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Полноэкранный полупрозрачный слой
        overlay_path = QPainterPath()
        overlay_path.addRect(0, 0, self.width(), self.height())

        target_rect = self._get_target_rect()
        accent = ThemeManager.get_current_accent_color()

        if target_rect:
            # Мягкий вырез вокруг цели
            pad = 8
            spot_rect = target_rect.adjusted(-pad, -pad, pad, pad)
            spot_path = QPainterPath()
            spot_path.addRoundedRect(spot_rect, 12, 12)

            # Вычитаем вырез из оверлея
            draw_path = overlay_path.subtracted(spot_path)
            painter.fillPath(draw_path, QColor(0, 0, 0, 175))

            # Рисуем светящуюся рамку вокруг выреза
            pen = QPen(QColor(accent), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(spot_rect, 12, 12)
        else:
            painter.fillPath(overlay_path, QColor(0, 0, 0, 175))

        painter.end()

    def mousePressEvent(self, event):
        # Блокируем клики мимо карточки
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.skip_tour()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Right, Qt.Key.Key_Space):
            self.next_step()
            event.accept()
        elif event.key() == Qt.Key.Key_Left:
            self.prev_step()
            event.accept()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_geometry_to_parent()
        self._position_card()

    def next_step(self):
        if self.current_step_idx < len(self.steps) - 1:
            self.current_step_idx += 1
            self._show_current_step()
        else:
            self.finish_tour()

    def prev_step(self):
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self._show_current_step()

    def skip_tour(self):
        self._save_completed_flag()
        self.hide()
        self.finished.emit()

    def finish_tour(self):
        self._save_completed_flag()
        self.hide()
        self.finished.emit()

    def _save_completed_flag(self):
        settings = QSettings("WaterMetrics", "Onboarding")
        settings.setValue("FirstRunCompleted", True)

    def _on_demo_clicked(self):
        self.demo_requested.emit()
        # После клика переходим на следующий шаг через небольшую паузу
        QTimer.singleShot(400, self.next_step)
