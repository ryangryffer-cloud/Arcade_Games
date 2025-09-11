#!/usr/bin/env python3
"""
Pet Rock — desktop pet simulator
- Single-file Python script.
- Requirements: PyQt5 (install with `pip install PyQt5`).
- Run: python pet_rock.py
"""

import sys
import math
import random

try:
    from PyQt5.QtWidgets import QApplication, QWidget, QMenu
    from PyQt5.QtCore import Qt, QPoint, QPointF, QTimer, QRectF
    from PyQt5.QtGui import (
        QPainter,
        QColor,
        QBrush,
        QRadialGradient,
        QPainterPath,
        QPen,
    )
except ImportError:
    print("This script requires PyQt5. Install with: pip install PyQt5")
    sys.exit(1)


class PetRock(QWidget):
    def __init__(self, size=220):
        super().__init__()
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        # Allow per-pixel transparency
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.size = size
        self.setFixedSize(self.size, int(self.size * 0.8))

        self.drag_offset = None
        self.picked = False
        self.bob_phase = random.random() * 10
        self.seed = random.randint(0, 99999)

        self.initUI()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)  # ~30 FPS for smooth idle animation

    def initUI(self):
        # Place near bottom-right of primary screen
        scr = QApplication.primaryScreen().availableGeometry()
        x = scr.right() - self.width() - 80
        y = scr.bottom() - self.height() - 140
        self.move(x, y)
        self.show()

    def _tick(self):
        if not self.picked:
            self.bob_phase += 0.06
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # bobbing offset when idle, lift when picked
        bob = math.sin(self.bob_phase) * 3 if not self.picked else -8
        painter.translate(0, bob)

        # soft shadow beneath the rock
        shadow_center = QPointF(w / 2, h * 0.75)
        shadow_radius = max(w, h) * 0.5
        grad = QRadialGradient(shadow_center, shadow_radius)
        grad.setColorAt(0, QColor(0, 0, 0, 120))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(shadow_center, w * 0.35, h * 0.11)

        # rock base path (slightly irregular oval)
        rect = QRectF(w * 0.07, h * 0.06, w * 0.86, h * 0.7)
        path = QPainterPath()
        path.addEllipse(rect)

        # rock gradient shading
        grad2 = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.7)
        grad2.setColorAt(0.0, QColor(220, 220, 210))
        grad2.setColorAt(0.6, QColor(170, 160, 150))
        grad2.setColorAt(1.0, QColor(120, 110, 100))
        painter.setBrush(QBrush(grad2))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # subtle speckles
        rnd = random.Random(self.seed)
        painter.setPen(Qt.NoPen)
        for i in range(14):
            rx = rect.left() + rnd.random() * rect.width()
            ry = rect.top() + rnd.random() * rect.height() * 0.8
            r = 1.5 + rnd.random() * 4.0
            painter.setBrush(QColor(90, 80, 70, 200))
            painter.drawEllipse(QPointF(rx, ry), r, r)

        # glossy highlight
        highlight = QPainterPath()
        highlight.addEllipse(
            QRectF(
                rect.left() + rect.width() * 0.12,
                rect.top() + rect.height() * 0.05,
                rect.width() * 0.35,
                rect.height() * 0.28,
            )
        )
        painter.setBrush(QColor(255, 255, 255, 80))
        painter.drawPath(highlight)

        # outline
        pen = QPen(QColor(60, 50, 45, 220), 2.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # small indicator when picked up
        if self.picked:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 30))
            painter.drawEllipse(QPointF(w / 2, h * 0.12), w * 0.05, h * 0.03)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self.picked = True
            self.bob_phase = 0
            self.update()
        elif event.button() == Qt.RightButton:
            menu = QMenu(self)
            act_reset = menu.addAction("Reset position")
            act_exit = menu.addAction("Exit")
            chosen = menu.exec_(event.globalPos())
            if chosen == act_reset:
                self.initUI()
            elif chosen == act_exit:
                QApplication.quit()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            self.move(event.globalPos() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = None
            self.picked = False
            self.update()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    # You can change size here (recommended 160-320)
    rock = PetRock(size=260)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
