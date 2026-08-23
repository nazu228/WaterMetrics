"""
ui/gl/wave_mesh_widget.py — Gerstner Wave Mesh (WaterMetrics).

QOpenGLWidget с 3D водяными волнами Герстнера (Trochoidal / Gerstner Waves).
- Сетка растянута за пределы экрана [-1.45, 1.45], чтобы не было видно краёв.
- Скорость волн уменьшена для плавного, спокойного движения.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Tuple, Union

import numpy as np

from PySide6.QtCore import QElapsedTimer, QTimer, Signal
from PySide6.QtGui import QCursor, QSurfaceFormat
from PySide6.QtOpenGL import (
    QOpenGLBuffer,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLVertexArrayObject,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_FLOAT,
    GL_LINES,
    GL_LINE_SMOOTH,
    GL_LINE_SMOOTH_HINT,
    GL_MULTISAMPLE,
    GL_NICEST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    glBlendFunc,
    glClear,
    glClearColor,
    glDrawArrays,
    glEnable,
    glHint,
    glUniform1f,
    glUniform2f,
    glUniform4f,
    glViewport,
)

# ---------------------------------------------------------------------------
# VERTEX SHADER — Плавные волны Герстнера
# ---------------------------------------------------------------------------
VERTEX_SHADER = """
#version 330 core

layout(location = 0) in vec2 aPos;

uniform float uTime;
uniform vec2  uMouse;
uniform float uWaveAmp;
uniform float uWaveSteep;
uniform float uTilt;
uniform float uMouseRadius;
uniform float uMouseAmp;

out float vHeight;
out float vMouseProx;

vec3 gerstner(vec2 pos, vec2 D, float A, float k, float speed, float Q, float t) {
    float phase = k * dot(D, pos) - speed * t;
    float C = cos(phase);
    float S = sin(phase);
    return vec3(
        Q * A * D.x * C,
        Q * A * D.y * C,
        A * S
    );
}

void main() {
    vec2  p = aPos;
    float A = uWaveAmp;
    float Q = uWaveSteep;

    // Плавная скорость перемещения (уменьшена в 2.5 раза)
    vec3 w1 = gerstner(p, normalize(vec2( 1.0,  0.7)), A * 1.00, 3.2, 0.65, Q,       uTime);
    vec3 w2 = gerstner(p, normalize(vec2(-0.6,  1.0)), A * 0.65, 4.8, 0.85, Q * 0.8, uTime);
    vec3 w3 = gerstner(p, normalize(vec2( 0.9, -0.4)), A * 0.30, 8.0, 1.20, Q * 0.3, uTime);
    vec3 w4 = gerstner(p, normalize(vec2(-0.3, -0.8)), A * 0.50, 2.0, 0.45, Q * 0.6, uTime);

    vec2 xy = w1.xy + w2.xy + w3.xy + w4.xy;
    float z = w1.z  + w2.z  + w3.z  + w4.z;

    vec2 dPos = p + xy * 0.22;

    vec2  mDelta = dPos - uMouse;
    float mDist  = length(mDelta);
    float mProx  = smoothstep(uMouseRadius, 0.0, mDist);
    z += mProx * uMouseAmp;

    vHeight    = z;
    vMouseProx = mProx;

    float projX = dPos.x;
    float projY = dPos.y * cos(uTilt) - z * sin(uTilt);

    gl_Position = vec4(projX, projY, z * 0.1, 1.0);
}
"""

# ---------------------------------------------------------------------------
# FRAGMENT SHADER
# ---------------------------------------------------------------------------
FRAGMENT_SHADER = """
#version 330 core

in  float vHeight;
in  float vMouseProx;
out vec4  fragColor;

uniform vec4  uLineColor;
uniform vec4  uGlowColor;
uniform float uHeightTint;

void main() {
    float tint = vHeight * uHeightTint * 1.6;
    vec4  base = uLineColor;
    base.rgb   = clamp(base.rgb + tint, 0.0, 1.0);

    vec4 final = mix(base, uGlowColor, vMouseProx * 0.80);
    fragColor  = final;
}
"""

# ---------------------------------------------------------------------------
# MeshTheme
# ---------------------------------------------------------------------------
Color4f = Tuple[float, float, float, float]


@dataclass
class MeshTheme:
    name:         str
    bg_color:     Color4f
    line_color:   Color4f
    glow_color:   Color4f
    wave_amp:     float = 0.22
    wave_steep:   float = 0.55
    tilt:         float = 0.48
    mouse_radius: float = 0.45
    mouse_amp:    float = 0.14
    height_tint:  float = 0.55
    line_width:   float = 1.4
    draw_waves:   bool  = True   # False — только сплошной фон, без 3D-волн


THEMES: dict[str, MeshTheme] = {
    "Cyberpunk Neon": MeshTheme(
        name="Cyberpunk Neon",
        bg_color=(0.04, 0.01, 0.07, 1.0),
        line_color=(1.00, 0.05, 0.55, 1.0),
        glow_color=(0.00, 1.00, 0.85, 1.0),
        wave_amp=0.22, wave_steep=0.55, tilt=0.48, line_width=1.4
    ),
    "Dark Tech Azure": MeshTheme(
        name="Dark Tech Azure",
        bg_color=(0.008, 0.008, 0.025, 1.0),
        line_color=(0.0, 0.95, 1.0, 1.0),
        glow_color=(0.0, 0.6, 0.8, 1.0),
        wave_amp=0.18, wave_steep=0.50, tilt=0.48, line_width=1.2
    ),
    "Emerald Cyber": MeshTheme(
        name="Emerald Cyber",
        bg_color=(0.01, 0.05, 0.03, 1.0),
        line_color=(0.06, 0.85, 0.55, 1.0),
        glow_color=(0.0, 1.0, 0.6, 1.0),
        wave_amp=0.18, wave_steep=0.50, tilt=0.48, line_width=1.2
    ),
    "Deep Violet Glass": MeshTheme(
        name="Deep Violet Glass",
        bg_color=(0.035, 0.02, 0.08, 1.0),
        line_color=(0.75, 0.35, 1.0, 1.0),
        glow_color=(0.90, 0.65, 1.0, 1.0),
        wave_amp=0.20, wave_steep=0.50, tilt=0.48, line_width=1.2
    ),
    "Pearl Light": MeshTheme(
        name="Pearl Light",
        bg_color=(0.94, 0.97, 0.98, 1.0),
        line_color=(0.01, 0.50, 0.56, 1.0),
        glow_color=(0.01, 0.70, 0.75, 1.0),
        wave_amp=0.15, wave_steep=0.40, tilt=0.48, line_width=1.0
    ),
    "light": MeshTheme(
        name="light",
        bg_color=(1.0, 1.0, 1.0, 1.0),
        line_color=(0.08, 0.08, 0.10, 1.0),
        glow_color=(0.35, 0.35, 0.45, 1.0),
    ),
    "dark": MeshTheme(
        name="dark",
        bg_color=(0.06, 0.06, 0.09, 1.0),
        line_color=(0.75, 0.78, 0.90, 1.0),
        glow_color=(0.30, 0.65, 1.00, 1.0),
    ),
    "neon": MeshTheme(
        name="neon",
        bg_color=(0.04, 0.01, 0.07, 1.0),
        line_color=(1.00, 0.05, 0.55, 1.0),
        glow_color=(0.00, 1.00, 0.85, 1.0),
    ),
    # Классическая тема без 3D-волн (#ECE9D8 — бежевый в стиле Windows Classic)
    "Как дома": MeshTheme(
        name="Как дома",
        bg_color=(0.925, 0.914, 0.847, 1.0),
        line_color=(0.0, 0.0, 0.0, 0.0),
        glow_color=(0.0, 0.0, 0.0, 0.0),
        wave_amp=0.0,
        draw_waves=False,
    ),
}


class WaveMeshWidget(QOpenGLWidget):
    fps_updated = Signal(float)

    def __init__(
        self,
        parent=None,
        grid_n: int = 30,
        theme: Union[str, MeshTheme] = "Cyberpunk Neon",
    ):
        super().__init__(parent)
        self._grid_n: int = grid_n
        self._theme: MeshTheme = self._resolve_theme(theme)
        self._time: float = 0.0
        self._paused: bool = False

        self._line_opacity: float = 1.0
        self._speed_scale: float = 1.0
        self._custom_wave_amp: float | None = None
        self._custom_tilt: float | None = None

        self._program: QOpenGLShaderProgram | None = None
        self._vao: QOpenGLVertexArrayObject | None = None
        self._vbo: QOpenGLBuffer | None = None
        self._vertex_count: int = 0
        self._u: dict[str, int] = {}

        self._elapsed = QElapsedTimer()
        self._last_ns: int = 0
        self._fps_buf: list[float] = []

        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        if self._line_opacity > 0.0:
            self._timer.start(25)

    def _on_timer_tick(self) -> None:
        if not self.isVisible() or self._paused or self._line_opacity <= 0.0:
            if hasattr(self, '_timer') and self._timer.isActive() and self._line_opacity <= 0.0:
                self._timer.stop()
            return
        self.update()

    @property
    def theme(self) -> MeshTheme:
        return self._theme

    def set_theme(self, theme: Union[str, MeshTheme]) -> None:
        self._theme = self._resolve_theme(theme)
        self.update()

    def set_grid_density(self, n: int) -> None:
        n = max(4, min(100, n))
        self._grid_n = n
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
        self._line_opacity = max(0.0, min(1.0, alpha))
        if self._line_opacity <= 0.0:
            if hasattr(self, '_timer') and self._timer.isActive():
                self._timer.stop()
        else:
            if hasattr(self, '_timer') and not self._timer.isActive() and not self._paused and self.isVisible():
                self._timer.start(25)
        self.update()

    def set_wave_amplitude(self, amp: float) -> None:
        self._custom_wave_amp = max(0.0, min(0.6, amp))
        self.update()

    def set_speed_scale(self, scale: float) -> None:
        self._speed_scale = max(0.0, min(5.0, scale))

    def set_tilt(self, tilt: float) -> None:
        self._custom_tilt = max(0.0, min(1.2, tilt))
        self.update()

    def pause(self) -> None:
        self._paused = True
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()

    def resume(self) -> None:
        self._paused = False
        if hasattr(self, '_timer') and not self._timer.isActive() and self.isVisible() and self._line_opacity > 0.0:
            self._timer.start(25)

    def hideEvent(self, event):
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, '_timer') and not self._timer.isActive() and not self._paused and self._line_opacity > 0.0:
            self._timer.start(25)

    def initializeGL(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        self._program = QOpenGLShaderProgram(self)

        if not self._program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERTEX_SHADER):
            log = self._program.log()
            print(f"[WaveMesh] Vertex shader error:\n{log}", file=sys.stderr)
            return

        if not self._program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAGMENT_SHADER):
            log = self._program.log()
            print(f"[WaveMesh] Fragment shader error:\n{log}", file=sys.stderr)
            return

        if not self._program.link():
            log = self._program.log()
            print(f"[WaveMesh] Link error:\n{log}", file=sys.stderr)
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

        if dt > 0.0:
            self._fps_buf.append(1.0 / dt)
        if len(self._fps_buf) >= 60:
            self.fps_updated.emit(sum(self._fps_buf) / len(self._fps_buf))
            self._fps_buf.clear()

        t = self._theme

        glClearColor(*t.bg_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

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
        self.makeCurrent()
        try:
            if self._vbo: self._vbo.destroy()
            if self._vao: self._vao.destroy()
            if self._program: self._program.removeAllShaders()
        except Exception:
            pass
        self.doneCurrent()
        super().closeEvent(event)

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

    @staticmethod
    def _resolve_theme(theme: Union[str, MeshTheme]) -> MeshTheme:
        if isinstance(theme, MeshTheme):
            return theme
        resolved = THEMES.get(theme)
        if resolved is not None:
            return resolved
        return THEMES["Cyberpunk Neon"]


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)

    win = QMainWindow()
    win.setWindowTitle("Gerstner Wave Mesh Test")
    win.resize(960, 720)

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    mesh = WaveMeshWidget(grid_n=30, theme="Cyberpunk Neon")
    mesh.fps_updated.connect(
        lambda fps: win.setWindowTitle(f"Gerstner Wave Mesh Test  |  {fps:.1f} FPS")
    )
    layout.addWidget(mesh)

    win.setCentralWidget(central)
    win.show()
    sys.exit(app.exec())
