"""empty message

Revision ID: 1a6275e2796
Revises: 716bd436db
Create Date: 2015-07-17 21:06:52.341269

"""

# revision identifiers, used by Alembic.
revision = '1a6275e2796'
down_revision = '716bd436db'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, VARCHAR, ForeignKey



def upgrade():
    op.add_column('url',
        Column('item_id', VARCHAR(100), ForeignKey('item.item_id'), autoincrement=False, nullable=False)
    )




def downgrade():
    with op.batch_alter_table("url") as batch_op:
    	batch_op.drop_column('item_id')