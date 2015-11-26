"""add generic id support

Revision ID: 3bc50ecd0bb
Revises: 18ced36d0df
Create Date: 2015-10-28 19:25:26.378971

"""

# chunk size to process tv/movies
PROCESS_CHUNK_SIZE = 5000

# revision identifiers, used by Alembic.
revision = '3bc50ecd0bb'
down_revision = '30688404cda'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence, MetaData
import config

meta = MetaData()

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    dbid = op.create_table('dbids',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('db_id', sa.String(length=50), nullable=True),
        sa.Column('db', sa.Enum('TVRAGE', 'TVMAZE', 'OMDB', 'IMDB', name='enum_dbid_name'), nullable=True),
        sa.Column('tvshow_id', sa.Integer(), nullable=True),
        sa.Column('movie_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )
    op.create_index('idx_db_id_db', 'dbids', ['db_id', 'db'], unique=False)
    op.create_index(op.f('ix_dbids_movie_id'), 'dbids', ['movie_id'], unique=False)
    op.create_index(op.f('ix_dbids_tvshow_id'), 'dbids', ['tvshow_id'], unique=False)

    bind = op.get_bind()

    i = 0

    releases = sa.Table('releases', meta, autoload=True, autoload_with=bind)
    movies = sa.Table('movies', meta, autoload=True, autoload_with=bind)
    tvshows = sa.Table('tvshows', meta, autoload=True, autoload_with=bind)
    episodes = sa.Table('episodes', meta, autoload=True, autoload_with=bind)

    op.drop_constraint('releases_movie_id_fkey', 'releases')
    op.drop_constraint('releases_tvshow_id_fkey', 'releases')
    op.drop_constraint('episodes_tvshow_id_fkey', 'episodes')

    print('Starting ID conversion.')
    for show in bind.execute(tvshows.select().order_by(tvshows.c.id)):
        try:
            print('TVRAGE: {} ({}) -> {}'.format(show[tvshows.c.name], show[tvshows.c.id], i))
        except:
            # it's just for show, it doesn't matter
            pass

        bind.execute(dbid.insert().values(
            id=i,
            db='TVRAGE',
            db_id=show[tvshows.c.id],
            tvshow_id=i
        ))

        bind.execute(releases.update().where(releases.c.tvshow_id==show[tvshows.c.id]).values(tvshow_id=i))
        bind.execute(episodes.update().where(episodes.c.tvshow_id==show[tvshows.c.id]).values(tvshow_id=i))
        bind.execute(tvshows.update().where(tvshows.c.id==show[tvshows.c.id]).values(id=i))

        i += 1

    for movie in bind.execute(movies.select().order_by(movies.c.id)):
        try:
            print('IMDB: {} ({}) -> {}'.format(movie[movies.c.name], movie[movies.c.id], i))
        except:
            pass

        bind.execute(dbid.insert().values(
            id=i,
            db='IMDB',
            db_id='tt{}'.format(movie[movies.c.id]),
            movie_id=i
        ))
        bind.execute(releases.update().where(releases.c.movie_id==movie[movies.c.id]).values(movie_id=i))
        bind.execute(movies.update().where(movies.c.id==movie[movies.c.id]).values(id=i))

        i += 1

    bind.execute(CreateSequence(Sequence('movies_id_seq', start=i)))



    if config.db.get('engine') == 'postgresql':
        bind.execute('ALTER TABLE movies ALTER COLUMN id TYPE INTEGER USING id::integer')
        bind.execute('ALTER TABLE releases ALTER COLUMN movie_id TYPE INTEGER USING movie_id::integer')
    else:
        op.alter_column('movies', 'id',
                   existing_type=sa.VARCHAR(length=20),
                   type_=sa.Integer(),
                   existing_nullable=False,
                   server_default=sa.text('nextval(\'movies_id_seq\'::regclass)')
        )

        op.alter_column('releases', 'movie_id',
                   existing_type=sa.VARCHAR(length=20),
                   type_=sa.Integer(),
                   existing_nullable=False
        )

    op.create_foreign_key('releases_movie_id_fkey', 'releases', 'movies', ['movie_id'], ['id'])
    op.create_foreign_key('releases_tvshow_id_fkey', 'releases', 'tvshows', ['tvshow_id'], ['id'])
    op.create_foreign_key('episodes_tvshow_id_fkey', 'episodes', 'tvshows', ['tvshow_id'], ['id'])
    op.create_foreign_key('dbids_tvshow_id_fkey', 'dbids', 'tvshows', ['tvshow_id'], ['id'])
    op.create_foreign_key('dbids_movie_id_fkey', 'dbids', 'movies', ['movie_id'], ['id'])

    bind.execute("select setval('dbids_id_seq', (select max(id) from dbids));")
    bind.execute("select setval('tvshows_id_seq', (select max(id) from tvshows));")
    bind.execute("select setval('movies_id_seq', (select max(id) from movies));")
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('movies', 'id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.drop_index(op.f('ix_dbids_tvshow_id'), table_name='dbids')
    op.drop_index(op.f('ix_dbids_movie_id'), table_name='dbids')
    op.drop_index('idx_db_id_db', table_name='dbids')
    op.drop_table('dbids')
    ### end Alembic commands ###
