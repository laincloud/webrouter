# -*- coding: utf-8
import time
import subprocess
import os
from utils import report
from config import INSTANCE_NO, KEY_PREFIX


def validate_nginx_config():
    step = 10
    key = "%s.webrouter.syntax_valid.%s" % (KEY_PREFIX, INSTANCE_NO)
    with open(os.devnull, 'w') as out:
        while True:
            result = 1
            try:
                subprocess.check_call(["nginx", "-t"], stdout=out, stderr=out)
            except:
                result = 0
            report(key, result, int(time.time()))
            time.sleep(step)
