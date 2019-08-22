#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from lib.util import *


class TestUtils:
    def test_in_sorted(self):
        empty_list = []
        list1 = [1, 2]
        list2 = [1, 3, 9]
        assert not in_sorted(1, empty_list)
        assert in_sorted(1, list1)
        assert in_sorted(2, list1)
        assert in_sorted(1, list2)
        assert in_sorted(3, list2)
        assert not in_sorted(-1, list1)
        assert not in_sorted(5, list1)
        assert not in_sorted(100, list1)
