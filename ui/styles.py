# ui/styles.py
"""
Единая дизайн-система WaterMetrics в стиле Apple Frosted Glass.
Содержит реестр векторных SVG-иконок high-DPI,
утилитную функцию get_svg_icon() и менеджер тем оформления ThemeManager.
"""

from PySide6.QtCore import QSettings, QSize, QByteArray, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

# ==============================================================================
# РЕЕСТР ВЕКТОРНЫХ SVG-ИКОНОК (APPLE CONTROL CENTER STYLE)
# ==============================================================================
SVG_ICONS = {
    "dashboard": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="9" rx="1.5"/>
        <rect x="14" y="3" width="7" height="5" rx="1.5"/>
        <rect x="14" y="12" width="7" height="9" rx="1.5"/>
        <rect x="3" y="16" width="7" height="5" rx="1.5"/>
    </svg>""",

    "norms": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.4 2.4 0 0 1 0-3.4l2.6-2.6a2.4 2.4 0 0 1 3.4 0l12.6 12.6z"/>
        <path d="m14.5 12.5 2-2"/>
        <path d="m11.5 9.5 2-2"/>
        <path d="m8.5 6.5 2-2"/>
        <path d="m17.5 15.5 2-2"/>
    </svg>""",

    "logs": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="4 17 10 11 4 5"/>
        <line x1="12" y1="19" x2="20" y2="19"/>
    </svg>""",

    "tests": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 2v7.31L4.75 18.1A2 2 0 0 0 6.47 21h11.06a2 2 0 0 0 1.72-2.9L14 9.31V2"/>
        <line x1="8.5" y1="2" x2="15.5" y2="2"/>
        <path d="M8.5 14h7"/>
    </svg>""",

    "about": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>""",

    "run": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>""",

    "replace": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.5 2v6h-6"/>
        <path d="M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
    </svg>""",

    "folder": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    </svg>""",

    "trash": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    </svg>""",

    "edit": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
    </svg>""",

    "search": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>""",

    "plus": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>""",

    "save": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
        <polyline points="17 21 17 13 7 13 7 21"/>
        <polyline points="7 3 7 8 15 8"/>
    </svg>""",

    "toggle": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
    </svg>""",

    "pin": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="17" x2="12" y2="22"/>
        <path d="M5 17h14v-2l-2.5-3.5V5h1V2H6.5v3h1v6.5L5 15v2z"/>
    </svg>""",

    "unpin": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="2" y1="2" x2="22" y2="22"/>
        <path d="M12 17v5"/>
        <path d="M9 9v2.5L6.5 15v2h10.5"/>
        <path d="M15 9.34V5h1V2H7.5v3h1v1.34"/>
    </svg>""",

    "tray": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="4" width="20" height="12" rx="2"/>
        <path d="M6 16v2a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-2"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <polyline points="9 11 12 14 15 11"/>
    </svg>""",

    "minimize": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="12" x2="19" y2="12"/>
    </svg>""",

    "window_restore": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
        <line x1="4" y1="9" x2="20" y2="9"/>
    </svg>""",

    "droplet": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
    </svg>""",

    "flame": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 3.5z"/>
    </svg>""",

    "copy": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>""",

    "x": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
    </svg>""",

    "github": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/>
        <path d="M9 18c-4.51 2-5-2-7-2"/>
    </svg>""",

    "update": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
        <path d="M12 8v4l3 3"/>
    </svg>""",

    "sparkles": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
        <path d="M5 3v4"/>
        <path d="M19 17v4"/>
        <path d="M3 5h4"/>
        <path d="M17 19h4"/>
    </svg>""",

    "download": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>""",

    "check_circle": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>""",

    "help_wizard": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>""",

    "mail": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="20" height="16" x="2" y="4" rx="2"/>
        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
    </svg>""",

    "external_link": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/>
        <line x1="10" y1="14" x2="21" y2="3"/>
    </svg>""",

    "feedback": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        <path d="M12 7v6"/>
        <path d="M12 17h.01"/>
    </svg>"""
}


def get_svg_icon(name: str, color: str = "#94A3B8", checked_color: str = None, size: QSize = QSize(20, 20)) -> QIcon:
    """Генерация двухрежимного векторного QIcon из SVG-строки с высокой четкостью (High-DPI)."""
    if checked_color is None:
        checked_color = ThemeManager.get_current_accent_color()

    svg_str = SVG_ICONS.get(name, SVG_ICONS["about"])
    icon = QIcon()
    for state, col in [(QIcon.State.Off, color), (QIcon.State.On, checked_color)]:
        colored_svg = svg_str.replace('stroke="currentColor"', f'stroke="{col}"').replace('fill="currentColor"', f'fill="{col}"')
        renderer = QSvgRenderer(QByteArray(colored_svg.encode('utf-8')))

        pixmap = QPixmap(size.width() * 2, size.height() * 2)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter()
        if painter.begin(pixmap):
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter)
            painter.end()

        pixmap.setDevicePixelRatio(2.0)
        icon.addPixmap(pixmap, QIcon.Mode.Normal, state)
        icon.addPixmap(pixmap, QIcon.Mode.Active, state)
    return icon


# ==============================================================================
# ТЕМЫ ОФОРМЛЕНИЯ APPLE FROSTED GLASS
# ==============================================================================
DARK_AZURE_QSS = """
/* OceanWidget рисует фон сам в paintEvent — QSS-фон не нужен */
QWidget#MainContainer, QWidget#OceanBackground {
    background: transparent;
}
/* Страницы прозрачны -> показывают фон РОДИТЕЛЯ (OceanWidget = океан) */
QWidget#DashboardPage,
QWidget#NormsPage,
QWidget#LogsPage,
QWidget#AutoTestsPage,
QWidget#AboutPage {
    background: transparent;
    color: #F8FAFC;
    font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
}

QWidget {
    font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
    color: #F8FAFC;
}

QStackedWidget {
    background: transparent;
}

/* Оформление матовых диалоговых окон QDialog в стиле Apple Frosted Glass */
QDialog {
    background: qradialgradient(cx:0.5, cy:0.2, radius:1.2, fx:0.5, fy:0.2,
                stop:0 #1F4257, stop:0.6 #071E3D, stop:1 #030F26);
    color: #F8FAFC;
    border: 1.5px solid rgba(0, 242, 254, 0.4);
    border-top: 1.5px solid rgba(255, 255, 255, 0.45);
    border-radius: 20px;
}

.icon-badge, QLabel#IconBadge {
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-top: 1.5px solid rgba(255, 255, 255, 0.42);
    border-bottom: 1px solid rgba(0, 0, 0, 0.25);
    border-radius: 14px;
    padding: 8px;
}

QFrame#GlassCard, QFrame[glass="true"] {
    background-color: #0B1736;
    border: 1px solid rgba(0, 242, 254, 0.22);
    border-top: 1.5px solid rgba(255, 255, 255, 0.35);
    border-radius: 18px;
}

QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {
    background-color: #0F2048;
    border: 1.5px solid #00F2FE;
    border-top: 2px solid #FFFFFF;
    border-radius: 18px;
}

QFrame#GlassCard[drag="true"] {
    background-color: rgba(0, 242, 254, 0.12);
    border: 2px dashed #00F2FE;
    border-radius: 14px;
}

QFrame#GlassCard[state="linked"] {
    background-color: rgba(0, 242, 254, 0.08);
    border: 1.5px solid #00F2FE;
    border-radius: 14px;
}

QFrame#GlassCard[state="warning"] {
    background-color: rgba(248, 113, 113, 0.10);
    border: 1.5px solid #F87171;
    border-radius: 14px;
}

QFrame#ControlPanelContainer {
    background-color: #071026;
    border: 1px solid rgba(0, 242, 254, 0.35);
    border-radius: 14px;
}

QFrame#SidebarPanel {
    background-color: #050B1E;
    border-right: 1.5px solid rgba(0, 242, 254, 0.35);
}

QFrame#CustomTitleBar {
    background-color: rgba(5, 11, 30, 0.90);
    border-top: 2px solid #00F2FE;
    border-bottom: 1px solid rgba(0, 242, 254, 0.25);
}
QLabel#TitleLabel {
    color: #CBD5E1;
    font-weight: 600;
    font-size: 13px;
    background: transparent;
}
QPushButton#TitlePaletteBtn {
    background-color: rgba(0, 242, 254, 0.08);
    border: 1px solid rgba(0, 242, 254, 0.25);
    border-radius: 6px;
    color: #00F2FE;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    min-height: 20px;
}
QPushButton#TitlePaletteBtn:hover {
    background-color: rgba(0, 242, 254, 0.20);
    border-color: #00F2FE;
    color: #FFFFFF;
}
QPushButton#ArcusModeButton {
    background-color: rgba(0, 242, 254, 0.08);
    border: 1px solid rgba(0, 242, 254, 0.35);
    border-radius: 8px;
    padding: 5px 12px;
    color: #00F2FE;
    font-weight: 600;
    font-size: 12px;
    min-height: 22px;
}
QPushButton#ArcusModeButton:hover {
    background-color: rgba(0, 242, 254, 0.20);
    border: 1px solid #00F2FE;
    color: #FFFFFF;
}
QPushButton#ArcusModeButton:checked {
    background-color: #00A896;
    border: 1px solid #00F2FE;
    color: #020617;
}
QPushButton#TitleMinBtn, QPushButton#TitleMaxBtn {
    background: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#TitleMinBtn:hover, QPushButton#TitleMaxBtn:hover {
    background-color: rgba(0, 242, 254, 0.16);
    color: #00F2FE;
}
QPushButton#TitleCloseBtn {
    background: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#TitleCloseBtn:hover {
    background-color: #EF4444;
    color: #FFFFFF;
}

QScrollArea, QScrollArea > QWidget > QWidget {
    background: transparent !important;
    border: none;
}

QLabel { color: #F8FAFC; font-size: 13px; }
QLabel#PageTitle { color: #F8FAFC; font-size: 22px; font-weight: 700; }
QLabel#SectionTitle { color: #00F2FE; font-size: 15px; font-weight: 600; }
QLabel#FieldLabel { color: #94A3B8; font-size: 13px; font-weight: 600; }

QLineEdit {
    background-color: #0E1D42;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 10px;
    padding: 8px 12px;
    color: #FFFFFF;
    font-size: 13px;
    selection-background-color: #028090;
    selection-color: #FFFFFF;
}

/* Минималистичный стеклянный выпадающий список QComboBox */
QComboBox {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 6px 12px;
    color: #F8FAFC;
    font-size: 12px;
    font-weight: 500;
}
QComboBox:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.25);
}
QComboBox:focus, QComboBox:on {
    background-color: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.35);
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
    border-left: 2px solid rgba(255, 255, 255, 0.45);
    border-bottom: 2px solid rgba(255, 255, 255, 0.45);
    border-top: none;
    border-right: none;
    margin-right: 8px;
    margin-top: -4px;
}
QComboBox::down-arrow:on {
    border-left: 2px solid #00F2FE;
    border-bottom: 2px solid #00F2FE;
    margin-top: 4px;
}

/* Ошибка валидации: красная граница при неверном вводе */
QLineEdit[invalid="true"] {
    border: 1.5px solid #EF4444 !important;
    background-color: rgba(239, 68, 68, 0.12) !important;
}

/* Эффект свечения граней (Glow Effect) при фокусе QLineEdit */
QLineEdit:focus {
    border: 2px solid #00F2FE;
    background-color: #122554;
}

QComboBox QAbstractItemView {
    background-color: #0B1736;
    border: 1.5px solid #00F2FE;
    border-radius: 10px;
    padding: 4px;
    color: #FFFFFF;
    selection-background-color: #028090;
    selection-color: #FFFFFF;
    outline: none;
}

QPushButton#PrimaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #028090, stop:0.5 #00A896, stop:1 #00F2FE);
    color: #020617;
    font-weight: 700;
    font-size: 13px;
    border-radius: 10px;
    padding: 9px 18px;
    border: none;
    min-height: 24px;
    qproperty-iconSize: 18px 18px;
}
QPushButton#PrimaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00A896, stop:1 #00F2FE);
}
QPushButton#PrimaryButton:disabled { background: rgba(30, 41, 59, 0.5); color: #64748B; }

QPushButton#SecondaryButton {
    background-color: rgba(255, 255, 255, 0.08);
    color: #F8FAFC;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 7px 14px;
    min-height: 20px;
    qproperty-iconSize: 16px 16px;
}
QPushButton#SecondaryButton:hover {
    background-color: rgba(255, 255, 255, 0.16);
    border-color: #00F2FE;
    color: #00F2FE;
}

QPushButton#AccentButton {
    background-color: rgba(0, 242, 254, 0.12);
    color: #00F2FE;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid rgba(0, 242, 254, 0.35);
    border-top: 1px solid rgba(0, 242, 254, 0.6);
    border-radius: 10px;
    padding: 8px 16px;
    min-height: 22px;
    qproperty-iconSize: 18px 18px;
}
QPushButton#AccentButton:hover {
    background-color: rgba(0, 242, 254, 0.22);
    border-color: #00F2FE;
}

QPushButton#DangerButton {
    background-color: rgba(239, 68, 68, 0.15);
    color: #F87171;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 10px;
    padding: 7px 14px;
    min-height: 20px;
    qproperty-iconSize: 16px 16px;
}
QPushButton#DangerButton:hover { background-color: rgba(239, 68, 68, 0.3); border-color: #EF4444; }

QPushButton.navBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
    qproperty-iconSize: 22px 22px;
}
QPushButton.navBtn:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #F8FAFC;
}
QPushButton.navBtn:checked {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-top: 1.5px solid rgba(255, 255, 255, 0.42);
    border-radius: 12px;
    color: #00F2FE;
    font-weight: 700;
}

QCheckBox { color: #F8FAFC; font-size: 13px; font-weight: 600; spacing: 6px; }
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    background-color: rgba(8, 18, 55, 0.60);
}
QCheckBox::indicator:checked { background-color: #028090; border-color: #00F2FE; }

/* ─── QSlider Слайдеры ─── */
QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #00F2FE;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00F2FE;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #FFFFFF;
    border-color: #00F2FE;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: rgba(255, 255, 255, 0.10);
    max-height: 8px;
    text-align: center;
    color: #F8FAFC;
}
QProgressBar::chunk {
    background-color: #00F2FE;
    border-radius: 4px;
}

QToolTip {
    background-color: #071026;
    color: #F8FAFC;
    border: 1px solid rgba(0, 242, 254, 0.40);
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11px;
}

QMenu {
    background-color: #0B1736;
    color: #F8FAFC;
    border: 1px solid rgba(0, 242, 254, 0.35);
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: rgba(0, 242, 254, 0.20);
    color: #00F2FE;
}

QTextEdit#LogViewer {
    background-color: #050B1E;
    color: #FFFFFF;
    border-radius: 10px;
    font-family: "Consolas", monospace;
    font-size: 12px;
    padding: 10px;
    border: 1px solid rgba(0, 242, 254, 0.30);
}

QMessageBox {
    background-color: #0F172A;
    color: #F8FAFC;
}

/* ─── Table Views ─── */
QTableWidget, QTableView {
    background-color: #071026 !important;
    alternate-background-color: #0B1736;
    border: 1.5px solid rgba(0, 242, 254, 0.35) !important;
    border-radius: 14px;
    gridline-color: rgba(255, 255, 255, 0.08);
    color: #F8FAFC;
    selection-background-color: rgba(0, 242, 254, 0.25);
    selection-color: #F8FAFC;
    outline: none;
}
QTableWidget::item, QTableView::item {
    padding: 6px 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
    min-height: 34px;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(0, 242, 254, 0.25) !important;
    color: #F8FAFC !important;
    border-left: 3px solid #00F2FE;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: rgba(0, 242, 254, 0.12);
}
QHeaderView::section {
    background-color: #0E1D42 !important;
    color: #00F2FE;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid rgba(0, 242, 254, 0.30);
    border-right: 1px solid rgba(0, 242, 254, 0.20);
    font-weight: bold;
    font-size: 12px;
    min-height: 32px;
}
QTableCornerButton::section {
    background-color: #0E1D42 !important;
    border: none;
}

/* ─── Scrollbar ─── */
QScrollBar:vertical {
    background: rgba(255, 255, 255, 0.04);
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.20);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(0, 242, 254, 0.50);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; background: transparent; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal {
    background: rgba(255, 255, 255, 0.04);
    height: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.20);
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(0, 242, 254, 0.50);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; background: transparent; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QScrollBar::corner { background: transparent; }

/* ─── QStatusBar ─── */
QStatusBar {
    background-color: #050B1E;
    color: #94A3B8;
    border-top: 1px solid rgba(0, 242, 254, 0.20);
    font-size: 12px;
    font-weight: 500;
    min-height: 26px;
    padding-left: 12px;
}
QStatusBar::item {
    border: none;
    padding-right: 10px;
}
QStatusBar QLabel {
    color: #94A3B8;
    background: transparent;
    qproperty-wordWrap: false;
    white-space: nowrap;
}
"""

PEARL_LIGHT_QSS = """
QMainWindow {
    background: transparent;
}
QWidget#MainContainer {
    background: transparent;
}
QWidget#DashboardPage,
QWidget#NormsPage,
QWidget#LogsPage,
QWidget#AutoTestsPage,
QWidget#AboutPage {
    background: transparent;
    color: #0F172A;
    font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
}

QWidget {
    font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif;
    color: #0F172A;
}

QStackedWidget {
    background: transparent;
}

QDialog {
    background: #F8FAFC;
    color: #0F172A;
    border: 1.5px solid #028090;
    border-radius: 20px;
}

.icon-badge, QLabel#IconBadge {
    background-color: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(200, 220, 240, 0.60);
    border-top: 1.5px solid rgba(255, 255, 255, 0.90);
    border-bottom: 1px solid rgba(150, 180, 210, 0.30);
    border-radius: 14px;
    padding: 8px;
}

QFrame#GlassCard, QFrame[glass="true"] {
    background-color: #F8FAFC;
    border: 1.5px solid #028090;
    border-top: 2px solid #FFFFFF;
    border-radius: 18px;
}

QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {
    background-color: #FFFFFF;
    border: 2px solid #028090;
    border-radius: 18px;
}

QFrame#GlassCard[drag="true"] {
    background-color: rgba(2, 128, 144, 0.12);
    border: 2px dashed #028090;
    border-radius: 14px;
}

QFrame#GlassCard[state="linked"] {
    background-color: rgba(2, 128, 144, 0.08);
    border: 2px solid #028090;
    border-radius: 14px;
}

QFrame#GlassCard[state="warning"] {
    background-color: rgba(239, 68, 68, 0.08);
    border: 2px solid #EF4444;
    border-radius: 14px;
}

QFrame#ControlPanelContainer {
    background-color: rgba(220, 240, 255, 0.82);
    border: 1px solid rgba(2, 128, 144, 0.35);
    border-radius: 14px;
}

QFrame#SidebarPanel {
    background-color: rgba(220, 240, 255, 0.87);
    border-right: 1px solid rgba(2, 128, 144, 0.20);
}

QFrame#CustomTitleBar {
    background: rgba(220, 240, 255, 0.95);
    border-top: 2px solid #028090;
    border-bottom: 1px solid rgba(2, 128, 144, 0.20);
}
QLabel#TitleLabel {
    color: #0F172A;
    font-weight: 600;
    font-size: 13px;
    background: transparent;
}
QPushButton#TitlePaletteBtn {
    background-color: rgba(2, 128, 144, 0.08);
    border: 1px solid rgba(2, 128, 144, 0.25);
    border-radius: 6px;
    color: #028090;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    min-height: 20px;
}
QPushButton#TitlePaletteBtn:hover {
    background-color: rgba(2, 128, 144, 0.18);
    border-color: #028090;
}
QPushButton#ArcusModeButton {
    background-color: rgba(2, 128, 144, 0.08);
    border: 1px solid rgba(2, 128, 144, 0.35);
    border-radius: 8px;
    padding: 5px 12px;
    color: #028090;
    font-weight: 600;
    font-size: 12px;
    min-height: 22px;
}
QPushButton#ArcusModeButton:hover {
    background-color: rgba(2, 128, 144, 0.18);
    border: 1px solid #028090;
    color: #0F172A;
}
QPushButton#ArcusModeButton:checked {
    background-color: #0A246A;
    border: 1px solid #0A246A;
    color: #FFFFFF;
}
QPushButton#TitleMinBtn, QPushButton#TitleMaxBtn {
    background: transparent;
    color: #475569;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#TitleMinBtn:hover, QPushButton#TitleMaxBtn:hover {
    background-color: rgba(2, 128, 144, 0.12);
    color: #028090;
}
QPushButton#TitleCloseBtn {
    background: transparent;
    color: #475569;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#TitleCloseBtn:hover {
    background-color: #EF4444;
    color: #FFFFFF;
}

QStatusBar {
    background-color: rgba(220, 240, 255, 0.95);
    border-top: 1px solid rgba(2, 128, 144, 0.20);
    color: #475569;
}
QStatusBar QLabel {
    color: #475569;
    background: transparent;
    qproperty-wordWrap: false;
    white-space: nowrap;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #E2E8F0;
    max-height: 8px;
}
QProgressBar::chunk {
    background-color: #028090;
    border-radius: 4px;
}

QScrollArea, QScrollArea > QWidget > QWidget {
    background: transparent !important;
    border: none;
}

QLabel { color: #0F172A; font-size: 13px; }
QLabel#PageTitle { color: #0F172A; font-size: 22px; font-weight: 700; }
QLabel#SectionTitle { color: #028090; font-size: 15px; font-weight: 600; }
QLabel#FieldLabel { color: #475569; font-size: 13px; font-weight: 600; }

QLineEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 8px 12px;
    color: #0F172A;
    font-size: 13px;
    selection-background-color: #028090;
    selection-color: #FFFFFF;
}

QLineEdit[invalid="true"] {
    border: 1.5px solid #EF4444 !important;
    background-color: rgba(239, 68, 68, 0.08) !important;
}

QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #028090;
    background-color: #FFFFFF;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
    border-left: 2px solid #475569;
    border-bottom: 2px solid #475569;
    border-top: none;
    border-right: none;
    margin-right: 8px;
    margin-top: -4px;
}
QComboBox::down-arrow:on {
    border-left: 2px solid #028090;
    border-bottom: 2px solid #028090;
    margin-top: 4px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #028090;
    selection-background-color: #028090;
    color: #0F172A;
    outline: none;
}

QPushButton#PrimaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #028090, stop:1 #00A896);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 13px;
    border-radius: 10px;
    padding: 9px 18px;
    border: none;
    min-height: 24px;
}
QPushButton#PrimaryButton:hover {
    background: #00A896;
}

QPushButton#SecondaryButton {
    background-color: #F1F5F9;
    color: #0F172A;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 7px 14px;
    min-height: 20px;
}
QPushButton#SecondaryButton:hover {
    background-color: #E2E8F0;
    border-color: #028090;
    color: #028090;
}

QPushButton#AccentButton {
    background-color: rgba(2, 128, 144, 0.1);
    color: #028090;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid rgba(2, 128, 144, 0.4);
    border-radius: 10px;
    padding: 8px 16px;
}

QPushButton#DangerButton {
    background-color: rgba(239, 68, 68, 0.1);
    color: #EF4444;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 10px;
    padding: 7px 14px;
}

QPushButton.navBtn {
    background-color: transparent;
    color: #64748B;
    border: none;
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}
QPushButton.navBtn:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}
QPushButton.navBtn:checked {
    background-color: rgba(255, 255, 255, 0.70);
    border: 1px solid rgba(2, 128, 144, 0.35);
    border-top: 1.5px solid rgba(255, 255, 255, 0.90);
    border-radius: 12px;
    color: #028090;
    font-weight: 700;
}

QCheckBox { color: #0F172A; font-size: 13px; font-weight: 600; spacing: 6px; }
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #CBD5E1;
    border-radius: 4px;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked { background-color: #028090; border-color: #028090; }

/* ─── QSlider Слайдеры ─── */
QSlider::groove:horizontal {
    height: 6px;
    background: #CBD5E1;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #028090;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #028090;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #00A896;
}

QTableWidget {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 14px;
    gridline-color: #F1F5F9;
}
QTableWidget::item { padding: 6px 10px; color: #0F172A; border: none; min-height: 36px; }
QTableWidget::item:selected { background-color: rgba(2, 128, 144, 0.15); color: #028090; }

QHeaderView::section {
    background-color: #F8FAFC !important;
    color: #475569;
    border: none;
    border-bottom: 1px solid #CBD5E1;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
    min-height: 32px;
}

QTextEdit#LogViewer {
    background-color: #F8FAFC;
    color: #0F172A;
    border-radius: 10px;
    font-family: "Consolas", monospace;
    font-size: 12px;
    padding: 10px;
    border: 1px solid #CBD5E1;
}

/* ─── Защита от переполнения / наслаивания ─── */
QLabel {
    qproperty-wordWrap: true;
}
QLabel#PageTitle {
    min-width: 0px;
}
QFrame#SidebarPanel {
    min-width: 60px;
}
QWidget#MainContainer, QWidget#OceanBackground {
    min-width: 0px;
}
QScrollArea {
    min-width: 0px;
}

/* ─── Table Views ─── */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    gridline-color: #E2E8F0;
    color: #0F172A;
    selection-background-color: rgba(2, 128, 144, 0.20);
    selection-color: #028090;
    outline: none;
}
QTableWidget::item, QTableView::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F1F5F9;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(2, 128, 144, 0.20);
    color: #028090;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: rgba(2, 128, 144, 0.08);
}
QHeaderView::section {
    background-color: #F1F5F9;
    color: #475569;
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #CBD5E1;
    font-weight: 600;
    font-size: 11px;
}
QTableCornerButton::section {
    background-color: #F1F5F9;
    border: none;
}

/* ─── Scrollbar ─── */
QScrollBar:vertical {
    background: rgba(2, 128, 144, 0.06);
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(2, 128, 144, 0.30);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(2, 128, 144, 0.65);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; background: transparent; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal {
    background: rgba(2, 128, 144, 0.06);
    height: 8px;
    border-radius: 4px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: rgba(2, 128, 144, 0.30);
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(2, 128, 144, 0.65);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; background: transparent; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QScrollBar::corner { background: transparent; }
"""

# --- Cyberpunk Neon: глубокий пурпурно-розовый ---
CYBERPUNK_NEON_QSS = DARK_AZURE_QSS \
    .replace("#1E1B4B", "#1A002C") \
    .replace("#0F172A", "#0D001A") \
    .replace("#020617", "#05000A") \
    .replace("#00F2FE", "#FF007F") \
    .replace("#028090", "#D9006C")
CYBERPUNK_NEON_QSS += """
QFrame#CustomTitleBar {
    background-color: rgba(18, 2, 27, 0.90);
    border-top: 2px solid #FF007F;
    border-bottom: 1px solid rgba(255, 0, 127, 0.25);
}
QPushButton#TitlePaletteBtn {
    background-color: rgba(255, 0, 127, 0.08);
    border: 1px solid rgba(255, 0, 127, 0.25);
    color: #FF007F;
}
QPushButton#TitlePaletteBtn:hover {
    background-color: rgba(255, 0, 127, 0.20);
    border-color: #FF007F;
    color: #FFFFFF;
}
QPushButton#TitleMinBtn:hover, QPushButton#TitleMaxBtn:hover {
    background-color: rgba(255, 0, 127, 0.16);
    color: #FF007F;
}
QProgressBar::chunk {
    background-color: #FF007F;
}
QToolTip {
    background-color: #180324;
    color: #F8FAFC;
    border: 1px solid rgba(255, 0, 127, 0.40);
}
QFrame#GlassCard, QFrame[glass="true"] {
    background-color: #240536;
    border: 1.5px solid #FF007F;
    border-top: 2px solid rgba(255, 255, 255, 0.40);
    border-radius: 18px;
}
QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {
    background-color: #300748;
    border: 2px solid #FF007F;
    border-top: 2px solid #FFFFFF;
    border-radius: 18px;
}
QFrame#ControlPanelContainer {
    background-color: #180324;
    border: 1.5px solid #FF007F;
}
QFrame#SidebarPanel {
    background-color: #12021B;
    border-right: 1.5px solid rgba(255, 0, 127, 0.35);
}
QLineEdit {
    background-color: #2E0645;
    color: #FFFFFF;
    border: 1px solid rgba(255, 0, 127, 0.35);
}
QLineEdit:focus {
    background-color: #3B0858;
    border: 2px solid #FF007F;
}
QTableWidget {
    background-color: #180324 !important;
    border: 1.5px solid rgba(255, 0, 127, 0.35) !important;
}
QHeaderView::section, QTableCornerButton::section {
    background-color: #2E0645 !important;
    color: #FF007F;
}
QTextEdit#LogViewer {
    background-color: #12021B;
    border: 1px solid rgba(255, 0, 127, 0.35);
}
QStatusBar {
    background-color: #12021B;
    border-top: 1px solid rgba(255, 0, 127, 0.25);
}
QComboBox QAbstractItemView {
    background-color: #240536;
    border: 1.5px solid #FF007F;
}
"""

# --- Emerald Cyber: глубокий тёмно-изумрудный лес ---
EMERALD_CYBER_QSS = DARK_AZURE_QSS \
    .replace("#1E1B4B", "#064E3B") \
    .replace("#0F172A", "#062319") \
    .replace("#020617", "#02120C") \
    .replace("#00F2FE", "#10B981") \
    .replace("background-color: #028090;", "background-color: #064E3B;")
EMERALD_CYBER_QSS += """
QFrame#CustomTitleBar {
    background-color: rgba(3, 18, 11, 0.90);
    border-top: 2px solid #10B981;
    border-bottom: 1px solid rgba(16, 185, 129, 0.25);
}
QPushButton#TitlePaletteBtn {
    background-color: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #10B981;
}
QPushButton#TitlePaletteBtn:hover {
    background-color: rgba(16, 185, 129, 0.20);
    border-color: #10B981;
    color: #FFFFFF;
}
QPushButton#TitleMinBtn:hover, QPushButton#TitleMaxBtn:hover {
    background-color: rgba(16, 185, 129, 0.16);
    color: #10B981;
}
QProgressBar::chunk {
    background-color: #10B981;
}
QToolTip {
    background-color: #04180F;
    color: #F8FAFC;
    border: 1px solid rgba(16, 185, 129, 0.40);
}
QFrame#GlassCard, QFrame[glass="true"] {
    background-color: #062618;
    border: 1.5px solid #10B981;
    border-top: 2px solid rgba(255, 255, 255, 0.40);
    border-radius: 18px;
}
QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {
    background-color: #093320;
    border: 2px solid #10B981;
    border-top: 2px solid #FFFFFF;
    border-radius: 18px;
}
QFrame#ControlPanelContainer {
    background-color: #04180F;
    border: 1.5px solid #10B981;
}
QFrame#SidebarPanel {
    background-color: #03120B;
    border-right: 1.5px solid rgba(16, 185, 129, 0.35);
}
QLineEdit {
    background-color: #0A3622;
    color: #FFFFFF;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
QLineEdit:focus {
    background-color: #0D452B;
    border: 2px solid #10B981;
}
QTableWidget {
    background-color: #04180F !important;
    border: 1.5px solid rgba(16, 185, 129, 0.35) !important;
}
QHeaderView::section, QTableCornerButton::section {
    background-color: #0A3622 !important;
    color: #10B981;
}
QTextEdit#LogViewer {
    background-color: #03120B;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
QStatusBar {
    background-color: #03120B;
    border-top: 1px solid rgba(16, 185, 129, 0.25);
}
QComboBox QAbstractItemView {
    background-color: #062618;
    border: 1.5px solid #10B981;
}
"""

# --- Deep Violet Glass: глубокая фиолетовая ночь ---
DEEP_VIOLET_QSS = DARK_AZURE_QSS \
    .replace("#1E1B4B", "#4C1D95") \
    .replace("#0F172A", "#1E1B4B") \
    .replace("#020617", "#090514") \
    .replace("#00F2FE", "#A855F7") \
    .replace("background-color: #028090;", "background-color: #4C1D95;")
DEEP_VIOLET_QSS += """
QFrame#CustomTitleBar {
    background-color: rgba(12, 4, 28, 0.90);
    border-top: 2px solid #A855F7;
    border-bottom: 1px solid rgba(168, 85, 247, 0.25);
}
QPushButton#TitlePaletteBtn {
    background-color: rgba(168, 85, 247, 0.08);
    border: 1px solid rgba(168, 85, 247, 0.25);
    color: #A855F7;
}
QPushButton#TitlePaletteBtn:hover {
    background-color: rgba(168, 85, 247, 0.20);
    border-color: #A855F7;
    color: #FFFFFF;
}
QPushButton#TitleMinBtn:hover, QPushButton#TitleMaxBtn:hover {
    background-color: rgba(168, 85, 247, 0.16);
    color: #A855F7;
}
QProgressBar::chunk {
    background-color: #A855F7;
}
QToolTip {
    background-color: #100626;
    color: #F8FAFC;
    border: 1px solid rgba(168, 85, 247, 0.40);
}
QFrame#GlassCard, QFrame[glass="true"] {
    background-color: #180A38;
    border: 1.5px solid #A855F7;
    border-top: 2px solid rgba(255, 255, 255, 0.40);
    border-radius: 18px;
}
QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {
    background-color: #220E4A;
    border: 2px solid #A855F7;
    border-top: 2px solid #FFFFFF;
    border-radius: 18px;
}
QFrame#ControlPanelContainer {
    background-color: #100626;
    border: 1.5px solid #A855F7;
}
QFrame#SidebarPanel {
    background-color: #0C041C;
    border-right: 1.5px solid rgba(168, 85, 247, 0.35);
}
QLineEdit {
    background-color: #200D48;
    color: #FFFFFF;
    border: 1px solid rgba(168, 85, 247, 0.35);
}
QLineEdit:focus {
    background-color: #2A115E;
    border: 2px solid #A855F7;
}
QTableWidget {
    background-color: #100626 !important;
    border: 1.5px solid rgba(168, 85, 247, 0.35) !important;
}
QHeaderView::section, QTableCornerButton::section {
    background-color: #200D48 !important;
    color: #A855F7;
}
QTextEdit#LogViewer {
    background-color: #0C041C;
    border: 1px solid rgba(168, 85, 247, 0.35);
}
QStatusBar {
    background-color: #0C041C;
    border-top: 1px solid rgba(168, 85, 247, 0.25);
}
QComboBox QAbstractItemView {
    background-color: #180A38;
    border: 1.5px solid #A855F7;
}
"""

BEACH_QSS = DARK_AZURE_QSS


# ==============================================================================
# КЛАССИЧЕСКАЯ ТЕМА «КАК ДОМА» — Windows Classic / АРКУС / 1С стиль
# ==============================================================================
HOME_CLASSIC_QSS = """
/* Классический серый/бежевый фон в стиле Windows Classic / АРКУС */
QMainWindow, QWidget#MainContainer, QWidget#OceanBackground {
    background-color: #ECE9D8;
    color: #000000;
    font-family: "Tahoma", "Segoe UI", sans-serif;
}

QWidget {
    font-family: "Tahoma", "Segoe UI", sans-serif;
    color: #000000;
}

QStackedWidget {
    background: transparent;
}

QWidget#DashboardPage,
QWidget#NormsPage,
QWidget#LogsPage,
QWidget#AutoTestsPage,
QWidget#AboutPage {
    background: transparent;
    color: #000000;
    font-family: "Tahoma", "Segoe UI", sans-serif;
}

/* Диалоги */
QDialog {
    background-color: #ECE9D8;
    color: #000000;
    border: 1.5px solid #7F9DB9;
    border-radius: 4px;
}

/* Строгие классические карточки без размытия */
QFrame#GlassCard, QFrame[glass="true"] {
    background-color: #FFFFFF;
    border: 1px solid #7F9DB9;
    border-radius: 2px;
}

QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {
    background-color: #FFFFFF;
    border: 1px solid #0A246A;
    border-radius: 2px;
}

QFrame#GlassCard[drag="true"] {
    background-color: rgba(10, 36, 106, 0.08);
    border: 2px dashed #0A246A;
    border-radius: 2px;
}

QFrame#GlassCard[state="linked"] {
    background-color: rgba(10, 36, 106, 0.06);
    border: 2px solid #0A246A;
    border-radius: 2px;
}

QFrame#GlassCard[state="warning"] {
    background-color: rgba(200, 0, 0, 0.07);
    border: 2px solid #CC0000;
    border-radius: 2px;
}

QFrame#ControlPanelContainer {
    background-color: #F0EEE4;
    border: 1px solid #7F9DB9;
    border-radius: 2px;
}

/* Боковая панель */
QFrame#SidebarPanel {
    background-color: #D4D0C8;
    border-right: 1px solid #999999;
}

/* Заголовок окна */
QFrame#CustomTitleBar {
    background-color: #0A246A;
    border-bottom: 2px solid #000080;
}
QLabel#TitleLabel {
    color: #FFFFFF;
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 0.3px;
}
QPushButton#TitlePaletteBtn {
    background-color: rgba(255, 255, 255, 0.15);
    border: 1px solid #808080;
    border-radius: 2px;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: bold;
    padding: 1px 6px;
    min-height: 18px;
}
QPushButton#TitlePaletteBtn:hover {
    background-color: rgba(255, 255, 255, 0.30);
    border-color: #FFFFFF;
}
QPushButton#ArcusModeButton {
    background-color: #0A246A;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 12px;
    border: 1px solid #000000;
    border-radius: 2px;
    padding: 5px 12px;
    min-height: 22px;
}
QPushButton#ArcusModeButton:hover {
    background-color: #163988;
}
QPushButton#ArcusModeButton:checked {
    background-color: #0A246A;
    color: #FFFFFF;
    border: 1.5px solid #000080;
}
QPushButton#TitleMinBtn, QPushButton#TitleMaxBtn {
    background-color: #D4D0C8;
    color: #000000;
    border: 1px solid #808080;
    border-radius: 2px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#TitleMinBtn:hover, QPushButton#TitleMaxBtn:hover {
    background-color: #E8E6DE;
}
QPushButton#TitleCloseBtn {
    background-color: #D4D0C8;
    color: #000000;
    border: 1px solid #808080;
    border-radius: 2px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#TitleCloseBtn:hover {
    background-color: #CC0000;
    color: #FFFFFF;
}

.icon-badge, QLabel#IconBadge {
    background-color: #D4D0C8;
    border: 1px solid #999999;
    border-radius: 2px;
    padding: 6px;
}

QScrollArea, QScrollArea > QWidget > QWidget {
    background: transparent !important;
    border: none;
}

QLabel { color: #000000; font-size: 12px; }
QLabel#PageTitle { color: #000000; font-size: 20px; font-weight: 700; }
QLabel#SectionTitle { color: #0A246A; font-size: 13px; font-weight: 700; }
QLabel#FieldLabel { color: #444444; font-size: 12px; font-weight: 600; }

/* Поля ввода */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #7F9DB9;
    border-radius: 2px;
    padding: 4px 6px;
    color: #000000;
    font-size: 12px;
    selection-background-color: #0A246A;
    selection-color: #FFFFFF;
}
QLineEdit[invalid="true"] {
    border: 1.5px solid #CC0000 !important;
    background-color: rgba(204, 0, 0, 0.07) !important;
}
QLineEdit:focus {
    border: 1.5px solid #0A246A;
}

/* Выпадающий список */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #7F9DB9;
    border-radius: 2px;
    padding: 4px 6px;
    color: #000000;
    font-size: 12px;
    selection-background-color: #0A246A;
    selection-color: #FFFFFF;
}
QComboBox:focus, QComboBox:on {
    border: 1.5px solid #0A246A;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #7F9DB9;
    background-color: #D4D0C8;
}
QComboBox::down-arrow {
    width: 8px;
    height: 8px;
    border-left: 2px solid #444444;
    border-bottom: 2px solid #444444;
    border-top: none;
    border-right: none;
    margin-right: 5px;
    margin-top: -3px;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #7F9DB9;
    color: #000000;
    selection-background-color: #0A246A;
    selection-color: #FFFFFF;
    outline: none;
}

/* Классические кнопки */
QPushButton#PrimaryButton {
    background-color: #0A246A;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 12px;
    border-radius: 3px;
    padding: 6px 14px;
    border: 1px solid #000000;
    min-height: 22px;
}
QPushButton#PrimaryButton:hover {
    background-color: #163988;
}
QPushButton#PrimaryButton:disabled {
    background-color: #A0A0A0;
    color: #D0D0D0;
}

QPushButton#SecondaryButton {
    background-color: #D4D0C8;
    color: #000000;
    font-weight: normal;
    font-size: 12px;
    border: 1px solid #7F9DB9;
    border-radius: 3px;
    padding: 5px 12px;
    min-height: 20px;
}
QPushButton#SecondaryButton:hover {
    background-color: #E3E0D8;
    border-color: #0A246A;
}

QPushButton#AccentButton {
    background-color: #005A9E;
    color: #FFFFFF !important;
    font-weight: bold;
    font-size: 12px;
    border: 1px solid #003D7A;
    border-radius: 3px;
    padding: 6px 14px;
    min-height: 22px;
}
QPushButton#AccentButton:hover {
    background-color: #0068B4;
    border-color: #003D7A;
    color: #FFFFFF !important;
}
QPushButton#AccentButton:pressed {
    background-color: #004080;
    color: #FFFFFF !important;
}

QPushButton#DangerButton {
    background-color: #D4D0C8;
    color: #CC0000;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #CC0000;
    border-radius: 3px;
    padding: 5px 12px;
    min-height: 20px;
}
QPushButton#DangerButton:hover {
    background-color: #FFCCCC;
    border-color: #990000;
}

/* Кнопки навигации сайдбара */
QPushButton.navBtn {
    background-color: transparent;
    color: #000000;
    border: none;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 12px;
    text-align: left;
    qproperty-iconSize: 22px 22px;
}
QPushButton.navBtn:hover {
    background-color: #B5C9E7;
    color: #000000;
}
QPushButton.navBtn:checked {
    background-color: #0A246A;
    color: #FFFFFF;
    font-weight: bold;
    border-radius: 3px;
}

/* QSlider Слайдеры */
QSlider::groove:horizontal {
    height: 6px;
    background: #FFFFFF;
    border: 1px solid #7F9DB9;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #0A246A;
    border-radius: 1px;
}
QSlider::handle:horizontal {
    background: #D4D0C8;
    border: 1px solid #000000;
    width: 12px;
    height: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 2px;
}
QSlider::handle:horizontal:hover {
    background: #E8E6DE;
}

QCheckBox { color: #000000; font-size: 12px; spacing: 6px; }
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #7F9DB9;
    border-radius: 2px;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #0A246A;
    border-color: #0A246A;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><polyline points='3.5 8.5 6.5 11.5 12.5 4.5' fill='none' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/></svg>");
}

/* Таблицы в стиле классического Excel / 1С */
QTableWidget {
    background-color: #FFFFFF !important;
    border: 1px solid #7F9DB9 !important;
    border-radius: 0px;
    gridline-color: #D4D0C8;
    outline: none;
}
QTableWidget::item { padding: 5px 8px; color: #000000; border: none; min-height: 28px; }
QTableWidget::item:selected {
    background-color: #0A246A;
    color: #FFFFFF;
}

QTableCornerButton::section,
QHeaderView::section,
QHeaderView::section:vertical,
QHeaderView::section:horizontal {
    background-color: #D4D0C8 !important;
    color: #000000;
    border: 1px solid #999999;
    border-radius: 0px;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 12px;
    min-height: 22px;
}

/* Текстовые поля и логи */
QTextEdit#LogViewer {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #7F9DB9;
    border-radius: 0px;
    font-family: "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
}

QMessageBox {
    background-color: #ECE9D8;
    color: #000000;
}

QStatusBar {
    background-color: #D4D0C8;
    border-top: 1px solid #999999;
    color: #000000;
}
QStatusBar QLabel {
    color: #000000;
    background: transparent;
    qproperty-wordWrap: false;
    white-space: nowrap;
}
QProgressBar {
    border: 1px solid #999999;
    border-radius: 4px;
    background-color: #FFFFFF;
    max-height: 8px;
}
QProgressBar::chunk {
    background-color: #0A246A;
    border-radius: 2px;
}

/* ─── Защита от переполнения / наслаивания ─── */
QLabel {
    qproperty-wordWrap: true;
}
QLabel#PageTitle {
    min-width: 0px;
}
QFrame#SidebarPanel {
    min-width: 60px;
}
QWidget#MainContainer, QWidget#OceanBackground {
    min-width: 0px;
}
QScrollArea {
    min-width: 0px;
}
"""


class ThemeManager:
    """Менеджер тем интерфейса с оверлей-оповещением акцентных цветов."""

    THEME_DATA = {
        "Dark Tech Azure": {
            "qss": DARK_AZURE_QSS,
            "accent": "#00F2FE",
            "secondary": "#028090",
            "bg": "#030712"
        },
        "Pearl Light": {
            "qss": PEARL_LIGHT_QSS,
            "accent": "#028090",
            "secondary": "#00A896",
            "bg": "#F1F5F9"
        },
        "Cyberpunk Neon": {
            "qss": CYBERPUNK_NEON_QSS,
            "accent": "#FF007F",
            "secondary": "#D9006C",
            "bg": "#05000A"
        },
        "Emerald Cyber": {
            "qss": EMERALD_CYBER_QSS,
            "accent": "#10B981",
            "secondary": "#064E3B",
            "bg": "#02120C"
        },
        "Deep Violet Glass": {
            "qss": DEEP_VIOLET_QSS,
            "accent": "#A855F7",
            "secondary": "#4C1D95",
            "bg": "#090514"
        },
        # Классическая тема без 3D-волн
        "Как дома": {
            "qss": HOME_CLASSIC_QSS,
            "accent": "#0A246A",
            "secondary": "#005A9E",
            "bg": "#ECE9D8"
        }
    }

    on_theme_changed = []

    GENERAL_THEME_NAMES = [
        "Dark Tech Azure",
        "Pearl Light",
        "Cyberpunk Neon",
        "Emerald Cyber",
        "Deep Violet Glass",
        "Как дома"
    ]

    @classmethod
    def get_theme_names(cls) -> list[str]:
        return list(cls.GENERAL_THEME_NAMES)

    @classmethod
    def get_current_theme_name(cls) -> str:
        settings = QSettings("WaterMetrics", "ThemeSystem")
        return settings.value("Theme", "Dark Tech Azure", type=str)

    @classmethod
    def get_current_accent_color(cls) -> str:
        name = cls.get_current_theme_name()
        return cls.THEME_DATA.get(name, cls.THEME_DATA["Dark Tech Azure"])["accent"]

    @classmethod
    def get_current_bg_color(cls) -> str:
        name = cls.get_current_theme_name()
        return cls.THEME_DATA.get(name, cls.THEME_DATA["Dark Tech Azure"]).get("bg", "#030712")

    @classmethod
    def apply_theme(cls, theme_name: str):
        tdata = cls.THEME_DATA.get(theme_name, cls.THEME_DATA["Dark Tech Azure"])
        qss = tdata["qss"]
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
        settings = QSettings("WaterMetrics", "ThemeSystem")
        settings.setValue("Theme", theme_name)

        valid_callbacks = []
        for cb in cls.on_theme_changed:
            try:
                cb(theme_name)
                valid_callbacks.append(cb)
            except (RuntimeError, ReferenceError):
                # Объект C++ был удален, исключаем из списка
                pass
            except Exception:
                valid_callbacks.append(cb)
        cls.on_theme_changed = valid_callbacks