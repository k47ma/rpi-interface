import pygame
from lib.util import is_key_active


class Button:
    def __init__(self, parent, x, y, width=30, height=30, text="", image=None,
                 text_color=(255, 255, 255), background_color=None,
                 background_alpha=255, border_color=None, border_width=0,
                 font=None, on_click=None, on_click_param=None,
                 focus_color=None, focus_width=0, shortcut_key=None):
        super(Button, self).__init__()

        self.parent = parent
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.image = image
        self.text_color = text_color
        self.background_color = background_color
        self.background_alpha = background_alpha
        self.border_color = border_color
        self.border_width = border_width
        self.on_click = on_click
        self.on_click_param = on_click_param
        self.focus_color = focus_color
        self.focus_width = focus_width
        self.shortcut_key = shortcut_key
        self.is_active = False

        if font:
            self.font = font
        elif self.text:
            self.font = pygame.font.SysFont(pygame.font.get_default_font(), 30)
        else:
            self.font = None

        if self.text:
            self.rendered_text = self.font.render(self.text, True, self.text_color)
        else:
            self.rendered_text = None

        text_width = self.rendered_text.get_width() if self.text else 0
        text_height = self.rendered_text.get_height() if self.text else 0
        image_width = self.image.get_width() if self.image else 0
        image_height = self.image.get_height() if self.image else 0

        self.width = max(text_width, image_width, self.width)
        self.height = max(text_height, image_height, self.height)

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def is_shortcut(self):
        return is_key_active(self.shortcut_key) and self.is_active

    def is_focused(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.parent.invert_screen:
            mouse_pos = (self.parent.screen_width - mouse_pos[0],
                         self.parent.screen_height - mouse_pos[1])

        return (self.get_rect().collidepoint(mouse_pos) or self.is_shortcut()) and self.is_active

    def is_clicked(self):
        return self.is_focused() and pygame.mouse.get_pressed()[0]

    def draw(self, screen):
        if not self.is_active:
            return

        if self.background_color is not None:
            color = self.focus_color if self.focus_color and (self.is_focused() or self.is_shortcut()) else self.background_color
            alpha = min(255, self.background_alpha + 50) if (self.is_clicked() or self.is_shortcut()) else self.background_alpha
            background_surface = pygame.Surface((self.width, self.height))
            background_surface.fill(color)
            background_surface.set_alpha(alpha)
            screen.blit(background_surface, (self.x, self.y))

        if self.border_color is not None and self.border_width > 0:
            border_width = self.focus_width if self.is_focused() else self.border_width
            pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.width, self.height), border_width)

        if self.rendered_text:
            text_x = self.x + (self.width - self.rendered_text.get_width()) // 2
            text_y = self.y + (self.height - self.rendered_text.get_height()) // 2
            screen.blit(self.rendered_text, (text_x, text_y))

        if self.image:
            screen.blit(self.image, (self.x, self.y))

    def click(self):
        if self.on_click:
            if self.on_click_param is not None:
                self.on_click(self.on_click_param)
            else:
                self.on_click()

    def set_active(self, status):
        self.is_active = status

    def set_pos(self, x, y):
        self.x = x
        self.y = y

    def set_text(self, text):
        self.text = text
        self.rendered_text = self.font.render(self.text, True, self.text_color)

    def get_text(self):
        return self.text


class SelectorButton(Button):
    def __init__(self, *args, **kwargs):
        super(SelectorButton, self).__init__(*args, **kwargs)

        self.font = pygame.font.Font('fonts/FreeSans.ttf', 15)
        
        self._selected = False

    def click(self):
        if self.on_click:
            if self.on_click_param is not None:
                self.on_click(self.on_click_param)
            else:
                self.on_click()
        self.toggle_selected()

    def set_selected(self, status):
        if self._selected != status:
            self.toggle_selected()

    def toggle_selected(self):
        self._selected = not self._selected
        if self._selected:
            self.set_text('x')
        else:
            self.set_text(' ')

    def get_text(self):
        return self.text == 'x'
