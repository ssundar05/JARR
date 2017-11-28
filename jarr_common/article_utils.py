import html
import logging
import re
from datetime import timezone
from enum import Enum
from urllib.parse import SplitResult, urlsplit, urlunsplit

import dateutil.parser
from requests.exceptions import MissingSchema
from the_conf import TheConf

from jarr_common.html_parsing import extract_tags, extract_title, extract_lang
from jarr_common.utils import jarr_get, utc_now
from jarr_common.clustering_af.word_utils import extract_valuable_tokens
from jarr.lib.article_cleaner import clean_urls

logger = logging.getLogger(__name__)
PROCESSED_DATE_KEYS = {'published', 'created', 'updated'}
FETCHABLE_DETAILS = {'link', 'title', 'tags', 'lang'}


def extract_id(entry):
    """ extract a value from an entry that will identify it among the other of
    that feed"""
    return entry.get('entry_id') or entry.get('id') or entry['link']


def construct_article(entry, feed, fields=None, fetch=True):
    "Safe method to transorm a feedparser entry into an article"
    now = utc_now()
    article = {}

    def push_in_article(key, *args):
        """feeding article with entry[key]
        if 'fields' is None or if key in 'fields'.
        You can either pass on value or a callable and some args to feed it"""
        if fields and key not in fields:
            return
        if len(args) == 1:
            value = args[0]
        else:
            value = args[0](*args[1:])
        article[key] = value
    push_in_article('feed_id', feed['id'])
    push_in_article('user_id', feed['user_id'])
    push_in_article('entry_id', extract_id, entry)
    push_in_article('retrieved_date', now)
    if not fields or 'date' in fields:
        for date_key in PROCESSED_DATE_KEYS:
            if entry.get(date_key):
                try:
                    article['date'] = dateutil.parser.parse(entry[date_key])\
                            .astimezone(timezone.utc)
                except Exception:
                    pass
                else:
                    break
    push_in_article('content', get_entry_content, entry)
    push_in_article('comments', entry.get, 'comments')
    push_in_article('lang', get_entry_lang, entry)
    if fields is None or FETCHABLE_DETAILS.intersection(fields):
        details = get_article_details(entry, fetch)
        for detail, value in details.items():
            if not article.get(detail):
                push_in_article(detail, value)
        if details.get('tags') and article.get('tags'):
            push_in_article('tags',
                            set(details['tags']).union, article['tags'])
        if 'content' in article and details.get('link'):
            push_in_article('content',
                            clean_urls, article['content'], details['link'])
    push_in_article('valuable_tokens', extract_valuable_tokens, article)
    return article


def get_entry_content(entry):
    content = ''
    if entry.get('content'):
        content = entry['content'][0]['value']
    elif entry.get('summary'):
        content = entry['summary']
    return content


def get_entry_lang(entry):
    lang = None
    if entry.get('content', []):
        lang = (entry['content'][0] or {}).get('language')
        if lang:
            return lang
    for sub_key in 'title_detail', 'summary_detail':
        lang = entry.get(sub_key, {}).get('language')
        if lang:
            return lang


def _fetch_article(link):
    try:
        # resolves URL behind proxies (like feedproxy.google.com)
        return jarr_get(link, timeout=5)
    except MissingSchema:
        split = urlsplit(link)
        for scheme in 'https', 'http':
            new_link = urlunsplit(SplitResult(scheme, *split[1:]))
            try:
                return jarr_get(new_link, timeout=5)
            except Exception as error:
                continue
    except Exception as error:
        logger.info("Unable to get the real URL of %s. Won't fix "
                    "link or title. Error: %s", link, error)


def get_article_details(entry, fetch=True):
    conf = TheConf()
    detail = {'title': html.unescape(entry.get('title', '')),
              'link': entry.get('link'),
              'tags': {tag.get('term', '').lower().strip()
                       for tag in entry.get('tags', [])
                       if tag.get('term', '').strip()}}
    missing_elm = any(not detail.get(key) for key in ('title', 'tags', 'lang'))
    if fetch and detail['link'] and (conf.crawler.resolv or missing_elm):
        response = _fetch_article(detail['link'])
        if response is None:
            return detail
        detail['link'] = response.url
        if not detail['title']:
            detail['title'] = extract_title(response)
        detail['tags'] = detail['tags'].union(extract_tags(response))
        lang = extract_lang(response)
        if lang:
            detail['lang'] = lang
    return detail


class FiltersAction(Enum):
    READ = 'mark as read'
    LIKED = 'mark as favorite'
    SKIP = 'skipped'


class FiltersType(Enum):
    REGEX = 'regex'
    MATCH = 'simple match'
    EXACT_MATCH = 'exact match'
    TAG_MATCH = 'tag match'
    TAG_CONTAINS = 'tag contains'


class FiltersTrigger(Enum):
    MATCH = 'match'
    NO_MATCH = 'no match'


def _is_filter_to_skip(filter_action, only_actions, article):
    if filter_action not in only_actions:
        return True
    if filter_action in {FiltersType.REGEX, FiltersType.MATCH,
            FiltersType.EXACT_MATCH} and 'title' not in article:
        return True
    if filter_action in {FiltersType.TAG_MATCH, FiltersType.TAG_CONTAINS} \
            and 'tags' not in article:
        return True
    return False


def _is_filter_matching(filter_, article):
    pattern = filter_.get('pattern', '')
    filter_type = FiltersType(filter_.get('type'))
    filter_trigger = FiltersTrigger(filter_.get('action on'))
    if filter_type is not FiltersType.REGEX:
        pattern = pattern.lower()
    title = article.get('title', '').lower()
    tags = [tag.lower() for tag in article.get('tags', [])]
    if filter_type is FiltersType.REGEX:
        match = re.match(pattern, title)
    elif filter_type is FiltersType.MATCH:
        match = pattern in title
    elif filter_type is FiltersType.EXACT_MATCH:
        match = pattern == title
    elif filter_type is FiltersType.TAG_MATCH:
        match = pattern in tags
    elif filter_type is FiltersType.TAG_CONTAINS:
        match = any(pattern in tag for tag in tags)
    return match and filter_trigger is FiltersTrigger.MATCH \
            or not match and filter_trigger is FiltersTrigger.NO_MATCH


def process_filters(filters, article, only_actions=None):
    skipped, read, liked = False, None, False
    filters = filters or []
    if only_actions is None:
        only_actions = set(FiltersAction)
    for filter_ in filters:
        filter_action = FiltersAction(filter_.get('action'))

        if _is_filter_to_skip(filter_action, only_actions, article):
            logger.debug('ignoring filter %r', filter_)
            continue

        if not _is_filter_matching(filter_, article):
            continue

        if filter_action is FiltersAction.READ:
            read = True
        elif filter_action is FiltersAction.LIKED:
            liked = True
        elif filter_action is FiltersAction.SKIP:
            skipped = True

    if skipped or read or liked:
        logger.info("%r applied on %r", filter_action.value,
                    article.get('link') or article.get('title'))
    return skipped, read, liked


def get_skip_and_ids(entry, feed):
    entry_ids = construct_article(entry, feed,
                {'entry_id', 'feed_id', 'user_id'}, fetch=False)
    skipped, _, _ = process_filters(feed['filters'],
            construct_article(entry, feed, {'title', 'tags'}, fetch=False),
            {FiltersAction.SKIP})
    return skipped, entry_ids
