import pygame

class Button:
    def __init__(self, x, y, text="", image=None, color=(255, 255, 255),
                 background=None, thickness=0, font=None, on_click=None):
        self.x = x
        self.y = y
        self.text = text
        self.image = image
        self.color = color
        self.background = background
        self.thickness = thickness
        self.on_click = on_click

        if font:
            self.font = font
        else:
            self.font = self.date_font = pygame.font.SysFont(pygame.font.get_default_font(), 30)

        if self.text:
            self.rendered_text = self.font.render(self.text, True, self.color)
        else:
            self.rendered_text = None

        self.width = 0
        self.height = 0
        self._setup()

    def _setup(self):
        text_width = self.text.get_width() if self.text else 0
        text_height = self.text.get_height() if self.text else 0
        image_width = self.image.get_width() if self.image else 0
        image_height = self.image.get_height() if self.image else 0

        self.width = max(text_width, image_width)
        self.height = max(image_width, image_height)

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.get_width(), self.get_height())

    def draw(self, surface):
        width = self.get_width()
        height = self.get_height()

        if self.background is not None:
            pygame.draw.rect(surface, self.background, (self.x, self.y, width, height), self.thickness)

        if self.rendered_text:
            surface.blit(self.rendered_text, (self.x, self.y))

        if self.image:
            surface.blit(self.image, (self.x, self.y))

    def click(self):
        if self.on_click:
            self.on_click()
