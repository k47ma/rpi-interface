import argparse
from lib.app import App

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--invert', action='store_true', default=False, help="invert screen")
    parser.add_argument('-f', '--fullscreen', action='store_true', default=False, help="full screen")
    args = parser.parse_args()
    app = App(args=args)
    app.start()
