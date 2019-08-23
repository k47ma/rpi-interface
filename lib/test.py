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

    def test_bytes_to_string(self):
        assert bytes_to_string(0) == "0B"
        assert bytes_to_string(100) == "100B"
        assert bytes_to_string(1000) == "1.00K"
        assert bytes_to_string(1024) == "1.02K"
        assert bytes_to_string(10240) == "10.24K"
        assert bytes_to_string(1000 ** 2) == "1.00M"
        assert bytes_to_string(1.5 * 1000 ** 2) == "1.50M"
        assert bytes_to_string(1000 ** 3) == "1.00G"
        assert bytes_to_string(100.3 * 1000 ** 3) == "100.30G"
