"""empty message

Revision ID: 2dd6f931bf
Revises: 1a6275e2796
Create Date: 2015-07-20 14:15:19.267017

"""

# revision identifiers, used by Alembic.
revision = '2dd6f931bf'
down_revision = '1a6275e2796'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import *

metadata = MetaData()

def upgrade():
    op.add_column('item',
        Column('group_item_id', VARCHAR(100), autoincrement=False, 
            server_default="0", nullable=False))


    # op.add_column('item',
    #     Column('group_item_id', VARCHAR(100), autoincrement=False, nullable=True))
    # new = Table('item', Column('group_item_id'))
    # original_id = Table('item', Column('item_id'))
    # op.execute(new.update().values(group_item_id=original_id))
    # op.alter_column('item', 'group_item_id', nullable=False)




def downgrade():
    with op.batch_alter_table("item") as batch_op:
        batch_op.drop_column('group_item_id')