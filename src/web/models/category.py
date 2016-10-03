from sqlalchemy import (Index, Column, ForeignKey,
                        Integer, String, Boolean)
from sqlalchemy.orm import relationship
from bootstrap import db
from web.models.right_mixin import RightMixin


class Category(db.Model, RightMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    cluster_on_title = Column(Boolean, default=False)

    # relationships
    user_id = Column(Integer, ForeignKey('user.id'))
    feeds = relationship('Feed', backref='category',
                         cascade='all,delete-orphan')
    articles = relationship('Article', back_populates='category',
                            cascade='all,delete-orphan')
    clusters = relationship('Article', back_populates='category')

    # index
    idx_category_uid = Index('user_id')

    # api whitelists
    @staticmethod
    def _fields_base_read():
        return {'id', 'user_id'}

    @staticmethod
    def _fields_base_write():
        return {'name', 'cluster_on_title'}
