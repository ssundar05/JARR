from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from jarr.bootstrap import Base
from jarr.models.right_mixin import RightMixin


class Category(Base, RightMixin):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    cluster_on_title = Column(Boolean, default=False)

    # foreign keys
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))

    # relationships
    user = relationship('User', back_populates='categories')
    feeds = relationship('Feed', back_populates='category',
                         cascade='all,delete-orphan')
    articles = relationship('Article', back_populates='category',
                            cascade='all,delete-orphan')
    clusters = relationship('Cluster', back_populates='categories',
            foreign_keys='[Article.category_id, Article.cluster_id]',
            secondary='article')

    # index
    ix_category_uid = Index('user_id')

    # api whitelists
    @staticmethod
    def _fields_base_read():
        return {'id', 'user_id'}

    @staticmethod
    def _fields_base_write():
        return {'name', 'cluster_on_title'}
