"""changed the type of the column 'last_modified' to string.

Revision ID: 17dcb75f3fe
Revises: cde34831ea
Create Date: 2015-03-10 14:20:53.676344

"""
from datetime import datetime

import sqlalchemy as sa
from alembic import op

from jarr.bootstrap import conf


revision = '17dcb75f3fe'
down_revision = 'cde34831ea'



def upgrade():
    unix_start = datetime(1970, 1, 1)
    if 'sqlite' not in conf.sqlalchemy.db_uri:
        op.drop_column('feed', 'last_modified')
        op.add_column('feed', sa.Column('last_modified', sa.String(),
                      nullable=True, default=unix_start,
                      server_default=str(unix_start)))


def downgrade():
    unix_start = datetime(1970, 1, 1)
    if 'sqlite' not in conf.sqlalchemy.db_uri:
        op.drop_column('feed', 'last_modified')
        op.add_column('feed', sa.Column('last_modified', sa.DateTime(),
                      nullable=True, default=unix_start,
                      server_default=unix_start))
