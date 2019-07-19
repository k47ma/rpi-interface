#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
import random
import time
import copy
from abc import abstractmethod
from lib.widgets import Widget, List
from lib.util import *


class Game(Widget):
    def __init__(self, parent, exit_event):
        super(Game, self).__init__(parent, 0, 0)

        self.exit_event = exit_event

        self.scoreboard_font = pygame.font.Font("fonts/FreeSans.ttf", 15)

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

    def _on_enter(self):
        self.parent.app.game_frame_rate(True)
        self._game_on_enter()

    def _on_exit(self):
        self._game_on_exit()
        self.exit_event()
        self.parent.app.game_frame_rate(False)

    def _toggle_color(self):
        if self._color == (0, 0, 0):
            self._color = (0, 0, 255)
        else:
            self._color = (0, 0, 0)

    @abstractmethod
    def _game_on_enter(self):
        pass

    @abstractmethod
    def _game_on_exit(self):
        pass


class GameSnake(Game):
    def __init__(self, parent, exit_event, total_rows=16, total_cols=20, cell_size=20, cell_padding=1):
        super(GameSnake, self).__init__(parent, exit_event)

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.cell_size = cell_size
        self.cell_padding = cell_padding

        self._score = 0
        self._score_width = 50
        self._score_padding = 10
        self._board_x = self._score_width + (self._screen_width - self.total_cols * self.cell_size) // 2
        self._board_y = (self._screen_height - self.total_rows * self.cell_size) // 2
        self._snake = []
        self._snake_direction = "right"
        self._snake_speed = 5
        self._snake_lastmove = time.time()
        self._snake_extend = False
        self._apple = (0, 0)
        self._started = False
        self._win = False
        self._auto_play = False
        self._start_time = time.time()
        self._progress_time = self._start_time
        self._cell_color = self._get_color("lightgray")
        self._snake_color = self._get_color("green")
        self._snake_head_color = self._get_color("orange")
        self._apple_color = self._get_color("red")

    def _game_on_enter(self):
        self._init_game()

    def _game_on_exit(self):
        pass

    def _on_update(self):
        if not self.is_active or not self._started:
            return

        current_time = time.time()
        self._progress_time = current_time
        if current_time - self._snake_lastmove >= 1 / self._snake_speed:
            if self._auto_play:
                self._update_optimal_direction()
            self._snake_move()
            self._snake_lastmove = current_time

    def _on_draw(self, screen):
        if not self.is_active:
            return

        screen.fill(self._get_color("black"))
        self._draw_scoreboard(screen)
        self._draw_board(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self._started:
                    if not self._score == 0:
                        self._init_game()
                    self._auto_play = True
                    self._start_game()
            elif event.key == pygame.K_r:
                self._init_game()

            if not self._started:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    if not self._score == 0:
                        self._init_game()
                    self._start_game()

            if self._started and not self._auto_play:
                if not self._command_waiting:
                    if self._snake_direction in ["up", "down"]:
                        if event.key == pygame.K_LEFT:
                            self._snake_direction = "left"
                            self._command_waiting = True
                        elif event.key == pygame.K_RIGHT:
                            self._snake_direction = "right"
                            self._command_waiting = True
                    else:
                        if event.key == pygame.K_UP:
                            self._snake_direction = "up"
                            self._command_waiting = True
                        elif event.key == pygame.K_DOWN:
                            self._snake_direction = "down"
                            self._command_waiting = True

    def _start_game(self):
        self._started = True
        self._start_time = time.time()
        self._progress_time = self._start_time

    def _end_game(self):
        self._started = False
        self._command_waiting = False

    def _init_game(self):
        self._snake = []
        self._snake.append((self.total_rows // 2, self.total_cols // 2 + 1))
        self._snake.append((self.total_rows // 2, self.total_cols // 2))
        self._snake_direction = "right"
        self._score = 0
        self._started = False
        self._command_waiting = False
        self._snake_extend = False
        self._auto_play = False
        self._win = False
        self._snake_lastmove = self._start_time
        self._progress_time = self._start_time
        self._add_apple()

    def _add_apple(self):
        free_spots = []
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                if (row_ind, col_ind) not in self._snake:
                    free_spots.append((row_ind, col_ind))
        row, col = random.choice(free_spots)
        self._apple = (row, col)

    def _draw_scoreboard(self, screen):
        x, y = 10, 10
        score_text = self.scoreboard_font.render("Score: {}".format(self._score), True, self._get_color("white"))
        screen.blit(score_text, (x, y))
        y += score_text.get_height() + self._score_padding

        min = int(self._progress_time - self._start_time) // 60
        sec = int(self._progress_time - self._start_time) % 60
        time_text = self.scoreboard_font.render("Time: {:02}:{:02}".format(min, sec), True, self._get_color("white"))
        screen.blit(time_text, (x, y))
        y += time_text.get_height() + self._score_padding

        if not self._started and self._progress_time > self._start_time:
            if self._win:
                result_text = "You Win!"
            else:
                result_text = "Oops!"
            rendered_result = self.scoreboard_font.render(result_text, True, self._get_color("lightblue"))
            screen.blit(rendered_result, (x, y))

    def _draw_board(self, screen):
        rect_size = self.cell_size - 2 * self.cell_padding
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                color = self._cell_color
                if (row_ind, col_ind) in self._snake:
                    color = self._snake_color
                elif (row_ind, col_ind) == self._apple:
                    color = self._apple_color
                x = self._board_x + col_ind * self.cell_size + self.cell_padding
                y = self._board_y + row_ind * self.cell_size + self.cell_padding
                pygame.draw.rect(screen, color, (x, y, rect_size, rect_size))

                if (row_ind, col_ind) == self._snake[0]:
                    if self._snake_direction == "up":
                        head_pos = (x + rect_size // 2, y)
                    elif self._snake_direction == "down":
                        head_pos = (x + rect_size // 2, y + rect_size)
                    elif self._snake_direction == "left":
                        head_pos = (x, y + rect_size // 2)
                    else:
                        head_pos = (x + rect_size, y + rect_size // 2)
                    pygame.draw.circle(screen, self._snake_head_color, head_pos, 2)

    def _snake_move(self):
        snake_row, snake_col = self._snake[0]
        if self._snake_direction == "left":
            snake_col = self.total_cols - 1 if snake_col == 0 else snake_col -1
        elif self._snake_direction == "right":
            snake_col = 0 if snake_col == self.total_cols - 1 else snake_col + 1
        elif self._snake_direction == "up":
            snake_row = self.total_rows - 1 if snake_row == 0 else snake_row - 1
        else:
            snake_row = 0 if snake_row == self.total_rows - 1 else snake_row + 1

        if self._snake_extend:
            self._snake = [(snake_row, snake_col)] + self._snake
            self._snake_extend = False
        else:
            self._snake = [(snake_row, snake_col)] + self._snake[:-1]

        if (snake_row, snake_col) == self._apple:
            self._score += 1
            self._snake_extend = True
            self._add_apple()

        if self._check_is_over():
            self._end_game()
            return

        self._command_waiting = False

    def _update_optimal_direction(self):
        row, col = self._snake[0]

        available_cells = {"down": [row + 1, col],
                           "up": [row - 1, col],
                           "right": [row, col + 1],
                           "left": [row, col - 1]}
        for direction, cell in available_cells.items():
            if cell[0] == -1:
                cell[0] = self.total_rows - 1
            elif cell[0] == self.total_rows:
                cell[0] = 0
            elif cell[1] == -1:
                cell[1] = self.total_cols - 1
            elif cell[1] == self.total_cols:
                cell[1] = 0

        if self._snake_direction == "left":
            del available_cells["right"]
        elif self._snake_direction == "right":
            del available_cells["left"]
        elif self._snake_direction == "up":
            del available_cells["down"]
        elif self._snake_direction == "down":
            del available_cells["up"]

        min_distance = None
        min_direction = None
        for direction, cell in available_cells.items():
            if (cell[0], cell[1]) in self._snake[:-1]:
                continue

            curr_distance = distance(cell, self._apple)
            if min_distance is None:
                min_distance = curr_distance
                min_direction = direction
                continue

            if curr_distance < min_distance:
                min_distance = curr_distance
                min_direction = direction

        if min_direction is not None:
            self._snake_direction = min_direction

    def _check_is_over(self):
        if len(self._snake) == self.total_rows * self.total_cols:
            self._win = True
            return True

        if self._snake[0] in self._snake[1:]:
            self._win = False
            return True

        return False


class GameTetris(Game):
    def __init__(self, parent, exit_event, total_rows=16, total_cols=10, cell_size=20, cell_padding=1):
        super(GameTetris, self).__init__(parent, exit_event)

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.cell_size = cell_size
        self.cell_padding = cell_padding

        self._score_width = 50
        self._score_padding = 10
        self._board_x = self._score_width + (self._screen_width - self.total_cols * self.cell_size) // 2
        self._board_y = (self._screen_height - self.total_rows * self.cell_size) // 2
        self._cell_color = self._get_color('lightgray')
        self._block_color = self._get_color('orange')

        self._block1 = TetrisBlock([['x', '.', '.'], ['x', 'x', 'x']], self._block_color)
        self._block2 = TetrisBlock([['x'], ['x'], ['x'], ['x']], self._block_color)
        self._block3 = TetrisBlock([['.', 'x', '.'], ['x', 'x', 'x']], self._block_color)
        self._block4 = TetrisBlock([['x', 'x'], ['x', 'x']], self._block_color)
        self._block5 = TetrisBlock([['.', '.', 'x'], ['x', 'x', 'x']], self._block_color)
        self._avail_blocks = [self._block1, self._block2, self._block3, self._block4, self._block5]
        self._block_speed = 2
        self._score = 0
        self._started = False
        self._game_over = False
        self._fixed_blocks = []
        self._board = []
        self._active_block = None
        self._start_time = time.time()
        self._progress_time = self._start_time
        self._block_lastmove = time.time()

    def _game_on_enter(self):
        self._init_game()

    def _game_on_exit(self):
        pass

    def _on_update(self):
        if not self.is_active:
            return

        if self._started:
            current_time = time.time()
            self._progress_time = current_time
            if current_time - self._block_lastmove >= 1 / self._block_speed:
                self._move_down()
                self._block_lastmove = current_time

    def _on_draw(self, screen):
        if not self.is_active:
            return

        screen.fill(self._get_color("black"))
        self._draw_scoreboard(screen)
        self._draw_board(screen)

    def _draw_scoreboard(self, screen):
        x, y = 10, 10
        score_text = self.scoreboard_font.render("Score: {}".format(self._score), True, self._get_color("white"))
        screen.blit(score_text, (x, y))
        y += score_text.get_height() + self._score_padding

        min = int(self._progress_time - self._start_time) // 60
        sec = int(self._progress_time - self._start_time) % 60
        time_text = self.scoreboard_font.render("Time: {:02}:{:02}".format(min, sec), True, self._get_color("white"))
        screen.blit(time_text, (x, y))
        y += time_text.get_height() + self._score_padding

        if not self._started and self._progress_time > self._start_time:
            if self._game_over:
                result_text = "Oops!"
                rendered_result = self.scoreboard_font.render(result_text, True, self._get_color("lightblue"))
                screen.blit(rendered_result, (x, y))

    def _draw_board(self, screen):
        rect_size = self.cell_size - 2 * self.cell_padding
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                color = self._cell_color
                x = self._board_x + col_ind * self.cell_size + self.cell_padding
                y = self._board_y + row_ind * self.cell_size + self.cell_padding
                pygame.draw.rect(screen, color, (x, y, rect_size, rect_size))

        self._draw_block(screen, self._active_block)
        for block in self._fixed_blocks:
            self._draw_block(screen, block)

    def _draw_block(self, screen, block):
        rect_size = self.cell_size - 2 * self.cell_padding
        for point in block.points:
            x = self._board_x + point.col * self.cell_size + self.cell_padding
            y = self._board_y + point.row * self.cell_size + self.cell_padding
            pygame.draw.rect(screen, block.color, (x, y, rect_size, rect_size))

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._start_game()
            elif event.key == pygame.K_r:
                self._init_game()

            if not self._started:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    if not self._score == 0:
                        self._init_game()
                    self._start_game()
            elif event.key == pygame.K_LEFT:
                self._move_left()
            elif event.key == pygame.K_RIGHT:
                self._move_right()
            elif event.key == pygame.K_DOWN:
                self._drop_block()
            elif event.key == pygame.K_UP:
                self._rotate_block()

    def _init_game(self):
        self._score = 0
        self._active_block = self._get_new_block()
        self._fixed_blocks = []
        self._board = [['.' for _ in range(self.total_cols)] for _ in range(self.total_rows)]
        self._started = False
        self._game_over = False

    def _start_game(self):
        self._started = True
        self._start_time = time.time()
        self._progress_time = self._start_time

    def _get_new_block(self):
        new_block = copy.deepcopy(random.choice(self._avail_blocks))
        width = len(new_block.shape[0])
        new_block.add_offset(0, self.total_cols // 2 - width // 2)
        return new_block

    def _rotate_block(self, clockwise=True):
        if self._active_block is None:
            return

        if clockwise:
            self._rotate_clockwise()
        else:
            for _ in range(3):
                self._rotate_clockwise()

        width = len(self._active_block.shape[0])
        row, col = self._active_block.get_origin()
        if col < 0:
            self._move_right()
        elif col + width >= self.total_cols:
            self._move_left()

    def _move_left(self):
        row, col = self._active_block.get_origin()

        if col > 0:
            self._active_block.add_offset(0, -1)

    def _move_right(self):
        width = len(self._active_block.shape[0])
        height = len(self._active_block.shape)
        row, col = self._active_block.get_origin()
        if width + col < self.total_cols:
            self._active_block.add_offset(0, 1)

    def _move_down(self):
        width = len(self._active_block.shape[0])
        height = len(self._active_block.shape)
        row, col = self._active_block.get_origin()

        if row + height < self.total_rows and self._check_move_down():
            self._active_block.add_offset(1, 0)
            return True
        else:
            self._fixed_blocks.append(self._active_block)
            self._active_block = self._get_new_block()
            return False

    def _drop_block(self):
        width = len(self._active_block.shape[0])
        height = len(self._active_block.shape)
        row, col = self._active_block.get_origin()

        while row + height < self.total_rows and self._check_move_down():
            self._active_block.add_offset(1, 0)
            row, col = self._active_block.get_origin()

    def _check_move_down(self):
        next_block = copy.deepcopy(self._active_block)
        next_block.add_offset(1, 0)
        for block in self._fixed_blocks:
            if next_block.has_overlap(block):
                return False
        return True

    def _rotate_clockwise(self):
        width = len(self._active_block.shape[0])
        height = len(self._active_block.shape)
        x_offset, y_offset = self._active_block.get_origin()

        new_shape = [[self._active_block.shape[height - 1 - y][x] for y in range(height)] for x in range(width)]
        self._active_block.shape = new_shape
        self._active_block.load_points()
        self._active_block.add_offset(x_offset, y_offset)


class TetrisBlock:
    def __init__(self, shape, color):
        super(TetrisBlock, self).__init__()

        self.shape = shape
        self.color = color
        self.points = []

        self.load_points()

    def get_origin(self):
        return (min([point.row for point in self.points]), min([point.col for point in self.points]))

    def add_offset(self, x_offset, y_offset):
        for point in self.points:
            point.add_offset(x_offset, y_offset)

    def load_points(self):
        self.points = []
        for row_ind in range(len(self.shape)):
            for col_ind in range(len(self.shape[0])):
                if self.shape[row_ind][col_ind] == 'x':
                    self.points.append(TetrisPoint(row_ind, col_ind))

    def has_overlap(self, other):
        for point in self.points:
            for other_point in other.points:
                if point.row == other_point.row and point.col == other_point.col:
                    return True
        return False


class TetrisPoint:
    def __init__(self, row, col):
        super(TetrisPoint, self).__init__()

        self.row = row
        self.col = col

    def add_offset(self, x_offset, y_offset):
        self.row += x_offset
        self.col += y_offset
