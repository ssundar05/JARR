import base64

from jarr_common.utils import jarr_get

from jarr.bootstrap import session
from jarr.models import Icon

from .abstract import AbstractController


class IconController(AbstractController):
    _db_cls = Icon
    _user_id_key = None

    @staticmethod
    def _build_from_url(attrs):
        if 'url' in attrs and 'content' not in attrs:
            try:
                resp = jarr_get(attrs['url'])
            except Exception:
                return attrs
            attrs.update({'url': resp.url,
                    'mimetype': resp.headers.get('content-type', None),
                    'content': base64.b64encode(resp.content).decode('utf8')})
        return attrs

    def create(self, **attrs):
        return super().create(**self._build_from_url(attrs))

    def update(self, filters, attrs, *args, **kwargs):
        attrs = self._build_from_url(attrs)
        return super().update(filters, attrs, *args, **kwargs)

    def delete(self, url):
        obj = self.get(url=url)
        session.delete(obj)
        session.commit()
        return obj
