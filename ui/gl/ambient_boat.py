"""
ui/gl/ambient_boat.py — Маленький кибер-кораблик на 3D-волнах Герстнера (WaterMetrics).

Реализует:
1. Физику качания оригами-кораблика по формуле волн Герстнера (z, roll, pitch).
2. Детектор бездействия (Idle Tracker): появление при простое пользователя.
3. Смену моделей каждые 5 минут (Оригами-парусник, Кибер-яхта, Лодочка с фонариком, Субмарина).
4. Анимацию убегания и плавного растворения при движении мыши (Fleeing on Activity).
"""

from __future__ import annotations

import math
import time
from enum import Enum
from typing import Tuple, List

import numpy as np


class BoatState(Enum):
    HIDDEN = 0
    SPAWNING = 1
    SAILING = 2
    FLEEING = 3


class AmbientBoat:
    """Управляет состоянием, геометрией и рендерингом 3D-кораблика на волнах."""

    def __init__(self):
        self.state: BoatState = BoatState.HIDDEN
        self.pos = np.array([-1.35, -0.2], dtype=np.float32)  # 2D координаты в сетке волн
        self.speed = 0.08                                      # Базовая скорость движения
        self.heading = 0.12                                    # Направление движения (радианы)
        self.scale = 0.040                                     # Миниатюрный размер (маленький кораблик)
        self.alpha = 0.0                                       # Текущая прозрачность (0..1)
        self.target_alpha = 0.0
        self.boat_style = 0                                    # 0: Origami, 1: Yacht, 2: Lantern, 3: Submarine
        self.last_style_switch_time = time.time()
        self.idle_start_time = time.time()
        self.idle_threshold_sec = 25.0                         # Время простоя до появления кораблика (сек)
        self.style_interval_sec = 300.0                        # Каждые 5 минут (300 сек) — новый кораблик

        self._models = [
            self._build_origami_boat(),
            self._build_cyber_yacht(),
            self._build_lantern_boat(),
            self._build_submarine()
        ]

    def reset_idle(self) -> None:
        """Сброс таймера простоя при активности пользователя (мышь/клавиатура)."""
        now = time.time()
        self.idle_start_time = now

        # Если кораблик сейчас плывет или появляется — запускаем ускоренное убегание
        if self.state in (BoatState.SAILING, BoatState.SPAWNING):
            self.state = BoatState.FLEEING
            self.target_alpha = 0.0

    def update(self, dt: float) -> None:
        """Обновление физики и анимации кораблика."""
        now = time.time()
        idle_duration = now - self.idle_start_time

        # Проверка 5-минутного интервала для смены стиля
        if now - self.last_style_switch_time >= self.style_interval_sec:
            self.boat_style = (self.boat_style + 1) % len(self._models)
            self.last_style_switch_time = now

        # 1. Состояние HIDDEN: проверяем порог простоя
        if self.state == BoatState.HIDDEN:
            if idle_duration >= self.idle_threshold_sec:
                self._spawn_boat()

        # 2. Плавное изменение прозрачности (Fade In / Fade Out)
        if self.alpha < self.target_alpha:
            self.alpha = min(self.target_alpha, self.alpha + dt * 1.5)
        elif self.alpha > self.target_alpha:
            fade_spd = 2.5 if self.state == BoatState.FLEEING else 1.2
            self.alpha = max(self.target_alpha, self.alpha - dt * fade_spd)

        # 3. Движение в зависимости от состояния
        if self.state in (BoatState.SPAWNING, BoatState.SAILING):
            # Неспешное покачивающееся плавание
            move_spd = self.speed
            self.pos[0] += math.cos(self.heading) * move_spd * dt
            self.pos[1] += math.sin(self.heading) * move_spd * dt
            # Легкое синусоидальное покачивание курса
            self.heading += math.sin(now * 0.8) * 0.05 * dt

            if self.alpha >= 0.85 and self.state == BoatState.SPAWNING:
                self.state = BoatState.SAILING

            # Если уплыл за правый край экрана
            if self.pos[0] > 1.45:
                self.state = BoatState.HIDDEN
                self.alpha = 0.0
                self.target_alpha = 0.0

        elif self.state == BoatState.FLEEING:
            # Турбо-ускорение в сторону ближайшего края экрана
            flee_spd = self.speed * 4.5
            self.pos[0] += math.cos(self.heading) * flee_spd * dt
            self.pos[1] += math.sin(self.heading) * flee_spd * dt

            if self.alpha <= 0.01:
                self.state = BoatState.HIDDEN
                self.alpha = 0.0

    def _spawn_boat(self) -> None:
        """Рождение нового кораблика у левого края экрана."""
        self.state = BoatState.SPAWNING
        # Выбираем случайную или гармоничную Y-координату в нижней/средней части экрана
        y_pos = -0.45 + (time.time() % 0.6) - 0.3
        self.pos = np.array([-1.35, y_pos], dtype=np.float32)
        self.heading = 0.08 + (time.time() % 0.15) - 0.07
        self.target_alpha = 0.90
        self.alpha = 0.0

    def get_projected_lines(
        self,
        t: float,
        wave_amp: float = 0.22,
        wave_steep: float = 0.55,
        tilt: float = 0.48
    ) -> np.ndarray:
        """
        Вычисляет 3D проекцию линий кораблика на основе текущей высоты и нормали волны.
        Возвращает массив точек (N, 2) в координатах OpenGL [-1.45, 1.45].
        """
        if self.state == BoatState.HIDDEN or self.alpha <= 0.005:
            return np.empty((0, 2), dtype=np.float32)

        local_verts = self._models[self.boat_style]
        p = self.pos

        # Вычисление высоты и градиента волны в точке нахождения кораблика
        A = wave_amp
        Q = wave_steep
        waves = [
            (np.array([1.0, 0.7]), A * 1.00, 3.2, 0.65, Q),
            (np.array([-0.6, 1.0]), A * 0.65, 4.8, 0.85, Q * 0.8),
            (np.array([0.9, -0.4]), A * 0.30, 8.0, 1.20, Q * 0.3),
            (np.array([-0.3, -0.8]), A * 0.50, 2.0, 0.45, Q * 0.6),
        ]

        xy_shift = np.zeros(2, dtype=np.float32)
        z0 = 0.0
        grad = np.zeros(2, dtype=np.float32)

        for D, wA, k, spd, wQ in waves:
            D_norm = D / np.linalg.norm(D)
            phase = k * (D_norm[0] * p[0] + D_norm[1] * p[1]) - spd * t
            C = math.cos(phase)
            S = math.sin(phase)
            xy_shift += np.array([wQ * wA * D_norm[0] * C, wQ * wA * D_norm[1] * C], dtype=np.float32)
            z0 += wA * S
            grad += np.array([wA * k * D_norm[0] * C, wA * k * D_norm[1] * C], dtype=np.float32)

        # Вычисление нормали к водной поверхности
        normal = np.array([-grad[0], -grad[1], 1.0], dtype=np.float32)
        norm_len = np.linalg.norm(normal)
        if norm_len > 1e-6:
            normal /= norm_len
        else:
            normal = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # Направляющий вектор кораблика, спроецированный на касательную плоскость воды
        fwd_raw = np.array([math.cos(self.heading), math.sin(self.heading), 0.0], dtype=np.float32)
        fwd = fwd_raw - np.dot(fwd_raw, normal) * normal
        fwd_len = np.linalg.norm(fwd)
        if fwd_len > 1e-6:
            fwd /= fwd_len
        else:
            fwd = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        # Правый вектор
        right = np.cross(fwd, normal)
        right_len = np.linalg.norm(right)
        if right_len > 1e-6:
            right /= right_len
        else:
            right = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        rot_matrix = np.column_stack([fwd, right, normal])

        # Применение масштаба и легкого динамического покачивания
        bob = math.sin(t * 3.5) * 0.008
        scaled_verts = local_verts * self.scale

        proj_points = []
        cos_tilt = math.cos(tilt)
        sin_tilt = math.sin(tilt)

        for v in scaled_verts:
            world_3d = rot_matrix @ v + np.array([p[0], p[1], z0 + bob], dtype=np.float32)
            # Горизонтальный сдвиг Герстнера
            dPos = world_3d[:2] + xy_shift * 0.22
            z = world_3d[2]

            # 3D изометрическая проекция
            px = dPos[0]
            py = dPos[1] * cos_tilt - z * sin_tilt
            proj_points.append([px, py])

        return np.array(proj_points, dtype=np.float32)

    # ─── 3D Wireframe Модели корабликов ─────────────────────────────────

    @staticmethod
    def _build_origami_boat() -> np.ndarray:
        """Стиль 0: Классический оригами-парусник с мачтой и флажком."""
        lines = [
            # Киль (дно)
            ([-0.8, 0.0, 0.0], [0.8, 0.0, 0.0]),
            # Борта
            ([-0.8, 0.0, 0.0], [-1.2, 0.0, 0.25]),
            ([-1.2, 0.0, 0.25], [-0.5, 0.3, 0.25]),
            ([-0.5, 0.3, 0.25], [0.5, 0.3, 0.25]),
            ([0.5, 0.3, 0.25], [1.2, 0.0, 0.25]),
            ([1.2, 0.0, 0.25], [0.8, 0.0, 0.0]),

            ([-1.2, 0.0, 0.25], [-0.5, -0.3, 0.25]),
            ([-0.5, -0.3, 0.25], [0.5, -0.3, 0.25]),
            ([0.5, -0.3, 0.25], [1.2, 0.0, 0.25]),

            # Ребра корпуса
            ([-0.5, 0.3, 0.25], [-0.5, -0.3, 0.25]),
            ([0.5, 0.3, 0.25], [0.5, -0.3, 0.25]),
            ([0.0, 0.0, 0.0], [0.0, 0.0, 0.25]),

            # Мачта
            ([0.0, 0.0, 0.25], [0.0, 0.0, 1.6]),

            # Главный парус
            ([0.0, 0.0, 1.5], [0.8, 0.0, 0.35]),
            ([0.8, 0.0, 0.35], [0.0, 0.0, 0.35]),
            ([0.0, 0.0, 1.5], [0.4, 0.12, 0.85]),
            ([0.4, 0.12, 0.85], [0.8, 0.0, 0.35]),

            # Передний парус (стаксель)
            ([0.0, 0.0, 1.3], [-0.65, 0.0, 0.35]),
            ([-0.65, 0.0, 0.35], [0.0, 0.0, 0.35]),

            # Неоновый флажок на мачте
            ([0.0, 0.0, 1.6], [-0.35, 0.0, 1.72]),
            ([-0.35, 0.0, 1.72], [0.0, 0.0, 1.48]),
        ]
        verts = []
        for p1, p2 in lines:
            verts.extend([p1, p2])
        return np.array(verts, dtype=np.float32)

    @staticmethod
    def _build_cyber_yacht() -> np.ndarray:
        """Стиль 1: Кибер-яхта с футуристической рубкой и спойлером."""
        lines = [
            # Корпус
            ([-1.1, 0.0, 0.0], [1.3, 0.0, 0.0]),
            ([-1.1, 0.0, 0.0], [-1.0, 0.4, 0.22]),
            ([-1.0, 0.4, 0.22], [0.8, 0.35, 0.22]),
            ([0.8, 0.35, 0.22], [1.3, 0.0, 0.0]),

            ([-1.1, 0.0, 0.0], [-1.0, -0.4, 0.22]),
            ([-1.0, -0.4, 0.22], [0.8, -0.35, 0.22]),
            ([0.8, -0.35, 0.22], [1.3, 0.0, 0.0]),

            # Транец
            ([-1.0, 0.4, 0.22], [-1.0, -0.4, 0.22]),

            # Рубка
            ([-0.4, 0.22, 0.22], [0.4, 0.18, 0.22]),
            ([0.4, 0.18, 0.22], [0.2, 0.15, 0.65]),
            ([0.2, 0.15, 0.65], [-0.4, 0.18, 0.65]),
            ([-0.4, 0.18, 0.65], [-0.4, 0.22, 0.22]),

            ([-0.4, -0.22, 0.22], [0.4, -0.18, 0.22]),
            ([0.4, -0.18, 0.22], [0.2, -0.15, 0.65]),
            ([0.2, -0.15, 0.65], [-0.4, -0.18, 0.65]),
            ([-0.4, -0.18, 0.65], [-0.4, -0.22, 0.22]),

            # Верх рубки
            ([0.2, 0.15, 0.65], [0.2, -0.15, 0.65]),
            ([-0.4, 0.18, 0.65], [-0.4, -0.18, 0.65]),

            # Радар / Антенна
            ([0.0, 0.0, 0.65], [0.0, 0.0, 1.1]),
            ([-0.15, 0.0, 1.1], [0.15, 0.0, 1.1]),
        ]
        verts = []
        for p1, p2 in lines:
            verts.extend([p1, p2])
        return np.array(verts, dtype=np.float32)

    @staticmethod
    def _build_lantern_boat() -> np.ndarray:
        """Стиль 2: Бумажная лодочка с сияющим фонариком на носу."""
        lines = [
            # Классическая лодочка трапецией
            ([-0.9, 0.0, 0.0], [0.9, 0.0, 0.0]),
            ([-0.9, 0.0, 0.0], [-1.3, 0.35, 0.3]),
            ([-1.3, 0.35, 0.3], [1.3, 0.35, 0.3]),
            ([1.3, 0.35, 0.3], [0.9, 0.0, 0.0]),

            ([-0.9, 0.0, 0.0], [-1.3, -0.35, 0.3]),
            ([-1.3, -0.35, 0.3], [1.3, -0.35, 0.3]),
            ([1.3, -0.35, 0.3], [0.9, 0.0, 0.0]),

            # Треугольный центральный гребень
            ([-0.4, 0.0, 0.3], [0.0, 0.0, 0.95]),
            ([0.0, 0.0, 0.95], [0.4, 0.0, 0.3]),
            ([-0.4, 0.0, 0.3], [0.4, 0.0, 0.3]),

            # Носовой фонарик
            ([1.1, 0.0, 0.25], [1.1, 0.0, 0.75]),
            ([1.1, 0.0, 0.75], [1.25, 0.0, 0.6]),
            ([1.25, 0.0, 0.6], [1.1, 0.0, 0.45]),
            ([1.1, 0.0, 0.45], [0.95, 0.0, 0.6]),
            ([0.95, 0.0, 0.6], [1.1, 0.0, 0.75]),
        ]
        verts = []
        for p1, p2 in lines:
            verts.extend([p1, p2])
        return np.array(verts, dtype=np.float32)

    @staticmethod
    def _build_submarine() -> np.ndarray:
        """Стиль 3: Неоновая субмарина с перископом и кольцами гидролокатора."""
        lines = [
            # Капсульный корпус
            ([-1.2, 0.0, 0.1], [1.2, 0.0, 0.1]),
            ([-1.0, 0.3, 0.1], [1.0, 0.3, 0.1]),
            ([-1.0, -0.3, 0.1], [1.0, -0.3, 0.1]),
            ([-1.2, 0.0, 0.1], [-1.0, 0.3, 0.1]),
            ([-1.2, 0.0, 0.1], [-1.0, -0.3, 0.1]),
            ([1.2, 0.0, 0.1], [1.0, 0.3, 0.1]),
            ([1.2, 0.0, 0.1], [1.0, -0.3, 0.1]),

            # Рубка
            ([-0.3, 0.15, 0.1], [0.3, 0.15, 0.1]),
            ([0.3, 0.15, 0.1], [0.2, 0.1, 0.55]),
            ([0.2, 0.1, 0.55], [-0.2, 0.1, 0.55]),
            ([-0.2, 0.1, 0.55], [-0.3, 0.15, 0.1]),

            ([-0.3, -0.15, 0.1], [0.3, -0.15, 0.1]),
            ([0.3, -0.15, 0.1], [0.2, -0.1, 0.55]),
            ([0.2, -0.1, 0.55], [-0.2, -0.1, 0.55]),
            ([-0.2, -0.1, 0.55], [-0.3, -0.15, 0.1]),

            ([0.2, 0.1, 0.55], [0.2, -0.1, 0.55]),
            ([-0.2, 0.1, 0.55], [-0.2, -0.1, 0.55]),

            # Перископ
            ([0.0, 0.0, 0.55], [0.0, 0.0, 0.95]),
            ([0.0, 0.0, 0.95], [0.18, 0.0, 0.95]),
        ]
        verts = []
        for p1, p2 in lines:
            verts.extend([p1, p2])
        return np.array(verts, dtype=np.float32)
