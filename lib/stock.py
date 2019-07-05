#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import requests
import time
from datetime import datetime
from termcolor import colored

if __name__ == '__main__':
    symbol = "TSLA"
    bar_char = u'\u25a0'
    url = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey=T9O3IK0TF72YCBP8".format(symbol)

    while True:
        time.sleep(5)
        response = requests.get(url)
        res = response.json()

        quote = res.get("Global Quote")
        if not quote:
            continue

        current_time = str(datetime.now())[11:19]
        open_price = quote.get("02. open")
        high_price = quote.get("03. high")
        low_price = quote.get("04. low")
        price = quote.get("05. price")
        change = quote.get("09. change")
        percent = quote.get("10. change percent")
        price_range = float(high_price) - float(low_price)

        change_num = float(change)
        if change_num > 0:
            color = "green"
            shape = u'▲'
        elif change_num < 0:
            color = "red"
            shape = u'▼'
        else:
            color = "white"
            shape = u'▬'

        colored_change = str(colored(change, color))
        colored_percent = str(colored(u'{} {}'.format(percent, shape), color))
        bar_count = int(abs(float(price) - float(open_price)) / price_range * 10)
        percent_bar = bar_count * bar_char + (10 - bar_count) * ' '
        sys.stdout.write(u'\r{}@{} | {} {} {} [{}]'.format(symbol, current_time, price, colored_change, colored_percent, percent_bar))
        sys.stdout.flush()
