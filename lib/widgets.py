#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import os
import cv2
import math
import glob
import copy
import time
import queue
import pygame
import psutil
import qrcode
import requests
import polyline
import calendar
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime as dt
from abc import ABCMeta, abstractmethod
from string import printable, digits, ascii_letters
from lib.table import Table
from lib.buttons import Button
from lib.threads import RequestThread, ImageFetchThread
from lib.shapes import Rectangle, Text, Line, Lines, DashLine, Polygon, \
    Circle, ScreenSurface
from lib.util import log_to_file, shift_pressed, ctrl_pressed, \
    bytes_to_string, pygame_key_to_char, char_to_pygame_key, \
    get_font_height


class Widget:
    __metaclass__ = ABCMeta

    def __init__(self, parent, x, y):
        self.parent = parent
        self.x = x
        self.y = y

        self.width = 0
        self.height = 0

        self._colors = {"black": (0, 0, 0),
                        "white": (255, 255, 255),
                        "gray": (100, 100, 100),
                        "lightgray": (75, 75, 75),
                        "green": (0, 255, 0),
                        "darkgreen": (50, 205, 50),
                        "red": (255, 0, 0),
                        "blue": (30, 144, 255),
                        "lightblue": (0, 191, 255),
                        "yellow": (255, 255, 0),
                        "orange": (255, 165, 0)}
        self.default_font_name = pygame.font.get_default_font()
        self.default_font = pygame.font.SysFont(self.default_font_name, 25)
        self.is_active = False
        self.draw_subwidgets = True

        self.buttons = []

        self._screen_width = self.parent.screen_width
        self._screen_height = self.parent.screen_height
        self._screen_padding = 3
        self._timeout = None
        self._last_active = time.time()
        self._shapes = []
        self._subwidgets = []
        self._key_binds = {}

    def setup(self):
        for widget in self._subwidgets:
            widget.setup()
        self.clear_shapes()
        self._on_setup()

    def update(self):
        if self._timeout is not None and self.is_active and time.time() - self._last_active > self._timeout:
            self.parent.set_active_widget(None)

        for widget in self._subwidgets:
            widget.update()
        self._on_update()

    def draw(self, screen):
        self._draw_background(screen)
        if self.draw_subwidgets:
            for widget in self._subwidgets:
                widget.draw(screen)
        for shape in self._shapes:
            self._draw_shape(screen, shape)
        for button in self.buttons:
            button.draw(screen)
        self._on_draw(screen)

    def set_align(self, align):
        if align == "top":
            self.set_pos(self.x, self._screen_padding)
        elif align == "bottom":
            self.set_pos(self.x, self._screen_height - self.get_height() - self._screen_padding)
        elif align == "left":
            self.set_pos(self._screen_padding, self.y)
        elif align == "right":
            self.set_pos(self._screen_width - self.get_width() - self._screen_padding, self.y)
        elif align == "center":
            self.set_pos((self._screen_width - self.get_width()) // 2,
                         (self._screen_height - self.get_height()) // 2)

    def set_pos(self, x, y):
        x_offset = x - self.x
        y_offset = y - self.y
        for widget in self._subwidgets:
            new_x = widget.x + x_offset
            new_y = widget.y + y_offset
            widget.set_pos(new_x, new_y)

        for button in self.buttons:
            new_x = button.x + x_offset
            new_y = button.y + y_offset
            button.set_pos(new_x, new_y)

        self.x = x
        self.y = y
        self.setup()

    def set_timeout(self, timeout):
        if timeout > 0 or timeout is None:
            self._timeout = timeout

    def _get_color(self, color):
        color_code = self._colors.get(color)
        if color_code is None:
            return 255, 255, 255
        return color_code

    @abstractmethod
    def _on_setup(self):
        pass

    @abstractmethod
    def _on_update(self):
        pass

    @abstractmethod
    def _on_draw(self, screen):
        pass

    def _draw_background(self, screen):
        pass

    def _handle_widget_events(self, event):
        pass

    def _on_enter(self):
        pass

    def _on_exit(self):
        pass

    def _draw_shape(self, screen, shape):
        if isinstance(shape, Line):
            pygame.draw.line(screen, shape.color, shape.start_pos, shape.end_pos, shape.width)
        elif isinstance(shape, DashLine):
            for line in shape.lines:
                self._draw_shape(screen, line)
        elif isinstance(shape, Lines):
            if shape.anti_alias:
                try:
                    pygame.draw.aalines(screen, shape.color, shape.closed, shape.pointlist, shape.width)
                except ValueError:
                    pygame.draw.lines(screen, shape.color, shape.closed, shape.pointlist, shape.width)
            else:
                pygame.draw.lines(screen, shape.color, shape.closed, shape.pointlist, shape.width)
            for point in shape.pointlist:
                screen.set_at(point, shape.color)
        elif isinstance(shape, Text):
            screen.blit(shape.text_surface, shape.pos)
        elif isinstance(shape, Rectangle):
            if shape.alpha is None:
                pygame.draw.rect(screen, shape.color, shape.to_pygame_rect(), shape.line_width)
            else:
                self._draw_transparent_rect(screen, shape.x, shape.y, shape.width, shape.height,
                                            shape.alpha, color=shape.color)
        elif isinstance(shape, Polygon):
            pygame.draw.polygon(screen, shape.color, shape.pointlist, shape.width)
        elif isinstance(shape, Circle):
            pygame.draw.circle(screen, shape.color, shape.pos, shape.radius, shape.width)
        elif isinstance(shape, ScreenSurface):
            screen.blit(shape.surface, shape.pos)

    def _draw_transparent_rect(self, screen, x, y, width, height, alpha, color=(255, 255, 255)):
        rect_surface = pygame.Surface((width, height))
        rect_surface.fill(color)
        rect_surface.set_alpha(alpha)
        screen.blit(rect_surface, (x, y))

    def enter(self):
        for button in self.buttons:
            button.set_active(True)

        self._on_enter()

    def exit(self):
        for button in self.buttons:
            button.set_active(False)

        self._on_exit()

    def add_shape(self, shape):
        self._shapes.append(shape)

    def clear_shapes(self):
        self._shapes = []

    def get_pos(self):
        return self.x, self.y

    def add_offset(self, x_offset, y_offset):
        self.x += x_offset
        self.y += y_offset

        for shape in self._shapes:
            shape.add_offset(x_offset, y_offset)

        for widget in self._subwidgets:
            widget.add_offset(x_offset, y_offset)

        for button in self.buttons:
            button.add_offset(x_offset, y_offset)

    def handle_events(self, event):
        self._last_active = time.time()

        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.is_focused():
                    button.click()
                    return True

        for widget in self._subwidgets:
            if widget.is_active:
                widget.handle_events(event)
                return True

        handled = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.is_active:
                self.set_active(False)
                handled = True
            elif self._key_binds.get(event.key) is not None and self.is_active:
                bind = self._key_binds[event.key]
                if (shift_pressed() == bind['shift']) and (ctrl_pressed() == bind['ctrl']):
                    bind['func']()
                    handled = True

        self._handle_widget_events(event)
        return handled

    def set_active(self, status):
        if self.is_active != status:
            self.is_active = status
            if status:
                self._last_active = time.time()
                self.enter()
            else:
                self.exit()

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def bind_key(self, key, func, shift=False, ctrl=False):
        self._key_binds[key] = {'func': func, 'shift': shift, 'ctrl': ctrl}


class News(Widget):
    def __init__(self, parent, x, y):
        super(News, self).__init__(parent, x, y)

        self._news_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._message_font = pygame.font.Font("fonts/FreeSans.ttf", 20)
        self._news_url = "https://newsapi.org/v2/top-headlines"
        self._news_key = "6f19ade7dcd846ef95d927341765f200"
        self._news_payload = {"sources": "google-news-ca", "apiKey": self._news_key}
        self._news_last_update = time.time()
        self._news_index_last_update = time.time()
        self._news_index = 0
        self._news_info_update_interval = 1800
        self._news_line_update_interval = 15
        self._news_info = None
        self._title_max_width = self._screen_width - self.x - 20

    def _get_news(self):
        res = requests.get(self._news_url, params=self._news_payload)
        response = res.json()
        if response.get("status") == "ok":
            self._news_info = response.get("articles")
            self._news_index = 0

        log_to_file("News updated")

    def _on_setup(self):
        self._get_news()

    def _on_update(self):
        curr_time = time.time()
        if curr_time - self._news_last_update > self._news_info_update_interval or self._news_info is None:
            self._get_news()
            self._news_last_update = curr_time

        if curr_time - self._news_index_last_update > self._news_line_update_interval and self._news_info:
            self._news_index += 1
            if self._news_index == len(self._news_info):
                self._news_index = 0
            self._news_index_last_update = curr_time

    def _on_draw(self, screen):
        if self._news_info:
            article = self._news_info[self._news_index]
            title = article.get("title")
            title_text = self._news_font.render(title, True, self._get_color('white'))
            if title_text.get_width() > self._title_max_width:
                words = title.split(' ')
                brief_title = words[0]
                current_width = self._news_font.render(brief_title, True, self._get_color('white')).get_width()
                space_width = self._news_font.render(' ', True, self._get_color('white')).get_width()
                dots_width = self._news_font.render('...', True, self._get_color('white')).get_width()
                for word in words[1:]:
                    word_width = self._news_font.render(word, True, self._get_color('white')).get_width()
                    if current_width + word_width + space_width + dots_width < self._title_max_width:
                        brief_title += ' ' + word
                        current_width += word_width + space_width
                    else:
                        break
                title_text = self._news_font.render(brief_title + "...", True, self._get_color('white'))

            screen.blit(title_text, (self.x + 20, self.y))

            percent = (float(time.time()) - self._news_index_last_update) / self._news_line_update_interval
            pygame.draw.arc(screen, self._get_color('green'), (self.x + 5, self.y + 5, 10, 10), math.pi * (0.5 - percent * 2), math.pi * 0.5, 2)


class NewsList(News):
    def __init__(self, parent, x, y, max_width=480, max_height=320, title_widget=None):
        super(NewsList, self).__init__(parent, x, y)

        self.max_width = max_width
        self.max_height = max_height
        self.width = max_width
        self.height = max_height
        self.title_widget = title_widget
        self._background_alpha = 120
        self._news_title_font = pygame.font.Font("fonts/FreeSans.ttf", 17)
        self._prefix = " - "
        self._news_image_directory = "news_images"
        self._title_contents = []
        self._display_lines = []
        self._display_count = 0
        self._start_index = 0
        self._active_index = 0
        self._sidebar_width = 6
        self._sidebar_length = int(self.max_height * 0.618)
        self._active_news = False
        self._display_image = False
        self._images = {}

    def _on_exit(self):
        self._active_news = False
        self._display_image = False
        self._parse_news()

    def _get_news(self):
        super(NewsList, self)._get_news()

        self._title_contents = []
        start_x, start_y = self.x, self.y
        for news in self._news_info:
            title = news.get("title")
            title_content = Content(self.parent, start_x, start_y, title,
                                    font=self._news_title_font, max_width=self.max_width,
                                    max_height=self.max_height, prefix=self._prefix)
            title_content.setup()
            start_y += title_content.get_height()
            self._title_contents.append(title_content)

            image_url = news.get("urlToImage")
            news['imageName'] = self._parse_image_name(image_url) if image_url else ""
            if not image_url:
                continue

            if image_url:
                if not os.path.isdir(self._news_image_directory):
                    os.mkdir(self._news_image_directory)
                image_thread = ImageFetchThread(image_url, news, self._news_image_directory)
                image_thread.daemon = True
                image_thread.start()

    def _parse_news(self):
        self.clear_shapes()
        self._display_lines = []
        self._display_count = 0
        total_height = 0
        is_full = False
        for title_ind, content in enumerate(self._title_contents[self._start_index:]):
            for line_ind, content_line in enumerate(content.get_lines()):
                total_height += content_line.get_height()
                if total_height > self.max_height:
                    is_full = True
                    break
                self._display_lines.append(content_line)
                if self._active_news and title_ind + self._start_index == self._active_index:
                    prefix_length = self._news_title_font.render(self._prefix, True, self._get_color('white')).get_width()
                    text_length = content_line.get_width()
                    start_pos = (self.x + prefix_length, self.y + total_height)
                    end_pos = (self.x + text_length, self.y + total_height)
                    self.add_shape(Line(self._get_color('green'), start_pos, end_pos))
                if line_ind == len(content.get_lines()) - 1:
                    self._display_count += 1
            if is_full:
                break

    def _page_up(self):
        if self._start_index > 0:
            self._start_index -= 1
            self._parse_news()

    def _page_down(self):
        if len(self._display_lines) < sum([len(content.get_lines()) for content in self._title_contents[self._start_index:]]):
            self._start_index += 1
            self._parse_news()

    def _row_up(self):
        if self._active_index > 0:
            self._active_index -= 1
            if self._start_index > self._active_index:
                self._page_up()
            self._parse_news()

    def _row_down(self):
        if self._active_index < len(self._title_contents) - 1:
            self._active_index += 1
            while self._start_index + self._display_count - 1 < self._active_index:
                self._page_down()
            self._parse_news()

    def _on_setup(self):
        self._get_news()
        self._parse_news()

    def _on_update(self):
        curr_time = time.time()
        if curr_time - self._news_last_update > self._news_info_update_interval or self._news_info is None:
            self._get_news()
            self._parse_news()
            self._news_last_update = curr_time

    def _on_draw(self, screen):
        total_height = 0
        for ind, line in enumerate(self._display_lines):
            screen.blit(line, (self.x, self.y + total_height))
            total_height += line.get_height()

        # draw sidebar
        if len(self._display_lines) < sum([len(content.get_lines()) for content in self._title_contents]):
            pre_length = self._start_index * self.max_height // len(self._news_info)
            sidebar_start = (self.x + self.max_width, self.y + pre_length)
            sidebar_end = (self.x + self.max_width, self.y + pre_length + self._sidebar_length)
            if sidebar_end[1] > self.y + self.max_height:
                sidebar_end = (sidebar_end[0], self.y + self.max_height)
            pygame.draw.line(screen, self._get_color('white'), sidebar_start, sidebar_end, self._sidebar_width)
            pygame.draw.line(screen, self._get_color('white'),
                             (self.x + self.max_width - self._sidebar_width // 2, self.y),
                             (self.x + self.max_width + self._sidebar_width // 2, self.y), 1)
            pygame.draw.line(screen, self._get_color('white'),
                             (self.x + self.max_width - self._sidebar_width // 2, self.y + self.max_height),
                             (self.x + self.max_width + self._sidebar_width // 2, self.y + self.max_height), 1)
            if self.is_active:
                pygame.draw.rect(screen, self._get_color('white'),
                                 (self.x, self.y, self.get_width(), self.get_height()), 1)

        # draw image
        if self._display_image:
            if self.title_widget:
                self.title_widget.set_text(self._news_info[self._active_index]['title'])
            pygame.draw.rect(screen, self._get_color('blue'), (self.x, self.y, self.max_width, self.max_height), 3)
            image = None
            image_url = self._news_info[self._active_index]['urlToImage']
            if image_url:
                image_name = self._news_info[self._active_index]['imageName']
                image_path = os.path.join("news_images", image_name)
                if self._images.get(image_name) is not None:
                    image = self._images.get(image_name)
                elif os.path.isfile(image_path):
                    try:
                        image = pygame.image.load(image_path)
                    except pygame.error:
                        image = None
                    if image:
                        image_width, image_height = image.get_size()
                        ratio = self.max_width / self.max_height
                        image_ratio = image_width / image_height
                        if ratio > image_ratio:
                            scaled_width = int(self.max_height * image_ratio)
                            scaled_height = self.max_height
                        else:
                            scaled_width = self.max_width
                            scaled_height = int(self.max_width / image_ratio)
                        image = pygame.transform.scale(image, (scaled_width, scaled_height))
                        image = image.convert()
                        self._images[image_name] = image

                if image:
                    image_width, image_height = image.get_size()
                    image_x = self.x + (self.max_width - image_width) // 2
                    image_y = self.y + (self.max_height - image_height) // 2
                    pygame.draw.rect(screen, self._get_color('black'), (self.x, self.y, self.max_width, self.max_height))
                    screen.blit(image, (image_x, image_y))
                else:
                    self._draw_no_image_message(screen)
            else:
                self._draw_no_image_message(screen)
        elif self.title_widget:
            self.title_widget.set_text("")
    
    def _draw_background(self, screen):
        self._draw_transparent_rect(screen, self.x, self.y, self.get_width(), self.get_height(), self._background_alpha,
                                    color=self._get_color('lightgray'))

    def _draw_no_image_message(self, screen):
        pygame.draw.rect(screen, self._get_color('black'), (self.x, self.y, self.max_width, self.max_height), 0)
        message_text = self._message_font.render("No image to show here...", True, self._get_color('white'))
        screen.blit(message_text, (self.x + (self.max_width - message_text.get_width()) // 2,
                                   self.y + (self.max_height - message_text.get_height()) // 2))

    def _parse_image_name(self, image_url):
        image_name = image_url.split('/')[-1]
        image_name = '.'.join(image_name.split('.')[-2:])
        image_name = image_name.lower()
        q_ind = image_name.find('?')
        if q_ind != -1:
            image_name = image_name[:q_ind]
        return image_name

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                if not self._active_news:
                    self._page_down()
                else:
                    self._row_down()
            elif event.key == pygame.K_UP:
                if not self._active_news:
                    self._page_up()
                else:
                    self._row_up()
            elif event.key == pygame.K_RETURN:
                if self._active_news and self._display_image:
                    self._display_image = False
                    if self.title_widget:
                        self.title_widget.set_text("")
                elif self._active_news:
                    self._display_image = True
                elif not self._active_news:
                    self._active_news = True
                    self._active_index = self._start_index
                    self._parse_news()
    
    def get_width(self):
        return self.width + self._sidebar_width


class Weather(Widget):
    def __init__(self, parent, x, y):
        super(Weather, self).__init__(parent, x, y)

        self.weather_font = pygame.font.Font("fonts/FreeSans.ttf", 50)
        self.degree_font = pygame.font.Font("fonts/FreeSans.ttf", 35)
        self.forecast_font = pygame.font.Font("fonts/FreeSans.ttf", 25)
        self.desc_font = pygame.font.Font("fonts/FreeSans.ttf", 25)
        self.digit_font = pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.change_font = pygame.font.Font("fonts/FreeSans.ttf", 16)
        self.last_update_font = pygame.font.Font("fonts/FreeSans.ttf", 10)

        self._weather_last_update = time.time()
        self._current_weather = None
        self._forecast_weather = None
        self._weather_update_interval = 1800
        self._weather_x = self.x
        self._weather_y = self.y
        self._perc_bar_length = int(get_font_height(self.weather_font) * 0.7)
        self._perc_bar_width = 10
        self._perc_bar_padding = 5

        self._weather_key = "508b76be5129c25115e5e60848b4c20c"
        self._current_url = "http://api.openweathermap.org/data/2.5/weather"
        self._forecase_url = "http://api.openweathermap.org/data/2.5/forecast"
        self._weather_payload = {"q": "Waterloo,ca", "appid": self._weather_key,
                                 "units": "metric"}
        self._waterloo_key = "97a591e399f591e64a5f4536d08d9574"

        self._current_icon_size = 35
        self._change_icon_size = 25
        self._perc_icon_size = 18
        self._icon_directory = os.path.join("images", "weather")
        self._current_icons = {}
        self._change_icons = {}
        self._perc_icons = {}

    def _get_weather(self):
        current_res = requests.get(self._current_url, params=self._weather_payload)
        self._current_weather = current_res.json()

        forecast_res = requests.get(self._forecase_url, params=self._weather_payload)
        self._forecast_weather = forecast_res.json()

        self._weather_last_update = time.time()
        self._parse_info()

        log_to_file("Weather updated")

    def _parse_info(self):
        try:
            current_desc = self._current_weather['weather'][0]['main']
            current_temp = int(self._current_weather['main']['temp'])
            current_str = u"{}".format(current_temp)
            current_icon = self._current_icons[self._current_weather['weather'][0]['icon']]
            current_humidity = self._current_weather['main']['humidity']
            current_clouds = self._current_weather['clouds']['all']
            forecast_temp = [int(pred['main']['temp']) for pred in self._forecast_weather['list'][:8]]
        except KeyError:
            self._current_weather = None
            self._forecast_weather = None
            return

        self.clear_shapes()

        forecast_min = min(forecast_temp)
        forecast_max = max(forecast_temp)
        forecast_str = u"{} - {}℃".format(forecast_min, forecast_max)

        desc_text = self.desc_font.render(current_desc, True, self._get_color('white'))
        current_text = self.weather_font.render(current_str, True, self._get_color('white'))
        degree_text = self.degree_font.render('℃', True, self._get_color('white'))
        forecast_text = self.forecast_font.render(forecast_str, True, self._get_color('white'))

        self.add_shape(Text(desc_text, (self.x, self.y)))
        self.add_shape(Text(current_icon, (self.x + desc_text.get_width(), self.y)))
        self.add_shape(Text(current_text, (self.x, self.y + desc_text.get_height())))
        self.add_shape(Text(degree_text, (self.x + current_text.get_width() + 5,
                                          self.y + desc_text.get_height() + 5)))
        self.add_shape(Text(forecast_text, (self.x, self.y + desc_text.get_height()
                                            + current_text.get_height())))

        # add humidity info
        humidity_text = self.digit_font.render("{}%".format(current_humidity), True, self._get_color('white'))
        humidity_x = self.x + max(current_text.get_width() + degree_text.get_width() + 10,
                                  forecast_text.get_width()) + 10
        humidity_y = self.y + desc_text.get_height() + current_text.get_height() - humidity_text.get_height()
        self.add_shape(Rectangle(self._get_color('lightgray'), humidity_x, humidity_y,
                                 humidity_text.get_width(), humidity_text.get_height(),
                                 line_width=0, alpha=180))
        self.add_shape(Text(humidity_text, (humidity_x, humidity_y)))

        humidity_bar_x = humidity_x + (humidity_text.get_width() - self._perc_bar_width) // 2
        humidity_bar_y = humidity_y - self._perc_bar_length
        self._add_percent_bar(current_humidity, humidity_bar_x, humidity_bar_y - self._perc_bar_padding,
                              width=self._perc_bar_width, length=self._perc_bar_length,
                              color=self._get_color('lightblue'))

        humidity_icon_x = humidity_x + (humidity_text.get_width() - self._perc_icon_size) // 2
        humidity_icon_y = humidity_y + humidity_text.get_height()
        self.add_shape(ScreenSurface(self._perc_icons['water'], (humidity_icon_x, humidity_icon_y)))

        # add clouds info
        clouds_text = self.digit_font.render("{}%".format(current_clouds), True, self._get_color('white'))
        clouds_x = humidity_x + humidity_text.get_width() + 5
        clouds_y = humidity_y
        self.add_shape(Rectangle(self._get_color('lightgray'), clouds_x, clouds_y,
                                 clouds_text.get_width(), clouds_text.get_height(),
                                 line_width=0, alpha=180))
        self.add_shape(Text(clouds_text, (clouds_x, clouds_y)))

        clouds_bar_x = clouds_x + (clouds_text.get_width() - self._perc_bar_width) // 2
        clouds_bar_y = clouds_y - self._perc_bar_length
        self._add_percent_bar(current_clouds, clouds_bar_x, clouds_bar_y - self._perc_bar_padding,
                              width=self._perc_bar_width, length=self._perc_bar_length,
                              color=self._get_color('orange'))

        clouds_icon_x = clouds_x + (clouds_text.get_width() - self._perc_icon_size) // 2
        clouds_icon_y = clouds_y + clouds_text.get_height()
        self.add_shape(ScreenSurface(self._perc_icons['cloud'], (clouds_icon_x, clouds_icon_y)))

        # add change info
        change_info = []
        change_count = 0
        for pred in self._forecast_weather['list'][:8]:
            if change_count == 3:
                break
            pred_desc = pred['weather'][0]['main']
            icon_id = pred['weather'][0]['icon']
            if (not change_info and pred_desc != current_desc) or \
               (change_info and pred_desc != change_info[-1][0]):
                change_text = "{} -> {} ".format(pred['dt_txt'][11:16], pred_desc)
                rendered_text = self.change_font.render(change_text, True, self._get_color('white'))
                change_info.append((pred_desc, rendered_text, icon_id))
                change_count += 1

        x = self.x
        y = self.y + desc_text.get_height() + current_text.get_height() + forecast_text.get_height() + 5
        max_text_width = max([info[1].get_width() for info in change_info]) if change_info else 0
        for text, rendered_text, icon_id in change_info:
            self.add_shape(Text(rendered_text, (x, y)))
            self.add_shape(ScreenSurface(self._change_icons[icon_id], (x + max_text_width, y)))
            y += rendered_text.get_height()

        self._weather_x = x
        self._weather_y = y

    def _add_percent_bar(self, perc, x, y, width=10, length=30, color=(255, 255, 255), intervals=4):
        bar_length = int(length * perc / 100)
        self.add_shape(Rectangle(color, x, y + length - bar_length, width, bar_length, line_width=0))
        self.add_shape(Line(self._get_color('white'), (x, y), (x, y + length)))

        interval_length = length // intervals
        for i in range(intervals + 1):
            interval_y = y + i * interval_length
            if i == intervals:
                interval_y = y + length
            start_pos = (x, interval_y)
            end_pos = (x + width // 2, interval_y)
            self.add_shape(Line(self._get_color('white'), start_pos, end_pos))

    def _load_icons(self):
        for icon_path in glob.glob(os.path.join(self._icon_directory, "*.png")):
            icon_name = icon_path.split('/')[-1].split('.')[0]
            icon = pygame.image.load(icon_path)
            if re.match(r'\d+[dn]', icon_name):
                current_icon = pygame.transform.scale(icon, (self._current_icon_size, self._current_icon_size))
                change_icon = pygame.transform.scale(icon, (self._change_icon_size, self._change_icon_size))
                self._current_icons[icon_name] = current_icon.convert_alpha()
                self._change_icons[icon_name] = change_icon.convert_alpha()
            else:
                self._perc_icons[icon_name] = icon.convert_alpha()

    def _on_setup(self):
        self._load_icons()
        self._get_weather()

    def _on_update(self):
        if (time.time() - self._weather_last_update > self._weather_update_interval
                or self._current_weather is None
                or self._forecast_weather is None):
            self._get_weather()

    def _on_draw(self, screen):
        # draw last update time
        last_update_mins = int((time.time() - self._weather_last_update) / 60)
        last_update_text = "Last Update: {} min ago".format(last_update_mins)
        rendered_last_update_text = self.last_update_font.render(last_update_text, True, self._get_color('white'))
        screen.blit(rendered_last_update_text, (self._weather_x, self._weather_y))


class Calendar(Widget):
    def __init__(self, parent, x, y, max_rows=-1, max_past_days=-1, timeout=10, align=None, max_name_length=None):
        super(Calendar, self).__init__(parent, x, y)

        self.max_rows = max_rows
        self.max_past_days = max_past_days
        self.header_font = pygame.font.Font("fonts/arial.ttf", 18)
        self.content_font = pygame.font.Font("fonts/arial.ttf", 16)
        self.timeout = timeout
        self.align = align
        self.max_name_length = max_name_length

        self.set_timeout(self.timeout)

        self._background_alpha = 120
        self._background_alpha_active = 180

        self._calendar_file = "calendars/calendar.xml"
        self._calendar_titles = []
        self._parsed_calendar = []
        self._parsed_calendar_display = []
        self._calendar_table = None
        self._calendar_last_update = dt.now().day
        self._calendar_selected_row = 0

        self._text_cal = TextCalendar(parent, self.x, self.y)
        self._text_cal.setup()
        self._text_cal_mode = False

        self._delete_mode = False
        self._selected_color = self._get_color('green')

        self._load_calendar()
        self._load_table()
        if self._calendar_table.is_empty():
            self._text_cal_mode = True
        self.set_align(self.align)

    def _load_calendar(self):
        current_day = dt.now().day
        with open(self._calendar_file, 'r') as file:
            calendar_text = file.read()
            file.close()

        # parse html file into a BeautifulSoup object
        soup = BeautifulSoup(calendar_text, 'xml')
        calendar_table = soup.find('table')

        # get table rows
        status_tags = calendar_table.find_all('status')
        events = calendar_table.find_all('event')
        titles = calendar_table.find('tr').find_all('th')
        title_texts = [tag.get_text() for tag in titles]
        content_rows = [[event.find('name'), event.find('date')] for event in events]

        # add contents to list
        self._parsed_calendar = []
        calendar_status = []

        self._calendar_titles = [text for text in title_texts] + ["Days"]
        for status_tag in status_tags:
            calendar_status.append(status_tag.get_text())

        for content_row in content_rows:
            self._parsed_calendar.append([content.get_text() for content in content_row])

        self._add_days_col(self._parsed_calendar, calendar_status)

        self._parsed_calendar.sort(key=lambda x: (int(x[-2]), int(x[-1])))
        self._parsed_calendar_display = copy.deepcopy(self._parsed_calendar)

        if self.max_past_days != -1:
            self._parsed_calendar_display = [row for row in self._parsed_calendar_display
                                             if row[-1] == '1' or int(row[-2]) >= -self.max_past_days]

        if self.max_rows != -1:
            self._parsed_calendar_display = self._parsed_calendar_display[:self.max_rows]

        self._calendar_last_update = current_day
        log_to_file("Calendar updated")

    def _add_days_col(self, calendar, status):
        try:
            time_ind = self._calendar_titles.index("Date")
        except NameError:
            return

        curr_date = dt.today().replace(hour=0, minute=0, second=0, microsecond=0)
        for ind, row in enumerate(calendar):
            # convert string to datetime object
            try:
                date = dt.strptime(row[time_ind], "%Y-%m-%d")
                date = date.replace(hour=0, minute=0)
                diff_date = date - curr_date

                row.append(str(diff_date.days))
            except ValueError:
                row.append("")
                row.append(status[ind])
                continue

            row.append(status[ind])

    def _open_calendar_file(self):
        with open(self._calendar_file, 'r') as f:
            soup = BeautifulSoup(f.read(), features='lxml')
        return soup

    def _save_calendar_file(self, soup):
        with open(self._calendar_file, 'w') as file:
            file.write(str(soup))
            file.close()

    def _toggle_calendar_row_status(self, row_index):
        self._parsed_calendar_display[row_index][-1] = '0' if self._parsed_calendar_display[row_index][-1] == '1' else '1'

        target_name = self._parsed_calendar_display[row_index][0]
        if target_name.endswith('...'):
            target_name = target_name[:-3]
        soup = self._open_calendar_file()
        events = soup.find_all('event')
        for row_tag in events:
            row_name = row_tag.find('name').get_text()
            if row_name.startswith(target_name):
                row_tag.find('status').string = self._parsed_calendar_display[row_index][-1]
                break

        self._save_calendar_file(soup)
        self.reload_calendar()

    def _add_event_from_popup(self):
        e = self.parent.popup.get_input()
        status = '0' if e.get('Active') is False else '1'

        new_soup = BeautifulSoup('<event></event>', features='lxml')
        row_tag = new_soup.event
        name_tag = new_soup.new_tag('name')
        name_tag.string = e['Event']
        row_tag.append(name_tag)
        date_tag = new_soup.new_tag('date')
        date_tag.string = e['Date']
        row_tag.append(date_tag)
        status_tag = new_soup.new_tag('status')
        status_tag.string = status
        row_tag.append(status_tag)

        soup = self._open_calendar_file()
        table = soup.find('tbody')
        table.append(row_tag)

        self._save_calendar_file(soup)
        self.reload_calendar()

    def _edit_event_from_popup(self, row_ind):
        self._delete_event(row_ind, reload=False)
        self._add_event_from_popup()

    def _delete_event(self, row_ind, reload=True):
        self._calendar_selected_row = row_ind
        target = self._get_selected_event()
        target_name = target[0]
        target_date = target[1]
        target_status = target[-1]

        soup = self._open_calendar_file()
        events = soup.find_all('event')
        for row_tag in events:
            row_name = row_tag.find('name').get_text()
            row_date = row_tag.find('date').get_text()
            row_status = row_tag.find('status').get_text()
            is_alter = (target_name.endswith('...') and row_name.startswith(target_name[:-3]))
            if ((row_name, row_date, row_status) == (target_name, target_date, target_status)
                    or is_alter):
                row_tag.extract()

        self._save_calendar_file(soup)
        if reload:
            self.reload_calendar()

    def _get_selected_event(self):
        return self._parsed_calendar_display[self._calendar_selected_row]

    def _toggle_text_calendar(self):
        self._text_cal_mode = not self._text_cal_mode
        self._text_cal.is_active = self._text_cal_mode
        self.reload_calendar()

    def _toggle_delete_mode(self):
        self._delete_mode = not self._delete_mode
        if self._delete_mode:
            self._selected_color = self._get_color('red')
        else:
            self._selected_color = self._get_color('green')
        self._load_table()

    def _load_table(self):
        if self._text_cal_mode:
            return

        if self.max_name_length is not None:
            for row in self._parsed_calendar_display:
                if len(row[0]) > self.max_name_length:
                    row[0] = row[0][:self.max_name_length] + "..."

        calendar_contents = [row[:-1] for row in self._parsed_calendar_display]
        calendar_status = [bool(int(row[-1])) for row in self._parsed_calendar_display]
        self._calendar_table = Table(calendar_contents, titles=self._calendar_titles,
                                     header_font=self.header_font, content_font=self.content_font,
                                     x=self.x, y=self.y, content_centered=[False, False, True], x_padding=2,
                                     selected=self.is_active, selected_row=self._calendar_selected_row,
                                     selected_line_color=self._selected_color, row_status=calendar_status)

        self._shapes = self._calendar_table.get_shapes()

    def _on_setup(self):
        self._load_table()

    def _on_update(self):
        current_day = dt.now().day
        if current_day != self._calendar_last_update:
            self.reload_calendar()

        self._text_cal.update()

    def _on_draw(self, screen):
        if self._text_cal_mode:
            self._text_cal.draw(screen)
        elif self.is_active and self._calendar_table:
            self._calendar_table.draw(screen)

    def _on_enter(self):
        self._calendar_selected_row = 0
        if self._delete_mode:
            self._delete_mode = False
            self._selected_color = self._get_color('green')

        self._calendar_last_active = time.time()
        if self._text_cal_mode:
            self._text_cal.is_active = True
        
        self._load_table()

    def _on_exit(self):
        self._text_cal.reset()
        self._text_cal.is_active = False
        self._load_table()

    def _draw_background(self, screen):
        if self.is_active:
            alpha = self._background_alpha_active
        else:
            alpha = self._background_alpha

        self._draw_transparent_rect(screen, self.x, self.y,
                                    self.get_width(), self.get_height(), alpha,
                                    color=self._get_color('lightgray'))

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if self._text_cal_mode and self._text_cal:
                self._text_cal.handle_events(event)
            elif not self._text_cal_mode:
                if event.key == pygame.K_UP:
                    if self._parsed_calendar_display:
                        self._calendar_selected_row = max(self._calendar_selected_row - 1, 0)
                        self._load_table()
                elif event.key == pygame.K_DOWN:
                    if self._parsed_calendar_display:
                        self._calendar_selected_row = min(self._calendar_selected_row + 1,
                                                          len(self._parsed_calendar_display) - 1)
                        self._load_table()
                elif event.key == pygame.K_RETURN:
                    if self._delete_mode:
                        target = self._get_selected_event()
                        self.parent.create_popup('confirm', self.parent, 300, 200,
                                                 'Are you sure you want to delete "{}"?'.format(target[0]),
                                                 actions={"Yes": lambda: self._delete_event(self._calendar_selected_row),
                                                          "No": None}, default_action="Yes")
                        self.parent.popup.set_title('Delete Event')
                    else:
                        self._toggle_calendar_row_status(self._calendar_selected_row)

            if event.key == pygame.K_t:
                self._toggle_text_calendar()
            elif event.key == pygame.K_a:
                self.parent.create_popup('input', self.parent, 300, 200, input_width=150,
                                         text="Please enter event:", entries=["Event", "Date"],
                                         required=[True, r'^\d{4}-\d{2}-\d{2}$'],
                                         close_action=self._add_event_from_popup)
                self.parent.popup.set_title('Add New Event')
            elif event.key == pygame.K_e:
                if self._calendar_selected_row < len(self._parsed_calendar_display):
                    target = self._get_selected_event()
                    active_status = target[-1] == '1'
                    self.parent.create_popup('input', self.parent, 300, 230, input_width=150,
                                             text="Please enter event:", entries=["Event", "Date", "Active"],
                                             styles=['input', 'input', 'selector'],
                                             values=target[:2] + [active_status],
                                             required=[True, r'^\d{4}-\d{2}-\d{2}$'],
                                             close_action=lambda: self._edit_event_from_popup(self._calendar_selected_row))
                    self.parent.popup.set_title('Edit Event')

                if self._delete_mode:
                    self._toggle_delete_mode()
            elif event.key == pygame.K_d:
                self._toggle_delete_mode()

    def reload_calendar(self):
        if self._text_cal_mode:
            self._text_cal.set_events(self._parsed_calendar)
        else:
            self._load_calendar()
            self._load_table()
        self.set_align(self.align)

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.setup()
        self._text_cal.set_pos(x, y)

    def get_width(self):
        if self._text_cal_mode:
            return self._text_cal.get_width()
        elif self._calendar_table:
            return self._calendar_table.get_width()
        else:
            return 0

    def get_height(self):
        if self._text_cal_mode:
            return self._text_cal.get_height()
        elif self._calendar_table:
            return self._calendar_table.get_height()
        else:
            return 0


class TextCalendar(Widget):
    def __init__(self, parent, x, y):
        super(TextCalendar, self).__init__(parent, x, y)

        self.calendar_font = pygame.font.Font("fonts/LiberationMono.ttf", 18)

        space_text = self.calendar_font.render(' ', True, self._get_color('white'))
        date_text = self.calendar_font.render('00', True, self._get_color('white'))
        self._cal_font_width = space_text.get_width()
        self._cal_font_height = space_text.get_height()
        self._cal_date_width = date_text.get_width()
        self._cal_date_height = date_text.get_height()

        self._cal_last_update = dt.now().day
        self._cal = calendar.TextCalendar()
        self._cal_date_padding = 1
        self._cal_selector_line_width = 2
        self._cal_text_color = self._get_color('white')
        self._cal_selector_color = self._get_color('green')
        self._cal_event_color = self._get_color('orange')
        self._cal_completed_event_color = self._get_color('lightblue')
        self._cal_arrow_color = self._get_color('gray')
        self._cal_arrow_pressed_color = self._get_color('white')
        self._cal_text_lines = []

        self._events = []

        self._total_width = 0
        self._total_height = 0

        self._curr_year = 0
        self._curr_month = 0
        self._curr_day = 0

    def _on_setup(self):
        self._reset_date()
        self._load_cal()

    def _on_update(self):
        curr_day = dt.now().day
        if curr_day != self._cal_last_update:
            self._reset_date()
            self._load_cal()
            self._cal_last_update = curr_day

    def _on_draw(self, screen):
        if self.is_active and self._cal_text_lines:
            left_arrow_pos = [(self.x + 1, self.y + self._cal_font_height // 2),
                              (self.x + self._cal_font_width - 1, self.y + 3),
                              (self.x + self._cal_font_width - 1, self.y + self._cal_font_height - 3)]
            right_arrow_pos = [(self.x + self._total_width - 1, self.y + self._cal_font_height // 2),
                               (self.x + self._total_width - self._cal_font_width + 1, self.y + 3),
                               (self.x + self._total_width - self._cal_font_width + 1, self.y + self._cal_font_height - 3)]

            pressed = pygame.key.get_pressed()
            left_color = self._cal_arrow_pressed_color if pressed[pygame.K_LEFT] else self._cal_arrow_color
            right_color = self._cal_arrow_pressed_color if pressed[pygame.K_RIGHT] else self._cal_arrow_color

            pygame.draw.polygon(screen, left_color, left_arrow_pos)
            pygame.draw.polygon(screen, right_color, right_arrow_pos)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self._next_month()
            elif event.key == pygame.K_LEFT:
                self._last_month()
            elif event.key == pygame.K_r:
                self._reset_month()

    def _reset_date(self):
        now = dt.now()
        self._curr_year = now.year
        self._curr_month = now.month
        self._curr_day = now.day

    def _load_cal(self):
        self.clear_shapes()
        self._total_width = 0
        self._total_height = 0

        self._cal_text_lines = self._cal.formatmonth(self._curr_year, self._curr_month).splitlines()

        offset_x = 0
        offset_y = 0
        now = dt.now()
        is_present_month = (self._curr_year == now.year and self._curr_month == now.month)
        days_with_events = [(str(int(event[1][8:10])), event[-1]) for event in self._events
                            if int(event[1][:4]) == self._curr_year
                            and int(event[1][5:7]) == self._curr_month]
        event_ind = 0
        for line in self._cal_text_lines:
            rendered_line = self.calendar_font.render(line, True, self._cal_text_color)
            self.add_shape(Text(rendered_line, (self.x, self.y + offset_y)))
            self._total_width = max(self._total_width, rendered_line.get_width())
            if is_present_month and str(self._curr_day) in line.split():
                curr_day_ind = line.split().index(str(self._curr_day))
                leading_space_ind = (len(line) - len(line.lstrip(' '))) // 3
                offset_x = self._cal_font_width * (curr_day_ind + leading_space_ind) * 3

                self.add_shape(Rectangle(
                    self._cal_selector_color,
                    self.x + offset_x - self._cal_date_padding,
                    self.y + offset_y - self._cal_date_padding,
                    self._cal_date_width + 2 * self._cal_date_padding,
                    self._cal_date_height + 2 * self._cal_date_padding,
                    line_width=self._cal_selector_line_width))

            while event_ind < len(days_with_events) and days_with_events[event_ind][0] in line.split():
                event_day_ind = line.split().index(days_with_events[event_ind][0])
                offset_x = self._cal_font_width * event_day_ind * 3
                leading_spaces = (len(line) - len(line.lstrip(' ')))
                if leading_spaces > 0:
                    offset_x += (leading_spaces - 1) * self._cal_font_width

                start_pos = (self.x + offset_x, self.y + offset_y + self._cal_date_height - 3)
                end_pos = (self.x + offset_x + self._cal_date_width, self.y + offset_y + self._cal_date_height - 3)
                color = self._cal_event_color if days_with_events[event_ind][1] == '1' else self._cal_completed_event_color
                self.add_shape(Line(color, start_pos, end_pos, width=self._cal_selector_line_width))
                event_ind += 1

            offset_y += rendered_line.get_height()

        self._total_height = offset_y

    def _next_month(self):
        self._curr_month += 1
        if self._curr_month == 13:
            self._curr_year += 1
            self._curr_month = 1
        self._load_cal()

    def _last_month(self):
        self._curr_month -= 1
        if self._curr_month == 0:
            self._curr_year -= 1
            self._curr_month = 12
        self._load_cal()

    def _reset_month(self):
        self._reset_date()
        self._load_cal()

    def reset(self):
        self._reset_month()

    def set_events(self, events):
        self._events = events

    def get_width(self):
        return self._total_width

    def get_height(self):
        return self._total_height


class Traffic(Widget):
    def __init__(self, parent, x, y):
        super(Traffic, self).__init__(parent, x, y)

        self.traffic_font = pygame.font.Font("fonts/FreeSans.ttf", 13)
        self.traffic_font_height = self.traffic_font.render(' ', True, self._get_color('white')).get_height()

        self._traffic_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self._traffic_key = "AIzaSyDKl1oPieC1EwVdsnUJpg0btJV2Bwg0cd4"
        self._traffic_payload = {"units": "matrics", "key": self._traffic_key, "origins": "", "destinations": ""}

        self._traffic_icon_path = os.path.join("images", "traffic", "traffic.png")
        self._traffic_icon_size = self.traffic_font_height
        icon = pygame.image.load(self._traffic_icon_path)
        self._traffic_icon = pygame.transform.scale(icon, (self._traffic_icon_size, self._traffic_icon_size))

        self._origin_address = "University of Waterloo"
        self._dest_address = "University of Toronto"

        self._traffic_last_update = time.time()
        self._traffic_update_interval = 1800
        self._traffic_info = None

        self._background_alpha = 120

    def set_locations(self):
        self.parent.create_popup('input', self.parent, 300, 200, input_width=150,
                                 text="Please enter locations:", entries=["Origin", "Destination"],
                                 values=[self._origin_address, self._dest_address], required=[True, True],
                                 close_action=lambda: self._set_locations_from_popup())
        self.parent.popup.set_title('Set Locations')

    def _set_locations_from_popup(self):
        locations = self.parent.popup.get_input()
        self._origin_address = locations['Origin']
        self._dest_address = locations['Destination']
        self._load_traffic()

    def _load_traffic(self):
        self.clear_shapes()

        self._traffic_payload['origins'] = '+'.join(self._origin_address.split())
        self._traffic_payload['destinations'] = '+'.join(self._dest_address.split())

        traffic_info_res = requests.get(self._traffic_url, params=self._traffic_payload)
        self._traffic_info = traffic_info_res.json()

        try:
            traffic_distance = self._traffic_info['rows'][0]['elements'][0]['distance']['text']
            traffic_duration = self._traffic_info['rows'][0]['elements'][0]['duration']['text']
        except IndexError:
            return

        self._distance_text = self.traffic_font.render(traffic_distance, True, self._get_color('white'))
        self._duration_text = self.traffic_font.render(traffic_duration, True, self._get_color('white'))

        self.width = max(self._traffic_icon.get_width(), self._distance_text.get_width(),
                         self._duration_text.get_width())
        self._text_height = self._traffic_icon.get_height()
        self.height = 3 * self._text_height

        distance_text_x = self.x + (self.width - self._distance_text.get_width()) // 2
        traffic_icon_x = self.x + (self.width - self._traffic_icon.get_width()) // 2

        self.add_shape(Text(self._traffic_icon, (traffic_icon_x, self.y)))
        self.add_shape(Text(self._distance_text, (distance_text_x, self.y + self._text_height)))
        self.add_shape(Text(self._duration_text, (self.x, self.y + 2 * self._text_height)))

        log_to_file("Traffic updated")

    def _on_setup(self):
        self._load_traffic()

    def _on_update(self):
        if (time.time() - self._traffic_last_update > self._traffic_update_interval
                or self._traffic_info is None):
            self._load_traffic()
            self._traffic_last_update = time.time()

    def _on_draw(self, screen):
        pass

    def _draw_background(self, screen):
        self._draw_transparent_rect(screen, self.x, self.y,
                                    self.get_width(), self.get_height(),
                                    self._background_alpha,
                                    color=self._get_color('lightgray'))


class Stock(Widget):
    def __init__(self, parent, x, y, chart=False, chart_width=100, chart_height=100):
        super(Stock, self).__init__(parent, x, y)

        self.chart = chart
        self.chart_width = chart_width
        self.chart_height = chart_height

        self.stock_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self.stock_font_height = self.stock_font.render(' ', True, self._get_color('white')).get_height()
        self.stock_footnote_font = pygame.font.Font("fonts/FreeSans.ttf", 10)
        self.stock_label_font = pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.stock_range_font = pygame.font.Font("fonts/FreeSans.ttf", 13)

        self._stock_url = "https://www.alphavantage.co/query"
        self._stock_keys = ['T9O3IK0TF72YCBP8", "JEIP3D1ZI2UTJZUL", "TI8F72SY4LKSD23L']
        self._stock_symbol = ""
        self._stock_payload = {"1D": {"function": "TIME_SERIES_INTRADAY", "symbol": self._stock_symbol,
                                      "interval": "5min", "outputsize": "full", "apikey": self._stock_keys[0]},
                               "5D": {"function": "TIME_SERIES_INTRADAY", "symbol": self._stock_symbol,
                                      "interval": "5min", "outputsize": "full", "apikey": self._stock_keys[0]},
                               "1M": {"function": "TIME_SERIES_INTRADAY", "symbol": self._stock_symbol,
                                      "interval": "60min", "outputsize": "full", "apikey": self._stock_keys[0]},
                               "3M": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "6M": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "1Y": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "5Y": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "MAX": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                       "outputsize": "full", "apikey": self._stock_keys[0]}}
        self._stock_range_ind = 0
        self._stock_range = ["1D", "5D", "1M", "3M", "6M", "1Y", "5Y", "MAX"]
        self._stock_info_queue = queue.Queue(maxsize=1)
        self._stock_info = {"intraday": None, "hourly": None, "daily": None}
        self._current_price = 0
        self._last_close_price = 0
        self._time_series = []
        self._loading_thread = None

        self._input_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._input_widget = Input(self.parent, self.x, self.y, font=self._input_font, width=150,
                                   enter_key_event=self._search, capital_lock=True, limit_chars=list(ascii_letters))
        self._subwidgets.append(self._input_widget)

        self._chart_widget = None
        if self.chart:
            self._chart_widget = Chart(self.parent, self.x, self.y + self.stock_font_height + self._input_widget.get_height() + 10,
                                       label_font=self.stock_label_font, width=self.chart_width, height=self.chart_height,
                                       background=True, background_color=self._get_color('lightgray'), background_alpha=180)
            self._subwidgets.append(self._chart_widget)

    def _search(self, reset=True):
        if reset:
            self.reset()
            self._stock_symbol = self._input_widget.get_text()
        self._chart_widget.reset()
        self._load_stock()

    def _load_stock(self):
        if not self._stock_symbol:
            return

        if self._stock_info[self._get_range_key()]:
            self._parse_stock_info()
            return

        if not self._loading_thread:
            current_range = self._stock_range[self._stock_range_ind]
            payload = self._stock_payload[current_range]
            payload['symbol'] = self._stock_symbol
            self._loading_thread = RequestThread(self._stock_info_queue, self._stock_url, payload)
            self._loading_thread.start()

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._input_widget.set_active(True)
            elif event.key == pygame.K_UP:
                self._range_up()
            elif event.key == pygame.K_DOWN:
                self._range_down()

    def _range_up(self):
        if self.chart and self._stock_range_ind > 0:
            self._stock_range_ind -= 1
            self._search(reset=False)

    def _range_down(self):
        if self.chart and self._stock_range_ind < len(self._stock_range) - 1:
            self._stock_range_ind += 1
            self._search(reset=False)

    def _on_enter(self):
        self._input_widget.set_active(True)

    def _on_exit(self):
        self._input_widget.set_active(False)

    def _on_setup(self):
        self._input_widget.set_active(True)
        self._input_widget.bind_key(pygame.K_UP, self._range_up)
        self._input_widget.bind_key(pygame.K_DOWN, self._range_down)

    def _on_update(self):
        self.clear_shapes()
        self._add_range()

        if not self._stock_info_queue.empty():
            self._stock_info[self._get_range_key()] = self._stock_info_queue.get()
            self._loading_thread = None
            self._parse_stock_info()

    def _get_range_key(self):
        current_range = self._stock_range[self._stock_range_ind]
        if current_range.endswith('D'):
            return "intraday"
        elif current_range == "1M":
            return "hourly"
        else:
            return "daily"

    def _get_time_series(self, time_series_key):
        range_key = self._get_range_key()
        if not self._stock_info[range_key].get(time_series_key):
            return None
        time_series = self._stock_info[range_key].get(time_series_key)
        time_series_list = []
        for key in sorted(time_series, reverse=True):
            time_series[key]['timestamp'] = key
            time_series_list.append(time_series[key])
        return time_series_list

    def _parse_stock_info(self):
        self._time_series = []
        current_range = self._stock_range[self._stock_range_ind]
        range_key = self._get_range_key()

        if self._stock_info[range_key] is None:
            return

        if current_range == "1D":
            time_series_key = "Time Series (5min)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            today_str = time_series_list[0]['timestamp'][:10]
            self._time_series = [element for element in time_series_list if element['timestamp'].startswith(today_str)]
            self._current_price = float(self._time_series[0].get('4. close'))
            self._last_close_price = float(time_series_list[len(self._time_series)].get('4. close'))
            self._chart_widget.set_x_range(0, 78)
        elif current_range == "5D":
            time_series_key = "Time Series (5min)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            today_str = time_series_list[0]['timestamp'][:10]
            quotes_today = [element for element in time_series_list if element['timestamp'].startswith(today_str)]
            quotes_previous = time_series_list[len(quotes_today):78 * 5]
            self._time_series = (quotes_today + quotes_previous)[::4]
            self._chart_widget.set_x_range(0, 98)
        elif current_range == "1M":
            time_series_key = "Time Series (60min)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:154:2]
            self._chart_widget.set_x_range(0, 77)
        elif current_range == "3M":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:66]
            self._chart_widget.set_x_range(0, 66)
        elif current_range == "6M":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:132]
            self._chart_widget.set_x_range(0, 132)
        elif current_range == "1Y":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:260:2]
            self._chart_widget.set_x_range(0, 130)
        elif current_range == "5Y":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:1304:10]
            self._chart_widget.set_x_range(0, 130)
        else:
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            ratio = len(time_series_list) // 100
            self._time_series = time_series_list[::ratio]
            self._chart_widget.set_x_range(0, 100)

        if self.chart and self._time_series:
            price_info = [(float(element['2. high']) + float(element['3. low'])) // 2 for element in self._time_series]
            self._chart_widget.set_info({"price": price_info})
            if current_range == "1D":
                self._chart_widget.set_constants([self._last_close_price])
            else:
                self._chart_widget.set_constants([float(self._time_series[-1].get('1. open'))])
            self._chart_widget.set_y_range(min(price_info) * 0.975, max(price_info) * 1.025)
            change = price_info[0] - self._last_close_price if current_range == "1D" else price_info[0] - price_info[-1]
            if change < 0:
                self._chart_widget.set_info_colors({"price": 'red'})
            else:
                self._chart_widget.set_info_colors({"price": 'green'})

    def _on_draw(self, screen):
        if self._loading_thread and self._loading_thread.is_alive():
            self._display_info(screen, "Loading stock info...")
            return

        range_key = self._get_range_key()
        current_stock_info = self._stock_info[range_key]
        if current_stock_info is None:
            return
        elif current_stock_info.get("Note"):
            self._display_info(screen, "Searching is too frequent!")
            return
        elif current_stock_info.get("Error Message"):
            self._display_info(screen, "Invalid stock symbol!")
            return

        self._draw_quote(screen)

    def _display_info(self, screen, text):
        loading_text = self.stock_font.render(text, True, self._get_color('white'))
        screen.blit(loading_text, (self.x, self.y + self._input_widget.get_height() + 5))

    def _draw_quote(self, screen):
        if not self._current_price or not self._last_close_price:
            return

        change = self._current_price - self._last_close_price
        percent = change / self._last_close_price * 100
        if change > 0:
            color = "green"
            arrow = u'▲'
        elif change < 0:
            color = "red"
            arrow = u'▼'
        else:
            color = "white"
            arrow = u'▬'

        symbol_text = self.stock_font.render(self._stock_symbol, True, self._get_color('white'))
        price_text = self.stock_font.render('{:.2f}'.format(self._current_price), True, self._get_color(color))
        bar_text = self.stock_font.render('  |  ', True, self._get_color('white'))
        percent_text = self.stock_font.render(u'{:.2f}% {}'.format(percent, arrow), True, self._get_color(color))
        quote_x = self.x
        quote_y = self.y + self._input_widget.get_height() + 5
        screen.blit(symbol_text, (quote_x, quote_y))
        quote_x += symbol_text.get_width() + 10
        for text in [price_text, bar_text, percent_text]:
            screen.blit(text, (quote_x, quote_y))
            quote_x += text.get_width()

    def _add_range(self):
        if not self.chart:
            return

        range_x = self.x + self.chart_width + 10
        range_y = self.y + self.stock_font_height + self._input_widget.get_height() + 10
        range_unit_distance = self.chart_height // (len(self._stock_range) - 1)
        self.add_shape(Line(self._get_color('white'), (range_x, range_y), (range_x, range_y + self.chart_height), width=3))
        for ind in range(len(self._stock_range)):
            y = range_y + range_unit_distance * ind if ind < len(self._stock_range) - 1 else range_y + self.chart_height
            if ind == self._stock_range_ind:
                color = self._get_color('green')
            else:
                color = self._get_color('white')
            rendered_text = self.stock_range_font.render(self._stock_range[ind], True, color)
            self.add_shape(Line(self._get_color('white'), (range_x, y), (range_x + 6, y)))
            self.add_shape(Text(rendered_text, (range_x + 10, y - rendered_text.get_height() // 2)))

    def reset(self):
        self._stock_symbol = ""
        self._stock_range_ind = 0
        self._stock_info_queue = queue.Queue(maxsize=1)
        self._stock_info = {"intraday": None, "hourly": None, "daily": None}
        self._current_price = 0
        self._last_close_price = 0
        self._time_series = []
        self._loading_thread = None

    def clear(self):
        self.reset()
        self._input_widget.reset()
        self._chart_widget.reset()


class SystemInfo(Widget):
    def __init__(self, parent, x, y, font=None, cpu_info=True, memory_info=True, disk_info=True, internet_info=True, percent_bar=True):
        super(SystemInfo, self).__init__(parent, x, y)

        self.font = font if font is not None else pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.cpu_info = cpu_info
        self.memory_info = memory_info
        self.disk_info = disk_info
        self.internet_info = internet_info
        self.percent_bar = percent_bar
        self._info_text_height = self.font.render(' ', True, self._get_color('white')).get_height()

        self._cpu_percent = 0.0
        self._cpu_temp = 0.0
        self._memory_percent = 0.0
        self._disk_percent = 0.0
        self._disk_partitions = [partition.mountpoint for partition in psutil.disk_partitions()]
        self._disk_total = 0
        self._last_net_sent_bytes = psutil.net_io_counters().bytes_sent
        self._last_net_recv_bytes = psutil.net_io_counters().bytes_recv
        self._net_sent_speed = 0
        self._net_recv_speed = 0

        self._percent_bar_width = 50 if self.percent_bar else 0
        self._percent_bar_height = int(self._info_text_height * 0.75)

        self._update_interval = 1.0
        self._last_update = time.time()

    def _update_info(self):
        self._memory_percent = psutil.virtual_memory().percent
        self._cpu_percent = psutil.cpu_percent()

        temperatures = psutil.sensors_temperatures()
        for sensor_name in temperatures:
            if sensor_name.find('cpu') != -1:
                cpu_temps = temperatures[sensor_name]
                if len(cpu_temps) > 0:
                    self._cpu_temp = cpu_temps[0].current
        
        try:
            disk_used = float(sum(psutil.disk_usage(path).used for path in self._disk_partitions))
            if not self._disk_total:
                self._disk_total = float(sum(psutil.disk_usage(path).total for path in self._disk_partitions))
            self._disk_percent = disk_used / self._disk_total * 100
        except WindowsError:
            self._disk_percent = 0.0

        current_sent_bytes = psutil.net_io_counters().bytes_sent
        current_recv_bytes = psutil.net_io_counters().bytes_recv
        self._net_sent_speed = current_sent_bytes - self._last_net_sent_bytes
        self._net_recv_speed = current_recv_bytes - self._last_net_recv_bytes
        self._last_net_sent_bytes = current_sent_bytes
        self._last_net_recv_bytes = current_recv_bytes

    def _add_percent_bar(self, percent, x, y):
        if percent <= 60:
            color = self._get_color('green')
        elif percent <= 80:
            color = self._get_color('yellow')
        else:
            color = self._get_color('red')
        width = int(self._percent_bar_width * percent / 100)
        self.add_shape(Rectangle(self._get_color('lightgray'), x, y, self._percent_bar_width, self._percent_bar_height, line_width=0))
        self.add_shape(Rectangle(color, x, y, width, self._percent_bar_height, line_width=0))

    def _on_setup(self):
        self._update_info()

    def _on_update(self):
        current_time = time.time()
        if current_time - self._last_update > self._update_interval:
            self._update_info()
            self._last_update = current_time

    def _on_draw(self, screen):
        self.clear_shapes()

        rendered_cpu_text = self.font.render("CPU: ", True, self._get_color('white'))
        rendered_memory_text = self.font.render("Memory: ", True, self._get_color('white'))
        rendered_disk_text = self.font.render("Disk: ", True, self._get_color('white'))
        percent_bar_x = self.x + max(rendered_cpu_text.get_width(), rendered_memory_text.get_width())
        percent_bar_y = self.y + (self._info_text_height - self._percent_bar_height) / 2
        rendered_cpu_percent_text = self.font.render(" {:.2f}% | {:.1f}℃".format(self._cpu_percent, self._cpu_temp),
                                                     True, self._get_color('white'))
        rendered_memory_percent_text = self.font.render(" {:.2f}%".format(self._memory_percent),
                                                        True, self._get_color('white'))
        rendered_disk_percent_text = self.font.render(" {:.2f}%".format(self._disk_percent),
                                                      True, self._get_color('white'))

        if self.percent_bar:
            self._add_percent_bar(self._cpu_percent, percent_bar_x, percent_bar_y)
            self._add_percent_bar(self._memory_percent, percent_bar_x, percent_bar_y + self._info_text_height)
            self._add_percent_bar(self._disk_percent, percent_bar_x, percent_bar_y + self._info_text_height * 2)

        upload_speed = bytes_to_string(self._net_sent_speed)
        download_speed = bytes_to_string(self._net_recv_speed)
        rendered_net_text = self.font.render(u"Internet: \u2193{}/s \u2191{}/s".format(download_speed, upload_speed), True, self._get_color('white'))

        y = self.y
        if self.cpu_info:
            screen.blit(rendered_cpu_text, (self.x, y))
            screen.blit(rendered_cpu_percent_text, (percent_bar_x + self._percent_bar_width, y))
            y += self._info_text_height

        if self.memory_info:
            screen.blit(rendered_memory_text, (self.x, y))
            screen.blit(rendered_memory_percent_text, (percent_bar_x + self._percent_bar_width, y))
            y += self._info_text_height

        if self.disk_info:
            screen.blit(rendered_disk_text, (self.x, y))
            screen.blit(rendered_disk_percent_text, (percent_bar_x + self._percent_bar_width, y))
            y += self._info_text_height

        if self.internet_info:
            screen.blit(rendered_net_text, (self.x, y))


class Time(Widget):
    def __init__(self, parent):
        super(Time, self).__init__(parent, 0, 0)

        self.date_str = dt.now().strftime("%A, %b %d")
        self.time_str = dt.now().strftime("%H:%M")

        self.date_font = pygame.font.SysFont(self.default_font_name, 30)
        self.time_font = pygame.font.SysFont(self.default_font_name, 65)

    def _on_setup(self):
        pass

    def _on_update(self):
        self.date_str = dt.now().strftime("%A, %b %d")
        self.time_str = dt.now().strftime("%H:%M")

    def _on_draw(self, screen):
        date_text = self.date_font.render(self.date_str, True, self._get_color('white'))
        time_text = self.time_font.render(self.time_str, True, self._get_color('white'))
        screen.blit(date_text, (self._screen_width - date_text.get_width() - 5, 10))
        screen.blit(time_text, (self._screen_width - time_text.get_width() - 5,
                                date_text.get_height() + 15))


class NightTime(Time):
    def __init__(self, parent):
        super(NightTime, self).__init__(parent)

        self.date_str = dt.now().strftime("%A, %b %d")
        self.time_str = dt.now().strftime("%H:%M")
        self.night_date_font = pygame.font.SysFont(self.default_font_name, 50)
        self.night_time_font = pygame.font.SysFont(self.default_font_name, 150)

    def _on_draw(self, screen):
        time_text = self.night_time_font.render(self.time_str, True, self._get_color('gray'))
        date_text = self.night_date_font.render(self.date_str, True, self._get_color('gray'))
        time_pos = ((self._screen_width - time_text.get_width()) // 2,
                    (self._screen_height - time_text.get_height()) // 2 - 30)
        date_pos = ((self._screen_width - date_text.get_width()) // 2,
                    time_pos[1] + time_text.get_height() + 10)
        screen.blit(time_text, time_pos)
        screen.blit(date_text, date_pos)


class Content(Widget):
    def __init__(self, parent, x, y, text, font=None, color=(255, 255, 255),
                 max_width=0, max_height=0, prefix=None, borders=[],
                 border_color=(255, 255, 255), border_width=1, margin=(0, 0, 0, 0),
                 underline=False):
        super(Content, self).__init__(parent, x, y)

        self.text = ''.join([c for c in text if c in printable])
        self.font = font
        self.color = color
        self.max_width = max_width
        self.max_height = max_height
        self.prefix = prefix
        self.prefix_text = None
        self.prefix_width = 0
        self.prefix_height = 0
        self.borders = borders
        self.border_color = border_color
        self.border_width = border_width
        self.margin = margin
        self.underline = underline
        if not self.font:
            self.font = self.default_font
        self.content_texts = []

    def _on_setup(self):
        self.content_texts = []
        x, y = self.x, self.y
        if self.prefix:
            self.prefix_text = self.font.render(self.prefix, True, self.color)
            self.content_texts.append([self.prefix, [x, y]])
            self.prefix_width = self.prefix_text.get_width()
            self.prefix_height = self.prefix_text.get_height()
            x += self.prefix_width
            self.max_width -= self.prefix_width

        content_text = self.font.render(str(self.text), True, self.color)
        if self.max_width <= 0 or content_text.get_width() <= self.max_width:
            self.content_texts.append([self.text, [x, y]])
            return

        words = self.text.split(' ')
        current_width = 0
        line_words = []
        space_width = self.font.render(' ', True, self.color).get_width()
        for word in words:
            word_width = self.font.render(word, True, self.color).get_width()
            if current_width + word_width + space_width > self.max_width:
                line = ' '.join(line_words)
                line_text = self.font.render(line, True, self.color)
                self.content_texts.append([line, [x, y]])
                line_words = []
                current_width = 0
                y += line_text.get_height()
                if self.max_height > 0 and y - self.y > self.max_height:
                    return
            line_words.append(word)
            current_width += word_width + space_width

        if line_words:
            line = ' '.join(line_words)
            self.content_texts.append([line, [x, y]])

        if self.underline:
            for content_text, pos in self.content_texts:
                rendered_text = self.font.render(content_text, True, self.color)
                start_pos = (pos[0], pos[1] + rendered_text.get_height())
                end_pos = (pos[0] + rendered_text.get_width(), pos[1] + rendered_text.get_height())
                self.add_shape(Line(self.color, start_pos, end_pos))

    def _on_update(self):
        if self.text:
            self._add_borders()

    def _on_draw(self, screen):
        for text, pos in self.content_texts:
            rendered_text = self.font.render(text, True, self.color)
            screen.blit(rendered_text, pos)

    def _add_borders(self):
        full_border = "full" in self.borders
        for border in self.borders:
            lt = (self.x - self.margin[0], self.y - self.margin[2])
            lb = (self.x - self.margin[0], self.y + self.margin[3] + self.get_height())
            rt = (self.x + self.margin[1] + self.get_width(), self.y - self.margin[2])
            rb = (self.x + self.margin[1] + self.get_width(), self.y + self.margin[3] + self.get_height())
            if border == "left" or full_border:
                self.add_shape(Line(self.border_color, lt, lb, width=self.border_width))
            elif border == "right" or full_border:
                self.add_shape(Line(self.border_color, rt, rb, width=self.border_width))
            elif border == "top" or full_border:
                self.add_shape(Line(self.border_color, lt, rt, width=self.border_width))
            elif border == "bottom" or full_border:
                self.add_shape(Line(self.border_color, lb, rb, width=self.border_width))

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text
        self.setup()

    def get_width(self):
        width = 0
        contents = self.content_texts[1:] if self.prefix else self.content_texts
        for text, pos in contents:
            rendered_text = self.font.render(text, True, self.color)
            width = max(width, rendered_text.get_width())

        if self.prefix:
            return self.prefix_width + width
        else:
            return width

    def get_height(self):
        if self.prefix:
            return sum([self.font.render(str(text), True, self.color).get_height() for text, pos in self.content_texts[1:]])
        elif self.content_texts:
            return sum([self.font.render(str(text), True, self.color).get_height() for text, pos in self.content_texts])
        else:
            return 0

    def get_lines(self):
        lines = []
        start_index = 1 if self.prefix else 0
        for ind in range(start_index, len(self.content_texts)):
            text, pos = self.content_texts[ind]
            if self.prefix and ind == 1:
                line = self.font.render(str(self.prefix) + str(text), True, self.color)
            else:
                line = self.font.render(str(len(self.prefix) * ' ') + str(text), True, self.color)
            lines.append(line)
        return lines

    def set_underline(self, status):
        self.underline = status
    
    def get_text_color(self):
        return self.color

    def set_text_color(self, color):
        self.color = color

    def add_offset(self, x_offset, y_offset):
        for text, pos in self.content_texts:
            pos[0] += x_offset
            pos[1] += y_offset


class Search(Widget):
    def __init__(self, parent, x, y, str_font=None, result_font=None, max_width=0, max_height=0):
        super(Search, self).__init__(parent, x, y)

        self.str_font = str_font
        self.result_font = result_font
        if not self.str_font:
            self.str_font = self.default_font
        if not self.result_font:
            self.result_font = self.default_font

        self.max_width = max_width
        self.max_height = max_height

        self._page_footnote_font = pygame.font.Font("fonts/FreeSans.ttf", 12)

        self._search_url = "https://www.bestbuy.ca/en-CA/Search/SearchResults.aspx"
        self._search_payload = {"query": ""}
        self._search_str_pos = (self.x + 10, self.y + 10)
        self._search_str_widget = Input(parent, self._search_str_pos[0], self._search_str_pos[1],
                                        font=self.str_font, width=self.max_width, enter_key_event=self._search)

        self._search_result_pos = (self.x + 10, self.y + 45)
        self._search_results = []
        self._search_result_pages = []
        self._page_index = 0
        self._subwidgets = [self._search_str_widget]

    def _on_setup(self):
        self._search_str_widget.set_active(True)

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        self._draw_footnote(screen)

        if self._search_result_pages:
            for search_result in self._search_result_pages[self._page_index]:
                search_result.draw(screen)

    def _on_enter(self):
        self._search_str_widget.set_active(True)

    def _on_exit(self):
        self._search_str_widget.set_active(False)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._move_page("up")
            elif event.key == pygame.K_DOWN:
                self._move_page("down")
            elif event.key == pygame.K_RETURN:
                self._search_str_widget.set_active(True)

    def _draw_footnote(self, screen):
        # draw page number
        page_text = "page: {}/{}".format(self._page_index + 1, len(self._search_result_pages))
        rendered_page_text = self._page_footnote_font.render(page_text, True, self._get_color('white'))
        page_text_pos = (self.x + self.max_width - rendered_page_text.get_width(),
                         self.y + self.max_height)
        if self._search_result_pages:
            screen.blit(rendered_page_text, page_text_pos)

        # draw source string
        source_text = "source: bestbuy.ca"
        rendered_source_text = self._page_footnote_font.render(source_text, True, self._get_color('white'))
        source_text_pos = (self.x + self.max_width - rendered_source_text.get_width(),
                           self.y + self.max_height + rendered_page_text.get_height())
        screen.blit(rendered_source_text, source_text_pos)

    def _move_page(self, direction):
        if direction == "up":
            if self._page_index > 0:
                self._page_index -= 1
        else:
            if self._page_index < len(self._search_result_pages) - 1:
                self._page_index += 1

    def _search(self):
        search_str = self._search_str_widget.get_text()
        if not search_str or search_str.isspace():
            return

        self._search_payload['query'] = search_str.replace(' ', '+')
        res = requests.get(self._search_url, params=self._search_payload)
        soup = BeautifulSoup(res.content, 'html.parser')
        with open("search_response.html", 'wb') as f:
            f.write(res.content)
        search_results = soup.find_all('li', class_=re.compile("listing-item"))

        self._page_index = 0
        self._search_result_pages = []
        page_contents = []

        if soup.find('div', class_="search-no-results"):
            title_content = Content(self.parent, self._search_result_pos[0], self._search_result_pos[1],
                                    "Can't find any results...",
                                    font=self.result_font, max_width=self.max_width)
            title_content.setup()
            self._search_result_pages.append([title_content])
            return

        for item in search_results:
            name = item.find('h4', class_="prod-title").get_text()
            price = item.find('span', class_="amount").get_text()
            stars_tag = item.find('div', class_="rating-stars-yellow")
            stars = ""
            if stars_tag:
                stars = stars_tag.get("style")[7:-1]

            x = self._search_result_pos[0]
            y = sum([content.get_height() for content in page_contents]) + self._search_result_pos[1]
            item_text = u'{} - {}'.format(name, price)
            if stars:
                item_text += u' | {}'.format(stars)
            title_content = Content(self.parent, x, y, item_text, font=self.result_font, max_width=self.max_width, prefix="- ")
            title_content.setup()

            if y + title_content.get_height() > self.y + self.max_height:
                title_content.set_pos(x, self._search_result_pos[1])
                title_content.setup()
                self._search_result_pages.append(page_contents)
                page_contents = []

            page_contents.append(title_content)

        if page_contents:
            self._search_result_pages.append(page_contents)

    def reset(self):
        self._search_results = []
        self._search_result_pages = []
        self._page_index = 0
        self._search_str_widget.reset()


class Input(Widget):
    def __init__(self, parent, x, y, font=None, width=100, enter_key_event=None,
                 capital_lock=False, limit_chars=None, max_char=-1,
                 align_right=False, cursor=True, color=(255, 255, 255)):
        super(Input, self).__init__(parent, x, y)

        self.font = font if font is not None else self.default_font
        self.width = width
        self.height = self.font.render(' ', True, self._get_color('white')).get_height()
        self.enter_key_event = enter_key_event
        self.capital_lock = capital_lock
        self.limit_chars = limit_chars
        self.max_char = max_char
        self.align_right = align_right
        self.cursor = cursor
        self.color = color

        self._background_alpha = 180
        self._cursor_index = 0
        self._cursor_active_time = time.time()
        self._string = ""
        self._content_widget = Content(self.parent, self.x, self.y, self._string,
                                       font=self.font, color=self.color)
        self._subwidgets = [self._content_widget]

    def _draw_cursor(self, screen):
        time_diff = time.time() - self._cursor_active_time
        if time_diff - math.floor(time_diff) > 0.5:
            return

        rendered_text = self.font.render(self._string[:self._cursor_index], True, self._get_color('white'))
        start_pos = (self.x + rendered_text.get_width(), self.y)
        end_pos = (self.x + rendered_text.get_width(),
                   self.y + rendered_text.get_height())
        pygame.draw.line(screen, self._get_color('white'), start_pos, end_pos)

    def _draw_background(self, screen):
        if not self.is_active:
            return

        self._draw_transparent_rect(screen, self.x, self.y,
                                    self.get_width(), self.get_height(),
                                    self._background_alpha,
                                    color=self._get_color('lightgray'))

    def _input(self, s):
        if ctrl_pressed():
            return

        if self.limit_chars is not None and s not in self.limit_chars:
            return

        if self.max_char != -1 and len(self.get_text()) >= self.max_char:
            return

        if self.capital_lock:
            s = s.upper()

        self._string = self._string[:self._cursor_index] + s + self._string[self._cursor_index:]
        self._cursor_index += 1
        self._content_widget.set_text(self._string)

    def _backspace(self):
        if self._cursor_index == 0:
            return

        self._string = self._string[:self._cursor_index - 1] + self._string[self._cursor_index:]
        self._cursor_index -= 1
        self._content_widget.set_text(self._string)

    def _delete(self):
        if self._cursor_index == len(self._string):
            return

        self._string = self._string[:self._cursor_index] + self._string[self._cursor_index + 1:]
        self._content_widget.set_text(self._string)

    def _clear_str(self):
        self._cursor_index = 0
        self._string = ""
        self._content_widget.set_text(self._string)

    def _move_cursor(self, direction):
        if not self.cursor:
            return

        self._cursor_active_time = time.time()
        if direction == "left":
            if self._cursor_index > 0:
                self._cursor_index -= 1
        else:
            if self._cursor_index < len(self._string):
                self._cursor_index += 1

    def _on_setup(self):
        pass

    def _on_update(self):
        self.clear_shapes()

        line_start_pos = (self.x, self.y + self._content_widget.get_height())
        line_end_pos = (self.x + self.width, self.y + self._content_widget.get_height())
        self.add_shape(Line(self._get_color('white'), line_start_pos, line_end_pos))

        if self.align_right:
            content_pos = self._content_widget.get_pos()
            content_width = self._content_widget.get_width()
            self._content_widget.set_pos(self.x + self.width - content_width, content_pos[1])

    def _on_draw(self, screen):
        if self.is_active and self.cursor:
            self._draw_cursor(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            c = pygame_key_to_char(event.key)
            if c is not None and c in printable:
                self._input(c)
                return

            if event.key == pygame.K_BACKSPACE:
                if ctrl_pressed():
                    self._clear_str()
                else:
                    self._backspace()
            elif event.key == pygame.K_DELETE:
                if ctrl_pressed():
                    self._clear_str()
                else:
                    self._delete()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.enter_key_event:
                    self.enter_key_event()
            elif event.key == pygame.K_LEFT:
                self._move_cursor("left")
            elif event.key == pygame.K_RIGHT:
                self._move_cursor("right")

    def reset(self):
        self._clear_str()

    def get_text(self):
        return self._string

    def is_empty(self):
        return len(self._string) == 0

    def set_text(self, text):
        self._string = text
        self._content_widget.set_text(self._string)
        self._cursor_index = len(self._string)

    def get_width(self):
        return self.width

    def get_height(self):
        return self.font.render(' ', True, self._get_color('white')).get_height()

    def enter_char(self, c):
        if c not in list(printable):
            return

        self._input(c)

    def delete_char(self, n):
        for _ in range(n):
            self._backspace()

    def set_color(self, color):
        self.color = color
        self._content_widget.set_text_color(color)


class Chart(Widget):
    def __init__(self, parent, x, y, info=None, label_font=None, constants=[], width=100, height=100,
                 max_x=100, max_y=100, min_x=0, min_y=0, info_colors=None, line_width=1,
                 x_unit=1, y_unit=1, x_label_interval=None, y_label_interval=None,
                 background=False, background_color=(255, 255, 255), background_alpha=255):
        super(Chart, self).__init__(parent, x, y)

        self.info = info
        self.label_font = label_font if label_font else pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.constants = constants
        self.width = width
        self.height = height
        self.max_x = max_x
        self.max_y = max_y
        self.min_x = min_x
        self.min_y = min_y
        self.info_colors = info_colors
        self.line_width = line_width
        self.x_unit = x_unit
        self.y_unit = y_unit
        self.x_label_interval = x_label_interval
        self.y_label_interval = y_label_interval
        self.background = background
        self.background_color = background_color
        self.background_alpha = background_alpha

    def _on_setup(self):
        pass

    def _on_update(self):
        self.clear_shapes()

        if self.background:
            self.add_shape(Rectangle(self.background_color, self.x, self.y,
                                     self.get_width(), self.get_height(),
                                     line_width=0, alpha=self.background_alpha))

        self._add_labels()
        self._add_curves()
        self._add_axis()

    def _add_labels(self):
        if self.x_label_interval:
            x = self.x
            y = self.y + self.height
            x_label_interval_distance = int(self.width / (self.max_x / self.x_label_interval))
            for i in range(int(self.max_x / self.x_label_interval) + 1):
                label_text = str(i * self.x_label_interval)
                rendered_label_text = self.label_font.render(label_text, True, self._get_color('white'))
                text_width = rendered_label_text.get_width()
                if i == int(self.max_x / self.x_label_interval):
                    x = self.x + self.width
                if i > 0:
                    self.add_shape(Line(self._get_color('white'), (x, self.y), (x, y)))
                    self.add_shape(Text(rendered_label_text, (x - text_width / 2, y + 2)))
                else:
                    self.add_shape(Text(rendered_label_text, (x, y + 2)))
                x += x_label_interval_distance

        if self.y_label_interval:
            x = self.x
            y = self.y + self.height
            y_label_interval_distance = int(self.height / (self.max_y / self.y_label_interval))
            for i in range(int(self.max_y / self.y_label_interval) + 1):
                label_text = str(i * self.y_label_interval)
                rendered_label_text = self.label_font.render(label_text, True, self._get_color('white'))
                text_height = rendered_label_text.get_height()
                if i == int(self.max_y / self.y_label_interval):
                    y = self.y
                if i > 0:
                    self.add_shape(Line(self._get_color('white'), (x, y), (x + self.width, y)))
                self.add_shape(Text(rendered_label_text, (x - rendered_label_text.get_width() - 3, y - text_height / 2)))
                y -= y_label_interval_distance

    def _add_axis(self):
        self.add_shape(Line(self._get_color('white'), (self.x, self.y),
                            (self.x, self.y + self.height), width=2))
        self.add_shape(Line(self._get_color('white'), (self.x, self.y + self.height),
                            (self.x + self.width, self.y + self.height), width=2))

    def _add_curves(self):
        if not self.info:
            return

        x_unit_distance = float(self.width) / (self.max_x - self.min_x - 1) * self.x_unit
        y_unit_distance = float(self.height) / (self.max_y - self.min_y) * self.y_unit
        for key, vals in self.info.items():
            if isinstance(vals, queue.Queue) and vals.qsize() <= 1:
                continue
            elif isinstance(vals, list) and len(vals) <= 1:
                continue

            points = []
            val_list = vals if isinstance(vals, list) else vals.queue
            for ind, val in enumerate(reversed(val_list)):
                pos_x = int(self.x + x_unit_distance * (ind - self.min_x))
                pos_y = int(self.y + self.height - y_unit_distance * (val - self.min_y))
                if pos_x <= self.x + self.width:
                    points.append((pos_x, pos_y))

            color_name = self.info_colors.get(key) if self.info_colors else "white"
            color = self._get_color(color_name)
            if not color:
                color = self._get_color('white')
            curve = Lines(color, False, points, anti_alias=True, width=self.line_width)
            self.add_shape(curve)

        for constant in self.constants:
            y = int(self.y + self.height - y_unit_distance * (constant - self.min_y))
            rendered_label_text = self.label_font.render(str(constant), True, self._get_color('white'))
            self.add_shape(DashLine(self._get_color('white'), (self.x, y), (self.x + self.width, y),
                                    width=self.line_width))
            self.add_shape(Text(rendered_label_text, (self.x + self.width - rendered_label_text.get_width(),
                                                      y - rendered_label_text.get_height())))

    def _on_draw(self, screen):
        pass

    def reset(self):
        self.info = None
        self.clear_shapes()
        self._add_axis()

    def set_info(self, info):
        self.info = info

    def set_info_colors(self, info_colors):
        self.info_colors = info_colors

    def set_constants(self, constants):
        self.constants = constants

    def set_x_range(self, min_x, max_x):
        self.min_x = min_x
        self.max_x = max_x

    def set_y_range(self, min_y, max_y):
        self.min_y = min_y
        self.max_y = max_y

    def set_background_color(self, color):
        self.background_color = color


class ChartCaption(Widget):
    def __init__(self, parent, x, y, info_colors, font=None, line_length=25):
        super(ChartCaption, self).__init__(parent, x, y)

        self.info_colors = info_colors
        self.font = font if font is not None else self.default_font
        self.line_length = line_length

    def _on_setup(self):
        x, y = self.x, self.y
        content_widgets = []
        for name in sorted(self.info_colors.keys()):
            content_widget = Content(self.parent, x, y, name, font=self.font)
            content_widget.setup()
            content_widgets.append(content_widget)
            y += content_widget.get_height()
        self._subwidgets.extend(content_widgets)

        line_x = self.x + max([widget.get_width() for widget in content_widgets]) + 5
        for content_widget in content_widgets:
            name = content_widget.get_text()
            line_y = content_widget.get_pos()[1] + content_widget.get_height() // 2
            self.add_shape(Line(self._get_color(self.info_colors.get(name)), (line_x, line_y), (line_x + self.line_length, line_y), width=2))

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass


class Map(Widget):
    def __init__(self, parent, x, y, map_width=200, map_height=150, map_padding=0.075, background_alpha=100):
        super(Map, self).__init__(parent, x, y)

        self.map_width = map_width
        self.map_height = map_height
        self.map_padding = map_padding
        self.background_alpha = background_alpha

        self._map_x = self.x + 30
        self._map_y = self.y + 90

        self._background_surface = pygame.Surface((self.map_width, self.map_height))
        self._background_surface.set_alpha(self.background_alpha)

        self._direction_info = None
        self._total_distance = 0.0
        self._total_time = 0.0
        self._polyline_points = []

        self._caption_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._input_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._result_font = pygame.font.Font("fonts/FreeSans.ttf", 16)
        self._address_font = pygame.font.Font("fonts/FreeSans.ttf", 12)

        self._from_text = self._caption_font.render("From: ", True, self._get_color('white'))
        self._to_text = self._caption_font.render("To: ", True, self._get_color('white'))
        self._mode_text = self._caption_font.render("Mode: ", True, self._get_color('white'))

        self._mode_ind = 0
        self._icon_size = 25
        self._mode_rect_width = 2
        self._modes = ["driving", "transit", "walking", "bicycling"]
        self._icon_directory = os.path.join("images", "traffic")
        self._icons = []

        self._map_api_key = "AIzaSyDKl1oPieC1EwVdsnUJpg0btJV2Bwg0cd4"
        self._direction_url = "https://maps.googleapis.com/maps/api/directions/json"
        self._direction_payload = {"units": "metric", "key": self._map_api_key,
                                   "origin": "", "destination": "", "mode": self._modes[self._mode_ind]}

        self._input_width = 200
        self._dot_radius = 5
        self._origin_widget = Input(self.parent, self.x + self._from_text.get_width() + 5, self.y,
                                    font=self._input_font, width=self._input_width, enter_key_event=self._search)
        self._dest_widget = Input(self.parent, self.x + self._from_text.get_width() + 5, self.y + 30,
                                  font=self._input_font, width=self._input_width, enter_key_event=self._search)

        self._subwidgets = [self._origin_widget, self._dest_widget]

    def _search(self):
        origin_address = self._origin_widget.get_text()
        dest_address = self._dest_widget.get_text()

        if not origin_address or not dest_address:
            return

        self._direction_payload['origin'] = '+'.join(origin_address.split())
        self._direction_payload['destination'] = '+'.join(dest_address.split())
        self._direction_payload['mode'] = self._modes[self._mode_ind]

        direction_res = requests.get(self._direction_url, params=self._direction_payload)
        self._direction_info = direction_res.json()

        self.clear_shapes()
        self._parse_info()

    def _parse_info(self):
        if not self._direction_info:
            return

        self._total_time = sum([step['duration']['value'] for step in self._direction_info['routes'][0]['legs'][0]['steps']])
        self._total_distance = sum([step['distance']['value'] for step in self._direction_info['routes'][0]['legs'][0]['steps']])

        # parse overview polyline
        polyline_width = int(self.map_width * (1 - self.map_padding * 2))
        polyline_height = int(self.map_height * (1 - self.map_padding * 2))
        polyline_x = self._map_x + (self.map_width - polyline_width) // 2
        polyline_y = self._map_y + (self.map_height - polyline_height) // 2

        points = polyline.decode(self._direction_info['routes'][0]['overview_polyline']['points'])
        latitudes = [point[0] for point in points]
        longitudes = [point[1] for point in points]
        min_lat = min(latitudes)
        max_lat = max(latitudes)
        min_long = min(longitudes)
        max_long = max(longitudes)

        coords = [(long - min_long, lat - min_lat) for lat, long in points]
        x_ratio = polyline_width // (max_long - min_long)
        y_ratio = polyline_height // (max_lat - min_lat)
        ratio = min(x_ratio, y_ratio)
        coords = [(int(polyline_x + x * ratio), int(polyline_y + polyline_height - y * ratio)) for x, y in coords]

        coords_x = [coord[0] for coord in coords]
        coords_y = [coord[1] for coord in coords]
        x_offset = polyline_width - (max(coords_x) - min(coords_x))
        y_offset = polyline_height - (max(coords_y) - min(coords_y))
        self._polyline_points = [(x + x_offset // 2, y - y_offset // 2) for x, y in coords]

        start_address = self._direction_info['routes'][0]['legs'][0]['start_address'].split(',')[0]
        rendered_start_text = self._address_font.render(start_address, True, self._get_color('white'))
        start_text_x = self._polyline_points[0][0] - rendered_start_text.get_width() // 2
        start_text_y = self._polyline_points[0][1] - rendered_start_text.get_height() - 5
        start_text_x, start_text_y = self._adjust_text_pos(start_text_x, start_text_y, rendered_start_text)

        end_address = self._direction_info['routes'][0]['legs'][0]['end_address'].split(',')[0]
        rendered_end_text = self._address_font.render(end_address, True, self._get_color('white'))
        end_text_x = self._polyline_points[-1][0] - rendered_end_text.get_width() // 2
        end_text_y = self._polyline_points[-1][1] - rendered_end_text.get_height() - 5
        end_text_x, end_text_y = self._adjust_text_pos(end_text_x, end_text_y, rendered_end_text)

        self.add_shape(ScreenSurface(self._background_surface, (self._map_x, self._map_y)))
        self.add_shape(Lines(self._get_color('green'), False, self._polyline_points, width=3, anti_alias=False))
        self.add_shape(Circle(self._get_color('orange'), self._polyline_points[0], self._dot_radius))
        self.add_shape(Circle(self._get_color('lightblue'), self._polyline_points[-1], self._dot_radius))
        self.add_shape(Rectangle(self._get_color('white'), self._map_x, self._map_y, self.map_width, self.map_height))
        self.add_shape(Text(rendered_start_text, (start_text_x, start_text_y)))
        self.add_shape(Text(rendered_end_text, (end_text_x, end_text_y)))

        return points

    def _adjust_text_pos(self, x, y, text):
        text_width = text.get_width()
        text_height = text.get_height()
        x_padding = self.map_width * self.map_padding // 2
        y_padding = self.map_height * self.map_padding // 2

        if x < self._map_x + x_padding:
            x = self._map_x + x_padding

        if x + text_width > self._map_x + self.map_width - x_padding:
            x = self._map_x + self.map_width - x_padding - text_width

        if y < self._map_y + y_padding:
            y = self._map_y + y_padding

        if y + text_height > self._map_y + self.map_height - y_padding:
            y = self._map_y + self.map_height - y_padding - text_height

        return x, y

    def _draw_texts(self, screen):
        screen.blit(self._from_text, (self.x, self.y))
        screen.blit(self._to_text, (self.x, self.y + 30))

        if self._direction_info:
            text_height = self._input_font.render(' ', True, self._get_color('white')).get_height()
            text_width = max(self._from_text.get_width(), self._to_text.get_width()) + self._input_width
            self.add_shape(Circle(self._get_color('orange'), (self.x + text_width + self._dot_radius * 2, self.y + text_height // 2), self._dot_radius))
            self.add_shape(Circle(self._get_color('lightblue'), (self.x + text_width + self._dot_radius * 2, self.y + text_height // 2 + 30), self._dot_radius))

    def _draw_icons(self, screen):
        x = self.x + 280
        y = self.y + 30
        screen.blit(self._mode_text, (x, self.y))
        for ind, icon in enumerate(self._icons):
            if ind == self._mode_ind:
                rect_area = (x - self._mode_rect_width, y - self._mode_rect_width,
                             icon.get_width() + 2 * self._mode_rect_width, icon.get_height() + 2 * self._mode_rect_width)
                pygame.draw.rect(screen, self._get_color('green'), rect_area, self._mode_rect_width)
            screen.blit(icon, (x, y))
            x += icon.get_width() + 20

    def _calculate_time(self, total_time):
        total_min = total_time // 60
        if total_min < 60:
            return "{:.1f} min".format(total_min)
        elif total_min < 60 * 24:
            return "{} h {} min".format(int(total_min / 60), int(total_min) % 60)
        else:
            total_hour = int(total_min / 60)
            return "{} d {} h {} min".format(total_hour // 24, total_hour % 24, int(total_min) % 60)

    def _draw_result(self, screen):
        if not self._direction_info:
            return

        result_text = "{:.1f} km | {}".format(float(self._total_distance) / 1000, self._calculate_time(float(self._total_time)))
        rendered_result_text = self._result_font.render(result_text, True, self._get_color('white'))
        screen.blit(rendered_result_text, (self._map_x, self.y + 60))

    def _on_enter(self):
        self._origin_widget.set_active(True)

    def _on_exit(self):
        self._origin_widget.set_active(False)
        self._dest_widget.set_active(False)

    def _on_setup(self):
        for mode in self._modes:
            image_path = os.path.join(self._icon_directory, mode + ".png")
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (self._icon_size, self._icon_size))
            self._icons.append(image.convert_alpha())

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        self._draw_texts(screen)
        self._draw_result(screen)
        self._draw_icons(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._toggle_mode()
            elif event.key == pygame.K_UP:
                self._origin_widget.set_active(True)
                self._dest_widget.set_active(False)
            elif event.key == pygame.K_DOWN:
                self._origin_widget.set_active(False)
                self._dest_widget.set_active(True)

    def _toggle_mode(self):
        if self._mode_ind < len(self._modes) - 1:
            self._mode_ind += 1
        else:
            self._mode_ind = 0

    def reset(self):
        self.clear_shapes()
        self._origin_widget.reset()
        self._dest_widget.reset()
        self._direction_info = None
        self._total_distance = 0.0
        self._total_time = 0.0
        self._polyline_points = []
        self._mode_ind = 0


class Camera(Widget):
    def __init__(self, parent, x, y, camera):
        super(Camera, self).__init__(parent, x, y)

        self.camera = camera

        self._camera_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._message_font = pygame.font.Font("fonts/FreeSans.ttf", 20)
        self._camera_rotation = 90
        self._camera_resolution = (self._screen_width, self._screen_height)
        self._camera_framerate = 0
        self._frame = None
        self._frame_last_update = time.time()
        self._text_last_update = time.time()

    def _on_setup(self):
        pass

    def _on_update(self):
        if self.camera:
            ret, self._frame = self.camera.read()

    def _on_draw(self, screen):
        if self._frame is None or not self._frame.any():
            self._draw_message(screen)
            return

        image_arr = cv2.cvtColor(self._frame, cv2.COLOR_BGR2RGB)

        image = Image.fromarray(image_arr)

        mode = image.mode
        size = image.size
        data = image.tobytes()

        rendered_image = pygame.image.fromstring(data, size, mode)
        rotated_image = pygame.transform.rotate(rendered_image, self._camera_rotation)
        screen.blit(rotated_image, (0, 0))

        self._add_framerate(screen)

    def _add_framerate(self, screen):
        current_time = time.time()
        update_interval = time.time() - self._frame_last_update
        self._frame_last_update = current_time

        if current_time - self._text_last_update > 1:
            self._camera_framerate = int(1.0 / update_interval)
            self._text_last_update = current_time

        framerate_text = self._camera_font.render("FPS: {}".format(self._camera_framerate), True, self._get_color('green'))
        screen.blit(framerate_text, (10, 10))

    def _draw_message(self, screen):
        message = "Camera Disabled"
        message_text = self._message_font.render(message, True, self._get_color('white'))

        x = (self._screen_width - message_text.get_width()) // 2
        y = (self._screen_height - message_text.get_height()) // 2
        screen.blit(message_text, (x, y))


class List(Widget):
    def __init__(self, parent, x, y, items=[], max_width=480, max_height=320,
                 selectable=False, select_event=None, line_padding=5, reset_on_exit=True):
        super(List, self).__init__(parent, x, y)

        self.items = items
        self.max_width = max_width
        self.max_height = max_height
        self.selectable = selectable
        self.select_event = select_event
        self.line_padding = line_padding
        self.reset_on_exit = reset_on_exit

        self.item_font = pygame.font.Font("fonts/FreeSans.ttf", 17)

        self._selected_ind = 0
        self._rendered_texts = []
        self._selector_color = self._get_color("lightblue")
        self._selector_size = 10

    def _on_setup(self):
        self._render_texts()

    def _on_exit(self):
        if self.reset_on_exit:
            self.reset()

    def _render_texts(self):
        self._rendered_texts = []
        for item in self.items:
            rendered_item = self.item_font.render(item, True, self._get_color("white"))
            self._rendered_texts.append(rendered_item)

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        if not self.items:
            return

        x, y = self.x, self.y
        for ind, text in enumerate(self._rendered_texts):
            if not self.selectable:
                screen.blit(text, (x, y))
            else:
                if ind == self._selected_ind and self.is_active:
                    font_height = text.get_height()
                    selector_x = x + self._selector_size // 2
                    selector_y = y + (font_height - self._selector_size) // 2
                    pygame.draw.rect(screen, self._selector_color, (selector_x, selector_y, self._selector_size, self._selector_size))
                screen.blit(text, (x + 2 * self._selector_size + 5, y))
            y += text.get_height() + self.line_padding

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._row_up()
            elif event.key == pygame.K_DOWN:
                self._row_down()
            elif event.key == pygame.K_RETURN:
                if self.select_event is not None:
                    self.select_event()

    def _row_up(self):
        if not self.items or self._selected_ind == 0:
            return

        self._selected_ind -= 1

    def _row_down(self):
        if not self.items or self._selected_ind == len(self.items) - 1:
            return

        self._selected_ind += 1

    def get_selected(self):
        return self._selected_ind

    def reset(self):
        self._selected_ind = 0


class Calculator(Widget):
    def __init__(self, parent, x, y, width=450, height=300, key_padding=0):
        super(Calculator, self).__init__(parent, x, y)

        self.width = width
        self.height = height
        self.key_padding = key_padding

        self._input_font = pygame.font.Font("fonts/FreeSans.ttf", 30)
        self._key_font = pygame.font.Font("fonts/FreeSans.ttf", 37)

        self._input_chars = list(digits + "+-*/().")
        self._input_widget = Input(self.parent, self.x, self.y, font=self._input_font,
                                   width=self.width, limit_chars=self._input_chars,
                                   align_right=True, cursor=False, enter_key_event=self._evaluate)

        self._keys_layout = ["789/C", "456*←", "123-(", "0.=+)"]
        self._key_width = 0
        self._key_height = 0
        self._key_background_color = self._get_color('lightgray')
        self._key_background_alpha = 120
        self._key_border_color = self._get_color('white')
        self._key_border_width = 1
        self._key_focus_color = self._get_color('orange')

        self._error_msg = "ERROR"

        self._subwidgets = [self._input_widget]

    def _on_setup(self):
        self._input_widget.bind_key(pygame.K_EQUALS, self._evaluate)
        self._input_widget.bind_key(pygame.K_c, self._clear)

        if self._keys_layout and self._keys_layout[0]:
            key_rows = len(self._keys_layout)
            key_cols = len(self._keys_layout[0])
            self._key_width = (self.width - self.key_padding * (key_cols - 1)) // key_cols
            self._key_height = (self.height - self._input_widget.get_height()
                                - self.key_padding * (key_rows - 1)) // key_rows

            for row_ind, row in enumerate(self._keys_layout):
                for col_ind, key in enumerate(row):
                    button_x = self.x + col_ind * (self._key_width + self.key_padding)
                    button_y = self.y + self._input_widget.get_height() + row_ind * (self._key_height + self.key_padding) + self.key_padding
                    button = Button(self.parent, button_x, button_y,
                                    width=self._key_width, height=self._key_height,
                                    text=key, background_color=self._key_background_color,
                                    background_alpha=self._key_background_alpha,
                                    border_color=self._key_border_color,
                                    border_width=self._key_border_width,
                                    font=self._key_font, on_click=self._click_key,
                                    on_click_param=key, focus_color=self._key_focus_color,
                                    focus_width=2 * self._key_border_width,
                                    shortcut_key=char_to_pygame_key(key))
                    self.parent.buttons.append(button)

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._input_widget.set_active(True)

    def _on_enter(self):
        self._input_widget.set_active(True)
        pygame.mouse.set_visible(True)

    def _on_exit(self):
        pygame.mouse.set_visible(False)

    def _evaluate(self):
        input_content = self._input_widget.get_text()
        if not input_content:
            self._input_widget.set_text("0")
            return
        elif input_content == self._error_msg:
            self._input_widget.reset()
            return

        try:
            result = str(eval(input_content))
        except SyntaxError:
            result = self._error_msg
        self._input_widget.set_text(result)

    def _click_key(self, key):
        if key == '=':
            self._evaluate()
        elif key == 'C':
            self._clear()
        elif key == '←':
            self._input_widget.delete_char(1)
        else:
            self._input_widget.enter_char(key)

    def _clear(self):
        self._input_widget.reset()

    def reset(self):
        self._input_widget.reset()


class QRCode(Widget):
    def __init__(self, parent, x, y, width=450, height=300):
        super(QRCode, self).__init__(parent, x, y)

        self.width = width
        self.height = height

        self._background_alpha = 255

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)
        self._input_font = pygame.font.Font("fonts/FreeSans.ttf", 18)
        self._setting_font = pygame.font.Font("fonts/FreeSans.ttf", 16)

        self._title_widget = Content(self.parent, self.x, self.y,
                                     "QR Code Generator", font=self._title_font)

        self._input_font_height = get_font_height(self._input_font)
        self._setting_font_height = get_font_height(self._setting_font)

        self._input_x = self.x + 15
        self._input_y = self.y + 35
        self._input_widget = Input(self.parent, self._input_x, self._input_y, 
                                   font=self._input_font, width=self.width,
                                   enter_key_event=self._validate_and_generate)

        self._total_levels = 4
        self._level = 1
        self._levels = [qrcode.constants.ERROR_CORRECT_L, qrcode.constants.ERROR_CORRECT_M,
                        qrcode.constants.ERROR_CORRECT_Q, qrcode.constants.ERROR_CORRECT_H]
        self._levels_text = ['7%', '15%', '25%', '30%']

        self._setting_width = 150
        self._qr_text = ''
        self._qr_image = None
        self._qr_padding = 20
        self._qr_image_size = self.height - self._input_font_height - self._qr_padding * 2
        self._qr_image_x = self._input_x + (self.width - self._qr_image_size + self._setting_width) // 2
        self._qr_image_y = self._input_y + self._input_font_height + self._qr_padding

        self._version_default = 'auto'
        self._version_x = self._input_x
        self._version_y = self._qr_image_y
        self._version_widget = Content(self.parent, self._version_x, self._version_y,
                                       "Version [auto|1-40]:", font=self._setting_font,
                                       max_width=120)
        self._version_input = Input(self.parent, self._version_x, self._version_y,
                                    font=self._setting_font, width=50,
                                    enter_key_event=self._validate_and_generate)

        self._level_bar_width = 10
        self._level_x = self._version_x
        self._level_y = self._version_y + self._setting_font_height * 2 + 10
        self._level_widget_text = "Error Correction Level: {}".format(self._levels_text[self._level])
        self._level_widget = Content(self.parent, self._level_x, self._level_y,
                                     self._level_widget_text, font=self._setting_font,
                                     max_width=120)

        self._subwidgets = [self._title_widget, self._input_widget,
                            self._version_widget, self._version_input,
                            self._level_widget]

    def _on_setup(self):
        self._version_input.set_text(self._version_default)
        self._version_input.set_pos(self._version_x + self._version_widget.get_width() + 5,
                                    self._version_y + self._version_widget.get_height() - \
                                    self._setting_font_height)

        self._input_widget.bind_key(pygame.K_TAB, self._toggle_input_widget)
        self._input_widget.bind_key(pygame.K_UP, self._move_level_up)
        self._input_widget.bind_key(pygame.K_DOWN, self._move_level_down)
        self._version_input.bind_key(pygame.K_TAB, self._toggle_input_widget)
        self._version_input.bind_key(pygame.K_UP, self._move_level_up)
        self._version_input.bind_key(pygame.K_DOWN, self._move_level_down)

        qr_text = self._setting_font.render("QR Code Here", True, self._get_color('white'))
        qr_text_x = self._qr_image_x + (self._qr_image_size - qr_text.get_width()) // 2
        qr_text_y = self._qr_image_y + (self._qr_image_size - qr_text.get_height()) // 2
        self.add_shape(Text(qr_text, (qr_text_x, qr_text_y)))

        line_color = self._get_color('white')
        line_dash_length = 10
        line_width = 1
        tl = (self._qr_image_x + line_width, self._qr_image_y + line_width)
        tr = (self._qr_image_x + self._qr_image_size - line_width, self._qr_image_y + line_width)
        bl = (self._qr_image_x + line_width, self._qr_image_y + self._qr_image_size - line_width)
        br = (self._qr_image_x + self._qr_image_size - line_width,
              self._qr_image_y + self._qr_image_size - line_width)
        self.add_shape(DashLine(line_color, tl, tr, dash_length=line_dash_length, width=line_width))
        self.add_shape(DashLine(line_color, tr, br, dash_length=line_dash_length, width=line_width))
        self.add_shape(DashLine(line_color, br, bl, dash_length=line_dash_length, width=line_width))
        self.add_shape(DashLine(line_color, bl, tl, dash_length=line_dash_length, width=line_width))

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        if self._qr_image is None:
            return

        screen.blit(self._qr_image, (self._qr_image_x, self._qr_image_y))

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._input_widget.set_active(True)
            elif event.key == pygame.K_TAB:
                self._toggle_input_widget()
            elif event.key == pygame.K_UP:
                self._move_level_up()
            elif event.key == pygame.K_DOWN:
                self._move_level_down()

    def _on_enter(self):
        self._input_widget.set_active(True)
    
    def _validate_and_generate(self):
        version_text = self._version_input.get_text()
        valid = True
        try:
            version = int(version_text)
            if version < 1 or version > 40:
                valid = False
        except ValueError:
            if version_text.lower() != self._version_default:
                valid = False
        
        if valid:
            self._version_widget.set_text_color(self._get_color('white'))
            self._generate()
        else:
            self._version_widget.set_text_color(self._get_color('red'))

    def _generate(self):
        input_text = self._input_widget.get_text()
        if not input_text:
            return

        self._qr_text = input_text

        qr = qrcode.QRCode(
            version=None,
            error_correction=self._levels[self._level],
            box_size=10,
            border=1,
        )
        qr.add_data(self._qr_text)
        qr.make(fit=True)

        image = qr.make_image(fill_color='black', back_color='white')
        image_mode = 'RGB'
        image = image.convert(image_mode)
        raw_str = image.tobytes('raw', image_mode)
        image = pygame.image.fromstring(raw_str, image.size, image.mode)
        self._qr_image = pygame.transform.scale(image, (self._qr_image_size, self._qr_image_size))

    def _toggle_input_widget(self):
        if self._input_widget.is_active:
            self._input_widget.set_active(False)
            self._version_input.set_active(True)
        elif self._version_input.is_active:
            self._version_input.set_active(False)
            self._input_widget.set_active(True)
        else:
            self._input_widget.set_active(True)

    def _move_level_up(self):
        self._move_level('up')

    def _move_level_down(self):
        self._move_level('down')

    def _move_level(self, direction):
        old_level_text = self._levels_text[self._level]
        if direction == 'up':
            if self._level < self._total_levels - 1:
                self._level += 1
        elif self._level > 0:
                self._level -= 1
        new_level_text = self._levels_text[self._level]
        if old_level_text == new_level_text:
            return

        self._level_widget_text = self._level_widget_text.replace(old_level_text,
                                                                  new_level_text)
        self._level_widget.set_text(self._level_widget_text)

    def _draw_background(self, screen):
        self._draw_transparent_rect(screen, 0, 0, self._screen_width, self._screen_height,
                                    self._background_alpha, color=self._get_color('black'))

    def reset(self):
        if self._version_widget.get_text_color() == self._get_color('red'):
            self._version_input.set_text(self._version_default)
        self._version_widget.set_text_color(self._get_color('white'))

        self._input_widget.reset()
        self._qr_text = ''
        self._qr_image = None
