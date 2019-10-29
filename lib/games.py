#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
import random
import time
import copy
import string
from abc import abstractmethod
from lib.widgets import Widget, Input
from lib.buttons import Button
from lib.util import distance


class Game(Widget):
    def __init__(self, parent, exit_event):
        super(Game, self).__init__(parent, 0, 0)

        self.exit_event = exit_event
        self.draw_subwidgets = False

        self._score_width = 50
        self._score_height = 0
        self._score_padding = 10
        self.scoreboard_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._scoreboard_lines = []

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
        self._draw_scoreboard(screen)
        self._draw_board(screen)

        for widget in self._subwidgets:
            widget.draw(screen)

    def _update_scoreboard(self):
        pass

    def _draw_scoreboard(self, screen):
        x, y = self._score_padding, self._score_padding
        for line, color in self._scoreboard_lines:
            rendered_text = self.scoreboard_font.render(line, True, color)
            screen.blit(rendered_text, (x, y))
            y += rendered_text.get_height() + self._score_padding
        self._score_height = y

    @abstractmethod
    def _draw_board(self, screen):
        pass

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
    def __init__(self, parent, exit_event, total_rows=16, total_cols=16, cell_padding=1):
        super(GameSnake, self).__init__(parent, exit_event)

        self.total_rows = total_rows
        self.total_cols = total_cols
        self.cell_padding = cell_padding

        self._max_board_size = 100
        self._score = 0
        self._high_score = 0
        self._score_width = 140
        self._board_padding = 10
        self._board_size = min(self._screen_width - self._score_width
                               - self._score_padding - self._board_padding,
                               self._screen_height) - 2 * self._board_padding
        self._board_x = self._score_width + self._score_padding + self._board_padding
        self._board_y = (self._screen_height - self._board_size + self._board_padding) // 2
        self._snake = []
        self._snake_direction = "right"
        self._snake_speed = 5
        self._snake_lastmove = time.time()
        self._snake_extend = False
        self._apple = (0, 0)
        self._game_started = False
        self._win = False
        self._auto_play = False
        self._start_time = time.time()
        self._progress_time = self._start_time
        self._cell_color = self._get_color("lightgray")
        self._snake_color = self._get_color("darkgreen")
        self._snake_head_color = self._get_color("orange")
        self._apple_color = self._get_color("red")

        self._row_widget = Input(self.parent, self._score_padding, self._score_height,
                                 font=self.scoreboard_font, width=30,
                                 limit_chars=list(string.digits), max_char=3,
                                 enter_key_event=self._confirm_settings)
        self._col_widget = Input(self.parent, self._score_padding, self._score_height,
                                 font=self.scoreboard_font, width=30,
                                 limit_chars=list(string.digits), max_char=3,
                                 enter_key_event=self._confirm_settings)
        self._speed_widget = Input(self.parent, self._score_padding, self._score_height,
                                   font=self.scoreboard_font, width=30,
                                   limit_chars=list(string.digits), max_char=3,
                                   enter_key_event=self._confirm_settings)
        self._row_widget.set_text(str(self.total_rows))
        self._col_widget.set_text(str(self.total_cols))
        self._speed_widget.set_text(str(self._snake_speed))
        self._row_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)
        self._col_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)
        self._speed_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)

        self._subwidgets = [self._row_widget, self._col_widget, self._speed_widget]

    def _game_on_enter(self):
        self._init_game()

        self._row_widget.set_text(str(self.total_rows))
        self._col_widget.set_text(str(self.total_cols))
        self._speed_widget.set_text(str(self._snake_speed))

    def _game_on_exit(self):
        pass

    def _on_update(self):
        if not self.is_active:
            return

        if self._game_started:
            current_time = time.time()
            self._progress_time = current_time
            if current_time - self._snake_lastmove >= 1 / self._snake_speed:
                if self._auto_play:
                    self._update_optimal_direction()
                self._snake_move()
                self._snake_lastmove = current_time

        self._update_scoreboard()

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self._game_started:
                    if not self._score == 0:
                        self._init_game()
                    self._auto_play = True
                    self._start_game()
            elif event.key == pygame.K_r:
                self._init_game()
            elif event.key == pygame.K_RETURN:
                self._col_widget.set_active(True)

            if not self._game_started:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    if not self._score == 0:
                        self._init_game()
                    self._start_game()

            if self._game_started and not self._auto_play:
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
        self._game_started = True
        self._start_time = time.time()
        self._progress_time = self._start_time

    def _end_game(self):
        self._game_started = False
        self._command_waiting = False

    def _init_game(self):
        self._snake = []
        self._snake.append((self.total_rows // 2, self.total_cols // 2 + 1))
        self._snake.append((self.total_rows // 2, self.total_cols // 2))
        self._snake_direction = "right"
        self._score = 0
        self._game_started = False
        self._command_waiting = False
        self._snake_extend = False
        self._auto_play = False
        self._win = False
        self._snake_lastmove = self._start_time
        self._progress_time = self._start_time
        self._add_apple()
        self._update_scoreboard()

    def _toggle_input_widget(self):
        if self._col_widget.is_active:
            self._col_widget.set_active(False)
            self._row_widget.set_active(True)
        elif self._row_widget.is_active:
            self._row_widget.set_active(False)
            self._speed_widget.set_active(True)
        elif self._speed_widget.is_active:
            self._speed_widget.set_active(False)
            self._col_widget.set_active(True)

    def _get_input_num(self, input_widget):
        if input_widget.is_empty():
            return None

        result = int(input_widget.get_text())
        if result > self._max_board_size or result <= 0:
            return None
        return result

    def _confirm_settings(self):
        new_rows = self._get_input_num(self._row_widget)
        new_cols = self._get_input_num(self._col_widget)
        new_speed = self._get_input_num(self._speed_widget)
        if new_rows is None or new_cols is None or new_speed is None \
           or (new_rows == self.total_rows
               and new_cols == self.total_cols
               and new_speed == self._snake_speed):
            return

        reset_game = new_rows != self.total_rows or new_cols != self.total_cols

        self.total_rows = new_rows
        self._row_widget.set_text(str(new_rows))

        self.total_cols = new_cols
        self._col_widget.set_text(str(new_cols))

        self._snake_speed = new_speed
        self._speed_widget.set_text(str(new_speed))

        if reset_game:
            self._init_game()

        self._row_widget.set_active(False)
        self._col_widget.set_active(False)
        self._speed_widget.set_active(False)

    def _add_apple(self):
        free_spots = []
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                if (row_ind, col_ind) not in self._snake:
                    free_spots.append((row_ind, col_ind))
        row, col = random.choice(free_spots)
        self._apple = (row, col)

    def _update_scoreboard(self):
        self._scoreboard_lines = []

        self._scoreboard_lines.append(("Score: {}".format(self._score), self._get_color("white")))
        self._scoreboard_lines.append(("High Score: {}".format(self._high_score), self._get_color("white")))

        min = int(self._progress_time - self._start_time) // 60
        sec = int(self._progress_time - self._start_time) % 60
        self._scoreboard_lines.append(("Time: {:02}:{:02}".format(min, sec), self._get_color("white")))

        if not self._game_started and self._progress_time > self._start_time:
            if self._win:
                result_text = "You Win!"
            else:
                result_text = "Oops!"
            self._scoreboard_lines.append((result_text, self._get_color("lightblue")))

        self._scoreboard_lines.append(("Board Width: ", self._get_color("white")))
        temp_text = self.scoreboard_font.render("Board Width: ", True, self._get_color("white"))
        temp_width = temp_text.get_width()
        temp_height = temp_text.get_height()
        self._col_widget.set_pos(self._score_padding + temp_width,
                                 self._score_height - 3 * (temp_height + self._score_padding))

        self._scoreboard_lines.append(("Board Height: ", self._get_color("white")))
        temp_text = self.scoreboard_font.render("Board Height: ", True, self._get_color("white"))
        temp_width = temp_text.get_width()
        temp_height = temp_text.get_height()
        self._row_widget.set_pos(self._score_padding + temp_width,
                                 self._score_height - 2 * (temp_height + self._score_padding))

        self._scoreboard_lines.append(("Snake Speed: ", self._get_color("white")))
        temp_text = self.scoreboard_font.render("Snake Speed: ", True, self._get_color("white"))
        temp_width = temp_text.get_width()
        temp_height = temp_text.get_height()
        self._speed_widget.set_pos(self._score_padding + temp_width,
                                   self._score_height - (temp_height + self._score_padding))

    def _draw_board(self, screen):
        cell_size = self._board_size // max(self.total_rows, self.total_cols)
        rect_size = cell_size - self.cell_padding
        for row_ind in range(self.total_rows):
            for col_ind in range(self.total_cols):
                color = self._cell_color
                if (row_ind, col_ind) in self._snake:
                    color = self._snake_color
                elif (row_ind, col_ind) == self._apple:
                    color = self._apple_color
                x = self._board_x + col_ind * cell_size + self.cell_padding
                y = self._board_y + row_ind * cell_size + self.cell_padding
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
            snake_col = self.total_cols - 1 if snake_col == 0 else snake_col - 1
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
            if self._score > self._high_score:
                self._high_score = self._score
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
        self._board_x = self._score_width + (self._screen_width - self.total_cols * self.cell_size) // 2
        self._board_y = (self._screen_height - self.total_rows * self.cell_size) // 2
        self._cell_color = self._get_color('lightgray')

        self._block1 = TetrisBlock([['x', '.', '.'], ['x', 'x', 'x']], self._get_color('red'))
        self._block2 = TetrisBlock([['x'], ['x'], ['x'], ['x']], self._get_color('orange'))
        self._block3 = TetrisBlock([['.', 'x', '.'], ['x', 'x', 'x']], self._get_color('lightblue'))
        self._block4 = TetrisBlock([['x', 'x'], ['x', 'x']], self._get_color('green'))
        self._block5 = TetrisBlock([['.', '.', 'x'], ['x', 'x', 'x']], self._get_color('yellow'))
        self._avail_blocks = [self._block1, self._block2, self._block3, self._block4, self._block5]
        self._block_speed = 2
        self._score = 0
        self._high_score = 0
        self._game_started = False
        self._game_over = False
        self._game_paused = False
        self._fixed_blocks = []
        self._active_block = None
        self._start_time = time.time()
        self._progress_time = 0
        self._last_update_time = self._start_time
        self._block_lastmove = time.time()

    def _game_on_enter(self):
        self._init_game()

    def _game_on_exit(self):
        pass

    def _on_update(self):
        if not self.is_active:
            return

        if self._game_started:
            current_time = time.time()
            self._progress_time += current_time - self._last_update_time
            self._last_update_time = current_time
            if current_time - self._block_lastmove >= 1 / self._block_speed:
                self._move_down()
                self._block_lastmove = current_time

        self._update_scoreboard()

    def _update_scoreboard(self):
        self._scoreboard_lines = []

        self._scoreboard_lines.append(("Score: {}".format(self._score), self._get_color("white")))
        self._scoreboard_lines.append(("High Score: {}".format(self._high_score), self._get_color("white")))

        min = int(self._progress_time) // 60
        sec = int(self._progress_time) % 60
        self._scoreboard_lines.append(("Time: {:02}:{:02}".format(min, sec), self._get_color("white")))

        if not self._game_started and self._game_over:
            self._scoreboard_lines.append(("Oops!", self._get_color("lightblue")))
            self._scoreboard_lines.append(("Press R to restart", self._get_color("green")))
        elif not self._game_started:
            self._scoreboard_lines.append(("Press direction key to start", self._get_color("green")))

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
            if event.key == pygame.K_r:
                self._init_game()

            if self._game_started:
                if event.key == pygame.K_p:
                    self._toggle_pause()

            if not self._game_started and not self._game_over:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    self._start_game()
            elif self._game_started:
                if event.key == pygame.K_LEFT:
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
        self._game_started = False
        self._game_over = False
        self._game_paused = False
        self._progress_time = 0

    def _start_game(self):
        self._game_started = True
        self._start_time = time.time()
        self._last_update_time = self._start_time

    def _toggle_pause(self):
        self._game_paused = not self._game_paused

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
            for _ in range(abs(col)):
                self._move_right()
        elif col + width >= self.total_cols:
            for _ in range(col + width - self.total_cols):
                self._move_left()

    def _move_left(self):
        row, col = self._active_block.get_origin()

        if col > 0 and self._check_move(0, -1):
            self._active_block.add_offset(0, -1)

    def _move_right(self):
        width = len(self._active_block.shape[0])
        row, col = self._active_block.get_origin()
        if width + col < self.total_cols and self._check_move(0, 1):
            self._active_block.add_offset(0, 1)

    def _move_down(self):
        height = len(self._active_block.shape)
        row, col = self._active_block.get_origin()

        if row + height < self.total_rows and self._check_move(1, 0):
            self._active_block.add_offset(1, 0)
        else:
            self._fixed_blocks.append(self._active_block)
            self._active_block = self._get_new_block()
            self._check_row_clear()
            self._check_game_over()

    def _drop_block(self):
        height = len(self._active_block.shape)
        row, col = self._active_block.get_origin()

        while row + height < self.total_rows and self._check_move(1, 0):
            self._active_block.add_offset(1, 0)
            row, col = self._active_block.get_origin()

        self._move_down()

    def _check_move(self, x_offset, y_offset):
        next_block = copy.deepcopy(self._active_block)
        next_block.add_offset(x_offset, y_offset)
        for point in next_block.points:
            if point.row < 0 or point.col < 0 or point.row >= self.total_rows or point.col >= self.total_cols:
                return False

        for block in self._fixed_blocks:
            if next_block.has_overlap(block):
                return False
        return True

    def _check_row_clear(self):
        board = [[0 for _ in range(self.total_cols)] for _ in range(self.total_rows)]
        for block in self._fixed_blocks:
            for point in block.points:
                board[point.row][point.col] = 1

        full_indices = []
        for row_ind, row in enumerate(board):
            if 0 not in row:
                full_indices.append(row_ind)

        for full_ind in full_indices:
            for block_ind in range(len(self._fixed_blocks) - 1, -1, -1):
                self._fixed_blocks[block_ind].clear_row(full_ind)
                if self._fixed_blocks[block_ind].is_empty():
                    del self._fixed_blocks[block_ind]

        self._score += 5 * (1 + len(full_indices)) * len(full_indices)

    def _check_game_over(self):
        for block in self._fixed_blocks:
            if self._active_block.has_overlap(block):
                self._game_started = False
                self._game_over = True

    def _rotate_clockwise(self):
        width = len(self._active_block.shape[0])
        height = len(self._active_block.shape)
        row_offset, col_offset = self._active_block.get_origin()

        new_shape = [[self._active_block.shape[height - 1 - y][x] for y in range(height)] for x in range(width)]
        self._active_block.shape = new_shape
        self._active_block.load_points()
        self._active_block.add_offset(row_offset + (height - width), col_offset)


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

    def clear_row(self, row_ind):
        for ind in range(len(self.points) - 1, -1, -1):
            if self.points[ind].row == row_ind:
                del self.points[ind]
            elif self.points[ind].row < row_ind:
                self.points[ind].add_offset(1, 0)

    def is_empty(self):
        return len(self.points) == 0


class TetrisPoint:
    def __init__(self, row, col):
        super(TetrisPoint, self).__init__()

        self.row = row
        self.col = col

    def add_offset(self, row_offset, col_offset):
        self.row += row_offset
        self.col += col_offset


class GameFlip(Game):
    def __init__(self, parent, exit_event, board_size=20, border_width=1, randomness=0.05):
        super(GameFlip, self).__init__(parent, exit_event)

        self.board_size = board_size
        self.border_width = border_width
        self.randomness = randomness

        self._max_board_size = 100
        self._score_width = 160
        self._board_padding = 10
        self._board_x = self._score_width
        self._board_y = 0
        self._cell_size = 0
        self._board_width = 0
        self._board_height = 0
        self._board_border_width = 1
        self._progress_bar_width = 130
        self._progress_bar_height = 10

        self._game_started = False
        self._game_over = False
        self._game_paused = False
        self._curr_player = 1
        self._player1_cells = []
        self._player2_cells = []
        self._possible_next_cells = set()
        self._player1_mode = "manual"
        self._player2_mode = "manual"
        self._curr_mode = self._player1_mode
        self._player1_color = self._get_color('orange')
        self._player2_color = self._get_color('lightblue')
        self._curr_color = self._player1_color
        self._origin_color = self._get_color('lightgray')
        self._origin_focus_color = self._get_color('gray')
        self._border_color = self._get_color('white')
        self._origin_alpha = 150
        self._clicked_alpha = 240
        self._winner = 0
        self._winner_color = self._origin_color
        self._last_update_time = time.time()
        self._progress_time = 0
        self._board = []

        self._size_widget = Input(self.parent, self._score_padding, self._score_height,
                                   font=self.scoreboard_font, width=30,
                                   limit_chars=list(string.digits), max_char=3,
                                   enter_key_event=self._confirm_settings)
        self._size_widget.set_text(str(self.board_size))
        self._size_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)

        self._randomness_widget = Input(self.parent, self._score_padding, self._score_height,
                                        font=self.scoreboard_font, width=40,
                                        limit_chars=list(string.digits + '.'), max_char=5,
                                        enter_key_event=self._confirm_settings)
        self._randomness_widget.set_text(str(self.randomness))
        self._randomness_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)

        self._subwidgets = [self._size_widget, self._randomness_widget]

    def _init_game(self):
        self._game_over = False
        self._game_paused = False
        self._curr_player = 1
        self._player1_cells = []
        self._player2_cells = []
        self._possible_next_cells = set()
        self._curr_mode = self._player1_mode
        self._winner = 1
        self._winner_color = self._origin_color
        self._curr_color = self._player1_color
        self._last_update_time = time.time()
        self._progress_time = 0

        for row in self._board:
            for cell in row:
                cell.background_color = self._origin_color
                cell.background_alpha = self._origin_alpha
                cell.focus_color = self._origin_focus_color

        self._click_cell((self.board_size // 2, self.board_size // 2))
        self._click_cell((self.board_size // 2, self.board_size // 2 - 1))
        self._click_cell((self.board_size // 2 - 1, self.board_size // 2 - 1))
        self._click_cell((self.board_size // 2 - 1, self.board_size // 2))

        self._game_started = False

    def _init_board(self):
        self.buttons = []
        self._board = []
        self._cell_size = (min(self._screen_width - self._score_width,
                           self._screen_height) - 2 * self._board_padding) // self.board_size

        for row in range(self.board_size):
            cell_row = []
            for col in range(self.board_size):
                button_x = self._board_x + self._board_padding + col * self._cell_size
                button_y = self._board_y + self._board_padding + row * self._cell_size
                border_width = 0 if self.board_size > 30 else self.border_width
                cell = Button(self.parent, button_x, button_y,
                              width=self._cell_size, height=self._cell_size,
                              background_color=self._origin_color, background_alpha=self._origin_alpha,
                              border_color=self._border_color, border_width=border_width,
                              on_click=self._click_cell, on_click_param=(row, col),
                              focus_color=self._origin_focus_color, focus_width=border_width)
                self.buttons.append(cell)
                cell_row.append(cell)
            self._board.append(cell_row)
        
        self._board_width = self._board_height = self._cell_size * self.board_size

    def _start_game(self):
        self._game_started = True
        self._last_update_time = time.time()

    def _on_setup(self):
        self._init_board()
        self._init_game()

    def _on_update(self):
        if not self.is_active:
            return

        current_time = time.time()
        if self._game_started and not self._game_paused:
            self._progress_time += current_time - self._last_update_time
            self._last_update_time = current_time

            if self._curr_mode == "auto":
                self._click_cell(self._find_best_move())
        self._update_scoreboard()

    def _update_scoreboard(self):
        self._scoreboard_lines = []

        min = int(self._progress_time) // 60
        sec = int(self._progress_time) % 60
        suffix1 = '←' if self._curr_player == 1 else ''
        suffix2 = '←' if self._curr_player == 2 else ''
        player1_total = len(self._player1_cells)
        player2_total = len(self._player2_cells)
        self._scoreboard_lines.append(("Time: {:02}:{:02}".format(min, sec), self._get_color("white")))
        self._scoreboard_lines.append(("Player1 ({}): {} {}".format(self._player1_mode, player1_total, suffix1), self._player1_color))
        self._scoreboard_lines.append(("Player2 ({}): {} {}".format(self._player2_mode, player2_total, suffix2), self._player2_color))
        self._scoreboard_lines.append(("Progress: {}%".format(int((player1_total + player2_total) / self.board_size ** 2 * 100)),
                                       self._get_color("darkgreen")))

        if self._game_over:
            if self._winner == 0:
                self._scoreboard_lines.append(("Draw!", self._winner_color))
            else:
                self._scoreboard_lines.append(("Player{} Wins!".format(self._winner), self._winner_color))

        randomness_text = self.scoreboard_font.render("Randomness: ", True, self._get_color("white"))
        size_text = self.scoreboard_font.render("Board Size: ", True, self._get_color("white"))

        self._scoreboard_lines.append(("Board Size: ", self._get_color("white")))
        self._size_widget.set_pos(self._score_padding + size_text.get_width(),
                                   self._score_height - size_text.get_height()
                                   - randomness_text.get_height() - self._score_padding * 2)

        self._scoreboard_lines.append(("Randomness: ", self._get_color("white")))
        self._randomness_widget.set_pos(self._score_padding + randomness_text.get_width(),
                                        self._score_height - randomness_text.get_height() - self._score_padding)

    def _draw_board(self, screen):
        for row in self._board:
            for cell in row:
                cell.draw(screen)
        
        # draw boarder
        border_rect = (self._board_x + self._board_padding, self._board_y + self._board_padding,
                       self._board_width, self._board_height)
        pygame.draw.rect(screen, self._get_color('white'), border_rect, self._board_border_width)

        self._draw_progress_bar(screen)
    
    def _draw_progress_bar(self, screen):
        progress_bar_x = self._score_padding
        progress_bar_y = self._score_height + self._score_padding

        player1_total = len(self._player1_cells)
        player2_total = len(self._player2_cells)
        player1_width = int(player1_total / (player1_total + player2_total) * self._progress_bar_width)
        player2_width = self._progress_bar_width - player1_width
        player1_rect = (progress_bar_x, progress_bar_y,
                        player1_width, self._progress_bar_height)
        player2_rect = (progress_bar_x + player1_width, progress_bar_y,
                        player2_width, self._progress_bar_height)
        line_start = (progress_bar_x + self._progress_bar_width // 2, progress_bar_y)
        line_end = (progress_bar_x + self._progress_bar_width // 2,
                    progress_bar_y + self._progress_bar_height)

        progress_bar_y += self._progress_bar_height + self._score_padding

        total_cells = self.board_size ** 2
        progress_width = int((player1_total + player2_total) / total_cells * self._progress_bar_width)
        background_rect = (progress_bar_x, progress_bar_y,
                           self._progress_bar_width, self._progress_bar_height)
        progress_rect = (progress_bar_x, progress_bar_y,
                         progress_width, self._progress_bar_height)

        pygame.draw.rect(screen, self._player1_color, player1_rect, 0)
        pygame.draw.rect(screen, self._player2_color, player2_rect, 0)
        pygame.draw.line(screen, self._get_color("white"), line_start, line_end, 2)
        pygame.draw.rect(screen, self._origin_color, background_rect, 0)
        pygame.draw.rect(screen, self._get_color("darkgreen"), progress_rect, 0)

    def _game_on_enter(self):
        pygame.mouse.set_visible(True)
        for row in self._board:
            for cell in row:
                cell.set_active(True)
        self._size_widget.set_text(str(self.board_size))
        self._randomness_widget.set_text(str(self.randomness))

        self._game_paused = False
        if self._game_started:
            self._last_update_time = time.time()

    def _game_on_exit(self):
        pygame.mouse.set_visible(False)
        for row in self._board:
            for cell in row:
                cell.set_active(False)

        if self._game_started:
            self._game_paused = True

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self._init_game()
            elif event.key == pygame.K_r:
                self._reset_player_mode()
            elif event.key == pygame.K_t:
                self._toggle_current_player_mode()
            elif event.key == pygame.K_RETURN:
                self._size_widget.set_active(True)
    
    def _toggle_input_widget(self):
        if self._size_widget.is_active:
            self._size_widget.set_active(False)
            self._randomness_widget.set_active(True)
        elif self._randomness_widget.is_active:
            self._randomness_widget.set_active(False)
            self._size_widget.set_active(True)

    def _is_valid_pos(self, row, col):
        return 0 <= row < self.board_size and 0 <= col < self.board_size

    def _reset_player_mode(self):
        self._player1_mode = "manual"
        self._player2_mode = "manual"

    def _toggle_current_player_mode(self):
        if self._curr_mode == "manual":
            self._curr_mode = "auto"
        else:
            self._curr_mode = "manual"

        if self._curr_player == 1:
            self._player1_mode = self._curr_mode
        else:
            self._player2_mode = self._curr_mode
    
    def _confirm_settings(self):
        self._set_board_size()
        self._set_randomness()

    def _set_board_size(self):
        if self._size_widget.is_empty():
            return

        new_board_size = int(self._size_widget.get_text())
        if self.board_size == new_board_size \
           or new_board_size > self._max_board_size \
           or new_board_size <= 0:
            return

        self.board_size = new_board_size
        self._size_widget.set_text(str(new_board_size))
        self._init_board()
        self._init_game()

        for row in self._board:
            for cell in row:
                cell.set_active(True)

        self._size_widget.set_active(False)
    
    def _set_randomness(self):
        if self._randomness_widget.is_empty():
            return
        
        try:
            new_randomness = float(self._randomness_widget.get_text())
        except ValueError:
            self._randomness_widget.set_text(str(self.randomness))
            return

        if 0 <= new_randomness <= 1:
            self.randomness = new_randomness
        else:
            self._randomness_widget.set_text(str(self.randomness))

        self._randomness_widget.set_active(False)

    def _click_cell(self, pos):
        row, col = pos
        if not self._is_valid_pos(row, col):
            return

        if not self._game_started and not self._game_over:
            self._start_game()

        if self._board[row][col].background_color == self._origin_color:
            self._board[row][col].background_color = self._curr_color
            self._board[row][col].background_alpha = self._clicked_alpha
            self._board[row][col].focus_color = None
            self._flip_cells(row, col, mutate_board=True)
            if self._curr_player == 1:
                self._player1_cells.append((row, col))
            else:
                self._player2_cells.append((row, col))
            self._toggle_player()
            self._check_game_over()

            self._possible_next_cells.discard(pos)
            for x_dir in (-1, 0, 1):
                for y_dir in (-1, 0, 1):
                    if x_dir == 0 and y_dir == 0:
                        continue
                    next_row = row + x_dir
                    next_col = col + y_dir
                    if self._is_valid_pos(next_row, next_col) and \
                            self._board[next_row][next_col].background_color == self._origin_color:
                        self._possible_next_cells.add((next_row, next_col))

    def _flip_cells(self, row, col, mutate_board=False):
        total_flips = 0
        for x_dir in (-1, 0, 1):
            for y_dir in (-1, 0, 1):
                if x_dir == 0 and y_dir == 0:
                    continue
                total_flips += self._flip_cells_direction(row, col, (x_dir, y_dir), mutate=mutate_board)

        return total_flips

    def _find_best_move(self):
        max_flips = 0
        max_flip_cell = random.choice(list(self._possible_next_cells))

        if random.random() < self.randomness:
            return max_flip_cell

        for row, col in self._possible_next_cells:
            flips = self._flip_cells(row, col, mutate_board=False)
            if flips > max_flips:
                max_flips = flips
                max_flip_cell = (row, col)

        return max_flip_cell

    def _flip_cells_direction(self, row, col, direction, mutate=True):
        row += direction[0]
        col += direction[1]
        visited = []
        while self._is_valid_pos(row, col):
            cell_color = self._board[row][col].background_color
            if cell_color == self._curr_color:
                if mutate:
                    for flip_cell in visited:
                        self._board[flip_cell[0]][flip_cell[1]].background_color = self._curr_color
                        if self._curr_player == 1:
                            self._player1_cells.append(flip_cell)
                            del self._player2_cells[self._player2_cells.index(flip_cell)]
                        else:
                            self._player2_cells.append(flip_cell)
                            del self._player1_cells[self._player1_cells.index(flip_cell)]
                return len(visited)
            elif cell_color == self._origin_color:
                return 0
            else:
                visited.append((row, col))
            row += direction[0]
            col += direction[1]

        return 0

    def _toggle_player(self):
        if self._curr_player == 1:
            self._curr_player = 2
            self._curr_color = self._player2_color
            self._curr_mode = self._player2_mode
        else:
            self._curr_player = 1
            self._curr_color = self._player1_color
            self._curr_mode = self._player1_mode

    def _check_game_over(self):
        player1_total = len(self._player1_cells)
        player2_total = len(self._player2_cells)
        if player1_total + player2_total == self.board_size ** 2:
            self._game_over = True
            self._game_started = False
            if player1_total > player2_total:
                self._winner = 1
                self._winner_color = self._player1_color
            elif player1_total < player2_total:
                self._winner = 2
                self._winner_color = self._player2_color
            else:
                self._winner = 0
                self._winner_color = self._origin_color
