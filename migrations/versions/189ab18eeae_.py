"""empty message

Revision ID: 189ab18eeae
Revises: None
Create Date: 2015-07-08 23:03:53.516498

"""

# revision identifiers, used by Alembic.
revision = '189ab18eeae'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('hashtag')
    op.drop_table('user_word')
    op.drop_table('url')
    op.drop_table('user')
    op.drop_table('user_url')
    op.drop_table('item_hashtag')
    op.drop_table('user_hashtag')
    op.drop_table('follower')
    op.drop_table('word')
    op.drop_table('item')
    op.drop_table('item_word')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('item_word',
    sa.Column('item_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('word_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], name='item_word_item_id_fkey'),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], name='item_word_word_id_fkey')
    )
    op.create_table('item',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('item_id_seq'::regclass)"), nullable=False),
    sa.Column('contestant', sa.VARCHAR(length=300), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('message', sa.VARCHAR(length=300), autoincrement=False, nullable=False),
    sa.Column('item_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('item_type', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('item_url', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('location', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('source', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('polarity', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('subjectivity', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('sentiment', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('comment_count', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('favorite_count', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('share_count', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('data', sa.TEXT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='item_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='item_pkey'),
    sa.UniqueConstraint('item_id', name='item_item_id_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('word',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('word_id_seq'::regclass)"), nullable=False),
    sa.Column('word', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='word_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('follower',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('parent_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('child_id', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['user.uid'], name='follower_parent_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='follower_pkey')
    )
    op.create_table('user_hashtag',
    sa.Column('hashtag_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['hashtag_id'], ['hashtag.id'], name='user_hashtag_hashtag_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='user_hashtag_user_id_fkey')
    )
    op.create_table('item_hashtag',
    sa.Column('hashtag_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('item_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['hashtag_id'], ['hashtag.id'], name='item_hashtag_hashtag_id_fkey'),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], name='item_hashtag_item_id_fkey')
    )
    op.create_table('user_url',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('url_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['url_id'], ['url.id'], name='user_url_url_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='user_url_user_id_fkey')
    )
    op.create_table('user',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('user_id_seq'::regclass)"), nullable=False),
    sa.Column('uid', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('screen_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('followers_count', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('friends_count', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('statuses_count', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('rank', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='user_pkey'),
    sa.UniqueConstraint('screen_name', name='user_screen_name_key'),
    sa.UniqueConstraint('uid', name='user_uid_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('url',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('url', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='url_pkey')
    )
    op.create_table('user_word',
    sa.Column('word_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='user_word_user_id_fkey'),
    sa.ForeignKeyConstraint(['word_id'], ['word.id'], name='user_word_word_id_fkey')
    )
    op.create_table('hashtag',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('hashtag', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='hashtag_pkey')
    )
    ### end Alembic commands ###
