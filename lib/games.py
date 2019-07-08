#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
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
    def __init__(self, parent, exit_event):
        super(GameSnake, self).__init__(parent, exit_event)
