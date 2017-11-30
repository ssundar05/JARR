#! /usr/bin/env python
# -*- coding: utf-8 -

# required imports and code exection for basic functionning

import logging
import random
from urllib.parse import urlparse

from blinker import signal
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

from the_conf import TheConf

conf = TheConf({'config_files': ['/etc/jarr.json', '~/.config/jarr.json'],
        'parameters': [
            {'jarr_testing': {'default': False, 'type': bool}},
            {'api_root': {'default': '/api/v2.0'}},
            {'babel': [{'timezone': {'default': 'Europe/Paris'}},
                       {'locale': {'default': 'en_GB'}}]},
            {'platform_url': {'default': 'http://0.0.0.0:5000/'}},
            {'sqlalchemy': [{'db_uri': {}},
                            {'test_uri': {'default': 'sqlite:///:memory:'}}]},
            {'secret_key': {'default': str(random.getrandbits(128))}},
            {'bundle_js': {'default': 'http://filer.1pxsolidblack.pl/'
                                     'public/jarr/current.min.js'}},
            {'log': [{'level': {'default': logging.WARNING, 'type': int}},
                     {'path': {'default': "jarr.log"}}]},
            {'crawler': [{'login': {'default': 'admin'}},
                         {'passwd': {'default': 'admin'}},
                         {'type': {'default': 'http'}},
                         {'resolv': {'type': bool, 'default': False}},
                         {'user_agent': {
                             'default': 'https://github.com/jaesivsm/JARR'}},
                         {'timeout': {'default': 30, 'type': int}}]},
            {'plugins': [{'readability_key': {'default': ''}},
                         {'rss_bridge': {'default': ''}}]},
            {'auth': [{'allow_signup': {'default': True, 'type': bool}}]},
            {'oauth': [{'allow_signup': {'default': True, 'type': bool}},
                       {'twitter_id': {'default': ''}},
                       {'twitter_secret': {'default': ''}},
                       {'facebook_id': {'default': ''}},
                       {'facebook_secret': {'default': ''}},
                       {'google_id': {'default': ''}},
                       {'google_secret': {'default': ''}},
                       {'linuxfr_id': {'default': ''}},
                       {'linuxfr_secret': {'default': ''}}]},
            {'notification': [{'email': {'default': ''}},
                              {'host': {'default': ''}},
                              {'starttls': {'type': bool, 'default': True}},
                              {'port': {'type': int, 'default': 587}},
                              {'login': {'default': ''}},
                              {'password': {'default': ''}}]},
            {'feed': [{'error_max': {'type': int, 'default': 6}},
                      {'error_threshold': {'type': int, 'default': 3}},
                      {'min_expires': {'type': int, 'default': 60 * 10}},
                      {'max_expires': {'type': int, 'default': 60 * 60 * 4}},
                      {'stop_fetch': {'default': 30, 'type': int}}]},
            {'webserver': [{'host': {'default': '0.0.0.0'}},
                           {'port': {'default': 5000, 'type': int}}]},
                      ]})

# utilities

def is_secure_served():
    return PARSED_PLATFORM_URL.scheme == 'https'

# init func

def init_logging(log_path=None, log_level=logging.INFO, modules=(),
                log_format='%(asctime)s %(levelname)s %(message)s'):

    if not modules:
        modules = ('root', 'wsgi', 'manager',
                   'jarr', 'jarr_crawler', 'jarr_common')
    if log_path:
        handler = logging.FileHandler(log_path)
    else:
        handler = logging.StreamHandler()
    formater = logging.Formatter(log_format)
    handler.setFormatter(formater)
    for logger_name in modules:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        for handler in logger.handlers:
            handler.setLevel(log_level)
        logger.setLevel(log_level)


def init_db(is_sqlite, echo=False):  # pragma: no cover
    kwargs = {'echo': echo}
    if is_sqlite:
        kwargs['connect_args'] = {'check_same_thread':False}
    if conf.jarr_testing:
        new_engine = create_engine(conf.sqlalchemy.test_uri, **kwargs)
    else:
        new_engine = create_engine(conf.sqlalchemy.db_uri, **kwargs)
    NewBase = declarative_base(new_engine)
    Session = sessionmaker(bind=new_engine)
    new_session = Session()

    return new_engine, new_session, NewBase


def init_integrations():
    from jarr import integrations
    return signal('article_parsing'), signal('feed_creation'), \
            signal('entry_parsing'), integrations


def init_models():
    from jarr import models
    return models


SQLITE_ENGINE = 'sqlite' in (conf.sqlalchemy.test_uri
            if conf.jarr_testing else conf.sqlalchemy.db_uri)
PARSED_PLATFORM_URL = urlparse(conf.platform_url)

init_logging(conf.log.path, log_level=conf.log.level)
engine, session, Base = init_db(SQLITE_ENGINE)
article_parsing, feed_creation, entry_parsing, _ = init_integrations()
init_models()
