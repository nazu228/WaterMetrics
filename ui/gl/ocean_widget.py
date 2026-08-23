"""
ui/gl/ocean_widget.py — CyberGridWidget / OceanWidget (WaterMetrics).

Центральный фоновый виджет — сам QOpenGLWidget.
Рисует 3D волны Герстнера на заднем экране приложения.
- Сетка растянута за пределы экрана [-1.45, 1.45], чтобы не было видно краёв.
- Скорость волн уменьшена для плавного, спокойного движения.
"""

from __future__ import annotations

import sys
from typing import Union

from PySide6.QtCore import QElapsedTimer, QTimer, QEvent, QSettings
from PySide6.QtGui import QCursor
from PySide6.QtOpenGL import (
    QOpenGLBuffer,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLVertexArrayObject,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QPushButton

import numpy as np

from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_FLOAT,
    GL_LINES,
    GL_MULTISAMPLE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    glBlendFunc,
    glClear,
    glClearColor,
    glDrawArrays,
    glEnable,
    glUniform1f,
    glUniform2f,
    glUniform4f,
    glViewport,
)

from ui.styles import ThemeManager
import ui.gl.wave_mesh_widget as _wm
from ui.gl.wave_mesh_widget import THEMES, MeshTheme

_VERT = _wm.VERTEX_SHADER
_FRAG = _wm.FRAGMENT_SHADER


class CyberGridWidget(QOpenGLWidget):
    """
    Центральный фоновый виджет — сам QOpenGLWidget.
    Рисует 3D волны Герстнера на заднем экране.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OceanBackground")

        theme_name = ThemeManager.get_current_theme_name()
        self._theme: MeshTheme = THEMES.get(theme_name, THEMES["Cyberpunk Neon"])

        self._time: float = 0.0
        self._paused: bool = False

        self._program: QOpenGLShaderProgram | None = None
        self._vao: QOpenGLVertexArrayObject | None = None
        self._vbo: QOpenGLBuffer | None = None
        self._vertex_count: int = 0
        self._u: dict[str, int] = {}

        self._elapsed = QElapsedTimer()
        self._last_ns: int = 0

        # Загрузка сохраненных настроек волн из QSettings
        settings = QSettings("WaterMetrics", "WaveSettings")
        self._waves_enabled: bool = settings.value("WavesEnabled", True, type=bool)
        self._grid_n: int = settings.value("GridDensity", 30, type=int)
        
        # Калибровка: 100% шкалы пользователя = 40% реальной альфы OpenGL, дефолт 28%
        opacity_pct = settings.value("LineOpacity", 28, type=int)
        self._line_opacity: float = (max(0, min(100, opacity_pct)) / 100.0) * 0.40
        self._speed_scale: float = settings.value("WaveSpeed", 10, type=int) / 10.0
        
        amp_pct = settings.value("WaveAmplitude", 100, type=int)
        self._custom_wave_amp: float | None = (amp_pct / 100.0) * 0.22

        tilt_deg = settings.value("WaveTilt", 48, type=int)
        self._custom_tilt: float | None = tilt_deg * 0.01

        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        if self._waves_enabled and self._line_opacity > 0.0:
            self._timer.start(25)

        ThemeManager.on_theme_changed.append(self._on_theme_changed)

    def pause_animation(self) -> None:
        self._paused = True
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()

    def resume_animation(self) -> None:
        self._paused = False
        if hasattr(self, '_timer') and not self._timer.isActive():
            if self._waves_enabled and self._line_opacity > 0.0 and self.isVisible():
                self._timer.start(25)

    def _on_timer_tick(self) -> None:
        if not self.isVisible() or self._paused or not self._waves_enabled or self._line_opacity <= 0.0:
            if hasattr(self, '_timer') and self._timer.isActive() and (not self._waves_enabled or self._line_opacity <= 0.0):
                self._timer.stop()
            return
        self.update()

    def set_waves_enabled(self, enabled: bool) -> None:
        self._waves_enabled = enabled
        QSettings("WaterMetrics", "WaveSettings").setValue("WavesEnabled", enabled)
        if not enabled:
            if hasattr(self, '_timer') and self._timer.isActive():
                self._timer.stop()
        else:
            if hasattr(self, '_timer') and not self._timer.isActive() and not self._paused and self._line_opacity > 0.0 and self.isVisible():
                self._timer.start(25)
        self.update()

    def set_grid_density(self, n: int) -> None:
        n = max(4, min(100, n))
        self._grid_n = n
        QSettings("WaterMetrics", "WaveSettings").setValue("GridDensity", n)
        if self._vbo and self._vbo.isCreated():
            line_verts = self._build_line_verts(n)
            self._vertex_count = len(line_verts)
            self.makeCurrent()
            self._vbo.bind()
            self._vbo.allocate(line_verts.tobytes(), line_verts.nbytes)
            self._vbo.release()
            self.doneCurrent()
            self.update()

    def set_line_opacity(self, alpha: float) -> None:
        if alpha > 0.40:
            alpha = (alpha / 100.0) * 0.40
        self._line_opacity = max(0.0, min(0.40, alpha))
        pct = int(round((self._line_opacity / 0.40) * 100))
        QSettings("WaterMetrics", "WaveSettings").setValue("LineOpacity", pct)
        if self._line_opacity <= 0.0:
            if hasattr(self, '_timer') and self._timer.isActive():
                self._timer.stop()
        else:
            if hasattr(self, '_timer') and not self._timer.isActive() and not self._paused and self._waves_enabled and self.isVisible():
                self._timer.start(25)
        self.update()

    def set_user_opacity_percent(self, pct: int) -> None:
        pct = max(0, min(100, pct))
        self.set_line_opacity((pct / 100.0) * 0.40)

    def set_wave_amplitude(self, amp: float) -> None:
        self._custom_wave_amp = max(0.0, min(0.6, amp))
        pct = int((amp / 0.22) * 100) if amp is not None else 100
        QSettings("WaterMetrics", "WaveSettings").setValue("WaveAmplitude", pct)
        self.update()

    def set_speed_scale(self, scale: float) -> None:
        self._speed_scale = max(0.0, min(5.0, scale))
        QSettings("WaterMetrics", "WaveSettings").setValue("WaveSpeed", int(scale * 10))

    def set_tilt(self, tilt: float) -> None:
        self._custom_tilt = max(0.0, min(1.2, tilt))
        QSettings("WaterMetrics", "WaveSettings").setValue("WaveTilt", int(tilt / 0.01))
        self.update()

    def __del__(self):
        try:
            ThemeManager.on_theme_changed.remove(self._on_theme_changed)
        except Exception:
            pass

    def _on_theme_changed(self, theme_name: str = None, **kwargs):
        name = theme_name or ThemeManager.get_current_theme_name()
        self._theme = THEMES.get(name, THEMES["Cyberpunk Neon"])
        self.update()

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE)

        self._program = QOpenGLShaderProgram(self)

        ok_v = self._program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, _VERT)
        ok_f = self._program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, _FRAG)
        ok_l = self._program.link()

        if not (ok_v and ok_f and ok_l):
            log = self._program.log()
            print(f"[OceanWidget] Shader error:\n{log}", file=sys.stderr)
            return

        self._program.bind()
        for name in ("uTime", "uMouse", "uWaveAmp", "uWaveSteep", "uTilt",
                     "uMouseRadius", "uMouseAmp",
                     "uLineColor", "uGlowColor", "uHeightTint"):
            self._u[name] = self._program.uniformLocation(name)
        self._program.release()

        line_verts = self._build_line_verts(self._grid_n)
        self._vertex_count = len(line_verts)

        self._vao = QOpenGLVertexArrayObject(self)
        self._vao.create()
        self._vao.bind()

        self._vbo = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self._vbo.create()
        self._vbo.bind()
        self._vbo.setUsagePattern(QOpenGLBuffer.UsagePattern.StaticDraw)
        self._vbo.allocate(line_verts.tobytes(), line_verts.nbytes)

        self._program.bind()
        self._program.enableAttributeArray(0)
        self._program.setAttributeBuffer(0, GL_FLOAT, 0, 2, 0)

        self._vao.release()
        self._vbo.release()
        self._program.release()

        self._elapsed.start()
        self._last_ns = self._elapsed.nsecsElapsed()

    def paintGL(self):
        now_ns = self._elapsed.nsecsElapsed()
        dt = (now_ns - self._last_ns) / 1e9
        self._last_ns = now_ns
        if not self._paused:
            self._time += dt * self._speed_scale

        t = self._theme
        glClearColor(*t.bg_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if not getattr(t, 'draw_waves', True) or not self._waves_enabled or self._line_opacity <= 0.0:
            return

        if not self._program or not self._vao or self._vertex_count == 0:
            return

        w = max(self.width(), 1)
        h = max(self.height(), 1)
        lp = self.mapFromGlobal(QCursor.pos())
        mx = max(-1.4, min(1.4, (lp.x() / w) * 2.8 - 1.4))
        my = max(-1.4, min(1.4, -((lp.y() / h) * 2.8 - 1.4)))

        self._program.bind()
        self._vao.bind()

        u = self._u
        wave_amp = self._custom_wave_amp if self._custom_wave_amp is not None else t.wave_amp
        tilt = self._custom_tilt if self._custom_tilt is not None else t.tilt
        line_col = (t.line_color[0], t.line_color[1], t.line_color[2], t.line_color[3] * self._line_opacity)

        glUniform1f(u["uTime"], float(self._time))
        glUniform2f(u["uMouse"], float(mx), float(my))
        glUniform1f(u["uWaveAmp"], float(wave_amp))
        glUniform1f(u["uWaveSteep"], float(t.wave_steep))
        glUniform1f(u["uTilt"], float(tilt))
        glUniform1f(u["uMouseRadius"], float(t.mouse_radius))
        glUniform1f(u["uMouseAmp"], float(t.mouse_amp))
        glUniform4f(u["uLineColor"], *line_col)
        glUniform4f(u["uGlowColor"], *t.glow_color)
        glUniform1f(u["uHeightTint"], float(t.height_tint))

        glDrawArrays(GL_LINES, 0, self._vertex_count)

        self._vao.release()
        self._program.release()

    def resizeGL(self, w: int, h: int):
        glViewport(0, 0, w, h)

    def closeEvent(self, event):
        self._timer.stop()
        try:
            ThemeManager.on_theme_changed.remove(self._on_theme_changed)
        except Exception:
            pass
        self.makeCurrent()
        try:
            if self._vbo: self._vbo.destroy()
            if self._vao: self._vao.destroy()
            if self._program: self._program.removeAllShaders()
        except Exception:
            pass
        self.doneCurrent()
        super().closeEvent(event)

    def trigger_storm(self, duration: float = 3.0):
        pass

    def add_ripple(self, x_px: float, y_px: float, strength: float = 1.0):
        pass

    def add_repel_impulse(self, x_px: float, y_px: float, strength: float = 1.0):
        pass

    def hideEvent(self, event):
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, '_timer') and not self._timer.isActive() and not self._paused:
            if self._waves_enabled and self._line_opacity > 0.0:
                self._timer.start(25)

    def eventFilter(self, obj, event) -> bool:
        if event.type() not in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove, QEvent.Type.Enter, QEvent.Type.Leave):
            return super().eventFilter(obj, event)
        try:
            if (event.type() == QEvent.Type.MouseButtonPress
                    and isinstance(obj, QPushButton)
                    and obj.objectName() == "btn_run"):
                self.trigger_storm(3.0)
        except Exception:
            pass
        return super().eventFilter(obj, event)

    @staticmethod
    def _build_line_verts(N: int) -> np.ndarray:
        # Растягиваем сетку за границы экрана [-1.45, 1.45], чтобы не было видно краёв!
        x = np.linspace(-1.45, 1.45, N, dtype=np.float32)
        y = np.linspace(-1.45, 1.45, N, dtype=np.float32)
        gx, gy = np.meshgrid(x, y)

        lines = []
        for r in range(N):
            for c in range(N - 1):
                lines.extend([[gx[r, c], gy[r, c]], [gx[r, c + 1], gy[r, c + 1]]])
        for c in range(N):
            for r in range(N - 1):
                lines.extend([[gx[r, c], gy[r, c]], [gx[r + 1, c], gy[r + 1, c]]])

        return np.array(lines, dtype=np.float32)


OceanWidget = CyberGridWidget
