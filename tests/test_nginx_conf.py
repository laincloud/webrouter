# -*- coding: utf-8 -*-

import os
from webrouter_conf import NginxConf


def test_nginx_conf_smoke(console_procs):
    apps = {'console': console_procs}
    nginx_conf = NginxConf(apps)
    assert len(nginx_conf.app_streams_list) == 1
    upstreams = nginx_conf.app_streams_list[0]
    assert upstreams.appname == 'console'
    assert len(upstreams.upstreams) == 1
    upstream = upstreams.upstreams[0]
    assert upstream.appname == 'console'
    assert upstream.name == "console__upstream__web"
    assert upstream.backends == ["172.20.0.3:8000"]
    assert upstream.mountpoint_list == [["console.lain.local", ""]]
    assert len(nginx_conf.server_confs) == 1
    server_conf = nginx_conf.server_confs[0]
    assert server_conf.server == 'console.lain.local'
    assert len(server_conf.locations) == 1
    location = server_conf.locations[0]
    assert location.server == 'console.lain.local'
    assert location.appname == 'console'
    assert location.uri_list == [""]
    assert location.upstream_name == "console__upstream__web"


def test_nginx_conf_with_ssl_config_and_extra_domains(ssl_and_extra_domains_procs):
    ssl = {
        "*.lain.local": "web",
        "*.lain.external": "external",
    }
    extra_domains = ["lain.external", "lain.domain"]
    apps = {'console': ssl_and_extra_domains_procs}
    nginx_conf = NginxConf(apps, ssl, extra_domains)
    assert len(nginx_conf.app_streams_list) == 1
    upstreams = nginx_conf.app_streams_list[0]
    assert upstreams.appname == 'console'
    assert len(upstreams.upstreams) == 1
    upstream = upstreams.upstreams[0]
    assert upstream.appname == 'console'
    assert upstream.name == "console__upstream__web"
    assert upstream.backends == ["172.20.0.3:8000"]
    expected_mountpoint_list = [['console.lain.local', ''],
                                ['console.lain', ''],
                                ['console.lain.com', ''],
                                ['console.lain.external', '']]
    expected_mountpoint_list.sort()
    upstream.mountpoint_list.sort()
    assert expected_mountpoint_list == upstream.mountpoint_list
    assert len(nginx_conf.server_confs) == 4
    console_lain_local = None
    console_lain_external = None
    console_lain = None
    for server_conf in nginx_conf.server_confs:
        if server_conf.server == 'console.lain.local':
            console_lain_local = server_conf
        elif server_conf.server == 'console.lain.external':
            console_lain_external = server_conf
        elif server_conf.server == 'console.lain.com':
            console_lain_com = server_conf
        elif server_conf.server == 'console.lain':
            console_lain = server_conf
        else:
            pass
    assert console_lain_local.server == 'console.lain.local'
    assert len(console_lain_local.locations) == 1
    assert console_lain_local.https_only is False
    assert console_lain_local.internal_domain is False
    assert console_lain_local.ssl_name == "web"
    location = console_lain_local.locations[0]
    assert location.server == 'console.lain.local'
    assert location.appname == 'console'
    assert location.uri_list == [""]
    assert location.upstream_name == "console__upstream__web"
    assert console_lain_external.internal_domain is True
    assert console_lain_external.ssl_name == "external"
    assert console_lain_com.internal_domain is False
    assert console_lain_com.ssl_name is None
    assert console_lain.internal_domain is True
    assert console_lain.ssl_name is None


def test_nginx_conf_complicated(registry_procs):
    apps = {'registry': registry_procs}
    nginx_conf = NginxConf(apps)
    assert len(nginx_conf.app_streams_list) == 1
    upstreams = nginx_conf.app_streams_list[0]
    assert upstreams.appname == 'registry'
    assert len(upstreams.upstreams) == 2
    assert len(nginx_conf.server_confs) == 4


def test_nginx_conf_healthcheck(searchengine_procs):
    apps = {'testapp': searchengine_procs}
    nginx_conf = NginxConf(apps)
    assert len(nginx_conf.app_streams_list) == 1
    upstreams = nginx_conf.app_streams_list[0]
    assert upstreams.appname == 'testapp'
    assert len(upstreams.upstreams) == 1
    assert len(nginx_conf.server_confs) == 3


def test_nginx_conf_multiserver_and_multiapp(searchengine_procs,
                                             registry_procs,
                                             hello_procs,
                                             console_procs,
                                             tmpdir,
                                             monkeypatch):
    apps = {
        'registry': registry_procs,
        'hello': hello_procs,
        'console': console_procs,
        'testapp': searchengine_procs
    }
    import webrouter_conf
    import config
    confpath = tmpdir.mkdir("nginx").strpath
    print confpath
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONF_PATH', confpath)
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONFD_BUFFER',
                        os.path.join(confpath, "buffer/conf.d"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_UPSTREAMS_BUFFER',
                        os.path.join(confpath, "buffer/upstreams"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_LOCATIONS_BUFFER',
                        os.path.join(confpath, "buffer/locations"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONFD_PATH',
                        os.path.join(confpath, "conf.d"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_UPSTREAMS_PATH',
                        os.path.join(confpath, "upstreams"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_LOCATIONS_PATH',
                        os.path.join(confpath, "locations"))
    monkeypatch.setattr(config, 'NGINX_APP_LOG_PATH', confpath)
    nginx_conf = NginxConf(apps)
    nginx_conf.render_to_buffer()
    nginx_conf.sync_from_buffer()
    # test empty and sync
    nginx_conf.render_to_buffer()
    nginx_conf.sync_from_buffer()


def test_nobackend_workaround(nobackend_procs, tmpdir, monkeypatch):
    apps = {
        'nobackend': nobackend_procs
    }
    import webrouter_conf
    import config
    confpath = tmpdir.mkdir("nginx").strpath
    print confpath
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONF_PATH', confpath)
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONFD_BUFFER',
                        os.path.join(confpath, "buffer/conf.d"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_UPSTREAMS_BUFFER',
                        os.path.join(confpath, "buffer/upstreams"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_LOCATIONS_BUFFER',
                        os.path.join(confpath, "buffer/locations"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONFD_PATH',
                        os.path.join(confpath, "conf.d"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_UPSTREAMS_PATH',
                        os.path.join(confpath, "upstreams"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_LOCATIONS_PATH',
                        os.path.join(confpath, "locations"))
    monkeypatch.setattr(config, 'NGINX_APP_LOG_PATH', confpath)
    nginx_conf = NginxConf(apps)
    nginx_conf.render_to_buffer()
    nginx_conf.sync_from_buffer()
    # test empty and sync
    nginx_conf.render_to_buffer()
    nginx_conf.sync_from_buffer()


def test_nginx_conf_with_ssl_config_and_extra_domains_render(ssl_and_extra_domains_procs, tmpdir, monkeypatch):
    ssl = {
        "*.lain.local": "web",
        "*.lain.external": "external",
    }
    extra_domains = ["lain.external", "lain.domain"]
    apps = {
        'console': ssl_and_extra_domains_procs
    }
    import webrouter_conf
    import config
    confpath = tmpdir.mkdir("nginx").strpath
    print confpath
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONF_PATH', confpath)
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONFD_BUFFER',
                        os.path.join(confpath, "buffer/conf.d"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_UPSTREAMS_BUFFER',
                        os.path.join(confpath, "buffer/upstreams"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_LOCATIONS_BUFFER',
                        os.path.join(confpath, "buffer/locations"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_CONFD_PATH',
                        os.path.join(confpath, "conf.d"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_UPSTREAMS_PATH',
                        os.path.join(confpath, "upstreams"))
    monkeypatch.setattr(webrouter_conf, 'NGINX_LOCATIONS_PATH',
                        os.path.join(confpath, "locations"))
    monkeypatch.setattr(config, 'NGINX_APP_LOG_PATH', confpath)
    nginx_conf = NginxConf(apps, ssl, extra_domains)
    nginx_conf.render_to_buffer()
    nginx_conf.sync_from_buffer()
    # test empty and sync
    nginx_conf.render_to_buffer()
    nginx_conf.sync_from_buffer()
