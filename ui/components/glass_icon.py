# ui/components/glass_icon.py
"""
GlassIconWidget — контейнер иконки с настоящим frosted glass эффектом.
Захватывает пиксели фона позади себя вне paintEvent (асинхронно через QTimer),
применяет Gaussian blur, рисует матовый оверлей и SVG-иконку поверх.
"""

from PySide6.QtWidgets import QLabel, QApplication, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, QSize, QByteArray, QTimer
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPixmap, QPen, QBrush
)
from PySide6.QtSvg import QSvgRenderer

from ui.styles import SVG_ICONS, ThemeManager


class GlassIconWidget(QLabel):
    """
    Интерактивный или декоративный контейнер иконки с матовым стеклом (Frosted Glass),
    размытием фона позади себя, матовым оверлеем, верхним бликом и SVG-иконкой.
    """

    def __init__(self, svg_name: str = "about", color: str = None, size: QSize = QSize(40, 40), blur_radius: int = 18, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassIconWidget")
        self._svg_name = svg_name
        self._color = color or ThemeManager.get_current_accent_color()
        self._blur_radius = blur_radius
        self._cached_blurred = None
        self._snapshot_pending = False

        self.setFixedSize(size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        ThemeManager.on_theme_changed.append(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str = None):
        accent = ThemeManager.get_current_accent_color()
        self.set_color(accent)

    def set_color(self, color: str):
        self._color = color
        self.invalidate_cache()

    def set_svg(self, svg_name: str):
        self._svg_name = svg_name
        self.invalidate_cache()

    def invalidate_cache(self):
        self._cached_blurred = None
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.invalidate_cache()

    def showEvent(self, event):
        super().showEvent(event)
        self.invalidate_cache()

    def _update_snapshot(self):
        self._snapshot_pending = False
        if not self.isVisible():
            return
        root = self.window()
        if not root or not root.isVisible():
            return
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        try:
            pos_in_root = self.mapTo(root, QPoint(0, 0))
            bg_rect = QRect(pos_in_root, self.size())
            bg_pixmap = root.grab(bg_rect)

            if not bg_pixmap.isNull():
                scene = QGraphicsScene()
                item = QGraphicsPixmapItem(bg_pixmap)
                effect = QGraphicsBlurEffect()
                effect.setBlurRadius(self._blur_radius)
                item.setGraphicsEffect(effect)
                scene.addItem(item)

                blurred = QPixmap(self.size())
                blurred.fill(Qt.GlobalColor.transparent)
                blur_painter = QPainter()
                if blur_painter.begin(blurred):
                    blur_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    scene.render(blur_painter, target=QRectF(0, 0, w, h), source=QRectF(item.boundingRect()))
                    blur_painter.end()
                    self._cached_blurred = blurred
                else:
                    self._cached_blurred = bg_pixmap
                self.update()
        except Exception:
            pass

    def paintEvent(self, event):
        if not self.isVisible():
            return

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        # Планируем захват фона асинхронно ВНЕ paintEvent для предотвращения рекурсивного repaint
        if self._cached_blurred is None and not self._snapshot_pending:
            self._snapshot_pending = True
            QTimer.singleShot(40, self._update_snapshot)

        painter = QPainter()
        if not painter.begin(self):
            return

        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 1. Клип по скругленному прямоугольнику
            path = QPainterPath()
            path.addRoundedRect(self.rect(), 14, 14)
            painter.setClipPath(path)

            # 2. Отрисовка размытого фона (если готов) или полупрозрачная подложка
            if self._cached_blurred and not self._cached_blurred.isNull():
                painter.drawPixmap(0, 0, self._cached_blurred)
            else:
                painter.fillPath(path, QColor(255, 255, 255, 20))

            # 3. Матовый оверлей (frosted glass layer)
            painter.fillPath(path, QColor(255, 255, 255, 28))

            # 4. Highlight-бордер (верхняя и боковые грани)
            pen = QPen(QColor(255, 255, 255, 100))
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 13, 13)

            # Дополнительная усиленная верхняя грань
            if w > 28:
                painter.setPen(QPen(QColor(255, 255, 255, 160)))
                painter.drawLine(14, 1, w - 14, 1)

            # 5. Векторная SVG-иконка
            svg_str = SVG_ICONS.get(self._svg_name, SVG_ICONS["about"])
            colored = svg_str.replace('stroke="currentColor"', f'stroke="{self._color}"').replace('fill="currentColor"', f'fill="{self._color}"')
            renderer = QSvgRenderer(QByteArray(colored.encode('utf-8')))

            margin = max(4, w // 4)
            icon_rect = self.rect().adjusted(margin, margin, -margin, -margin)
            renderer.render(painter, icon_rect)
        finally:
            painter.end()
