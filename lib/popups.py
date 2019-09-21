#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
from lib.button import Button
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
        self._frame_padding = 10

        self._title = ''
        self._title_font = pygame.font.Font('fonts/arial.ttf', 23)
        self._title_padding_y = 2
        self._rendered_title = self._title_font.render(self._title, True, self._title_color)
        self._header_height = self._rendered_title.get_height() + 2 * self._title_padding_y

        self.action_buttons = []
        self._action_button_font = pygame.font.Font('fonts/FreeSans.ttf', 18)
        self._action_button_size = 50
        self._action_button_padding = 2
        self._action_button_margin = 20
        self._action_button_temp = self._action_button_font.render(' ', True, self._get_color('white'))
        self._action_button_height = self._action_button_temp.get_height() + 2 * self._action_button_padding

        self._add_exit_button()
        self.set_align('center')

    def _add_exit_button(self):
        button_size = self._header_height
        exit_button = Button(self.parent, self.x + self.width - button_size, self.y,
                             width=button_size, height=button_size, text='x',
                             background_color=self._get_color('black'),
                             border_color=self._get_color('white'),
                             focus_color=self._get_color('lightgray'),
                             border_width=1, focus_width=1,
                             on_click=self.close, font=self._title_font)
        self.buttons.append(exit_button)

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

    def _calculate_button_pos(self):
        total_buttons = len(self.action_buttons)
        total_width = self._action_button_size * total_buttons \
            + self._action_button_margin * (total_buttons - 1)
        x_offset = (self.width - total_width) // 2
        y_offset = self.height - self._action_button_height - self._frame_padding
        for button in self.action_buttons:
            button.x += x_offset
            button.y += y_offset
            x_offset += self._action_button_size + self._action_button_margin

    def setup(self):
        super(Popup, self).setup()
        self._calculate_button_pos()

    def draw(self, screen):
        self._draw_frame(screen)
        super(Popup, self).draw(screen)

    def handle_events(self, event):
        if super(Popup, self).handle_events(event) == 0:
            return 0

        return self._handle_popup_event(event)

    def close(self):
        self.set_active(False)

    def set_title(self, title):
        self._title = title
        self._rendered_title = self._title_font.render(self._title, True, self._title_color)
        self._header_height = self._rendered_title.get_height() + 2 * self._title_padding_y

    def add_action_button(self, text, action=None):
        new_button = Button(self.parent, self.x, self.y, text=text,
                            width=self._action_button_size,
                            height=self._action_button_height,
                            background_color=self._get_color('black'),
                            border_color=self._get_color('white'),
                            focus_color=self._get_color('lightgray'),
                            border_width=1, focus_width=2,
                            on_click=action, font=self._action_button_font)
        self.buttons.append(new_button)
        self.action_buttons.append(new_button)


class InfoPopup(Popup):
    def __init__(self, parent, width, height, text):
        super(InfoPopup, self).__init__(parent, width, height)

        self.text = text

        self._text_padding = 10
        self._text_font = pygame.font.Font('fonts/FreeSans.ttf', 18)
        self._text_widget_max_width = self.width - 2 * self._text_padding
        self._text_widget_max_height = self.height - 2 * self._text_padding - self._header_height
        self._text_widget = Content(self.parent, 0, 0, self.text,
                                    max_width=self._text_widget_max_width,
                                    max_height=self._text_widget_max_height,
                                    font=self._text_font)
        self._text_widget.setup()
        text_x = self.x + (self.width - self._text_widget.get_width()) // 2
        text_y = self.y + (self.height - self._text_widget.get_height()) // 2
        self._text_widget.set_pos(text_x, text_y)

        self._subwidgets.append(self._text_widget)

        self.add_action_button('OK', action=self.close)

    def _on_setup(self):
        self.set_title('Info')

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass

    def _handle_popup_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.close()
