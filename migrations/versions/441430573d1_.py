"""empty message

Revision ID: 441430573d1
Revises: 245a32164da
Create Date: 2015-07-10 19:56:58.335049

"""

# revision identifiers, used by Alembic.
revision = '441430573d1'
down_revision = '245a32164da'


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, VARCHAR, Boolean

def upgrade():
    op.add_column('item', Column('sentiment_bayes', VARCHAR(100)))
    op.add_column('item', Column('sentiment_textblob', VARCHAR(100)))
    op.add_column('item', Column('verified_user', Boolean, default=False))


def downgrade():
    op.drop_column('sentiment_textblob')
    op.drop_column('sentiment_bayes')
    op.drop_column('verified_user')

