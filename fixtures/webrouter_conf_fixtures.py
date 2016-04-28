# -*- coding: utf-8 -*-

import pytest


@pytest.fixture
def console_procs():
    console_web_proc = {
        'annotation': '{"mountpoint": ["console.lain.local"]}',
        'containers': [
            {'container_ip': '172.20.0.3', 'container_port': 8000}
        ],
        'name': 'console',
        'proc_name': 'web',
        'proc_type': 'web'
    }
    return [console_web_proc]


@pytest.fixture
def ssl_and_extra_domains_procs():
    console_web_proc = {
        'annotation': '{"mountpoint": ["console.lain.local", "console.lain", "console.lain.external", "console.lain.com"], "https_only": true}',
        'containers': [
            {'container_ip': '172.20.0.3', 'container_port': 8000}
        ],
        'name': 'console',
        'proc_name': 'web',
        'proc_type': 'web'
    }
    return [console_web_proc]


@pytest.fixture
def hello_procs():
    hello_web_proc = {
        'annotation': '{"mountpoint": ["hello.lain.local", "hello.lain.com", "lain.demo.com/hello"]}',
        'containers': [
            {'container_ip': '172.20.0.5', 'container_port': 80},
        ],
        'name': 'hello',
        'proc_name': 'web',
        'proc_type': 'web'
    }
    return [hello_web_proc]


@pytest.fixture
def registry_procs():
    registry_web_proc = {
        'annotation': '{"mountpoint": ["registry.lain.local", "registry.lain.com", "lain.demo.com/registry"]}',
        'containers': [
            {'container_ip': '172.20.0.10', 'container_port': 5000},
            {'container_ip': '172.20.0.11', 'container_port': 5000}
        ],
        'name': 'registry',
        'proc_name': 'web',
        'proc_type': 'web'
    }
    registry_admin_proc = {
        'annotation': '{"mountpoint": ["registry.lain.local/admin", "admin.registry.lain.com", "lain.demo.com/registryadmin"]}',
        'containers': [
            {'container_ip': '172.20.0.12', 'container_port': 5001}
        ],
        'name': 'registry',
        'proc_name': 'admin',
        'proc_type': 'web'
    }
    return [registry_web_proc, registry_admin_proc]


@pytest.fixture
def searchengine_procs():
    search_web_proc = {
        'annotation': '{"mountpoint": ["testapp.lain", "testapp.lain.local", "yisou.lain.com"], "healthcheck": "/search/healthcheck"}',
        'containers': [
            {'container_ip': '172.20.0.10', 'container_port': 5000},
            {'container_ip': '172.20.0.11', 'container_port': 5000}
        ],
        'name': 'testapp',
        'proc_name': 'web',
        'proc_type': 'web'
    }
    return [search_web_proc]


@pytest.fixture
def nobackend_procs():
    nobackend_web_proc = {
        'annotation': '{"mountpoint": ["testapp.lain", "testapp.lain.local", "yisou.lain.com"], "healthcheck": "/search/healthcheck"}',
        'containers': [],
        'name': 'nobackend',
        'proc_name': 'web',
        'proc_type': 'web'
    }
    return [nobackend_web_proc]
