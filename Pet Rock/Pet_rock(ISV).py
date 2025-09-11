#!/usr/bin/env python3
"""
Pet Rock — desktop pet simulator (identity-seeded variant)
- Single-file Python script.
- Requirements: PyQt5 (install with `pip install PyQt5`).
- Behavior: by default the rock's appearance is deterministically generated from a hash of
  your machine's MAC address + IP address so each player gets a unique rock.

Privacy notes:
- The script only *hashes* the MAC+IP locally to create a seed. The raw MAC/IP are not
  printed or sent anywhere by default.
- To determine your public IP the script may make a short HTTPS request to a public
  IP echo service (api.ipify.org). If you prefer *no* external network calls, run with
  the `--local-only` flag or `--anon` to avoid identity-based seeding entirely.

Run examples:
  python pet_rock.py            # use MAC+IP where available
  python pet_rock.py --anon     # use an anonymous random rock (no identity)
  python pet_rock.py --local-only --show-hash  # use local IP only and print hash

"""

import sys
import math
import random
import socket
import uuid
import hashlib
import urllib.request
import urllib.error

try:
    from PyQt5.QtWidgets import QApplication, QWidget, QMenu
    from PyQt5.QtCore import Qt, QPointF, QTimer, QRectF
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


# ---------------------- identity helpers ----------------------

def get_public_ip(timeout=1.0):
    """Try to fetch public IP from a lightweight external service.
    Returns string like '1.2.3.4' or None on failure.
    NOTE: this makes a short outbound HTTPS request to the service.
    """
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=timeout) as r:
            ip = r.read().decode().strip()
            if ip:
                return ip
    except Exception:
        return None


def get_local_ip():
    """Try to determine the machine's local outward-facing IP without sending data.
    Falls back to gethostbyname if needed.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't actually send packets
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None


def get_mac():
    """Returns MAC as hex string (upper-case, colon separated). Uses uuid.getnode().
    Note: on some platforms uuid.getnode() may return a random value if it cannot find
    a hardware address.
    """
    n = uuid.getnode()
    mac = ':'.join(("%012X" % n)[i:i+2] for i in range(0, 12, 2))
    return mac


def compute_identity_hash(ip: str | None, mac: str | None) -> bytes:
    """Compute SHA-256 of the (mac|ip) pair and return raw bytes.
    We deliberately use a clear separator to avoid accidental collisions.
    """
    mac_s = mac or "unknown_mac"
    ip_s = ip or "unknown_ip"
    data = f"{mac_s}|{ip_s}".encode("utf-8")
    return hashlib.sha256(data).digest()


# ---------------------- PetRock widget ----------------------

class PetRock(QWidget):
    def __init__(self, size=220, seed=None):
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

        # Deterministic seed used for all visual randomness (speckles, etc.)
        if seed is None:
            seed = random.randint(0, 2**63 - 1)
        # keep the original bytes around in case someone wants to inspect
        self._seed_int = int(seed)

        self._speckle_seed = self._seed_int

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
        # Use a reproducible RNG seeded from the identity-derived seed so the speckles
        # are consistent per-user
        rnd = random.Random(self._speckle_seed)
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


# ---------------------- command-line + startup ----------------------

def main():
    # Basic, optional CLI flags
    use_anon = "--anon" in sys.argv
    local_only = "--local-only" in sys.argv
    show_hash = "--show-hash" in sys.argv

    # Determine IP (public preferred, then local). Honor local-only and anon flags.
    ip = None
    mac = None
    identity_hash = None
    seed_int = None

    if not use_anon:
        try:
            if not local_only:
                ip = get_public_ip()
            if ip is None:
                ip = get_local_ip()
            mac = get_mac()
            identity_hash = compute_identity_hash(ip, mac)
            # use first 8 bytes of the hash as a stable integer seed
            seed_int = int.from_bytes(identity_hash[:8], "big")
        except Exception:
            # if anything goes wrong, fall back to a random seed
            seed_int = random.randint(0, 2**63 - 1)
    else:
        seed_int = random.randint(0, 2**63 - 1)

    if show_hash and identity_hash is not None:
        print("identity hash:", identity_hash.hex())
    elif show_hash and identity_hash is None:
        print("identity hash: <not available — using anonymous seed>")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    rock = PetRock(size=260, seed=seed_int)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
