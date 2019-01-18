import pygame
from shapes import *


class Table:
    def __init__(self, data, titles=None, x=0, y=0, header_font=None, content_font=None,
                 header_color=(255, 255, 255), content_color=(255, 255, 255),
                 line_color=(255, 255, 255), content_centered=None,
                 x_padding=0, y_padding=0, selected=False, selected_row=0,
                 selected_line_color=(0, 255, 0), row_status=None,
                 content_inactive_color=(125, 125, 125)):
        self.data = data
        self.titles = titles
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.header_color = header_color
        self.content_color = content_color
        self.line_color = line_color
        self.content_centered = content_centered
        self.x_padding = x_padding
        self.y_padding = y_padding
        self.selected = selected
        self.selected_row = selected_row
        self.selected_line_color = selected_line_color
        self.row_status = row_status
        self.content_inactive_color = content_inactive_color

        self._total_width = 0
        self._total_height = 0

        if header_font is None:
            self.header_font = pygame.font.Font("fonts/arial.ttf", 18)
        else:
            self.header_font = header_font

        if content_font is None:
            self.content_font = pygame.font.Font("fonts/arial.ttf", 16)
        else:
            self.content_font = content_font

        self.rows = []
        self.shapes = []
        self._render_data()

    def _reset(self):
        self.rows = []
        self.shapes = []

    def _render_data(self):
        self._reset()

        if self.titles:
            # render titles
            rendered_titles = []
            for elem in self.titles:
                rendered_title = self.header_font.render(elem, True, self.header_color)
                rendered_titles.append(rendered_title)
            self.rows.append(rendered_titles)

        # render contents
        for row_ind, row in enumerate(self.data):
            rendered_row = []
            for elem in row:
                if self.row_status and not self.row_status[row_ind]:
                    rendered_text = self.content_font.render(elem, True, self.content_inactive_color)
                else:
                    rendered_text = self.content_font.render(elem, True, self.content_color)
                rendered_row.append(rendered_text)
            self.rows.append(rendered_row)

        widths = []
        for i in range(len(self.rows[0])):
            col = [row[i] for row in self.rows]
            widths.append(max([elem.get_width() + self.x_padding * 2 for elem in col]))

        heights = [max([elem.get_height() + self.y_padding * 2 for elem in row]) for row in self.rows]

        self._total_width = sum(widths)
        self._total_height = sum(heights)

        # build the boundaries of table
        for r in range(len(self.rows) + 1):
            start_pos = (self.x, self.y + sum(heights[:r]))
            end_pos = (self.x + self._total_width, self.y + sum(heights[:r]))
            self.shapes.append(Line(self.line_color, start_pos, end_pos))

        for c in range(len(self.rows[0]) + 1):
            start_pos = (self.x + sum(widths[:c]), self.y)
            end_pos = (self.x + sum(widths[:c]), self.y + self._total_height)
            self.shapes.append(Line(self.line_color, start_pos, end_pos))

        # add selected row
        if self.selected:
            self.shapes.append(Rectangle(self.selected_line_color, self.x, self.y + sum(heights[:self.selected_row+1]),
                                         self._total_width, heights[self.selected_row+1], line_width=3))

        # add contents to the table
        for r, row in enumerate(self.rows):
            for c, elem in enumerate(row):
                if r == 0 or (self.content_centered and self.content_centered[c]):
                    pos = (self.x + sum(widths[:c]) + (widths[c] - elem.get_width()) / 2 + self.x_padding,
                           self.y + sum(heights[:r]) + self.y_padding)
                else:
                    pos = (self.x + sum(widths[:c]) + self.x_padding,
                           self.y + sum(heights[:r]) + self.y_padding)
                if r > 0 and self.row_status and not self.row_status[r-1]:
                    line_start_pos = (pos[0], pos[1] + elem.get_height() / 2)
                    line_end_pos = (pos[0] + elem.get_width(), pos[1] + elem.get_height() / 2)
                    self.shapes.append(Line(self.content_inactive_color, line_start_pos, line_end_pos))
                self.shapes.append(Text(elem, pos))

    def _draw_shape(self, screen, shape):
        if isinstance(shape, Line):
            pygame.draw.line(screen, shape.color, shape.start_pos, shape.end_pos, shape.width)
        elif isinstance(shape, Text):
            screen.blit(shape.text_surface, shape.pos)
        elif isinstance(shape, Rectangle):
            pygame.draw.rect(screen, shape.color, shape.to_pygame_rect(), shape.line_width)

    def draw(self, screen):
        for shape in self.shapes:
            self._draw_shape(screen, shape)

    def get_width(self):
        return self._total_width

    def get_height(self):
        return self._total_height

    def set_pos(self, x, y):
        if self.x != x or self.y != y:
            self.x = x
            self.y = y
            self._render_data()
