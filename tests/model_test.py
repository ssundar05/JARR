from tests.base import JarrFlaskCommon
import dateutil.parser
from datetime import timedelta
from jarr.controllers import ArticleController, FeedController


class ModelTest(JarrFlaskCommon):

    def assertInRelation(self, obj, relation):
        self.assertTrue(obj in relation, "%r not in %r" % (obj, relation))

    def test_model_relations(self):
        article = ArticleController().read(category_id__ne=None).first()
        # article relations
        self.assertIsNotNone(article.cluster)
        self.assertIsNotNone(article.category)
        self.assertIsNotNone(article.feed)
        # feed parent relation
        self.assertEqual(article.category, article.feed.category)

        self.assertInRelation(article.cluster, article.feed.clusters)
        self.assertInRelation(article.cluster, article.category.clusters)
        self.assertInRelation(article.feed, article.cluster.feeds)
        self.assertInRelation(article.category, article.cluster.categories)

        self.assertInRelation(article.cluster.main_article,
                              article.cluster.articles)

    def test_time(self):
        naive = dateutil.parser.parse('2016-11-17T16:18:02.727802')
        aware = dateutil.parser.parse('2016-11-17T16:18:02.727802+00:00')
        aware2 = dateutil.parser.parse('2016-11-17T16:18:02.727802+12:00')
        fctrl = FeedController()
        self.assertRaises(Exception,
                fctrl.update, {'id': 1}, {'last_retrieved': naive})
        fctrl.update({'id': 1}, {'last_retrieved': aware})
        self.assertEqual(fctrl.read(id=1).first().last_retrieved, aware)

        fctrl.update({'id': 1}, {'last_retrieved': aware2})
        self.assertEqual(fctrl.read(id=1).first().last_retrieved, aware2)
        self.assertEqual(fctrl.read(id=1).first().last_retrieved,
                          aware - timedelta(hours=12))
