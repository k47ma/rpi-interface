#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import queue
import psutil
import pygame
from datetime import datetime as dt
from abc import ABCMeta
from lib.button import Button
from lib.games import GameSnake, GameTetris, GameFlip
from lib.widgets import News, NewsList, Weather, Calendar, Traffic, Stock, \
    SystemInfo, Time, NightTime, Content, Search, Chart, ChartCaption, Map, \
    List, Calculator, Camera
from lib.popups import InputPopup


class Panel:
    __metaclass__ = ABCMeta

    def __init__(self, app):
        super(Panel, self).__init__()

        self.app = app
        self.args = app.args
        self.always_update = False
        self.invert_screen = self.args.invert if self.args else False
        self.screen_width = app.get_width()
        self.screen_height = app.get_height()

        self.widgets = []
        self.buttons = []
        self.popup = None
        self.default_font_name = pygame.font.get_default_font()
        self.active_widget = None
        if self.widgets:
            self.active_widget = self.widgets[0]

    def set_active_widget(self, widget):
        if self.active_widget is not widget:
            if self.active_widget is not None:
                self.active_widget.set_active(False)
            self.active_widget = widget
            if widget is not None:
                widget.set_active(True)

    def _on_update(self):
        pass

    def _on_enter(self):
        pass

    def _on_exit(self):
        pass

    def is_always_update(self):
        return self.always_update

    def enter(self):
        for button in self.buttons:
            button.set_active(True)

        self._on_enter()

    def exit(self):
        for button in self.buttons:
            button.set_active(False)

        self._on_exit()

    def setup(self):
        for widget in self.widgets:
            widget.setup()

    def update(self):
        self._on_update()
        for widget in self.widgets:
            widget.update()

        if self.popup:
            self.popup.update()
            if not self.popup.is_active:
                self.popup = None

    def draw(self, screen):
        for widget in self.widgets:
            widget.draw(screen)
        for button in self.buttons:
            button.draw(screen)

        if self.popup:
            self.popup.draw(screen)

    def handle_events(self, event):
        if self.popup:
            self.popup.handle_events(event)
            return True

        handled = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked = False
            for button in self.buttons:
                if button.is_focused():
                    button.click()
                    clicked = True
                    handled = True
            if not clicked:
                self.handle_panel_events(event)

        if self.active_widget:
            self.active_widget.handle_events(event)
            if not self.active_widget.is_active:
                self.active_widget = None
            else:
                handled = True
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.app.set_active_panel(self.app.main_panel)
                else:
                    self.handle_panel_events(event)

        return handled

    def get_screen_size(self):
        return self.screen_width, self.screen_height

    def handle_panel_events(self, event):
        pass

    def set_popup(self, popup):
        self.popup = popup
        self.popup.setup()
        self.popup.set_active(True)
        self.popup.set_align('center')


class MainPanel(Panel):
    def __init__(self, app):
        super(MainPanel, self).__init__(app)

        self.news_widget = News(self, 30, 300)
        self.weather_widget = Weather(self, 10, 75)
        self.time_widget = Time(self)
        self.calendar_widget = Calendar(self, 215, 100, max_rows=9, max_past_days=2, align="right")
        self.stock_widget = Stock(self, 5, 5)
        self.systeminfo_widget = SystemInfo(self, 10, 10)
        self.traffic_widget = Traffic(self, 190, 10)
        self.widgets = [self.news_widget, self.weather_widget, self.time_widget,
                        self.calendar_widget, self.systeminfo_widget, self.traffic_widget]

        self._night_image_path = "images/night.gif"
        self._night_image = pygame.transform.scale(pygame.image.load(self._night_image_path), (30, 30))
        self.night_button = Button(self, -1, self.screen_height - 29, image=self._night_image,
                                   on_click=self.enter_night_mode)
        self.buttons = [self.night_button]

    def _on_update(self):
        now = dt.now()
        if now.hour == 0 and now.minute == 0 and now.sec == 0:
            self.enter_night_mode()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                self.set_active_widget(self.calendar_widget)
            elif event.key == pygame.K_o:
                new_popup = InputPopup(self, 300, 200, text="Please enter data:",
                                       entries=["Event Name", "Date"], required=[True, True],
                                       close_action=lambda: print(new_popup.get_input()))
                self.set_popup(new_popup)

    def enter_night_mode(self):
        self.app.set_active_panel(self.app.night_panel)


class NightPanel(Panel):
    def __init__(self, app):
        super(NightPanel, self).__init__(app)

        self.time_widget = NightTime(self)
        self.widgets = [self.time_widget]
        self._curr_hour = dt.now().hour
        self._curr_minute = dt.now().minute

    def _on_update(self):
        now = dt.now()
        self.curr_hour = now.hour
        self.curr_minute = now.minute
        self.curr_sec = now.second
        self._auto_set_night()

    def _auto_set_night(self):
        if self.curr_hour == 6 and self.curr_minute == 0 and self.curr_sec == 0:
            self.app.set_active_panel(self.app.main_panel)

    def handle_panel_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.app.set_active_panel(self.app.main_panel)


class NewsPanel(Panel):
    def __init__(self, app):
        super(NewsPanel, self).__init__(app)

        self._news_main_font = pygame.font.SysFont(self.default_font_name, 35)
        self._news_title_font = pygame.font.SysFont(self.default_font_name, 20)
        self.news_widget = Content(self, 10, 10, "News", font=self._news_main_font)
        self.title_widget = Content(self, 90, 10, "", font=self._news_title_font,
                                    max_width=self.screen_width - 100, max_height=30,
                                    borders=['left'], margin=(10, 0, 0, 0))
        self.newslist_widget = NewsList(self, 10, 45, max_width=self.screen_width - 20,
                                        max_height=self.screen_height - 60,
                                        title_widget=self.title_widget)
        self.widgets = [self.news_widget, self.title_widget, self.newslist_widget]

        self.set_active_widget(self.newslist_widget)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.set_active_widget(self.newslist_widget)
            self.active_widget.handle_events(event)

    def _on_enter(self):
        self.set_active_widget(self.newslist_widget)


class SearchPanel(Panel):
    def __init__(self, app):
        super(SearchPanel, self).__init__(app)

        self._search_str_font = pygame.font.Font("fonts/FreeSans.ttf", 18)
        self._search_result_font = pygame.font.Font("fonts/FreeSans.ttf", 16)
        self.search_widget = Search(self, 10, 10, str_font=self._search_str_font,
                                    result_font=self._search_result_font,
                                    max_width=self.screen_width - 40,
                                    max_height=self.screen_height - 40)
        self.widgets = [self.search_widget]

        self.set_active_widget(self.search_widget)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.search_widget)

    def _on_enter(self):
        self.set_active_widget(self.search_widget)

    def _on_exit(self):
        self.search_widget.reset()


class SystemInfoPanel(Panel):
    def __init__(self, app):
        super(SystemInfoPanel, self).__init__(app)

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)
        self._caption_font = pygame.font.Font("fonts/FreeSans.ttf", 13)
        self._info_font = pygame.font.Font("fonts/FreeSans.ttf", 13)

        self._max_size = 120
        self._update_interval = 0.5
        self._cpu_info = queue.Queue(maxsize=self._max_size)
        self._last_cpu_info = 0
        self._memory_info = queue.Queue(maxsize=self._max_size)
        self._system_info = {"CPU": self._cpu_info, "Memory": self._memory_info}
        self._info_colors = {"CPU": "green", "Memory": "yellow"}

        self.title_widget = Content(self, 10, 10, "System Info", font=self._title_font)
        self.chart_widget = Chart(self, 30, 50, info=self._system_info,
                                  width=self.screen_width - 70, height=self.screen_height - 80,
                                  max_x=int(self._max_size * self._update_interval),
                                  info_colors=self._info_colors,
                                  x_unit=self._update_interval, y_unit=1,
                                  x_label_interval=10, y_label_interval=20)
        self._info_widget = SystemInfo(self, 160, 20, font=self._info_font,
                                       cpu_info=False, memory_info=False,
                                       disk_info=False, percent_bar=False)
        self.caption_widget = ChartCaption(self, 360, 10, self._info_colors,
                                           font=self._caption_font)
        self.widgets = [self.title_widget, self.chart_widget, self._info_widget, self.caption_widget]

        self._last_update = time.time()

    def _on_update(self):
        current_time = time.time()
        if self._max_size <= 0 or current_time - self._last_update < self._update_interval:
            return
        if self._cpu_info.full():
            self._cpu_info.get_nowait()
        if self._memory_info.full():
            self._memory_info.get_nowait()

        cpu_info = psutil.cpu_percent()
        if cpu_info == 0:
            cpu_info = self._last_cpu_info
        else:
            self._last_cpu_info = cpu_info
        self._cpu_info.put(cpu_info)
        self._memory_info.put(psutil.virtual_memory().percent)

        self._last_update = current_time


class StockPanel(Panel):
    def __init__(self, app):
        super(StockPanel, self).__init__(app)

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)

        self.title_widget = Content(self, 10, 10, "Stock", font=self._title_font)
        self.stock_widget = Stock(self, 25, 40, chart=True, chart_width=self.screen_width - 80,
                                  chart_height=self.screen_height - 120)
        self.widgets = [self.title_widget, self.stock_widget]

    def _on_enter(self):
        self.set_active_widget(self.stock_widget)

    def _on_exit(self):
        self.stock_widget.clear()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.stock_widget)


class MapPanel(Panel):
    def __init__(self, app):
        super(MapPanel, self).__init__(app)

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)

        self.title_widget = Content(self, 10, 10, "Map", font=self._title_font)
        self.map_widget = Map(self, 10, 45, map_width=400, map_height=170,
                              map_padding=0.075, background_alpha=100)
        self.widgets = [self.title_widget, self.map_widget]

    def _on_enter(self):
        self.set_active_widget(self.map_widget)

    def _on_exit(self):
        self.map_widget.reset()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.map_widget)


class CameraPanel(Panel):
    def __init__(self, app, camera):
        super(CameraPanel, self).__init__(app)

        self.camera_widget = Camera(self, 0, 0, camera)
        self.widgets = [self.camera_widget]

    def _on_enter(self):
        self.set_active_widget(self.camera_widget)


class GamePanel(Panel):
    def __init__(self, app):
        super(GamePanel, self).__init__(app)

        self.title_font = pygame.font.SysFont(self.default_font_name, 35)
        self.title_widget = Content(self, 10, 10, "Game", font=self.title_font)

        self.game_names = []
        self.menu_widget = List(self, 10, 45, items=self.game_names,
                                max_width=400, max_height=260, selectable=True,
                                select_event=self.select_game, reset_on_exit=False)
        self.widgets = [self.title_widget, self.menu_widget]

        self.games = {}
        self._add_game("Snake", GameSnake(self, self.exit_game, total_rows=16, total_cols=16))
        self._add_game("Tetris", GameTetris(self, self.exit_game, total_rows=16, total_cols=10))
        self._add_game("Flip", GameFlip(self, self.exit_game, board_size=10, border_width=1))

    def _add_game(self, name, game):
        self.game_names.append(name)
        self.games[name] = game
        self.widgets.append(game)

    def select_game(self):
        selected_game = self.games.get(self.game_names[self.menu_widget.get_selected()])
        self.set_active_widget(selected_game)

    def exit_game(self):
        self.set_active_widget(self.menu_widget)

    def _on_enter(self):
        self.set_active_widget(self.menu_widget)

    def _on_exit(self):
        self.menu_widget.reset()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.menu_widget)


class CalculatorPanel(Panel):
    def __init__(self, app):
        super(CalculatorPanel, self).__init__(app)

        self.calculator_widget = Calculator(self, 10, 10, width=450, height=300, key_padding=3)

        self.widgets = [self.calculator_widget]

    def _on_enter(self):
        self.set_active_widget(self.calculator_widget)

    def _on_exit(self):
        self.calculator_widget.reset()
