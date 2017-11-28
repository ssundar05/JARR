#! /usr/bin/env python
# -*- coding: utf-8 -*-
import calendar
import pytz
import logging
from flask import Flask
from jarr.bootstrap import conf, session, PARSED_PLATFORM_URL


def init_babel(app):
    from flask import request
    from flask_babel import Babel
    from babel import Locale

    babel = Babel(app)

    @babel.localeselector
    def get_flask_locale():
        from jarr_common.utils import clean_lang
        for locale_id in request.accept_languages.values():
            try:
                return Locale(clean_lang(locale_id))
            except Exception:
                continue
        return Locale(conf.babel.locale)

    @babel.timezoneselector
    def get_flask_timezone():
        from flask_login import current_user
        return pytz.timezone(current_user.timezone or conf.babel.timezone)

    return get_flask_locale, get_flask_timezone


def load_blueprints(app):
    from jarr import views
    with app.app_context():
        views.session_mgmt.load(app)
        app.register_blueprint(views.articles_bp)
        app.register_blueprint(views.cluster_bp)
        app.register_blueprint(views.feeds_bp)
        app.register_blueprint(views.feed_bp)
        app.register_blueprint(views.icon_bp)
        app.register_blueprint(views.admin_bp)
        app.register_blueprint(views.users_bp)
        app.register_blueprint(views.user_bp)
        app.register_blueprint(views.session_mgmt.oauth_bp)
        views.api.feed.load(app)
        views.api.category.load(app)
        views.api.cluster.load(app)
        views.api.article.load(app)
        views.home.load(app)
        views.views.load(app)

    app.jinja_env.filters['month_name'] = lambda n: calendar.month_name[n]
    app.jinja_env.autoescape = False


application = Flask(__name__)
application.config.from_object(conf)
if conf.jarr_testing:
    application.debug = True
    application.config['TESTING'] = True
    conf.crawler.nbworker = 1
    application.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
else:
    application.debug = conf.log.level <= logging.DEBUG
application.config['SERVER_NAME'] = PARSED_PLATFORM_URL.netloc
application.config['PREFERRED_URL_SCHEME'] = PARSED_PLATFORM_URL.scheme

init_babel(application)
load_blueprints(application)


@application.teardown_request
def session_clear(exception=None):
    if exception and session.is_active:
        session.rollback()


if __name__ == '__main__':  # pragma: no cover
    application.run(host=conf.webserver.host,
                    port=conf.webserver.port,
                    debug=True)
