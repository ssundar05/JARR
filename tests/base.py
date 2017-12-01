from os import path
import json
import logging
import unittest
from base64 import b64encode

from flask_login import login_user, logout_user
from flask_testing import TestCase
from werkzeug.exceptions import NotFound
from the_conf import TheConf

from wsgi import create_app
from jarr.bootstrap import conf, session, Base, init_db, SQLITE_ENGINE
from jarr_common.utils import default_handler
from tests.fixtures.filler import populate_db


logger = logging.getLogger('jarr')


class BaseJarrTest(TestCase):
    _contr_cls = lambda x=1: None
    SQLALCHEMY_DATABASE_URI = conf.sqlalchemy.test_uri
    TESTING = True
    _application = None

    def create_app(self):
        self._application = create_app()
        return self._application

    def _get_from_contr(self, obj_id, user_id=None):
        return self._contr_cls(user_id).get(id=obj_id).dump()

    def _test_controller_rights(self, obj, user):
        obj_id = obj['id']

        # testing with logged user
        with self._application.test_request_context():
            login_user(user)
            self.assertEqual(obj, self._get_from_contr(obj_id))
            self.assertEqual(obj, self._get_from_contr(obj_id, user.id))
            self.assertRaises(NotFound, self._get_from_contr, obj_id, 99)
            # fetching non existent object
            self.assertRaises(NotFound, self._get_from_contr, 99, user.id)
            logout_user()

        # testing with pure jarr rights management
        self.assertEqual(obj, self._get_from_contr(obj_id))
        self.assertEqual(obj, self._get_from_contr(obj_id, user.id))
        # fetching non existent object
        self.assertRaises(NotFound, self._get_from_contr, 99, user.id)
        # fetching object with inexistent user
        self.assertRaises(NotFound, self._get_from_contr, obj_id, 99)
        # fetching object with wrong user
        self.assertRaises(NotFound, self._get_from_contr, obj_id, user.id + 1)
        self.assertRaises(NotFound, self._contr_cls().delete, 99)
        self.assertRaises(NotFound, self._contr_cls(user.id).delete, 99)
        self.assertEqual(obj['id'],
                self._contr_cls(user.id).delete(obj_id).id)
        self.assertRaises(NotFound, self._contr_cls(user.id).delete, obj_id)

    @staticmethod
    def _drop_all():
        for table in ('tag', 'article', 'cluster', 'feed', 'category',
                      '"user"', 'icon'):
            session.execute('DROP TABLE IF EXISTS %s CASCADE' % table)
        session.commit()
        session.flush()

    def setUp(self):
        init_db(SQLITE_ENGINE)
        self._drop_all()
        Base.metadata.create_all()
        populate_db()

    def tearDown(self):
        self._drop_all()
        TheConf._TheConf__instance = None
        session.close()


class JarrFlaskCommon(BaseJarrTest):

    def setUp(self):
        super().setUp()
        self._application.config['CSRF_ENABLED'] = False
        self._application.config['WTF_CSRF_ENABLED'] = False
        self.app = self._application.test_client()

    def assertStatusCode(self, status_code, response):
        self.assertEqual(status_code, response.status_code,
                "got %d when expecting %d: %r" % (response.status_code,
                    status_code, response.data))

    def _api(self, method_name, *urn_parts, **kwargs):
        method = getattr(self.app, method_name)
        kwargs['headers'] = {'Content-Type': 'application/json'}
        if 'data' in kwargs and not isinstance(kwargs['data'], str):
            kwargs['data'] = json.dumps(kwargs['data'],
                                        default=default_handler)
        if 'user' in kwargs:
            hash_ = bytes('%s:%s' % (kwargs['user'], kwargs['user']), 'utf8')
            hash_ = b64encode(hash_).decode('utf8')
            kwargs['headers']['Authorization'] = 'Basic %s' % hash_
            del kwargs['user']

        urn = path.join(conf.api_root, *map(str, urn_parts))
        kwargs.pop('timeout', None)  # removing timeout non supported by flask
        resp = method(urn, **kwargs)
        if resp.data and resp.content_type == 'application/json':
            resp.json = lambda *a, **kw: json.loads(resp.data.decode('utf8'))
        resp.encoding = 'utf8'
        return resp


if __name__ == '__main__':
    unittest.main()
