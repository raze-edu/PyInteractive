"""Particle and confetti effects system for celebratory feedback."""
import random
from typing import List, Tuple
import pygame

class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(-3.1415, 0.0)
        speed = random.uniform(200.0, 550.0)
        self.vx = math_cos(angle) * speed
        self.vy = math_sin(angle) * speed
        self.gravity = 750.0
        self.size = random.uniform(6.0, 12.0)
        self.lifetime = random.uniform(0.8, 1.6)
        self.age = 0.0
        self.rotation = random.uniform(0.0, 360.0)
        self.rot_speed = random.uniform(-300.0, 300.0)

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.rotation += self.rot_speed * dt
        return True

    def draw(self, screen: pygame.Surface) -> None:
        alpha = max(0.0, 1.0 - (self.age / self.lifetime))
        s = int(self.size * alpha)
        if s > 1:
            rect = pygame.Rect(int(self.x - s // 2), int(self.y - s // 2), s, s)
            pygame.draw.rect(screen, self.color, rect)

import math
def math_cos(a: float) -> float:
    return math.cos(a)
def math_sin(a: float) -> float:
    return math.sin(a)

class ConfettiSystem:
    def __init__(self):
        self.particles: List[Particle] = []
        self.palette = [
            (88, 204, 2),    # Lime green
            (28, 176, 246),  # Sky blue
            (255, 200, 0),   # Gold
            (255, 75, 140),  # Pink
            (255, 120, 0),   # Orange
            (160, 100, 255)  # Purple
        ]

    def burst(self, x: float, y: float, count: int = 40) -> None:
        for _ in range(count):
            c = random.choice(self.palette)
            self.particles.append(Particle(x, y, c))

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, screen: pygame.Surface) -> None:
        for p in self.particles:
            p.draw(screen)
