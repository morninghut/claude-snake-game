#!/usr/bin/env python3
"""
Terminal Snake Game - Enhanced version with curses
Features: Difficulty levels, high scores, power-ups, sound effects
"""

import curses
import random
import time
import os
import json
from collections import deque

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAME_OVER = 3

# Difficulty settings
DIFFICULTY = {
    '1': {'name': 'Easy', 'speed': 200, 'walls': False},
    '2': {'name': 'Medium', 'speed': 150, 'walls': False},
    '3': {'name': 'Hard', 'speed': 100, 'walls': False},
}

# Power-up types
POWERUP_NONE = 0
POWERUP_SLOW = 1
POWERUP_DOUBLE = 2

HIGHSCORE_FILE = os.path.expanduser("~/.snake_highscores")


class SnakeGame:
    def __init__(self, stdscr, difficulty='2'):
        self.stdscr = stdscr
        self.width = 40
        self.height = 18
        self.difficulty = difficulty
        self.base_speed = DIFFICULTY[difficulty]['speed']
        self.init_game()

    def init_game(self):
        self.state = STATE_PLAYING
        self.game_over = False
        self.score = 0
        self.speed = self.base_speed
        self.food_eaten = 0
        self.high_score = self.load_high_score()
        self.powerup_timer = 0
        self.snake_set = set()  # For O(1) collision detection

        mid_x, mid_y = self.width // 2, self.height // 2
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.snake_set = set(self.snake)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.input_queue = deque()  # Input buffer using deque for O(1)
        self.spawn_food()
        self.spawn_powerup()

    def spawn_food(self):
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            pos = (x, y)
            if pos not in self.snake_set and pos != getattr(self, 'powerup_pos', (-1, -1)):
                self.food = pos
                break

    def spawn_powerup(self):
        if random.random() < 0.1:  # 10% chance
            while True:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
                pos = (x, y)
                if pos not in self.snake_set and pos != self.food:
                    self.powerup_pos = pos
                    self.powerup_type = random.choice([POWERUP_SLOW, POWERUP_DOUBLE])
                    break
        else:
            self.powerup_pos = (-1, -1)
            self.powerup_type = POWERUP_NONE

    def load_high_score(self):
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get(self.difficulty, 0)
        except:
            pass
        return 0

    def save_high_score(self):
        try:
            data = {}
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
            if self.score > data.get(self.difficulty, 0):
                data[self.difficulty] = self.score
                with open(HIGHSCORE_FILE, 'w') as f:
                    json.dump(data, f)
        except:
            pass

    def handle_input(self):
        try:
            key = self.stdscr.getch()
        except:
            return

        # Menu controls
        if self.state == STATE_MENU:
            if key in [ord('1'), ord('2'), ord('3')]:
                self.difficulty = chr(key)
                self.base_speed = DIFFICULTY[self.difficulty]['speed']
            elif key in [ord('\n'), ord(' ')]:
                self.state = STATE_PLAYING
                self.init_game()
            elif key in (ord('q'), 27):
                self.state = STATE_GAME_OVER
                self.game_over = True
                self.save_high_score()
                self.quit = True
                return

        # Game over controls
        if self.state == STATE_GAME_OVER:
            if key == ord('r'):
                self.init_game()
                self.state = STATE_PLAYING
            elif key in (ord('q'), 27):
                self.save_high_score()
                self.state = STATE_MENU
            return

        # Quit during game
        if key in (ord('q'), 27):
            self.save_high_score()
            self.state = STATE_MENU
            return

        # Restart
        if key == ord('r'):
            self.init_game()
            return

        # Pause
        if key == ord(' '):
            self.state = STATE_PAUSED if self.state == STATE_PLAYING else STATE_PLAYING
            curses.beep()
            return

        if self.state != STATE_PLAYING:
            return

        # Direction controls - add to queue
        direction_map = {
            curses.KEY_UP: (0, -1), curses.KEY_DOWN: (0, 1),
            curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0),
            ord('w'): (0, -1), ord('s'): (0, 1),
            ord('a'): (-1, 0), ord('d'): (1, 0),
        }

        if key in direction_map:
            # Add to input queue (max 2 buffered inputs)
            if len(self.input_queue) < 2:
                self.input_queue.append(direction_map[key])

    def update(self):
        if self.state != STATE_PLAYING:
            return

        # Process input queue (deque.popleft is O(1))
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
            self.game_over = True
            self.state = STATE_GAME_OVER
            curses.beep()
            return

        # Self collision (use set for O(1) lookup)
        if new_head in self.snake_set:
            self.game_over = True
            self.state = STATE_GAME_OVER
            curses.beep()
            return

        self.snake.insert(0, new_head)
        self.snake_set.add(new_head)

        # Power-up collision
        if new_head == self.powerup_pos:
            curses.beep()
            if self.powerup_type == POWERUP_SLOW:
                self.speed = int(self.speed * 1.3)
                self.powerup_timer = 50
            elif self.powerup_type == POWERUP_DOUBLE:
                self.score += 20
            self.spawn_powerup()

        # Food collision
        if new_head == self.food:
            self.score += 10
            self.food_eaten += 1
            curses.beep()

            # Speed increase every 5 food
            if self.food_eaten % 5 == 0:
                self.speed = int(self.speed * 0.85)

            self.spawn_food()
        else:
            tail = self.snake.pop()
            self.snake_set.discard(tail)

        # Update power-up timer every frame
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
            if self.powerup_timer == 0:
                self.speed = int(self.speed / 1.3)

    def draw(self):
        self.stdscr.clear()

        # Draw based on state
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PAUSED:
            self.draw_game()
            self.draw_paused()
        elif self.state == STATE_GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        else:
            self.draw_game()

        self.stdscr.refresh()

    def draw_menu(self):
        h, w = self.stdscr.getmaxyx()

        # Title
        title = "=== SNAKE GAME ==="
        self.stdscr.addstr(h//4, (w - len(title))//2, title, curses.color_pair(3) | curses.A_BOLD)

        # Difficulty selection
        y = h//2 - 4
        self.stdscr.addstr(y, (w - 20)//2, "Select Difficulty:", curses.A_BOLD)

        for i, (key, diff) in enumerate(DIFFICULTY.items()):
            y += 2
            marker = ">> " if self.difficulty == key else "   "
            self.stdscr.addstr(y, (w - 30)//2,
                f"{marker}{key}. {diff['name']} (Speed: {diff['speed']}ms)",
                curses.color_pair(3) if self.difficulty == key else curses.A_NORMAL)

        # High scores
        y += 3
        self.stdscr.addstr(y, (w - 25)//2, f"High Score: {self.high_score}", curses.color_pair(2) | curses.A_BOLD)

        # Controls
        y += 3
        self.stdscr.addstr(y, (w - 30)//2, "WASD/Arrows: Select | Enter: Start")
        self.stdscr.addstr(y + 1, (w - 20)//2, "Q: Quit")

        # Credits
        y += 3
        self.stdscr.addstr(y, (w - 20)//2, "Enhanced Version v2.0", curses.color_pair(4))

    def draw_game(self):
        # Border
        for x in range(self.width):
            self.stdscr.addch(0, x, '#', curses.color_pair(2))
            self.stdscr.addch(self.height - 1, x, '#', curses.color_pair(2))
        for y in range(self.height):
            self.stdscr.addch(y, 0, '#', curses.color_pair(2))
            self.stdscr.addch(y, self.width - 1, '#', curses.color_pair(2))

        # Food
        fx, fy = self.food
        self.stdscr.addch(fy, fx, '*', curses.color_pair(1) | curses.A_BOLD)

        # Power-up
        if self.powerup_pos != (-1, -1):
            px, py = self.powerup_pos
            char = 'S' if self.powerup_type == POWERUP_SLOW else 'D'
            self.stdscr.addch(py, px, char, curses.color_pair(5) | curses.A_BOLD)

        # Snake
        for i, (sx, sy) in enumerate(self.snake):
            char = '@' if i == 0 else 'o'
            color = curses.color_pair(3) if i == 0 else curses.color_pair(4)
            self.stdscr.addch(sy, sx, char, color | curses.A_BOLD)

        # Status bar
        status = f"Score: {self.score} | High: {self.high_score} | Speed: {1000//self.speed}"
        self.stdscr.addstr(self.height, 0, status)

        # Power-up indicator
        if self.powerup_timer > 0:
            self.stdscr.addstr(self.height, len(status) + 2, "[SLOW]", curses.color_pair(5))

        # Controls
        controls = "WASD/Arrows: Move | Space: Pause | R: Restart | Q: Menu"
        self.stdscr.addstr(self.height + 1, 0, controls)

    def draw_paused(self):
        msg = "PAUSED"
        self.stdscr.addstr(self.height // 2, (self.width - len(msg)) // 2,
                         msg, curses.color_pair(3) | curses.A_BOLD | curses.A_BLINK)
        self.stdscr.addstr(self.height // 2 + 1, (self.width - 20) // 2,
                         "Press Space to Resume", curses.color_pair(2))

    def draw_game_over(self):
        self.save_high_score()

        msg1 = "GAME OVER!"
        msg2 = f"Final Score: {self.score}"
        msg3 = f"High Score: {max(self.score, self.high_score)}"

        y = self.height // 2 - 2
        self.stdscr.addstr(y, (self.width - len(msg1)) // 2,
                         msg1, curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(y + 1, (self.width - len(msg2)) // 2, msg2, curses.color_pair(3))
        self.stdscr.addstr(y + 2, (self.width - len(msg3)) // 2, msg3, curses.color_pair(2) | curses.A_BOLD)

        msg4 = "Press R to Restart | Q for Menu"
        self.stdscr.addstr(y + 4, (self.width - len(msg4)) // 2, msg4, curses.color_pair(4))

    def run(self):
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(10)  # More responsive input
        self.quit = False

        while not self.quit:
            self.handle_input()

            if self.state == STATE_PLAYING:
                # Use napms for more precise timing
                curses.napms(self.speed)
                self.update()
            elif self.state == STATE_GAME_OVER and self.game_over:
                self.quit = True

            self.draw()

            if self.state == STATE_MENU:
                self.high_score = self.load_high_score()

        # Final draw to show game over
        self.draw()


def main(stdscr):
    # Check terminal size
    h, w = stdscr.getmaxyx()
    if w < 42 or h < 22:
        stdscr.addstr(0, 0, f"Terminal too small! Need at least 42x22, got {w}x{h}")
        stdscr.getch()
        return

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)     # Food / Game Over
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Border / High Score
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake Head / Title
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Snake Body
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Power-up

    # Enable keyboard
    curses.cbreak()
    stdscr.keypad(1)

    game = SnakeGame(stdscr, '2')
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
        print("Install windows-curses on Windows: pip install windows-curses")
