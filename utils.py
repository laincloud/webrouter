import socket
import requests
import os
from log import logger

PLAINTEXT_FORMAT = "%s %s %s\n"
GRAPHITE_DOMAIN = "graphite.lain"
LAINLET_API_URL = "http://lainlet.lain:%s/v2/" % \
    os.environ.get("LAINLET_PORT", "9001")
GRAPHITE_PORT = os.environ.get("GRAPHITE_PORT", "2003")

need_report = False


def report(key, value, timestamp):
    if not need_report:
        return
    data = PLAINTEXT_FORMAT % (key, value, timestamp)
    sock = None
    try:
        sock = socket.create_connection(
            (GRAPHITE_DOMAIN, GRAPHITE_PORT), timeout=1)
        sock.send(data)
    except Exception as e:
        logger.error("Send data to graphite failed: %s" % e)
    finally:
        if sock is not None:
            sock.close()


def get_lain_config(key):
    try:
        resp = requests.get(LAINLET_API_URL + "configwatcher?target=" + key)
        if resp.status_code == requests.codes.ok:
            return resp.json()[key]
    except Exception as e:
        logger.error("Get config [%s] error: %s", key, e)
    return None


def init_global_config():
    global need_report
    need_report = get_lain_config("dnshijack/" + GRAPHITE_DOMAIN) is not None
    logger.info("Reporting to graphite is open: %s" % need_report)
