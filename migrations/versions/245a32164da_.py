"""empty message

Revision ID: 245a32164da
Revises: None
Create Date: 2015-07-09 16:17:01.240459

"""

# revision identifiers, used by Alembic.
revision = '245a32164da'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, VARCHAR

def upgrade():
    op.add_column('item',
        # Column('team', VARCHAR(50), nullable=False)
        Column('team', VARCHAR(50))
    )


def downgrade():
    op.drop_column('team')
