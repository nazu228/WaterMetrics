"""
Векторная система частиц (Particle System) для Deep Ocean Engine.
Содержит симуляцию пузырьков, брызг, пены и неоновых искорок без сторонних зависимостей.
"""

import math
import random
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPointF


class Particle:
    __slots__ = ('x', 'y', 'z', 'vx', 'vy', 'vz', 'life', 'max_life', 'size', 'type', 'opacity')

    def __init__(self, x=0.0, y=0.0, z=0.0, vx=0.0, vy=0.0, vz=0.0, life=1.0, max_life=1.0, size=4.0, ptype=0, opacity=1.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vx = float(vx)
        self.vy = float(vy)
        self.vz = float(vz)
        self.life = float(life)
        self.max_life = float(max_life)
        self.size = float(size)
        self.type = int(ptype)
        self.opacity = float(opacity)


class ParticleSystem:
    """Система частиц для океанической анимации с нулевыми зависимостями."""

    def __init__(self, max_particles=512):
        self.max_particles = max_particles
        self.particles: list[Particle] = []

    def emit_splash(self, x: float, y: float, strength: float = 1.0, count: int = 20):
        """Создает брызги воды по параболическим дугам при клике."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100.0, 300.0) * strength

            p = Particle(
                x=x, y=y, z=0.0,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - 50.0,
                vz=random.uniform(-15.0, 15.0),
                life=1.0,
                max_life=random.uniform(0.5, 1.1),
                size=random.uniform(3.0, 6.5),
                ptype=1,  # Splash
                opacity=0.9
            )
            self.particles.append(p)

    def emit_bubble_trail(self, x: float, y: float, count: int = 2):
        """Создает всплывающие пузырьки за курсором мыши."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            p = Particle(
                x=x + random.uniform(-6, 6),
                y=y + random.uniform(-6, 6),
                z=0.0,
                vx=random.uniform(-12.0, 12.0),
                vy=random.uniform(-70.0, -25.0),
                vz=0.0,
                life=1.0,
                max_life=random.uniform(1.2, 2.4),
                size=random.uniform(2.0, 5.0),
                ptype=0,  # Bubble
                opacity=0.8
            )
            self.particles.append(p)

    def emit_sparkle(self, x: float, y: float, count: int = 18):
        """Создает неоновые вспышки искорок при клике на кнопки."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(70.0, 180.0)

            p = Particle(
                x=x, y=y, z=0.0,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                vz=0.0,
                life=1.0,
                max_life=random.uniform(0.35, 0.75),
                size=random.uniform(3.0, 7.5),
                ptype=3,  # Sparkle
                opacity=1.0
            )
            self.particles.append(p)

    def update(self, dt: float):
        """Обновление физики частиц."""
        alive = []
        for p in self.particles:
            p.life -= dt / max(0.01, p.max_life)
            if p.life <= 0.0:
                continue

            p.x += p.vx * dt
            p.y += p.vy * dt

            # Гравитация для брызг (ptype=1)
            if p.type == 1:
                p.vy += 280.0 * dt

            # Колебания пузырьков (ptype=0)
            elif p.type == 0:
                p.vx += math.sin(p.y * 0.05) * 8.0 * dt

            p.opacity = max(0.0, p.life)
            alive.append(p)

        self.particles = alive

    def render_painter(self, painter: QPainter):
        """Отрисовка частиц для 2D QPainter фолбэк режима."""
        if not self.particles or not painter or not painter.isActive():
            return

        painter.setRenderHint(QPainter.Antialiasing)

        for p in self.particles:
            x, y = p.x, p.y
            size = p.size
            alpha = int(clamp(p.opacity * 255, 0, 255))
            ptype = p.type

            if ptype == 0:  # Bubble (Голубой пузырек)
                painter.setPen(QPen(QColor(0, 242, 254, alpha), 1.0))
                painter.setBrush(QBrush(QColor(0, 242, 254, int(alpha * 0.22))))
                painter.drawEllipse(QPointF(x, y), size, size)

            elif ptype == 1:  # Splash (Морская капля)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(16, 185, 129, alpha)))
                painter.drawEllipse(QPointF(x, y), size, size)

            elif ptype == 3:  # Sparkle (Неоновая вспышка)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 242, 254, alpha)))
                painter.drawEllipse(QPointF(x, y), size * 1.1, size * 1.1)


def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))
