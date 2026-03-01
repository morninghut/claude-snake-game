#!/usr/bin/env python3
"""
Terminal Snake Game - Enhanced v2.2
Features: True color, Unicode, Game modes, Visual effects, Sound
"""

import curses
import random
import time
import os
import json
from collections import deque
from enum import Enum
from typing import Optional, Tuple, Set, List, Dict, Any

# ============== Constants ==============

# Game states
class State(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3

# Game modes
class GameMode(Enum):
    CLASSIC = 'c'
    TIME_ATTACK = 't'
    ZEN = 'z'
    SURVIVAL = 's'

# Power-up types
class PowerupType(Enum):
    NONE = 0
    SLOW = 1
    DOUBLE = 2
    GROW = 3

# Difficulty settings
DIFFICULTY: Dict[str, Dict[str, Any]] = {
    '1': {'name': 'Easy', 'speed': 200},
    '2': {'name': 'Medium', 'speed': 150},
    '3': {'name': 'Hard', 'speed': 100},
}

# Game mode info
MODE_INFO: Dict[str, Dict[str, str]] = {
    'c': {'name': 'Classic', 'desc': 'Traditional snake gameplay'},
    't': {'name': 'Time Attack', 'desc': '2 min to score high'},
    'z': {'name': 'Zen', 'desc': 'Relax - no game over'},
    's': {'name': 'Survival', 'desc': 'Walls appear over time'},
}

# Power-up descriptions
POWERUP_DESC: Dict[int, str] = {
    1: 'Slow: Reduces speed temporarily',
    2: 'Double: 2x points',
    3: 'Grow: Extra length',
}

# Unicode symbols
SYMBOLS: Dict[str, str] = {
    'border_h': '═', 'border_v': '║',
    'corner_tl': '╔', 'corner_tr': '╗',
    'corner_bl': '╚', 'corner_br': '╝',
    'snake_head': '●', 'snake_body': '○',
    'food': '◆', 'food_alt': '★',
    'powerup_slow': '◐', 'powerup_double': '◑',
    'powerup_grow': '✦',
}

# ASCII fallback
ASCII_SYMBOLS: Dict[str, str] = {
    'border_h': '=', 'border_v': '|',
    'corner_tl': '+', 'corner_tr': '+',
    'corner_bl': '+', 'corner_br': '+',
    'snake_head': '@', 'snake_body': 'o',
    'food': '*', 'food_alt': '+',
    'powerup_slow': 'S', 'powerup_double': 'D',
    'powerup_grow': 'G',
}

# Color-blind friendly symbols
CB_SYMBOLS: Dict[str, str] = {
    'border_h': '=', 'border_v': '|',
    'corner_tl': '+', 'corner_tr': '+',
    'corner_bl': '+', 'corner_br': '+',
    'snake_head': 'O', 'snake_body': 'o',
    'food': 'X', 'food_alt': 'x',
    'powerup_slow': '[', 'powerup_double': ']',
    'powerup_grow': '*',
}

# Game configuration constants
TIME_LIMIT_SECONDS: int = 120
WALL_INTERVAL: int = 20
MAX_SURVIVAL_WALLS: int = 10
POWERUP_SPAWN_CHANCE: float = 0.08
SLOW_POWERUP_DURATION: int = 50
DOUBLE_SCORE_BONUS: int = 20
FOOD_SCORE: int = 10
SPEED_INCREASE_INTERVAL: int = 5
SPEED_MULTIPLIER: float = 0.85
SLOW_MULTIPLIER: float = 1.3
FOOD_PULSE_CYCLE: int = 20
SCORE_POPUP_DURATION: int = 30
MAX_INPUT_QUEUE: int = 2
SPAWN_MAX_ATTEMPTS: int = 100

DEFAULT_WIDTH: int = 40
DEFAULT_HEIGHT: int = 18
MIN_TERMINAL_WIDTH: int = 42
MIN_TERMINAL_HEIGHT: int = 22

HIGHSCORE_FILE: str = os.path.expanduser("~/.snake_highscores")
CONFIG_FILE: str = os.path.expanduser("~/.snake_config")


class SnakeGame:
    """Main game class for Terminal Snake."""

    def __init__(self, stdscr: curses.window, difficulty: str = '2',
                 game_mode: str = 'c', sound: bool = True,
                 use_unicode: bool = True, color_blind: bool = False) -> None:
        """Initialize the game."""
        self.stdscr = stdscr
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.difficulty = difficulty
        self.game_mode = game_mode
        self.sound = sound
        self.use_unicode = use_unicode
        self.color_blind = color_blind
        self.base_speed = DIFFICULTY[difficulty]['speed']
        self._update_symbols()
        self.init_game()

    def _update_symbols(self) -> None:
        """Update symbols based on current settings."""
        if not self.use_unicode:
            self.symbols = ASCII_SYMBOLS
        elif self.color_blind:
            self.symbols = CB_SYMBOLS
        else:
            self.symbols = SYMBOLS

    def init_game(self) -> None:
        """Initialize a new game."""
        self.state = State.PLAYING
        self.game_over = False
        self.score = 0
        self.speed = self.base_speed
        self.food_eaten = 0
        self.high_score = self.load_high_score()
        self.powerup_timer = 0
        self.snake_set: Set[Tuple[int, int]] = set()
        self.score_popup: Optional[Tuple[Tuple[int, int], str, int]] = None
        self.is_new_high_score = False

        # Time attack
        if self.game_mode == 't':
            self.time_remaining = TIME_LIMIT_SECONDS

        # Survival walls
        if self.game_mode == 's':
            self.walls: Set[Tuple[int, int]] = set()
        else:
            self.walls = set()

        # Initialize snake
        mid_x, mid_y = self.width // 2, self.height // 2
        self.snake: List[Tuple[int, int]] = [
            (mid_x, mid_y),
            (mid_x - 1, mid_y),
            (mid_x - 2, mid_y)
        ]
        self.snake_set = set(self.snake)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.input_queue: deque = deque(maxlen=MAX_INPUT_QUEUE)
        self.frame_count = 0

        # Initialize powerup_pos before spawning
        self.powerup_pos = (-1, -1)
        self.powerup_type = PowerupType.NONE

        self.spawn_food()
        self.spawn_powerup()

    def beep(self) -> None:
        """Play beep sound if sound is enabled."""
        if self.sound:
            try:
                curses.beep()
            except curses.error:
                pass

    def spawn_food(self) -> None:
        """Spawn food at a random valid position."""
        for _ in range(SPAWN_MAX_ATTEMPTS):
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            pos = (x, y)
            if (pos not in self.snake_set and
                pos != self.powerup_pos and
                pos not in self.walls):
                self.food = pos
                self.food_pulse = 0
                return
        # Fallback: spawn at first available position
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                pos = (x, y)
                if (pos not in self.snake_set and
                    pos != self.powerup_pos and
                    pos not in self.walls):
                    self.food = pos
                    self.food_pulse = 0
                    return

    def spawn_powerup(self) -> None:
        """Spawn power-up at a random valid position."""
        if random.random() < POWERUP_SPAWN_CHANCE:
            for _ in range(SPAWN_MAX_ATTEMPTS):
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
                pos = (x, y)
                if (pos not in self.snake_set and
                    pos != self.food and
                    pos not in self.walls):
                    self.powerup_pos = pos
                    self.powerup_type = random.choice([
                        PowerupType.SLOW, PowerupType.DOUBLE, PowerupType.GROW
                    ])
                    return
        self.powerup_pos = (-1, -1)
        self.powerup_type = PowerupType.NONE

    def add_survival_wall(self) -> None:
        """Add random walls in survival mode."""
        num_walls = self.food_eaten // WALL_INTERVAL
        target_walls = min(num_walls, MAX_SURVIVAL_WALLS)

        while len(self.walls) < target_walls:
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            pos = (x, y)
            if pos not in self.snake and pos != self.food:
                self.walls.add(pos)

    def load_high_score(self) -> int:
        """Load high score from file."""
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    key = f"{self.difficulty}_{self.game_mode}"
                    return data.get(key, 0)
        except (IOError, json.JSONDecodeError, KeyError):
            pass
        return 0

    def save_high_score(self) -> None:
        """Save high score to file."""
        try:
            data: Dict[str, int] = {}
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            key = f"{self.difficulty}_{self.game_mode}"
            if self.score > data.get(key, 0):
                data[key] = self.score
                self.is_new_high_score = True
            with open(HIGHSCORE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except (IOError, json.JSONDecodeError):
            pass

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return {'sound': True, 'unicode': True, 'color_blind': False}

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f)
        except IOError:
            pass

    def handle_input(self) -> None:
        """Handle user input."""
        try:
            key = self.stdscr.getch()
        except curses.error:
            return

        # Menu controls
        if self.state == State.MENU:
            if key in [ord('1'), ord('2'), ord('3')]:
                self.difficulty = chr(key)
                self.base_speed = DIFFICULTY[self.difficulty]['speed']
            elif key in [ord('c'), ord('t'), ord('z'), ord('s')]:
                self.game_mode = chr(key)
            elif key == ord('m'):  # Toggle sound
                self.sound = not self.sound
                self.save_config({
                    'sound': self.sound,
                    'unicode': self.use_unicode,
                    'color_blind': self.color_blind
                })
            elif key == ord('u'):  # Toggle unicode
                self.use_unicode = not self.use_unicode
                self._update_symbols()
                self.save_config({
                    'sound': self.sound,
                    'unicode': self.use_unicode,
                    'color_blind': self.color_blind
                })
            elif key == ord('b'):  # Toggle color blind mode
                self.color_blind = not self.color_blind
                self._update_symbols()
                self.save_config({
                    'sound': self.sound,
                    'unicode': self.use_unicode,
                    'color_blind': self.color_blind
                })
            elif key in [ord('\n'), ord(' ')]:
                self.state = State.PLAYING
                self.init_game()
            elif key in (ord('q'), 27):
                self.state = State.GAME_OVER
                self.game_over = True
                self.save_high_score()
                self.quit = True
            return

        # Game over controls
        if self.state == State.GAME_OVER:
            if key == ord('r'):
                self.init_game()
                self.state = State.PLAYING
            elif key in (ord('q'), 27):
                self.save_high_score()
                self.state = State.MENU
            return

        # Quit during game
        if key in (ord('q'), 27):
            self.save_high_score()
            self.state = State.MENU
            return

        # Restart
        if key == ord('r'):
            self.init_game()
            return

        # Pause
        if key == ord(' '):
            self.state = State.PAUSED if self.state == State.PLAYING else State.PLAYING
            self.beep()
            return

        if self.state != State.PLAYING:
            return

        # Direction controls
        direction_map = {
            curses.KEY_UP: (0, -1), curses.KEY_DOWN: (0, 1),
            curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0),
            ord('w'): (0, -1), ord('s'): (0, 1),
            ord('a'): (-1, 0), ord('d'): (1, 0),
        }

        if key in direction_map:
            if len(self.input_queue) < MAX_INPUT_QUEUE:
                self.input_queue.append(direction_map[key])

    def _set_game_over(self) -> None:
        """Set game over state."""
        self.game_over = True
        self.state = State.GAME_OVER
        self.beep()

    def update(self) -> None:
        """Update game state."""
        if self.state != State.PLAYING:
            return

        self.frame_count += 1

        # Time attack mode
        if self.game_mode == 't':
            if self.frame_count % 60 == 0:
                self.time_remaining -= 1
                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    self._set_game_over()
                    return

        # Process input queue
        if self.input_queue:
            new_dir = self.input_queue.popleft()
            if (new_dir[0] + self.direction[0] != 0 or
                new_dir[1] + self.direction[1] != 0):
                self.next_direction = new_dir

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Wall collision
        if (new_head[0] <= 0 or new_head[0] >= self.width - 1 or
            new_head[1] <= 0 or new_head[1] >= self.height - 1):
            if self.game_mode == 'z':  # Zen mode - wrap around
                new_head = (new_head[0] % (self.width - 1),
                           new_head[1] % (self.height - 1))
                if new_head[0] == 0:
                    new_head = (self.width - 2, new_head[1])
                if new_head[1] == 0:
                    new_head = (new_head[0], self.height - 2)
            else:
                self._set_game_over()
                return

        # Survival walls collision
        if self.game_mode == 's' and new_head in self.walls:
            self._set_game_over()
            return

        # Self collision
        if new_head in self.snake_set:
            self._set_game_over()
            return

        self.snake.insert(0, new_head)
        self.snake_set.add(new_head)

        # Power-up collision
        if new_head == self.powerup_pos:
            self.beep()
            if self.powerup_type == PowerupType.SLOW:
                self.speed = min(int(self.speed * SLOW_MULTIPLIER), 500)
                self.powerup_timer = SLOW_POWERUP_DURATION
            elif self.powerup_type == PowerupType.DOUBLE:
                self.score += DOUBLE_SCORE_BONUS
                self.score_popup = (new_head, f"+{DOUBLE_SCORE_BONUS}", SCORE_POPUP_DURATION)
            # GROW does nothing extra (snake already grew)
            self.spawn_powerup()

        # Food collision
        if new_head == self.food:
            self.score += FOOD_SCORE
            self.food_eaten += 1
            self.score_popup = (new_head, f"+{FOOD_SCORE}", SCORE_POPUP_DURATION)
            self.beep()

            # Speed increase every 5 food (not in zen mode)
            if self.game_mode != 'z' and self.food_eaten % SPEED_INCREASE_INTERVAL == 0:
                self.speed = max(int(self.speed * SPEED_MULTIPLIER), 30)

            # Add walls in survival mode
            if self.game_mode == 's':
                self.add_survival_wall()

            self.spawn_food()
        else:
            tail = self.snake.pop()
            self.snake_set.discard(tail)

        # Update power-up timer
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
            if self.powerup_timer == 0:
                self.speed = max(int(self.speed / SLOW_MULTIPLIER), 30)

        # Update food pulse
        self.food_pulse = (self.food_pulse + 1) % FOOD_PULSE_CYCLE

        # Update score popup
        if self.score_popup:
            self.score_popup = (self.score_popup[0], self.score_popup[1], self.score_popup[2] - 1)
            if self.score_popup[2] <= 0:
                self.score_popup = None

    def draw(self) -> None:
        """Draw the game."""
        self.stdscr.erase()

        if self.state == State.MENU:
            self.draw_menu()
        elif self.state == State.PAUSED:
            self.draw_game()
            self.draw_paused()
        elif self.state == State.GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        else:
            self.draw_game()

        self.stdscr.refresh()

    def draw_menu(self) -> None:
        """Draw the menu screen."""
        h, w = self.stdscr.getmaxyx()
        s = self.symbols

        # Title
        title = f"{s['corner_tl']}{s['border_h']*10} SNAKE {s['border_h']*10}{s['corner_tr']}"
        self.stdscr.addstr(h//6, (w - len(title))//2, title, curses.color_pair(3) | curses.A_BOLD)

        # Mode selection
        y = h//3
        self.stdscr.addstr(y, (w - 20)//2, "Select Mode:", curses.A_BOLD | curses.color_pair(3))
        for key, mode in MODE_INFO.items():
            y += 2
            marker = ">> " if self.game_mode == key else "   "
            color = curses.color_pair(3) if self.game_mode == key else curses.A_NORMAL
            self.stdscr.addstr(y, (w - 40)//2, f"{marker}{key}. {mode['name']}: {mode['desc']}", color)

        # Difficulty
        y += 3
        self.stdscr.addstr(y, (w - 20)//2, "Difficulty:", curses.A_BOLD | curses.color_pair(3))
        for key, diff in DIFFICULTY.items():
            y += 2
            marker = ">> " if self.difficulty == key else "   "
            color = curses.color_pair(3) if self.difficulty == key else curses.A_NORMAL
            self.stdscr.addstr(y, (w - 30)//2,
                f"{marker}{key}. {diff['name']} ({diff['speed']}ms)", color)

        # Power-up info
        y += 3
        self.stdscr.addstr(y, (w - 25)//2, "Power-ups:", curses.A_BOLD | curses.color_pair(3))
        for ptype, desc in POWERUP_DESC.items():
            y += 1
            self.stdscr.addstr(y, (w - 40)//2, f"  {desc}", curses.color_pair(5))

        # Options
        y += 2
        sound_str = "ON " if self.sound else "OFF"
        unicode_str = "ON " if self.use_unicode else "OFF"
        cb_str = "ON " if self.color_blind else "OFF"
        self.stdscr.addstr(y, (w - 50)//2,
            f"[M] Sound: {sound_str}  [U] Unicode: {unicode_str}  [B] ColorBlind: {cb_str}",
            curses.color_pair(4))

        # High scores
        y += 3
        key = f"{self.difficulty}_{self.game_mode}"
        self.stdscr.addstr(y, (w - 25)//2, f"High Score: {self.high_score}", curses.color_pair(2) | curses.A_BOLD)

        # Controls
        y += 3
        self.stdscr.addstr(y, (w - 35)//2, "Mode: C T Z S | Diff: 1 2 3")
        self.stdscr.addstr(y + 1, (w - 25)//2, "Enter/Space: Start | Q: Quit")

    def draw_game(self) -> None:
        """Draw the game screen."""
        s = self.symbols

        # Border
        self.stdscr.addstr(0, 0, s['corner_tl'] + s['border_h'] * (self.width - 2) + s['corner_tr'],
                          curses.color_pair(2))
        self.stdscr.addstr(self.height - 1, 0, s['corner_bl'] + s['border_h'] * (self.width - 2) + s['corner_br'],
                          curses.color_pair(2))
        for y in range(1, self.height - 1):
            self.stdscr.addstr(y, 0, s['border_v'], curses.color_pair(2))
            self.stdscr.addstr(y, self.width - 1, s['border_v'], curses.color_pair(2))

        # Survival walls
        for wx, wy in self.walls:
            self.stdscr.addch(wy, wx, '#', curses.color_pair(2))

        # Food with pulse
        fx, fy = self.food
        food_char = s['food'] if self.food_pulse < 10 else s['food_alt']
        self.stdscr.addch(fy, fx, food_char, curses.color_pair(1) | curses.A_BOLD)

        # Power-up
        if self.powerup_pos != (-1, -1):
            px, py = self.powerup_pos
            powerup_chars = {
                PowerupType.SLOW: s['powerup_slow'],
                PowerupType.DOUBLE: s['powerup_double'],
                PowerupType.GROW: s['powerup_grow'],
            }
            char = powerup_chars.get(self.powerup_type, '?')
            self.stdscr.addch(py, px, char, curses.color_pair(5) | curses.A_BOLD)

        # Snake
        for i, (sx, sy) in enumerate(self.snake):
            if i == 0:
                char = s['snake_head']
                color = curses.color_pair(3)
            else:
                char = s['snake_body']
                color = curses.color_pair(4)
            self.stdscr.addch(sy, sx, char, color | curses.A_BOLD)

        # Score popup
        if self.score_popup and self.state == State.PLAYING:
            pos, text, _ = self.score_popup
            self.stdscr.addstr(pos[1], pos[0], text, curses.color_pair(2) | curses.A_BOLD)

        # Status bar
        status = f" Score: {self.score} | High: {self.high_score} "
        if self.game_mode == 't':
            mins = self.time_remaining // 60
            secs = self.time_remaining % 60
            status += f"| Time: {mins}:{secs:02d} "
        status += f"| {max(1000//self.speed, 1)}f/s"
        self.stdscr.addstr(self.height, 0, status, curses.color_pair(4))

        # Power-up indicator
        if self.powerup_timer > 0:
            self.stdscr.addstr(self.height, len(status) + 1, "[SLOW]", curses.color_pair(5))

        # Controls
        controls = "WASD/Arrows: Move | Space: Pause | R: Restart | Q: Menu"
        self.stdscr.addstr(self.height + 1, 0, controls, curses.color_pair(2))

    def draw_paused(self) -> None:
        """Draw the paused overlay."""
        s = self.symbols
        msg = f" {s['border_h']*3} PAUSED {s['border_h']*3} "
        self.stdscr.addstr(self.height // 2, (self.width - len(msg)) // 2, msg, curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(self.height // 2 + 1, (self.width - 20) // 2, "Press Space to Resume", curses.color_pair(2))

    def draw_game_over(self) -> None:
        """Draw the game over screen."""
        self.save_high_score()
        s = self.symbols

        # Overlay
        for y in range(self.height // 2 - 3, self.height // 2 + 5):
            self.stdscr.addstr(y, self.width // 2 - 15, " " * 30, curses.color_pair(1))

        msg1 = f" {s['border_h']*3} GAME OVER {s['border_h']*3} "
        msg2 = f"Final Score: {self.score}"

        y = self.height // 2 - 1
        self.stdscr.addstr(y, (self.width - len(msg1)) // 2, msg1, curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(y + 1, (self.width - len(msg2)) // 2, msg2, curses.color_pair(3))

        # High score
        if self.is_new_high_score:
            msg3 = f"NEW HIGH SCORE: {self.score}!"
            self.stdscr.addstr(y + 2, (self.width - len(msg3)) // 2, msg3, curses.color_pair(1) | curses.A_BOLD | curses.A_BLINK)
        else:
            msg3 = f"High Score: {max(self.score, self.high_score)}"
            self.stdscr.addstr(y + 2, (self.width - len(msg3)) // 2, msg3, curses.color_pair(2) | curses.A_BOLD)

        msg4 = "Press R to Restart | Q for Menu"
        self.stdscr.addstr(y + 4, (self.width - len(msg4)) // 2, msg4, curses.color_pair(4))

    def run(self) -> None:
        """Main game loop."""
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(10)
        self.quit = False
        self.waiting_for_input = False

        while not self.quit:
            self.handle_input()

            if self.state == State.PLAYING:
                curses.napms(self.speed)
                self.update()
                self.waiting_for_input = False
            elif self.state == State.GAME_OVER and self.game_over:
                if not self.waiting_for_input:
                    self.waiting_for_input = True

            self.draw()

            if self.state == State.MENU:
                config = self.load_config()
                self.sound = config.get('sound', True)
                self.use_unicode = config.get('unicode', True)
                self.color_blind = config.get('color_blind', False)
                self._update_symbols()
                self.high_score = self.load_high_score()


def main(stdscr: curses.window) -> None:
    """Main entry point."""
    h, w = stdscr.getmaxyx()
    if w < MIN_TERMINAL_WIDTH or h < MIN_TERMINAL_HEIGHT:
        stdscr.addstr(0, 0, f"Terminal too small! Need at least {MIN_TERMINAL_WIDTH}x{MIN_TERMINAL_HEIGHT}, got {w}x{h}")
        stdscr.getch()
        return

    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)

    # Enable keyboard
    curses.cbreak()
    stdscr.keypad(1)

    # Load config
    config = {'sound': True, 'unicode': True, 'color_blind': False}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
    except (IOError, json.JSONDecodeError):
        pass

    game = SnakeGame(
        stdscr, '2', 'c',
        config.get('sound', True),
        config.get('unicode', True),
        config.get('color_blind', False)
    )
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
        print("Install windows-curses on Windows: pip install windows-curses")
