#!/usr/bin/env python3
"""
Terminal Snake Game - Enhanced v2.1
Features: True color, Unicode, Game modes, Visual effects, Sound
"""

import curses
import random
import time
import os
import json
from collections import deque
from enum import Enum

# Game states
class State(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3

# Game modes
class GameMode(Enum):
    CLASSIC = 0   # Classic snake
    TIME_ATTACK = 1  # Score as much as possible in time limit
    ZEN = 2       # No game over, wrap around
    SURVIVAL = 3  # Walls appear over time

# Difficulty settings
DIFFICULTY = {
    '1': {'name': 'Easy', 'speed': 200},
    '2': {'name': 'Medium', 'speed': 150},
    '3': {'name': 'Hard', 'speed': 100},
}

# Game mode settings
MODE_INFO = {
    'c': {'name': 'Classic', 'desc': 'Traditional snake gameplay'},
    't': {'name': 'Time Attack', 'desc': '2 min to score high'},
    'z': {'name': 'Zen', 'desc': 'Relax - no game over'},
    's': {'name': 'Survival', 'desc': 'Walls appear over time'},
}

# Power-up types
POWERUP_NONE = 0
POWERUP_SLOW = 1
POWERUP_DOUBLE = 2
POWERUP_GROW = 3  # Grow extra length

# Unicode symbols
SYMBOLS = {
    'border_h': '═', 'border_v': '║',
    'corner_tl': '╔', 'corner_tr': '╗',
    'corner_bl': '╚', 'corner_br': '╝',
    'snake_head': '●', 'snake_body': '○',
    'food': '◆', 'food_alt': '★',
    'powerup_slow': '◐', 'powerup_double': '◑',
    'powerup_grow': '✦',
}

# ASCII fallback
ASCII_SYMBOLS = {
    'border_h': '=', 'border_v': '|',
    'corner_tl': '+', 'corner_tr': '+',
    'corner_bl': '+', 'corner_br': '+',
    'snake_head': '@', 'snake_body': 'o',
    'food': '*', 'food_alt': '+',
    'powerup_slow': 'S', 'powerup_double': 'D',
    'powerup_grow': 'G',
}

HIGHSCORE_FILE = os.path.expanduser("~/.snake_highscores")
CONFIG_FILE = os.path.expanduser("~/.snake_config")


class SnakeGame:
    def __init__(self, stdscr, difficulty='2', game_mode='c', sound=True, use_unicode=True):
        self.stdscr = stdscr
        self.width = 40
        self.height = 18
        self.difficulty = difficulty
        self.game_mode = game_mode
        self.sound = sound
        self.use_unicode = use_unicode
        self.base_speed = DIFFICULTY[difficulty]['speed']
        self.symbols = SYMBOLS if use_unicode else ASCII_SYMBOLS

        # Time attack settings
        self.time_limit = 120  # 2 minutes
        self.time_remaining = self.time_limit

        # Survival mode
        self.wall_interval = 20  # Add wall every 20 food
        self.walls = set()

        # Visual effects
        self.food_pulse = 0
        self.score_popup = None
        self.death_animation = None

        self.init_game()

    def init_game(self):
        self.state = State.PLAYING
        self.game_over = False
        self.score = 0
        self.speed = self.base_speed
        self.food_eaten = 0
        self.high_score = self.load_high_score()
        self.powerup_timer = 0
        self.snake_set = set()
        self.score_popup = None
        self.death_animation = None

        # Time attack
        if self.game_mode == 't':
            self.time_remaining = self.time_limit

        # Survival walls
        if self.game_mode == 's':
            self.walls = set()

        mid_x, mid_y = self.width // 2, self.height // 2
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.snake_set = set(self.snake)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.input_queue = deque()
        self.frame_count = 0
        self.spawn_food()
        self.spawn_powerup()

    def beep(self):
        if self.sound:
            try:
                curses.beep()
            except:
                pass

    def spawn_food(self):
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            pos = (x, y)
            if (pos not in self.snake_set and
                pos != getattr(self, 'powerup_pos', (-1, -1)) and
                pos not in self.walls):
                self.food = pos
                self.food_pulse = 0
                break

    def spawn_powerup(self):
        if random.random() < 0.08:  # 8% chance
            while True:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
                pos = (x, y)
                if (pos not in self.snake_set and
                    pos != self.food and
                    pos not in self.walls):
                    self.powerup_pos = pos
                    self.powerup_type = random.choice([POWERUP_SLOW, POWERUP_DOUBLE, POWERUP_GROW])
                    break
        else:
            self.powerup_pos = (-1, -1)
            self.powerup_type = POWERUP_NONE

    def add_survival_wall(self):
        """Add random walls in survival mode"""
        num_walls = self.food_eaten // self.wall_interval
        target_walls = min(num_walls, 10)  # Max 10 walls

        while len(self.walls) < target_walls:
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            pos = (x, y)
            if pos not in self.snake and pos != self.food:
                self.walls.add(pos)

    def load_high_score(self):
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    key = f"{self.difficulty}_{self.game_mode}"
                    return data.get(key, 0)
        except:
            pass
        return 0

    def save_high_score(self):
        try:
            data = {}
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
            key = f"{self.difficulty}_{self.game_mode}"
            if self.score > data.get(key, 0):
                data[key] = self.score
                with open(HIGHSCORE_FILE, 'w') as f:
                    json.dump(data, f)
        except:
            pass

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'sound': True, 'unicode': True}

    def save_config(self, config):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def handle_input(self):
        try:
            key = self.stdscr.getch()
        except:
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
                self.save_config({'sound': self.sound, 'unicode': self.use_unicode})
            elif key == ord('u'):  # Toggle unicode
                self.use_unicode = not self.use_unicode
                self.symbols = SYMBOLS if self.use_unicode else ASCII_SYMBOLS
                self.save_config({'sound': self.sound, 'unicode': self.use_unicode})
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
            if len(self.input_queue) < 2:
                self.input_queue.append(direction_map[key])

    def update(self):
        if self.state != State.PLAYING:
            return

        self.frame_count += 1

        # Time attack mode - check time
        if self.game_mode == 't':
            if self.frame_count % 60 == 0:  # Approximate seconds
                self.time_remaining -= 1
                if self.time_remaining <= 0:
                    self.game_over = True
                    self.state = State.GAME_OVER
                    self.beep()
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

        # Wall collision (different behavior per mode)
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
                self.game_over = True
                self.state = State.GAME_OVER
                self.beep()
                return

        # Survival walls collision
        if self.game_mode == 's' and new_head in self.walls:
            self.game_over = True
            self.state = State.GAME_OVER
            self.beep()
            return

        # Self collision
        if new_head in self.snake_set:
            self.game_over = True
            self.state = State.GAME_OVER
            self.beep()
            return

        self.snake.insert(0, new_head)
        self.snake_set.add(new_head)

        # Power-up collision
        if new_head == self.powerup_pos:
            self.beep()
            if self.powerup_type == POWERUP_SLOW:
                self.speed = int(self.speed * 1.3)
                self.powerup_timer = 50
            elif self.powerup_type == POWERUP_DOUBLE:
                self.score += 20
                self.score_popup = (new_head, "+20", 30)
            elif self.powerup_type == POWERUP_GROW:
                # Grow extra length without moving tail
                pass
            self.spawn_powerup()

        # Food collision
        if new_head == self.food:
            self.score += 10
            self.food_eaten += 1
            self.score_popup = (new_head, "+10", 30)
            self.beep()

            # Speed increase every 5 food (not in zen mode)
            if self.game_mode != 'z' and self.food_eaten % 5 == 0:
                self.speed = int(self.speed * 0.85)

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
                self.speed = int(self.speed / 1.3)

        # Update food pulse
        self.food_pulse = (self.food_pulse + 1) % 20

        # Update score popup
        if self.score_popup:
            self.score_popup = (self.score_popup[0], self.score_popup[1], self.score_popup[2] - 1)
            if self.score_popup[2] <= 0:
                self.score_popup = None

    def draw(self):
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

    def draw_menu(self):
        h, w = self.stdscr.getmaxyx()
        s = self.symbols

        # Title with gradient effect
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

        # Options
        y += 3
        sound_str = "ON " if self.sound else "OFF"
        unicode_str = "ON " if self.use_unicode else "OFF"
        self.stdscr.addstr(y, (w - 40)//2, f"[M] Sound: {sound_str}  [U] Unicode: {unicode_str}", curses.color_pair(4))

        # High scores for current mode
        y += 3
        key = f"{self.difficulty}_{self.game_mode}"
        self.stdscr.addstr(y, (w - 25)//2, f"High Score: {self.high_score}", curses.color_pair(2) | curses.A_BOLD)

        # Controls
        y += 3
        self.stdscr.addstr(y, (w - 35)//2, "Mode: C T Z S | Diff: 1 2 3")
        self.stdscr.addstr(y + 1, (w - 25)//2, "Enter/Space: Start | Q: Quit")

    def draw_game(self):
        s = self.symbols

        # Border with Unicode or ASCII
        # Top
        self.stdscr.addstr(0, 0, s['corner_tl'] + s['border_h'] * (self.width - 2) + s['corner_tr'],
                          curses.color_pair(2))
        # Bottom
        self.stdscr.addstr(self.height - 1, 0, s['corner_bl'] + s['border_h'] * (self.width - 2) + s['corner_br'],
                          curses.color_pair(2))
        # Sides
        for y in range(1, self.height - 1):
            self.stdscr.addstr(y, 0, s['border_v'], curses.color_pair(2))
            self.stdscr.addstr(y, self.width - 1, s['border_v'], curses.color_pair(2))

        # Survival walls
        for wx, wy in self.walls:
            self.stdscr.addch(wy, wx, '#', curses.color_pair(2))

        # Food with pulse effect
        fx, fy = self.food
        if self.food_pulse < 10:
            food_char = s['food']
        else:
            food_char = s['food_alt']
        self.stdscr.addch(fy, fx, food_char, curses.color_pair(1) | curses.A_BOLD)

        # Power-up
        if self.powerup_pos != (-1, -1):
            px, py = self.powerup_pos
            if self.powerup_type == POWERUP_SLOW:
                char = s['powerup_slow']
            elif self.powerup_type == POWERUP_DOUBLE:
                char = s['powerup_double']
            else:
                char = s['powerup_grow']
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
        if self.score_popup:
            pos, text, _ = self.score_popup
            self.stdscr.addstr(pos[1], pos[0], text, curses.color_pair(2) | curses.A_BOLD)

        # Status bar
        status = f" Score: {self.score} | High: {self.high_score} "
        if self.game_mode == 't':
            mins = self.time_remaining // 60
            secs = self.time_remaining % 60
            status += f"| Time: {mins}:{secs:02d} "
        status += f"| {1000//self.speed}fps"
        self.stdscr.addstr(self.height, 0, status, curses.color_pair(4))

        # Power-up indicator
        if self.powerup_timer > 0:
            self.stdscr.addstr(self.height, len(status) + 1, "[SLOW]", curses.color_pair(5))

        # Controls
        controls = "WASD/Arrows: Move | Space: Pause | R: Restart | Q: Menu"
        self.stdscr.addstr(self.height + 1, 0, controls, curses.color_pair(2))

    def draw_paused(self):
        s = self.symbols
        msg = f" {s['border_h']*3} PAUSED {s['border_h']*3} "
        self.stdscr.addstr(self.height // 2, (self.width - len(msg)) // 2,
                         msg, curses.color_pair(3) | curses.A_BOLD)
        self.stdscr.addstr(self.height // 2 + 1, (self.width - 20) // 2,
                         "Press Space to Resume", curses.color_pair(2))

    def draw_game_over(self):
        self.save_high_score()
        s = self.symbols

        # Overlay
        for y in range(self.height // 2 - 3, self.height // 2 + 5):
            self.stdscr.addstr(y, self.width // 2 - 15, " " * 30, curses.color_pair(1))

        msg1 = f" {s['border_h']*3} GAME OVER {s['border_h']*3} "
        msg2 = f"Final Score: {self.score}"
        msg3 = f"High Score: {max(self.score, self.high_score)}"

        y = self.height // 2 - 1
        self.stdscr.addstr(y, (self.width - len(msg1)) // 2, msg1, curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(y + 1, (self.width - len(msg2)) // 2, msg2, curses.color_pair(3))
        self.stdscr.addstr(y + 2, (self.width - len(msg3)) // 2, msg3, curses.color_pair(2) | curses.A_BOLD)

        msg4 = "Press R to Restart | Q for Menu"
        self.stdscr.addstr(y + 4, (self.width - len(msg4)) // 2, msg4, curses.color_pair(4))

    def run(self):
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(10)
        self.quit = False

        while not self.quit:
            self.handle_input()

            if self.state == State.PLAYING:
                curses.napms(self.speed)
                self.update()
            elif self.state == State.GAME_OVER and self.game_over:
                self.quit = True

            self.draw()

            if self.state == State.MENU:
                config = self.load_config()
                self.sound = config.get('sound', True)
                self.use_unicode = config.get('unicode', True)
                self.symbols = SYMBOLS if self.use_unicode else ASCII_SYMBOLS
                self.high_score = self.load_high_score()


def main(stdscr):
    h, w = stdscr.getmaxyx()
    if w < 42 or h < 22:
        stdscr.addstr(0, 0, f"Terminal too small! Need at least 42x22, got {w}x{h}")
        stdscr.getch()
        return

    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    # Basic color pairs
    curses.init_pair(1, curses.COLOR_RED, -1)     # Food
    curses.init_pair(2, curses.COLOR_WHITE, -1)    # Border
    curses.init_pair(3, curses.COLOR_GREEN, -1)    # Snake Head / Title
    curses.init_pair(4, curses.COLOR_CYAN, -1)     # Snake Body / Status
    curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Power-up

    # Enable keyboard
    curses.cbreak()
    stdscr.keypad(1)

    # Load config
    config = {'sound': True, 'unicode': True}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
    except:
        pass

    game = SnakeGame(stdscr, '2', 'c', config.get('sound', True), config.get('unicode', True))
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
        print("Install windows-curses on Windows: pip install windows-curses")
