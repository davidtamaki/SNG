"""empty message

Revision ID: 716bd436db
Revises: 1093bfaf344
Create Date: 2015-07-14 22:45:15.315343

"""

# revision identifiers, used by Alembic.
revision = '716bd436db'
down_revision = '1093bfaf344'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column

def upgrade():
    op.add_column('retweet_growth',
        Column('creation_date', postgresql.TIMESTAMP(), nullable=False)
    )


def downgrade():
    op.drop_column('creation_date')
