# coding:utf-8

import time
from log import logger
from sseclient import SSEClient
from webrouter_conf import NginxConf, get_apps_from_lainlet
from config import DEBUG, INSTANCE_NO, KEY_PREFIX
from utils import get_lain_config, report, LAINLET_API_URL
import subprocess
import json


class Render:

    _extra_domains = []
    _ssl = []

    def __init__(self):
        pass

    def _reload_nginx(self):
        logger.info('reload nginx start')
        if not DEBUG:
            subprocess.call("nginx -t && nginx -s reload", shell=True)
        else:
            logger.debug('fake reload nginx')
        logger.info('reload nginx finish')

    def _render_once(self, data):
        new_apps = get_apps_from_lainlet(data)
        logger.info('>>>>>>>>>> render start <<<<<<<<<<')
        logger.debug('NginxConf start')
        nginx_conf = NginxConf(new_apps, self._ssl, self._extra_domains)
        nginx_conf.render_to_buffer()
        nginx_conf.sync_from_buffer()
        logger.debug('NginxConf finish')
        logger.info('>>>>>>>>>> render finish <<<<<<<<<<')
        self._reload_nginx()
        report("%s.webrouter.reload.%s.count" %
               (KEY_PREFIX, INSTANCE_NO), 1, int(time.time()))

    def render(self):
        logger.info('Render thread')
        action_events = ("init", "update", "delete")
        # Get ssl and extra_domains configuration first
        ssl_val = get_lain_config("ssl")
        if ssl_val is not None:
            self._ssl = json.loads(ssl_val)
        extra_domains_val = get_lain_config("extra_domains")
        if extra_domains_val is not None:
            self._extra_domains = json.loads(extra_domains_val)
        watch_url = LAINLET_API_URL + "webrouter/webprocs?watch=1"
        while True:
            try:
                messages = SSEClient(watch_url, timeout=(1, None))
                for msg in messages:
                    if msg.event in action_events:
                        self._render_once(json.loads(msg.data))
            except Exception:
                logger.exception("render and reload error")
            time.sleep(3)
