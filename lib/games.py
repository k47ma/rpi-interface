#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
import random
import time
from lib.widgets import Widget, List


class Game(Widget):
    def __init__(self, parent, exit_event):
        super(Game, self).__init__(parent, 0, 0)

        self.exit_event = exit_event

        self._color = (0, 0, 0)

    def _on_setup(self):
        pass

    def _on_update(self):
        if not self.is_active:
            return

    def _on_draw(self, screen):
        if not self.is_active:
            return

        screen.fill(self._color)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._toggle_color()

    def _on_exit(self):
        self.exit_event()

    def _toggle_color(self):
        if self._color == (0, 0, 0):
            self._color = (0, 0, 255)
        else:
            self._color = (0, 0, 0)


class GameSnake(Game):
    def __init__(self, parent, exit_event, total_rows=16, total_cols=20, cell_size=20, cell_padding=1):
        super(GameSnake, self).__init__(parent, exit_event)

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.cell_size = cell_size
        self.cell_padding = cell_padding

        self._score = 0
        self._score_width = 80
        self._board_x = self._score_width + (self._screen_width - self.total_cols * self.cell_size) // 2
        self._board_y = (self._screen_height - self.total_rows * self.cell_size) // 2
        self._board = []
        self._started = False
        self._start_time = time.time()
        self._cell_color = self._get_color("lightgray")
        self._snake_color = self._get_color("green")
        self._apple_color = self._get_color("red")

        self.scoreboard_font = pygame.font.Font("fonts/FreeSans.ttf", 15)

    def _on_setup(self):
        self._init_board()

    def _on_enter(self):
        self._init_board()

    def _on_update(self):
        if not self.is_active or not self._started:
            return

    def _on_draw(self, screen):
        if not self.is_active:
            return

        screen.fill((0, 0, 0))
        self._draw_scoreboard(screen)
        self._draw_board(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self._started:
                    self._start_game()

    def _start_game(self):
        self._started = True
        self._start_time = time.time()

    def _init_board(self):
        self._board = [[0 for _ in range(self.total_cols)] for _ in range(self.total_rows)]
        self._board[self.total_rows // 2][self.total_cols // 2] = 1
        self._board[self.total_rows // 2][self.total_cols // 2 + 1] = 1
        self._score = 0
        self._started = False
        self._add_apple()

    def _add_apple(self):
        free_spots = []
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                if self._board[row_ind][col_ind] == 0:
                    free_spots.append((row_ind, col_ind))
        row, col = random.choice(free_spots)
        self._board[row][col] = 2

    def _draw_scoreboard(self, screen):
        score_text = self.scoreboard_font.render("Score: {}".format(self._score), True, self._get_color("white"))
        screen.blit(score_text, (10, 10))

        curr_time = time.time()
        min = 0
        sec = 0
        if self._started:
            min = int(curr_time - self._start_time) // 60
            sec = int(curr_time - self._start_time) % 60
        time_text = self.scoreboard_font.render("Time: {:02}:{:02}".format(min, sec), True, self._get_color("white"))
        screen.blit(time_text, (10, 10 + score_text.get_height()))

    def _draw_board(self, screen):
        rect_size = self.cell_size - 2 * self.cell_padding
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                if self._board[row_ind][col_ind] == 0:
                    color = self._cell_color
                elif self._board[row_ind][col_ind] == 1:
                    color = self._snake_color
                else:
                    color = self._apple_color
                x = self._board_x + col_ind * self.cell_size + self.cell_padding
                y = self._board_y + row_ind * self.cell_size + self.cell_padding
                pygame.draw.rect(screen, color, (x, y, rect_size, rect_size))
