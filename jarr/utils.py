# This file provides functions used for:
# - import from a JSON file;
# - generation of tags cloud;
# - HTML processing.
#

import logging
from collections import Counter
from urllib.parse import urljoin, urlparse

import sqlalchemy
from flask import request

from jarr import controllers
from jarr.models import Article

logger = logging.getLogger(__name__)


def is_safe_url(target):
    """
    Ensures that a redirect target will lead to the same server.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    """
    Looks at various hints to find the redirect target.
    """
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def history(user_id, year=None, month=None):
    """
    Sort articles by year and month.
    """
    articles_counter = Counter()
    articles = controllers.ArticleController(user_id).read()
    if year is not None:
        articles = articles.filter(
                sqlalchemy.extract('year', Article.date) == year)
        if month is not None:
            articles = articles.filter(
                    sqlalchemy.extract('month', Article.date) == month)
    for article in articles.all():
        if year is not None:
            articles_counter[article.date.month] += 1
        else:
            articles_counter[article.date.year] += 1
    return articles_counter, articles
