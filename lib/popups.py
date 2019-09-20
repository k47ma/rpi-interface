#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
from lib.widgets import Widget, Content


class Popup(Widget):
    def __init__(self, parent, width, height):
        super(Popup, self).__init__(parent, 0, 0)

        self.width = width
        self.height = height

        self._title_color = self._get_color('white')
        self._frame_color = self._get_color('white')
        self._background_color = self._get_color('black')

        self._frame_width = 1

        self._title = ""
        self._title_font = pygame.font.Font("fonts/arial.ttf", 20)
        self._title_padding_y = 2
        self._rendered_title = self._title_font.render(self._title, True, self._title_color)
        self._header_height = self._rendered_title.get_height() + 2 * self._title_padding_y

        self.set_align("center")

    def draw(self, screen):
        self._draw_frame(screen)
        super(Popup, self).draw(screen)

    def _draw_frame(self, screen):
        frame_rect = (self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, self._background_color, frame_rect, 0)
        pygame.draw.rect(screen, self._frame_color, frame_rect, self._frame_width)

        title_x = self.x + (self.width - self._rendered_title.get_width()) // 2
        title_y = self.y + self._title_padding_y
        screen.blit(self._rendered_title, (title_x, title_y))

        start_pos = (self.x, self.y + self._rendered_title.get_height() + 2 * self._title_padding_y)
        end_pos = (self.x + self.width, self.y + self._rendered_title.get_height() + 2 * self._title_padding_y)
        pygame.draw.line(screen, self._frame_color, start_pos, end_pos, self._frame_width)

    def set_title(self, title):
        self._title = title
        self._rendered_title = self._title_font.render(self._title, True, self._title_color)
        self._header_height = self._rendered_title.get_height() + 2 * self._title_padding_y


class InfoPopup(Popup):
    def __init__(self, parent, width, height, text):
        super(InfoPopup, self).__init__(parent, width, height)

        self.text = text

        self._text_padding = 10
        self._text_font = pygame.font.Font("fonts/FreeSans.ttf", 18)
        self._text_widget_max_width = self.width - 2 * self._text_padding
        self._text_widget_max_height = self.height - 2 * self._text_padding - self._header_height
        self._text_widget = Content(self.parent, 0, 0, self.text,
                                    max_width=self._text_widget_max_width,
                                    max_height=self._text_widget_max_height)
        self._text_widget.setup()
        text_x = self.x + (self.width - self._text_widget.get_width()) // 2
        text_y = self.y + (self.height - self._text_widget.get_height()) // 2
        self._text_widget.set_pos(text_x, text_y)

        self._subwidgets = [self._text_widget]

    def _on_setup(self):
        self.set_title("Info")

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass