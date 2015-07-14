"""empty message

Revision ID: 1093bfaf344
Revises: 441430573d1
Create Date: 2015-07-14 16:21:01.505077

"""

# revision identifiers, used by Alembic.
revision = '1093bfaf344'
down_revision = '441430573d1'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('retweet_growth',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('item_id_seq'::regclass)"), nullable=False),
    sa.Column('item_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('date_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('elapsed_time', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('share_count', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.item_id'], name='retweet_growth_item_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='retweet_growth_pkey'),
    postgresql_ignore_search_path=False
    )


def downgrade():
    op.drop_table('retweet_growth')

