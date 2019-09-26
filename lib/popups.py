#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import pygame
from lib.buttons import Button, SelectorButton
from lib.widgets import Widget, Content, Input
from lib.util import get_font_width, get_font_height


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
        self._action_button_size = 70
        self._action_button_padding = 2
        self._action_button_margin = 20
        self._action_button_height = get_font_height(self._action_button_font) \
            + 2 * self._action_button_padding

        self._add_exit_button()

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
            button.x = self.x + x_offset
            button.y = self.y + y_offset
            x_offset += self._action_button_size + self._action_button_margin

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass

    def setup(self):
        super(Popup, self).setup()
        self._calculate_button_pos()

    def draw(self, screen):
        self._draw_frame(screen)
        super(Popup, self).draw(screen)

    def handle_events(self, event):
        if super(Popup, self).handle_events(event):
            return True

        return self._handle_popup_event(event)

    def close(self):
        self.set_active(False)

    def set_title(self, title):
        self._title = title
        self._rendered_title = self._title_font.render(self._title, True, self._title_color)
        self._header_height = self._rendered_title.get_height() + 2 * self._title_padding_y

    def add_action_button(self, text, action=None, action_param=None):
        new_button = Button(self.parent, self.x, self.y, text=text,
                            width=self._action_button_size,
                            height=self._action_button_height,
                            background_color=self._get_color('black'),
                            border_color=self._get_color('white'),
                            focus_color=self._get_color('lightgray'),
                            border_width=1, focus_width=2,
                            on_click=action, on_click_param=action_param,
                            font=self._action_button_font)
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

    def _handle_popup_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.close()


class ConfirmPopup(Popup):
    def __init__(self, parent, width, height, text, actions={}, default_action=None):
        super(ConfirmPopup, self).__init__(parent, width, height)

        self.text = text
        self.actions = actions
        self.default_action = default_action

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

        for key in actions:
            self.add_action_button(key, action=self._select_action, action_param=key)
        self.add_action_button('Cancel', action=self.close)

    def _on_setup(self):
        self.set_title('Confirm')

    def _handle_popup_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.default_action is not None:
                    self._select_action(self.default_action)
                self.close()

    def _select_action(self, key):
        if self.actions.get(key) is not None:
            self.actions[key]()
        self.close()


class InputPopup(Popup):
    def __init__(self, parent, width, height, text='', entries=[], styles=[], values=[],
                 required=None, close_action=None, input_width=100):
        super(InputPopup, self).__init__(parent, width, height)

        self.text = text
        self.entries = entries
        self.styles = styles
        self.required = required
        self.close_action = close_action
        self.values = values
        self.input_width = input_width

        self._text_padding = 10
        self._text_font = pygame.font.Font('fonts/FreeSans.ttf', 15)
        self._text_widget_max_width = self.width - 2 * self._text_padding
        self._text_widget_max_height = self.height - 2 * self._text_padding - self._header_height
        self._text_widget = Content(self.parent, 0, 0, self.text,
                                    max_width=self._text_widget_max_width,
                                    max_height=self._text_widget_max_height,
                                    font=self._text_font)
        self._text_widget.setup()
        self._text_x = self.x + 30
        self._text_y = self.y + self._header_height + 20
        self._text_widget.set_pos(self._text_x, self._text_y)
        self._subwidgets.append(self._text_widget)

        self._entry_font = pygame.font.Font('fonts/FreeSans.ttf', 15)
        self._input_widgets = []
        self._setup_input_widgets()

        self.add_action_button('OK', action=self._validate_close)
        self.add_action_button('Cancel', action=self.close)

    def _setup_input_widgets(self):
        if not self.entries:
            return

        x = self._text_x
        y = self._text_y + self._text_widget.get_height() + self._text_padding
        max_title = self._entry_font.render(max(self.entries, key=len), True, self._get_color('white'))
        max_title_width = max_title.get_width()

        for ind, entry in enumerate(self.entries):
            title_widget = Content(self.parent, x, y, entry + ': ', font=self._entry_font)
            title_widget.setup()
            self._subwidgets.append(title_widget)

            input_type = self.styles[ind] if self.styles else 'input'

            if input_type == 'input':
                input_widget = Input(self.parent, x + max_title_width + 15, y,
                                     font=self._entry_font, width=self.input_width,
                                     enter_key_event=self._validate_close)
                input_widget.setup()
                input_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)
                if self.values:
                    input_widget.set_text(self.values[ind])
                self._subwidgets.append(input_widget)
                self._input_widgets.append((entry, title_widget, input_widget))
            elif input_type == 'selector':
                selector_size = title_widget.get_height()
                input_widget = SelectorButton(self.parent, x + max_title_width + 15, y,
                                              width=selector_size, height=selector_size,
                                              border_color=self._get_color('white'),
                                              focus_color=self._get_color('lightgray'),
                                              background_color=self._get_color('black'),
                                              border_width=2, focus_width=2)
                self.buttons.append(input_widget)
                if self.values:
                    input_widget.set_selected(self.values[ind])
                self._input_widgets.append((entry, title_widget, input_widget))

            y += title_widget.get_height() + self._text_padding

        for t in self._input_widgets:
            if isinstance(t[2], Input):
                t[2].set_active(True)
                break

    def _on_setup(self):
        self.set_title('Input')

    def _handle_popup_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._toggle_input_widget()
            elif event.key == pygame.K_RETURN:
                self._validate_close()

    def _toggle_input_widget(self):
        found = False

        for ind, t in enumerate(self._input_widgets):
            if not isinstance(t[2], Input):
                continue

            if t[2].is_active:
                t[2].set_active(False)
                for next_t in self._input_widgets[ind + 1:]:
                    if isinstance(next_t[2], Input):
                        next_t[2].set_active(True)
                        found = True
                break

        if not found:
            for t in self._input_widgets:
                if isinstance(t[2], Input):
                    t[2].set_active(True)
                    break

    def _validate_close(self):
        if not self.required:
            return True

        result = True
        for ind, t in enumerate(self._input_widgets):
            if not isinstance(t[2], Input):
                continue

            t[1].set_color(self._get_color('white'))

            req = self.required[ind]
            entry_valid = True
            entry_text = t[2].get_text()
            if isinstance(req, bool) and req and not entry_text:
                entry_valid = False
            elif isinstance(self.required[ind], str) \
                    and not re.search(self.required[ind], entry_text):
                entry_valid = False

            if not entry_valid:
                t[1].set_color(self._get_color('red'))
                result = False

        if result:
            if self.close_action:
                self.close_action()
            self.close()

        return result

    def get_input(self):
        result = {}
        for t in self._input_widgets:
            result[t[0]] = t[2].get_text()

        return result
