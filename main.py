#!env python
# -*- coding: utf-8

from time import sleep
from threading import Thread
from render import Render
from monitor import validate_nginx_config
from utils import init_global_config


def main():
    try:
        init_global_config()
        r = Thread(target=Render().render)
        r.daemon = True
        r.start()
        monitor = Thread(target=validate_nginx_config)
        monitor.daemon = True
        monitor.start()
        while True:
            sleep(5)
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main()
