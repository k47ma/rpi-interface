import argparse
from lib.app import App

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--invert', action='store_true',
                        default=False, help="invert screen")
    parser.add_argument('-f', '--fullscreen', action='store_true',
                        default=False, help="enable full screen")
    parser.add_argument('-p', '--performance', action='store_true',
                        default=False, help="enable performance mode")
    parser.add_argument('-d', '--debug', action='store_true',
                        default=False, help="enable debug mode")
    parser.add_argument('-r', '--dryrun', action='store', type=int,
                        default=-1, help="dryrun testing, time in seconds")
    args = parser.parse_args()
    app = App(args=args)
    app.start()
