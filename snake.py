#!/usr/bin/env python3
"""
Terminal Snake Game - Auto-pilot demo version
Works without interactive terminal
"""

import random
import time
import os


class SnakeGame:
    def __init__(self):
        self.width = 30
        self.height = 15
        self.init_game()

    def init_game(self):
        self.game_over = False
        self.score = 0
        self.speed = 0.2
        self.food_eaten = 0
        self.paused = False

        mid_x, mid_y = self.width // 2, self.height // 2
        self.snake = [[mid_x, mid_y], [mid_x - 1, mid_y], [mid_x - 2, mid_y]]
        self.direction = [1, 0]
        self.next_direction = [1, 0]

        self.spawn_food()

    def spawn_food(self):
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if [x, y] not in self.snake:
                self.food = [x, y]
                break

    def update(self):
        if self.paused or self.game_over:
            return

        self.direction = self.next_direction[:]
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = [head_x + dx, head_y + dy]

        if (new_head[0] <= 0 or new_head[0] >= self.width - 1 or
            new_head[1] <= 0 or new_head[1] >= self.height - 1):
            self.game_over = True
            return

        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 10
            self.food_eaten += 1
            if self.food_eaten % 5 == 0:
                self.speed *= 0.85
            self.spawn_food()
        else:
            self.snake.pop()

        # Auto-pilot: change direction randomly to food
        head = self.snake[0]
        fx, fy = self.food

        # Simple AI: try to move toward food
        if head[0] < fx and self.direction != [-1, 0]:
            self.next_direction = [1, 0]
        elif head[0] > fx and self.direction != [1, 0]:
            self.next_direction = [-1, 0]
        elif head[1] < fy and self.direction != [0, -1]:
            self.next_direction = [0, 1]
        elif head[1] > fy and self.direction != [0, 1]:
            self.next_direction = [0, -1]

    def draw(self):
        os.system('clear')

        print('\x1b[32m' + '=' * (self.width + 2) + '\x1b[0m')

        for y in range(1, self.height - 1):
            line = '\x1b[37m|\x1b[0m'
            for x in range(1, self.width - 1):
                if [x, y] == self.food:
                    line += '\x1b[31m*\x1b[0m'
                elif [x, y] == self.snake[0]:
                    line += '\x1b[32m@\x1b[0m'
                elif [x, y] in self.snake:
                    line += '\x1b[32mo\x1b[0m'
                else:
                    line += ' '
            line += '\x1b[37m|\x1b[0m'
            print(line)

        print('\x1b[32m' + '=' * (self.width + 2) + '\x1b[0m')
        print(f'\x1b[33mScore: {self.score}\x1b[0m | Speed: {1/self.speed:.1f}/s')

        if self.game_over:
            print(f'\x1b[31mGAME OVER! Final Score: {self.score}\x1b[0m')

    def run(self):
        print("""
\x1b[32m=== SNAKE GAME (Auto-Pilot Demo) ===

This version runs automatically with basic AI.
Score increases as the snake eats food.
\x1b[0m
Press Enter to start...
""")
        input()

        while not self.game_over:
            self.update()
            self.draw()
            time.sleep(self.speed)

        print("\nPress Enter to exit...")
        input()


if __name__ == "__main__":
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        print('\nInterrupted!')
