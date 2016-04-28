# -*- coding: utf-8
from os import environ

DEBUG = environ.get("WATCHER_DEBUG", False)
LOG_LEVEL = environ.get("WATCHER_LOG_LEVEL", "DEBUG")
DOMAIN = environ.get("LAIN_DOMAIN", "lain.example.com")
KEY_PREFIX = DOMAIN.replace(".", "_")
NGINX_CONF_PATH = environ.get("WATCHER_NGINX_CONF_PATH", "/etc/nginx")
LOG_PATH = environ.get("WATCHER_LOG_PATH", "/var/log/watcher")
NGINX_APP_LOG_PATH = environ.get("APP_LOG_PATH", "/var/log/nginx")
INSTANCE_NO = environ.get("DEPLOYD_POD_INSTANCE_NO", 1)
