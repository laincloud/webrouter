# coding:utf-8

import os
import fnmatch
import errno
import shutil
import subprocess
import json
from jinja2 import Environment, FileSystemLoader
from config import NGINX_CONF_PATH, DOMAIN
from log import logger

NGINX_CONFD_BUFFER = os.path.join(NGINX_CONF_PATH, "buffer/conf.d")
NGINX_UPSTREAMS_BUFFER = os.path.join(NGINX_CONF_PATH, "buffer/upstreams")
NGINX_LOCATIONS_BUFFER = os.path.join(NGINX_CONF_PATH, "buffer/locations")
NGINX_CONFD_PATH = os.path.join(NGINX_CONF_PATH, "conf.d")
NGINX_UPSTREAMS_PATH = os.path.join(NGINX_CONF_PATH, "upstreams")
NGINX_LOCATIONS_PATH = os.path.join(NGINX_CONF_PATH, "locations")


TMPL_ENV = Environment(loader=FileSystemLoader(searchpath='./templates/'))
SERVER_TMPL = "server.conf.tmpl"
APP_UPSTREAMS_TMPL = "app.upstreams.tmpl"
APP_LOCATION_TMPL = "app.location.tmpl"


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_apps_from_lainlet(data):
    apps = {}
    for name, proc_info in data.iteritems():
        parts = name.split(".")
        if len(parts) < 3:
            logger.error("Get an invalid procname %s, skipped" % name)
            continue
        proc_name = parts[-1]
        app_name = ".".join(parts[:-2])
        proc = {}
        proc["proc_name"] = proc_name

        # The annotation of one proc are the same
        # During the deployment, podInfos may be empty for a while,
        # We should skip it
        if len(proc_info["PodInfos"]) == 0:
            continue

        proc["annotation"] = proc_info["PodInfos"][0]["Annotation"]
        proc["containers"] = []
        for c in proc_info["PodInfos"]:
            if len(c["ContainerInfos"]) > 0:
                proc["containers"].append({
                    "container_ip": c["ContainerInfos"][0]["ContainerIp"],
                    "container_port": c["ContainerInfos"][0]["Expose"],
                })
        if app_name in apps:
            apps[app_name].append(proc)
        else:
            apps[app_name] = [proc]
    return apps


def render_to_file(ctx, tmpl, dest):
    '''
    ctx:  dict params to render the template
    tmpl: template name according to templates path
    dest: absolute filename of the destination config file
    '''
    logger.debug(">>>>>>>>>> render start <<<<<<<<<<")
    logger.debug("    tmpl : %s" % (tmpl, ))
    logger.debug("    dest : %s" % (dest, ))
    logger.debug("    ctx : %s" % (ctx, ))
    t = TMPL_ENV.get_template(tmpl)
    mkdir_p(os.path.dirname(dest))
    with open(dest, "w") as dest_conf:
        dest_conf.write(t.render(ctx))
    logger.debug(">>>>>>>>>> render finish <<<<<<<<<<")


def empty_config_path(path):
    assert path.startswith(NGINX_CONF_PATH)
    mkdir_p(path)
    delete_list = os.listdir(path)
    for item in delete_list:
        abs_path = os.path.join(path, item)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        elif os.path.islink(abs_path):
            os.remove(abs_path)
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            logger.warning('something strange in config path: %s' % abs_path)


def sync_content(frompath, topath):
    assert frompath != topath
    assert frompath.startswith("%s/buffer" % (NGINX_CONF_PATH, ))
    assert topath.startswith(NGINX_CONF_PATH)
    frompath = frompath.rstrip("/")
    topath = topath.rstrip("/")
    mkdir_p(frompath)
    empty_config_path(topath)
    ret = subprocess.call("cp -rf %s/* %s/" % (frompath, topath), shell=True)
    if ret == 0:
        return True
    else:
        return None


def parse_mountpoint(mountpoint):
    m = mountpoint.strip().rstrip("/").split("/")
    return [m[0], "/".join(m[1:])]


def is_internal_domain(server_name, domains):
    for d in domains:
        if server_name.endswith("." + d):
            return True
    return False


def wildcards_match(server_name, wildcards_pattern):
    try:
        matched = fnmatch.fnmatch(server_name, wildcards_pattern)
    except:
        matched = False
    return matched


def get_ssl_key_prefix(server_name, ssl):
    try:
        for p in ssl.keys():
            if wildcards_match(server_name, p):
                return ssl[p]
        return None
    except:
        return None


class AppUpstream:

    def __init__(self, appname, proc):
        self.appname = appname
        self.procname = proc['proc_name']
        self.name = "%s__upstream__%s" % (appname, self.procname)
        self.backends = []
        for c in proc["containers"]:
            if c["container_port"] != 0 and c["container_ip"]:
                self.backends.append("%s:%s" % (
                    c["container_ip"], c["container_port"]
                ))
        annotation = json.loads(proc['annotation'])
        mountpoints = annotation.get('mountpoint')
        try:
            self.mountpoint_list = [parse_mountpoint(m) for m in mountpoints]
        except Exception as e:
            logger.error("invalid mountpoint info in proc %s: %s" % (
                proc, e
            ))
            self.mountpoint_list = []
        self.https_only = annotation.get('https_only', False)
        try:
            healthcheck_path = annotation.get('healthcheck', None)
            if healthcheck_path:
                self.healthcheck = True
                self.healthcheck_path = healthcheck_path
        except Exception as e:
            self.healthcheck = False
            self.healthcheck_path = ''


class AppUpstreams:

    def __init__(self, appname, procs):
        self.appname = appname
        self.upstreams = []
        for p in procs:
            self.upstreams.append(AppUpstream(appname, p))

    @property
    def filename(self):
        return "%s.upstreams" % (self.appname, )

    @property
    def buffer_filename(self):
        return os.path.join(NGINX_UPSTREAMS_BUFFER, self.filename)

    @property
    def config_filename(self):
        return os.path.join(NGINX_UPSTREAMS_PATH, self.filename)

    @property
    def ctx(self):
        return self.__dict__

    def render_to_buffer(self):
        render_to_file(self.ctx, APP_UPSTREAMS_TMPL, self.buffer_filename)


class AppLocation:

    def __init__(self, server, app_upstream):
        self.server = server
        self.appname = app_upstream.appname
        self.procname = app_upstream.procname
        self.uri_list = [m[1] for m in app_upstream.mountpoint_list
                         if m[0] == server]
        self.upstream_name = app_upstream.name

    @property
    def filename(self):
        return "%s__%s.location" % (self.appname, self.procname)

    @property
    def buffer_filename(self):
        return os.path.join(NGINX_LOCATIONS_BUFFER, self.server, self.filename)

    @property
    def config_filename(self):
        return os.path.join(NGINX_LOCATIONS_PATH, self.server, self.filename)

    @property
    def ctx(self):
        return self.__dict__

    def render_to_buffer(self):
        render_to_file(self.ctx, APP_LOCATION_TMPL, self.buffer_filename)


class ServerConf:

    def __init__(self, server, ssl, extra_domains, https_only=False):
        self.server = server
        self.https_only = https_only
        self.internal_domain = is_internal_domain(self.server, [DOMAIN, 'lain']
                                                  + extra_domains)
        self.ssl_name = get_ssl_key_prefix(self.server, ssl)
        self.locations = []

    @property
    def filename(self):
        return "%s.conf" % (self.server, )

    @property
    def buffer_filename(self):
        return os.path.join(NGINX_CONFD_BUFFER, self.filename)

    @property
    def config_filename(self):
        return os.path.join(NGINX_CONFD_PATH, self.filename)

    @property
    def ctx(self):
        return self.__dict__

    def render_to_buffer(self):
        render_to_file(self.ctx, SERVER_TMPL, self.buffer_filename)
        for location in self.locations:
            location.render_to_buffer()


class NginxConf:

    def __init__(self, apps, ssl=None, extra_domains=None):
        if ssl is None:
            ssl = {}
        if extra_domains is None:
            extra_domains = []
        app_streams_dict = {}
        for name, procs in apps.iteritems():
            app_streams_dict[name] = AppUpstreams(name, procs)
        server_conf_dict = {}
        for appname, app_upstreams in app_streams_dict.iteritems():
            for app_upstream in app_upstreams.upstreams:
                app_https_only = app_upstream.https_only
                for m in app_upstream.mountpoint_list:
                    server = m[0]
                    server_name_https_only = app_https_only and \
                        server.endswith(DOMAIN)
                    if server in server_conf_dict:
                        server_conf = server_conf_dict[server]
                    else:
                        server_conf = ServerConf(
                            server, ssl, extra_domains,
                            https_only=server_name_https_only)
                        server_conf_dict[server] = server_conf
                    app = AppLocation(server, app_upstream)
                    server_conf.locations.append(app)
        self.app_streams_list = app_streams_dict.values()
        self.server_confs = server_conf_dict.values()

    def render_to_buffer(self):
        empty_config_path(NGINX_UPSTREAMS_BUFFER)
        empty_config_path(NGINX_LOCATIONS_BUFFER)
        empty_config_path(NGINX_CONFD_BUFFER)
        for app_upstreams in self.app_streams_list:
            app_upstreams.render_to_buffer()
        for server_conf in self.server_confs:
            server_conf.render_to_buffer()

    def sync_from_buffer(self):
        empty_config_path(NGINX_UPSTREAMS_PATH)
        empty_config_path(NGINX_LOCATIONS_PATH)
        empty_config_path(NGINX_CONFD_PATH)
        return \
            sync_content(NGINX_UPSTREAMS_BUFFER, NGINX_UPSTREAMS_PATH) and \
            sync_content(NGINX_LOCATIONS_BUFFER, NGINX_LOCATIONS_PATH) and \
            sync_content(NGINX_CONFD_BUFFER, NGINX_CONFD_PATH)
