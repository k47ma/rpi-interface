#!/usr/bin/python3
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from pygame import Rect
from lib.util import distance


class Shape:
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Shape, self).__init__()
        self.color = None

    @abstractmethod
    def add_offset(self, x_offset, y_offset):
        pass


class Line(Shape):
    def __init__(self, color, start_pos, end_pos, width=1):
        super(Line, self).__init__()

        self.color = color
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.width = width

    def add_offset(self, x_offset, y_offset):
        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos
        self.start_pos = (start_x + x_offset, start_y + y_offset)
        self.end_pos = (end_x + x_offset, end_y + y_offset)


class Lines(Shape):
    def __init__(self, color, closed, pointlist, width=1, anti_alias=False):
        super(Lines, self).__init__()

        self.color = color
        self.closed = closed
        self.pointlist = pointlist
        self.width = width
        self.anti_alias = anti_alias

    def add_offset(self, x_offset, y_offset):
        temp_pointlist = []
        for point in self.pointlist:
            temp_pointlist.append((point[0] + x_offset, point[1] + y_offset))
        self.pointlist = temp_pointlist


class DashLine(Shape):
    def __init__(self, color, start_pos, end_pos, dash_length=5, width=1):
        super(DashLine, self).__init__()

        self.color = color
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.dash_length = dash_length
        self.width = width
        self.lines = self.generate_lines()

    def add_offset(self, x_offset, y_offset):
        for shape in self.lines:
            shape.add_offset(x_offset, y_offset)

    def generate_lines(self):
        lines = []
        total_lines = int(distance(self.start_pos, self.end_pos) / self.dash_length)
        x_distance = self.end_pos[0] - self.start_pos[0]
        y_distance = self.end_pos[1] - self.end_pos[1]
        for ind in range(total_lines):
            if ind % 2:
                continue

            start_x = int(self.start_pos[0] + x_distance * ind *
                          self.dash_length / distance(self.start_pos, self.end_pos))
            start_y = int(self.start_pos[1] + y_distance * ind *
                          self.dash_length / distance(self.start_pos, self.end_pos))
            end_x = int(self.start_pos[0] + x_distance * (ind + 1) *
                        self.dash_length / distance(self.start_pos, self.end_pos))
            end_y = int(self.start_pos[1] + y_distance * (ind + 1) *
                        self.dash_length / distance(self.start_pos, self.end_pos))

            line = Line(self.color, (start_x, start_y), (end_x, end_y), width=self.width)
            lines.append(line)

        return lines


class Rectangle(Shape):
    def __init__(self, color, x, y, width, height, line_width=1, alpha=None):
        super(Rectangle, self).__init__()

        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.line_width = line_width
        self.alpha = alpha

    def to_pygame_rect(self):
        return Rect(self.x, self.y, self.width, self.height)

    def add_offset(self, x_offset, y_offset):
        self.x += x_offset
        self.y += y_offset


class Circle(Shape):
    def __init__(self, color, pos, radius, width=0):
        super(Circle, self).__init__()

        self.color = color
        self.pos = pos
        self.radius = radius
        self.width = width

    def add_offset(self, x_offset, y_offset):
        x, y = self.pos
        self.pos = (x + x_offset, y + y_offset)


class Text(Shape):
    def __init__(self, text_surface, pos):
        super(Text, self).__init__()

        self.text_surface = text_surface
        self.pos = pos

    def add_offset(self, x_offset, y_offset):
        x, y = self.pos
        self.pos = (x + x_offset, y + y_offset)


class Polygon(Shape):
    def __init__(self, color, pointlist, width=0):
        super(Polygon, self).__init__()

        self.color = color
        self.pointlist = pointlist
        self.width = width

    def add_offset(self, x_offset, y_offset):
        temp_pointlist = []
        for point in self.pointlist:
            temp_pointlist.append((point[0] + x_offset, point[1] + y_offset))
        self.pointlist = temp_pointlist


class ScreenSurface(Shape):
    def __init__(self, surface, pos):
        super(ScreenSurface, self).__init__()

        self.surface = surface
        self.pos = pos

    def add_offset(self, x_offset, y_offset):
        x, y = self.pos
        self.pos = (x + x_offset, y + y_offset)
