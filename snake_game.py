"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SERPENT ELITE - Snake Game                               ║
║                                                                              ║
║  Architecture   : MVC-inspired OOP design                                   ║
║  Classes        : Snake, Food, Obstacle, ScoreManager, Renderer, Game       ║
║  Features       : Multi-difficulty, food types, obstacles, pause, HiScore   ║
║  Author         : Generated for College Software Engineering Project         ║
╚══════════════════════════════════════════════════════════════════════════════╝

SDLC Phases Represented:
  - Requirements: Feature list in README / docstrings
  - Design:       Class hierarchy, separation of concerns
  - Implementation: Modular classes below
  - Testing:      Play-test loop; collision, score, state transitions
  - Maintenance:  Config constants at top for easy tweaking
"""

import pygame # pyright: ignore[reportMissingImports]
import sys
import random
import json
import os
import math
import time

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION  (change values here to tweak gameplay easily)
# ─────────────────────────────────────────────────────────────────────────────
CELL          = 22          # pixels per grid cell
COLS          = 36          # grid columns
ROWS          = 28          # grid rows
SIDEBAR_W     = 220         # right-side HUD width
WIN_W         = COLS * CELL + SIDEBAR_W
WIN_H         = ROWS * CELL
FPS_CAP       = 60          # renderer FPS (always smooth)
HIGHSCORE_FILE = "serpent_highscore.json"

# Difficulty: (base tick ms, speed increase per 5 pts, obstacles enabled)
DIFFICULTIES = {
    "Easy":   {"tick": 160, "accel": 2,  "obstacles": False, "wrap": True},
    "Medium": {"tick": 120, "accel": 3,  "obstacles": True,  "wrap": False},
    "Hard":   {"tick":  80, "accel": 5,  "obstacles": True,  "wrap": False},
}

# Food properties: (score_value, color_hex, glow_color, lifespan_s, label)
FOOD_TYPES = {
    "normal": {"score":  1, "color": (80,  210,  80),  "glow": (120, 255, 120), "life": None, "label": ""},
    "bonus":  {"score":  5, "color": (255, 215,   0),  "glow": (255, 240, 100), "life": 7,    "label": "+5"},
    "poison": {"score": -2, "color": (180,  60, 220),  "glow": (220, 120, 255), "life": 10,   "label": "-2"},
}

# Colour palette (neon-on-dark theme)
C_BG          = (10,  12,  20)    # deep navy background
C_GRID        = (18,  22,  38)    # subtle grid lines
C_SIDEBAR     = (15,  18,  30)    # sidebar background
C_ACCENT      = (0,  230, 180)    # teal accent
C_TEXT        = (200, 220, 255)   # soft white text
C_DIM         = (80,  100, 140)   # dimmed text
C_PANEL       = (22,  28,  48)    # card background
C_SNAKE_HEAD  = (0,   255, 200)   # bright teal head
C_SNAKE_BODY  = (0,   180, 140)   # body base
C_SNAKE_TAIL  = (0,   100,  90)   # tail fade
C_OBSTACLE    = (180,  60,  60)   # red obstacles
C_OBSTACLE_G  = (255,  80,  80)   # obstacle glow
C_GAMEOVER    = (255,  60,  60)

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colours."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_rounded_rect(surf, color, rect, radius=8, alpha=255):
    """Draw a rounded rectangle with optional transparency."""
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))

def draw_glow(surf, color, center, radius, intensity=80):
    """Draw a radial glow circle (additive blending approximation)."""
    glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(intensity * (1 - r / radius) ** 2)
        pygame.draw.circle(glow_surf, (*color, alpha), (radius, radius), r)
    surf.blit(glow_surf, (center[0] - radius, center[1] - radius),
              special_flags=pygame.BLEND_RGBA_ADD)

def cell_to_px(col, row):
    """Convert grid (col, row) to pixel centre coordinates."""
    return (col * CELL + CELL // 2, row * CELL + CELL // 2)

# ─────────────────────────────────────────────────────────────────────────────
# CLASS: ScoreManager  – handles score, level, high score persistence
# ─────────────────────────────────────────────────────────────────────────────
class ScoreManager:
    """
    Responsibility: Track score, level, and persist high score to disk.
    """
    def __init__(self):
        self.score      = 0
        self.high_score = self._load_high_score()
        self.level      = 1

    def add(self, value: int):
        """Add (or subtract) points; update level and high score."""
        self.score = max(0, self.score + value)
        self.level  = self.score // 5 + 1
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    def _load_high_score(self) -> int:
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def _save_high_score(self):
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"high_score": self.high_score}, f)

    def reset(self):
        self.score = 0
        self.level = 1

# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Snake  – movement, collision, growth logic
# ─────────────────────────────────────────────────────────────────────────────
class Snake:
    """
    Responsibility: Maintain snake body, handle movement, growth and collision.
    """
    DIRS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
    OPPOSITES = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

    def __init__(self):
        self.reset()

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        # Start with 4 segments
        self.body    = [(cx, cy), (cx - 1, cy), (cx - 2, cy), (cx - 3, cy)]
        self.direction  = "RIGHT"
        self._next_dir  = "RIGHT"
        self._grow_count = 0          # pending growth segments

    def set_direction(self, new_dir: str):
        """Prevent 180° reversal."""
        if new_dir != self.OPPOSITES.get(self.direction):
            self._next_dir = new_dir

    def move(self, wrap: bool) -> bool:
        """
        Advance snake by one step.
        Returns False if self-collision occurs (game over).
        """
        self.direction = self._next_dir
        dx, dy = self.DIRS[self.direction]
        hx, hy = self.body[0]
        nx, ny  = hx + dx, hy + dy

        if wrap:
            nx %= COLS
            ny %= ROWS
        else:
            # Wall collision
            if not (0 <= nx < COLS and 0 <= ny < ROWS):
                return False

        # Self-collision (ignore tail tip if not growing, it will be removed)
        check_body = self.body if self._grow_count > 0 else self.body[:-1]
        if (nx, ny) in check_body:
            return False

        self.body.insert(0, (nx, ny))

        if self._grow_count > 0:
            self._grow_count -= 1   # keep tail → snake grows
        else:
            self.body.pop()         # remove tail → constant length

        return True

    def grow(self, segments: int = 1):
        """Schedule growth of given segment count."""
        self._grow_count += max(1, segments)

    def shrink(self, segments: int = 1):
        """Remove tail segments (poison food effect)."""
        remove = min(segments, len(self.body) - 2)   # keep at least 2 cells
        for _ in range(remove):
            self.body.pop()

    def collides_with(self, pos) -> bool:
        return pos in self.body

    @property
    def head(self):
        return self.body[0]

    @property
    def length(self):
        return len(self.body)

# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Food  – manages all active food items
# ─────────────────────────────────────────────────────────────────────────────
class Food:
    """
    Responsibility: Spawn, age, and remove food items on the grid.
    Supports normal, bonus, and poison types.
    """
    def __init__(self):
        self.items: list[dict] = []   # list of food dicts
        self._pulse = 0.0             # shared animation phase

    def spawn(self, kind: str, occupied: set):
        """Spawn one food item of the given type at a free cell."""
        free = [
            (c, r) for c in range(COLS) for r in range(ROWS)
            if (c, r) not in occupied
        ]
        if not free:
            return
        pos = random.choice(free)
        props = FOOD_TYPES[kind]
        self.items.append({
            "kind":    kind,
            "pos":     pos,
            "score":   props["score"],
            "color":   props["color"],
            "glow":    props["glow"],
            "life":    props["life"],        # seconds; None = permanent
            "born":    time.time(),
            "label":   props["label"],
            "phase":   random.uniform(0, math.tau),  # staggered pulse
        })

    def ensure_normal(self, occupied: set):
        """Always keep exactly one normal food on screen."""
        if not any(f["kind"] == "normal" for f in self.items):
            self.spawn("normal", occupied)

    def update(self) -> list[dict]:
        """
        Advance food timers. Return list of expired food items (to be removed).
        """
        now    = time.time()
        expired = [f for f in self.items
                   if f["life"] is not None and now - f["born"] >= f["life"]]
        for f in expired:
            self.items.remove(f)
        return expired

    def check_eat(self, head) -> dict | None:
        """Return the food item eaten by the snake head, or None."""
        for f in self.items:
            if f["pos"] == head:
                self.items.remove(f)
                return f
        return None

    def all_positions(self) -> set:
        return {f["pos"] for f in self.items}

# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Obstacle  – random map obstacles (Medium / Hard only)
# ─────────────────────────────────────────────────────────────────────────────
class Obstacle:
    """
    Responsibility: Maintain static obstacle cells on the grid.
    Obstacles are added as the player levels up.
    """
    def __init__(self):
        self.cells: set = set()
        self._last_level = 0

    def update_for_level(self, level: int, occupied: set):
        """Spawn new obstacles when the level increases."""
        if level <= self._last_level:
            return
        new_count = (level - self._last_level) * 2
        self._last_level = level
        candidates = [
            (c, r) for c in range(2, COLS - 2) for r in range(2, ROWS - 2)
            if (c, r) not in occupied and (c, r) not in self.cells
        ]
        random.shuffle(candidates)
        for pos in candidates[:new_count]:
            self.cells.add(pos)

    def collides(self, pos) -> bool:
        return pos in self.cells

    def reset(self):
        self.cells.clear()
        self._last_level = 0

# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Renderer  – all drawing logic isolated here
# ─────────────────────────────────────────────────────────────────────────────
class Renderer:
    """
    Responsibility: Draw every visual element each frame.
    Keeps all pygame surface / draw calls out of game logic classes.
    """
    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        self._tick   = 0           # frame counter for animations
        self._fonts  = self._load_fonts()

    def _load_fonts(self) -> dict:
        """Load fonts; fall back to system fonts gracefully."""
        try:
            big   = pygame.font.SysFont("consolas", 36, bold=True)
            med   = pygame.font.SysFont("consolas", 22, bold=True)
            small = pygame.font.SysFont("consolas", 16)
            tiny  = pygame.font.SysFont("consolas", 13)
        except Exception:
            big   = pygame.font.Font(None, 40)
            med   = pygame.font.Font(None, 26)
            small = pygame.font.Font(None, 20)
            tiny  = pygame.font.Font(None, 16)
        return {"big": big, "med": med, "small": small, "tiny": tiny}

    # ── Background & Grid ──────────────────────────────────────────────────
    def draw_background(self):
        self.screen.fill(C_BG)
        # Faint grid lines
        for c in range(COLS + 1):
            x = c * CELL
            pygame.draw.line(self.screen, C_GRID, (x, 0), (x, WIN_H))
        for r in range(ROWS + 1):
            y = r * CELL
            pygame.draw.line(self.screen, C_GRID, (0, y), (COLS * CELL, y))

    # ── Sidebar HUD ────────────────────────────────────────────────────────
    def draw_sidebar(self, score_mgr: ScoreManager, difficulty: str,
                     paused: bool, food: Food):
        sx = COLS * CELL
        pygame.draw.rect(self.screen, C_SIDEBAR, (sx, 0, SIDEBAR_W, WIN_H))
        # Accent top border
        pygame.draw.rect(self.screen, C_ACCENT, (sx, 0, 3, WIN_H))

        x = sx + 18
        y = 20

        # Title
        self._text("SERPENT ELITE", "med", C_ACCENT, x, y)
        y += 38
        pygame.draw.line(self.screen, C_ACCENT, (x, y), (sx + SIDEBAR_W - 18, y), 1)
        y += 14

        # Stat cards
        self._stat_card("SCORE",      str(score_mgr.score),      x, y, C_TEXT);   y += 72
        self._stat_card("HIGH SCORE", str(score_mgr.high_score), x, y, (255,215,0)); y += 72
        self._stat_card("LEVEL",      str(score_mgr.level),       x, y, C_ACCENT); y += 72

        # Difficulty badge
        diff_colors = {"Easy": (80,200,80), "Medium": (255,180,0), "Hard": (255,80,80)}
        dc = diff_colors.get(difficulty, C_TEXT)
        draw_rounded_rect(self.screen, (20, 26, 42), (x, y, SIDEBAR_W - 36, 34), 8)
        self._text(f"⚡  {difficulty.upper()}", "small", dc, x + 10, y + 8)
        y += 50

        # Food legend
        y += 8
        self._text("FOOD GUIDE", "tiny", C_DIM, x, y); y += 18
        for kind, props in FOOD_TYPES.items():
            pygame.draw.circle(self.screen, props["color"],
                               (x + 8, y + 7), 6)
            sc = props["score"]
            label = f"{kind.capitalize():8}  {'+' if sc >= 0 else ''}{sc} pt"
            self._text(label, "tiny", C_TEXT, x + 20, y)
            y += 18

        # Timed food countdowns
        timed = [f for f in food.items if f["life"] is not None]
        if timed:
            y += 8
            self._text("ACTIVE TIMED FOOD", "tiny", C_DIM, x, y); y += 16
            for f in timed:
                remaining = max(0, f["life"] - (time.time() - f["born"]))
                bar_w = int((SIDEBAR_W - 52) * remaining / f["life"])
                pygame.draw.rect(self.screen, (40, 40, 60), (x, y, SIDEBAR_W - 52, 6), border_radius=3)
                pygame.draw.rect(self.screen, f["color"], (x, y, bar_w, 6), border_radius=3)
                self._text(f"{f['kind']:6}  {remaining:.1f}s", "tiny", f["color"], x, y + 8)
                y += 24

        # Controls help
        y = WIN_H - 110
        pygame.draw.line(self.screen, C_PANEL, (x, y), (sx + SIDEBAR_W - 18, y), 1)
        y += 10
        controls = [("↑↓←→", "Move"), ("P", "Pause"), ("R", "Restart"), ("ESC", "Quit")]
        for key, act in controls:
            self._text(f"[{key}]", "tiny", C_ACCENT, x, y)
            self._text(act, "tiny", C_DIM, x + 52, y)
            y += 17

        # PAUSED overlay
        if paused:
            draw_rounded_rect(self.screen, (10, 12, 24), (sx + 10, WIN_H // 2 - 24, SIDEBAR_W - 20, 48), 10, 210)
            self._text("⏸  PAUSED", "med", (255, 220, 60), x + 12, WIN_H // 2 - 14)

    def _stat_card(self, label: str, value: str, x: int, y: int, vc):
        draw_rounded_rect(self.screen, C_PANEL, (x, y, SIDEBAR_W - 36, 62), 10)
        self._text(label, "tiny", C_DIM, x + 10, y + 8)
        self._text(value, "big", vc, x + 10, y + 26)

    def _text(self, msg, font_key, color, x, y):
        surf = self._fonts[font_key].render(msg, True, color)
        self.screen.blit(surf, (x, y))

    # ── Snake ──────────────────────────────────────────────────────────────
    def draw_snake(self, snake: Snake):
        length = snake.length
        for i, (cx, cy) in enumerate(snake.body):
            t = i / max(length - 1, 1)             # 0 at head → 1 at tail
            color = lerp_color(C_SNAKE_HEAD, C_SNAKE_TAIL, t)
            px, py = cx * CELL, cy * CELL
            margin = 2 if i > 0 else 0
            # Body segment
            draw_rounded_rect(self.screen, color,
                               (px + margin, py + margin,
                                CELL - margin * 2, CELL - margin * 2),
                               radius=6 if i > 0 else 8)
            # Head details: eyes
            if i == 0:
                self._draw_snake_head(snake, px, py)
        # Glow on head
        hx, hy = snake.head
        draw_glow(self.screen, C_SNAKE_HEAD,
                  (hx * CELL + CELL // 2, hy * CELL + CELL // 2),
                  18, 60)

    def _draw_snake_head(self, snake: Snake, px: int, py: int):
        d = snake.direction
        # Eye offset based on direction
        offsets = {
            "RIGHT": [(14, 5), (14, 14)],
            "LEFT":  [(5,  5), (5,  14)],
            "UP":    [(5,  5), (14, 5)],
            "DOWN":  [(5, 14), (14, 14)],
        }
        for ox, oy in offsets.get(d, []):
            pygame.draw.circle(self.screen, (10, 10, 20), (px + ox, py + oy), 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (px + ox - 1, py + oy - 1), 1)

    # ── Food ───────────────────────────────────────────────────────────────
    def draw_food(self, food: Food):
        t = time.time()
        for f in food.items:
            cx, cy = f["pos"]
            px, py = cx * CELL + CELL // 2, cy * CELL + CELL // 2
            phase  = f["phase"]
            pulse  = math.sin(t * 4 + phase) * 0.25 + 0.75   # 0.5–1.0
            radius = int(CELL * 0.38 * pulse)

            # Glow
            draw_glow(self.screen, f["glow"], (px, py), int(radius * 2.4), 70)
            # Body
            pygame.draw.circle(self.screen, f["color"], (px, py), radius)
            # Shine
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (px - radius // 3, py - radius // 3),
                               max(1, radius // 4))
            # Label
            if f["label"]:
                lbl = self._fonts["tiny"].render(f["label"], True, (255,255,255))
                self.screen.blit(lbl, (px - lbl.get_width() // 2,
                                       py - lbl.get_height() // 2))
            # Timeout warning flash (last 3 seconds)
            if f["life"] is not None:
                remaining = f["life"] - (t - f["born"])
                if remaining < 3:
                    alpha = int(abs(math.sin(t * 8)) * 200)
                    warn  = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    pygame.draw.rect(warn, (*f["color"], alpha),
                                     (0, 0, CELL, CELL), 2, border_radius=4)
                    self.screen.blit(warn, (cx * CELL, cy * CELL))

    # ── Obstacles ──────────────────────────────────────────────────────────
    def draw_obstacles(self, obstacle: Obstacle):
        t = time.time()
        for (cx, cy) in obstacle.cells:
            px, py = cx * CELL, cy * CELL
            draw_rounded_rect(self.screen, C_OBSTACLE, (px + 2, py + 2, CELL - 4, CELL - 4), 4)
            # Animated inner cross
            phase = math.sin(t * 2 + cx * 0.7 + cy * 0.5) * 0.5 + 0.5
            inner = lerp_color(C_OBSTACLE, C_OBSTACLE_G, phase)
            pygame.draw.line(self.screen, inner, (px + 6, py + 6), (px + CELL - 7, py + CELL - 7), 2)
            pygame.draw.line(self.screen, inner, (px + CELL - 7, py + 6), (px + 6, py + CELL - 7), 2)

    # ── Game Over Screen ───────────────────────────────────────────────────
    def draw_game_over(self, score_mgr: ScoreManager, snake: Snake,
                       difficulty: str, elapsed: float):
        # Dark overlay over grid only
        overlay = pygame.Surface((COLS * CELL, WIN_H), pygame.SRCALPHA)
        overlay.fill((5, 8, 18, 200))
        self.screen.blit(overlay, (0, 0))

        cx = COLS * CELL // 2
        # Panel
        pw, ph = 340, 280
        draw_rounded_rect(self.screen, (18, 22, 40),
                           (cx - pw // 2, WIN_H // 2 - ph // 2, pw, ph), 16, 240)
        pygame.draw.rect(self.screen, C_GAMEOVER,
                         (cx - pw // 2, WIN_H // 2 - ph // 2, pw, 4), border_radius=16)

        y = WIN_H // 2 - ph // 2 + 18
        self._center_text("GAME  OVER", "big", C_GAMEOVER, cx, y)
        y += 48
        pygame.draw.line(self.screen, (50, 30, 40), (cx - 130, y), (cx + 130, y), 1)
        y += 14

        stats = [
            ("Score",      str(score_mgr.score),           C_TEXT),
            ("High Score", str(score_mgr.high_score),      (255, 215, 0)),
            ("Level",      str(score_mgr.level),            C_ACCENT),
            ("Length",     str(snake.length),               C_TEXT),
            ("Difficulty", difficulty,                       (255,180,0)),
            ("Time",       f"{int(elapsed // 60)}m {int(elapsed % 60)}s", C_DIM),
        ]
        for label, val, col in stats:
            lbl_s = self._fonts["small"].render(label, True, C_DIM)
            val_s = self._fonts["small"].render(val,   True, col)
            self.screen.blit(lbl_s, (cx - 140, y))
            self.screen.blit(val_s, (cx + 140 - val_s.get_width(), y))
            y += 24

        if score_mgr.score >= score_mgr.high_score and score_mgr.score > 0:
            self._center_text("🏆 NEW HIGH SCORE!", "small", (255, 215, 0), cx, y + 4)
            y += 22

        y += 10
        t = time.time()
        blink = (math.sin(t * 3) + 1) / 2
        rc = lerp_color(C_DIM, C_TEXT, blink)
        self._center_text("[R] Restart   [ESC] Quit", "small", rc, cx, y)

    def _center_text(self, msg, font_key, color, cx, y):
        surf = self._fonts[font_key].render(msg, True, color)
        self.screen.blit(surf, (cx - surf.get_width() // 2, y))

    # ── Menu Screen ────────────────────────────────────────────────────────
    def draw_menu(self, selected: int, difficulties: list[str], high_score: int):
        self.screen.fill(C_BG)
        cx = WIN_W // 2
        cy = WIN_H // 2
        t  = time.time()

        # Animated background particles
        random.seed(42)
        for i in range(30):
            rx = random.randint(0, WIN_W)
            ry = random.randint(0, WIN_H)
            phase = random.uniform(0, math.tau)
            alpha = int((math.sin(t * 0.8 + phase) + 1) / 2 * 60 + 20)
            r = random.randint(1, 3)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_ACCENT, alpha), (r, r), r)
            self.screen.blit(s, (rx, ry), special_flags=pygame.BLEND_RGBA_ADD)
        random.seed()

        # Title
        t2 = math.sin(t * 2) * 4
        self._center_text("SERPENT ELITE", "big", C_ACCENT, cx, cy - 160 + int(t2))

        hs_text = f"High Score: {high_score}"
        self._center_text(hs_text, "small", (255, 215, 0), cx, cy - 110)

        self._center_text("SELECT DIFFICULTY", "small", C_DIM, cx, cy - 70)

        # Difficulty buttons
        for i, diff in enumerate(difficulties):
            is_sel = i == selected
            bw, bh = 220, 48
            bx, by = cx - bw // 2, cy - 30 + i * 60
            col = (22, 30, 52) if not is_sel else (0, 50, 45)
            draw_rounded_rect(self.screen, col, (bx, by, bw, bh), 12)
            if is_sel:
                pygame.draw.rect(self.screen, C_ACCENT, (bx, by, bw, bh), 2, border_radius=12)
            diff_colors = {"Easy": (80,200,80), "Medium": (255,180,0), "Hard": (255,80,80)}
            dc = diff_colors.get(diff, C_TEXT)
            tc = dc if is_sel else C_DIM
            self._center_text(diff.upper(), "med", tc, cx, by + 13)

        self._center_text("↑↓ Select   ENTER Start", "tiny", C_DIM, cx, cy + 175)
        self._center_text("ESC Quit", "tiny", C_DIM, cx, cy + 195)

    def tick(self):
        self.clock.tick(FPS_CAP)
        self._tick += 1

# ─────────────────────────────────────────────────────────────────────────────
# CLASS: InputHandler  – maps raw pygame events to game intents
# ─────────────────────────────────────────────────────────────────────────────
class InputHandler:
    """
    Responsibility: Translate pygame events into high-level game actions.
    Returns a dict of intent flags each frame.
    """
    @staticmethod
    def process(events) -> dict:
        intents = {
            "quit": False,
            "pause": False,
            "restart": False,
            "confirm": False,
            "up": False,
            "down": False,
            "move_dir": None,

            # 🔥 NEW (mouse support)
            "click": False,
            "mouse_pos": (0, 0),
        }

        for event in events:
            if event.type == pygame.QUIT:
                intents["quit"] = True

            elif event.type == pygame.KEYDOWN:
                k = event.key

                if k == pygame.K_ESCAPE:
                    intents["quit"] = True

                elif k == pygame.K_p:
                    intents["pause"] = True

                elif k == pygame.K_r:
                    intents["restart"] = True

                elif k == pygame.K_RETURN:
                    intents["confirm"] = True

                elif k in (pygame.K_UP, pygame.K_w):
                    intents["move_dir"] = "UP"
                    intents["up"] = True

                elif k in (pygame.K_DOWN, pygame.K_s):
                    intents["move_dir"] = "DOWN"
                    intents["down"] = True

                elif k in (pygame.K_LEFT, pygame.K_a):
                    intents["move_dir"] = "LEFT"

                elif k in (pygame.K_RIGHT, pygame.K_d):
                    intents["move_dir"] = "RIGHT"

            # 🔥 MOUSE CLICK ADD
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click
                    intents["click"] = True
                    intents["mouse_pos"] = event.pos

        return intents
# ─────────────────────────────────────────────────────────────────────────────
# CLASS: Game  – orchestrates all subsystems (top-level controller)
# ─────────────────────────────────────────────────────────────────────────────
class Game:
    """
    Responsibility: Main game loop, state machine, and subsystem coordination.

    States:
        MENU      → player selects difficulty
        PLAYING   → active gameplay
        PAUSED    → game frozen; waiting for unpause
        GAME_OVER → display stats; wait for restart/quit
    """

    STATE_MENU      = "MENU"
    STATE_PLAYING   = "PLAYING"
    STATE_PAUSED    = "PAUSED"
    STATE_GAME_OVER = "GAME_OVER"

    def __init__(self):
        pygame.init()
        self.screen     = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Serpent Elite 🐍")

        # Subsystems
        self.renderer   = Renderer(self.screen)
        self.score_mgr  = ScoreManager()
        self.snake      = Snake()
        self.food       = Food()
        self.obstacle   = Obstacle()
        self.input      = InputHandler()

        # State
        self.state      = self.STATE_MENU
        self.difficulty = "Medium"
        self._diff_list = list(DIFFICULTIES.keys())
        self._diff_idx  = 1            # default Medium
        self._tick_ms   = 120          # current move interval
        self._last_move = 0            # last move timestamp (ms)
        self._start_time = 0           # game start (for elapsed)
        self._game_over_time = 0

        # Bonus food spawn timer
        self._bonus_timer  = 0
        self._poison_timer = 0

    # ── Public Entry Point ─────────────────────────────────────────────────
    def run(self):
        while True:
            events  = pygame.event.get()
            intents = self.input.process(events)

            if intents["quit"]:
                self._quit()

            if self.state == self.STATE_MENU:
                self._update_menu(intents)
                self._draw_menu()

            elif self.state == self.STATE_PLAYING:
                self._update_playing(intents)
                self._draw_playing()

            elif self.state == self.STATE_PAUSED:
                if intents["pause"] or intents["confirm"]:
                    self.state = self.STATE_PLAYING
                self._draw_playing()

            elif self.state == self.STATE_GAME_OVER:
                if intents["restart"]:
                    self._start_game()
                self._draw_game_over()

            pygame.display.flip()
            self.renderer.tick()

    # ── Menu ─────────────────────────────────────────────

    def _update_menu(self, intents):
        if intents["up"]:
            self._diff_idx = (self._diff_idx - 1) % len(self._diff_list)

        if intents["down"]:
            self._diff_idx = (self._diff_idx + 1) % len(self._diff_list)

        if intents.get("click"):
            mx, my = intents["mouse_pos"]
            cx = WIN_W // 2
            cy = WIN_H // 2

            for i, diff in enumerate(self._diff_list):
                bw, bh = 220, 48
                bx, by = cx - bw // 2, cy - 30 + i * 60

                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    self._diff_idx = i
                    self.difficulty = diff
                    self._start_game()

        if intents["confirm"]:
            self.difficulty = self._diff_list[self._diff_idx]
            self._start_game()


    def _draw_menu(self):
        self.renderer.draw_menu(
            self._diff_idx,
            self._diff_list,
            self.score_mgr.high_score
        )
    # ── Start / Reset ──────────────────────────────────────────────────────
    def _start_game(self):
        cfg = DIFFICULTIES[self.difficulty]
        self._tick_ms    = cfg["tick"]
        self._last_move  = pygame.time.get_ticks()
        self._start_time = time.time()
        self._bonus_timer  = pygame.time.get_ticks() + 8000
        self._poison_timer = pygame.time.get_ticks() + 15000

        self.score_mgr.reset()
        self.snake.reset()
        self.food.items.clear()
        self.obstacle.reset()

        # Seed first normal food
        occupied = set(self.snake.body)
        self.food.ensure_normal(occupied)

        self.state = self.STATE_PLAYING

    # ── Gameplay Update ────────────────────────────────────────────────────
    def _update_playing(self, intents):
        cfg  = DIFFICULTIES[self.difficulty]
        now  = pygame.time.get_ticks()

        # Direction input (any time, not just on tick)
        if intents["move_dir"]:
            self.snake.set_direction(intents["move_dir"])

        if intents["pause"]:
            self.state = self.STATE_PAUSED
            return

        if intents["restart"]:
            self._start_game()
            return

        # Speed increase: reduce tick by accel for every 5 points
        speed_levels = self.score_mgr.score // 5
        min_tick = 40
        current_tick = max(min_tick, cfg["tick"] - speed_levels * cfg["accel"])

        # Move snake on tick
        if now - self._last_move >= current_tick:
            self._last_move = now

            # Advance snake
            alive = self.snake.move(cfg["wrap"])

            if not alive:
                self._trigger_game_over()
                return

            # Obstacle collision
            if cfg["obstacles"] and self.obstacle.collides(self.snake.head):
                self._trigger_game_over()
                return

            # Check food eaten
            eaten = self.food.check_eat(self.snake.head)
            if eaten:
                pts = eaten["score"]
                self.score_mgr.add(pts)
                if pts > 0:
                    self.snake.grow(pts)
                else:
                    self.snake.shrink(abs(pts))

            # Refresh occupied set for spawning
            occupied = set(self.snake.body) | self.food.all_positions() | self.obstacle.cells

            # Always keep one normal food
            self.food.ensure_normal(occupied)

            # Expire timed food
            self.food.update()

            # Spawn bonus food periodically
            if now >= self._bonus_timer:
                occupied = set(self.snake.body) | self.food.all_positions() | self.obstacle.cells
                self.food.spawn("bonus", occupied)
                self._bonus_timer = now + random.randint(8000, 14000)

            # Spawn poison food periodically (Medium / Hard)
            if self.difficulty != "Easy" and now >= self._poison_timer:
                occupied = set(self.snake.body) | self.food.all_positions() | self.obstacle.cells
                self.food.spawn("poison", occupied)
                self._poison_timer = now + random.randint(12000, 20000)

            # Obstacles follow level progression
            if cfg["obstacles"]:
                occupied = set(self.snake.body) | self.food.all_positions()
                self.obstacle.update_for_level(self.score_mgr.level, occupied)

    # ── Drawing ────────────────────────────────────────────────────────────
    def _draw_playing(self):
        self.renderer.draw_background()
        self.renderer.draw_obstacles(self.obstacle)
        self.renderer.draw_food(self.food)
        self.renderer.draw_snake(self.snake)
        self.renderer.draw_sidebar(self.score_mgr, self.difficulty,
                                   self.state == self.STATE_PAUSED, self.food)

    def _draw_game_over(self):
        self._draw_playing()
        elapsed = time.time() - self._start_time
        self.renderer.draw_game_over(self.score_mgr, self.snake,
                                     self.difficulty, elapsed)

    # ── State Transitions ──────────────────────────────────────────────────
    def _trigger_game_over(self):
        self.state = self.STATE_GAME_OVER
        self._game_over_time = time.time()

    def _quit(self):
        pygame.quit()
        sys.exit()

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
