#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
from panels import *


class App:
    def __init__(self, args=None):
        pygame.init()

        self.args = args

        self._screen_width = 480
        self._screen_height = 320
        self._screen_size = (self._screen_width, self._screen_height)
        self._frame_rate = 10
        self._fullscreen = self.args.fullscreen if self.args else False

        if self._fullscreen:
            self.display = pygame.display.set_mode(self._screen_size, pygame.FULLSCREEN)
        else:
            self.display = pygame.display.set_mode(self._screen_size)

        self._pygame_icon = pygame.image.load(os.path.join('images', 'icon', 'small-rpi.png')).convert_alpha()
        pygame.display.set_icon(self._pygame_icon)
        pygame.display.set_caption("rpi interface")

        self.screen = pygame.Surface(self._screen_size)
        self._invert_screen = self.args.invert if self.args else False

        self._done = False

        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        self.camera = cv2.VideoCapture(0)

        self.main_panel = MainPanel(self)
        self.night_panel = NightPanel(self)
        self.news_panel = NewsPanel(self)
        self.search_panel = SearchPanel(self)
        self.system_info_panel = SystemInfoPanel(self)
        self.system_info_panel.always_update = True
        self.stock_panel = StockPanel(self)
        self.map_panel = MapPanel(self)
        self.camera_panel = CameraPanel(self, self.camera)
        self.panels = [self.main_panel, self.night_panel, self.news_panel, self.search_panel,
                       self.system_info_panel, self.stock_panel, self.map_panel, self.camera_panel]
        self.active_panel = self.main_panel
        self._night_mode = False

        self._background_image_directory = os.path.join("images", "background")
        self._background_image_size = self._screen_height
        self._background_alpha = 180
        self._background_speed_rate = 0.1
        self._background_images = []

        self._brightness_last_update = time.time()
        self._brightness_update_interval = 0.5
        self._brightness_thres = 100
        self._brightness = 1.0

        self._setup()

    def _setup(self):
        self._background_image_sets = []
        for image_path in glob.glob(os.path.join(self._background_image_directory, "*.png")):
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (self._background_image_size, self._background_image_size))
            self._background_images.append(image)
        self._background_images.reverse()

        for panel in self.panels:
            panel.setup()

    def _handle_events(self):
        for event in pygame.event.get():
            self.active_panel.handle_events(event)

            if event.type == pygame.QUIT:
                self._done = True
            if event.type == pygame.KEYDOWN and self.active_panel is self.main_panel:
                if event.key == pygame.K_d:
                    self.set_active_panel(self.night_panel)
                elif event.key == pygame.K_n:
                    self.set_active_panel(self.news_panel)
                elif event.key == pygame.K_b:
                    self.set_active_panel(self.search_panel)
                elif event.key == pygame.K_i:
                    self.set_active_panel(self.system_info_panel)
                elif event.key == pygame.K_s:
                    self.set_active_panel(self.stock_panel)
                elif event.key == pygame.K_m:
                    self.set_active_panel(self.map_panel)
                elif event.key == pygame.K_v:
                    self.set_active_panel(self.camera_panel)

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_q] and (pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]):
            self._done = True

    def _update_screen(self):
        self.screen.fill((0, 0, 0))

        self._draw_background(self.screen)
        self.active_panel.draw(self.screen)
        self._apply_brightness(self.screen)
        if self._invert_screen:
            self.screen = pygame.transform.rotate(self.screen, 180)
        self.display.blit(self.screen, (0, 0))

        pygame.display.flip()

    def _on_update(self):
        if self.camera and time.time() - self._brightness_last_update > self._brightness_update_interval:
            self._update_brightness()
            self._brightness_last_update = time.time()

        for panel in self.panels:
            if panel == self.active_panel or panel.is_always_update():
                panel.update()

    def _draw_background(self, screen):
        x_offset = (self._screen_width - self._background_image_size) / 2
        y_offset = (self._screen_height - self._background_image_size) / 2
        current_time = int(time.time() * 100)
        background_surface = pygame.Surface((self._screen_width, self._screen_height))
        rotated_image_queue = Queue.Queue()
        threads = []
        for ind, image in enumerate(self._background_images):
            image_center = image.get_rect().center
            image_center = (image_center[0] + x_offset, image_center[1] + y_offset)
            degree = int(current_time / (2 ** ind) * self._background_speed_rate) % 360
            thread = ImageRotateThread(image, image_center, degree, rotated_image_queue)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for rotated_image, rect in rotated_image_queue.queue:
            background_surface.blit(rotated_image, rect)

        background_surface.set_alpha(self._background_alpha)
        screen.blit(background_surface.convert(), (0, 0))

    def _apply_brightness(self, screen):
        if self.active_panel is self.camera_panel:
            return

        brightness_surface = pygame.Surface((self._screen_width, self._screen_height))
        brightness_surface.fill((0, 0, 0))
        alpha_factor = min((1 - self._brightness), 0.3)
        brightness_surface.set_alpha(int(alpha_factor * 255))
        screen.blit(brightness_surface.convert(), (0, 0))

    def _update_brightness(self):
        ret, frame = self.camera.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        samples = random.sample(np.ravel(gray), 100)
        samples_avg = sum(samples) / len(samples)
        print samples_avg
        if samples_avg >= self._brightness_thres:
            self._brightness = 1.0
        else:
            self._brightness = float(samples_avg) / self._brightness_thres

    def set_active_panel(self, panel):
        if self.active_panel is not panel:
            self.active_panel.on_exit()
            panel.on_enter()
            self.active_panel = panel

    def get_screen(self):
        return self.screen

    def get_width(self):
        return self._screen_width

    def get_height(self):
        return self._screen_height

    def start(self):
        while not self._done:
            self._handle_events()
            self._update_screen()
            self._on_update()
            self.clock.tick(self._frame_rate)
