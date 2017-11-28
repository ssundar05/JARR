#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from jarr_common.utils import utc_now

from jarr.bootstrap import conf, create_app, db
from jarr.scripts.probes import ArticleProbe, FeedProbe, FeedLatenessProbe
from jarr.controllers import FeedController, UserController

application = create_app()
logger = logging.getLogger(__name__)
Migrate(application, db)
manager = Manager(application)
manager.add_command('db', MigrateCommand)


@manager.command
def db_create(login='admin', password='admin'):
    "Will create the database from conf parameters."
    admin = {'is_admin': True, 'is_api': True,
             'login': login, 'password': password}
    with application.app_context():
        db.create_all()
        UserController(ignore_context=True).create(**admin)


@manager.command
def fetch(limit=0, retreive_all=False):
    "Crawl the feeds with the client crawler."
    from jarr_crawler.http_crawler import main
    main(conf.crawler.login, conf.crawler.passwd,
         limit=limit, retreive_all=retreive_all)


@manager.command
def reset_feeds():
    """Will reschedule all active feeds to be fetched in the next two hours"""
    fcontr = FeedController(ignore_context=True)
    now = utc_now()
    feeds = [feed[0] for feed in fcontr.get_active_feed()
                                       .with_entities(fcontr._db_cls.id)]

    step = timedelta(seconds=conf.feed.max_expires / len(feeds))
    for i, feed_id in enumerate(feeds):
        fcontr.update({'id': feed_id},
                {'etag': '', 'last_modified': '',
                 'last_retrieved': datetime(1970, 1, 1, tzinfo=timezone.utc),
                 'expires': now + i * step})


manager.add_command('probe_articles', ArticleProbe())
manager.add_command('probe_feeds', FeedProbe())
manager.add_command('probe_feeds_lateness', FeedLatenessProbe())

if __name__ == '__main__':  # pragma: no cover
    manager.run()
