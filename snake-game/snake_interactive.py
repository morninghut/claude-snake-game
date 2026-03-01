#!/usr/bin/env python3
"""
Terminal Snake Game - Interactive version with curses
"""

import curses
import random
import time


class SnakeGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.width = 40
        self.height = 18
        self.init_game()

    def init_game(self):
        self.paused = False
        self.game_over = False
        self.score = 0
        self.speed = 150  # ms
        self.food_eaten = 0

        mid_x, mid_y = self.width // 2, self.height // 2
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.spawn_food()

    def spawn_food(self):
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if (x, y) not in self.snake:
                self.food = (x, y)
                break

    def handle_input(self):
        try:
            key = self.stdscr.getch()
        except:
            return

        if key in (ord('q'), 27):
            self.game_over = True
            return
        if key == ord('r'):
            self.init_game()
            return
        if key == ord(' '):
            self.paused = not self.paused
            return

        if self.paused:
            return

        direction_map = {
            curses.KEY_UP: (0, -1), curses.KEY_DOWN: (0, 1),
            curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0),
            ord('w'): (0, -1), ord('s'): (0, 1),
            ord('a'): (-1, 0), ord('d'): (1, 0),
        }

        if key in direction_map:
            new_dir = direction_map[key]
            if (new_dir[0] + self.direction[0] != 0 or
                new_dir[1] + self.direction[1] != 0):
                self.next_direction = new_dir

    def update(self):
        if self.paused or self.game_over:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if (new_head[0] <= 0 or new_head[0] >= self.width - 1 or
            new_head[1] <= 0 or new_head[1] >= self.height - 1 or
            new_head in self.snake):
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 10
            self.food_eaten += 1
            if self.food_eaten % 5 == 0:
                self.speed = int(self.speed * 0.85)
            self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        self.stdscr.clear()

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

        # Snake
        for i, (sx, sy) in enumerate(self.snake):
            char = '@' if i == 0 else 'o'
            color = curses.color_pair(3) if i == 0 else curses.color_pair(4)
            self.stdscr.addch(sy, sx, char, color | curses.A_BOLD)

        # Status
        self.stdscr.addstr(self.height, 0, f"Score: {self.score} | Speed: {1000//self.speed}fps")
        self.stdscr.addstr(self.height + 1, 0, "WASD/Arrows: Move | Space: Pause | Q: Quit | R: Restart")

        if self.game_over:
            msg = f"GAME OVER! Score: {self.score} - Press R"
            self.stdscr.addstr(self.height // 2, (self.width - len(msg)) // 2,
                             msg, curses.color_pair(1) | curses.A_BOLD)
        elif self.paused:
            msg = "PAUSED - Press Space"
            self.stdscr.addstr(self.height // 2, (self.width - len(msg)) // 2,
                             msg, curses.color_pair(3) | curses.A_BOLD)

        self.stdscr.refresh()

    def run(self):
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.timeout(100)

        last_time = time.time()

        while True:
            self.handle_input()
            if time.time() - last_time >= self.speed / 1000:
                self.update()
                last_time = time.time()
            self.draw()

            if self.game_over:
                self.stdscr.nodelay(False)
                while True:
                    key = self.stdscr.getch()
                    if key == ord('r'):
                        self.init_game()
                        self.stdscr.nodelay(True)
                        break
                    elif key in (ord('q'), 27):
                        return


def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    stdscr.clear()
    stdscr.addstr(5, 12, "=== SNAKE GAME ===", curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(7, 8, "WASD/Arrows: Move | Space: Pause")
    stdscr.addstr(8, 12, "Q: Quit | R: Restart")
    stdscr.addstr(10, 10, "Press any key to start...")
    stdscr.refresh()
    stdscr.getch()

    game = SnakeGame(stdscr)
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
        print("Install windows-curses on Windows: pip install windows-curses")
