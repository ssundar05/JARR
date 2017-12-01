from datetime import timedelta

from jarr_common.utils import utc_now
from jarr.bootstrap import conf, session
from jarr.controllers import (ArticleController, CategoryController,
                              FeedController, UserController)
from jarr.models import User, Category, Feed, Cluster, Article, Tag, Icon


def populate_db():
    #session.query(Cluster).update({'main_article_id': None})
    #for table in Tag, Article, Cluster, Feed, Icon, Category, User:
    #    session.query(table).delete()
    ucontr = UserController()
    ccontr = CategoryController()
    fcontr = FeedController()
    acontr = ArticleController()
    ccontr = CategoryController()
    ucontr.create(**{'is_admin': True, 'is_api': True,
                     'login': conf.crawler.login,
                     'password': conf.crawler.passwd})
    user1, user2 = [ucontr.create(login=name, email="%s@test.te" % name,
                                  password=name)
                    for name in ["user1", "user2"]]
    now = utc_now()

    article_total = 0
    for k in range(2):

        def to_name(u, iter_, cat=None, feed=None, art=None, *args):
            string = "i%d %s" % (iter_, u.login)
            if cat:
                string += " cat%s" % cat
            if feed is not None:
                string += " feed%s" % feed
            if art is not None:
                string += " art%s" % art
            return string + ''.join(args)
        for user in (user1, user2):
            for i in range(3):
                cat_id = None
                if i:
                    cat_id = ccontr.create(user_id=user.id,
                                           name=to_name(user, k, i)).id
                feed = fcontr.create(link="feed%d%d" % (k, i), user_id=user.id,
                                     category_id=cat_id,
                                     title=to_name(user, k, i, i))
                for j in range(3):
                    entry = to_name(user, k, i, i, j)
                    article_total += 1
                    acontr.create(entry_id=entry,
                            link='http://test.te/%d' % article_total,
                            feed_id=feed.id, user_id=user.id,
                            tags=[to_name(user, k, i, i, j, '1'),
                                  to_name(user, k, i, i, j, '2')],
                            category_id=cat_id, title=entry,
                            date=now + timedelta(seconds=k),
                            content="content %d" % article_total)
