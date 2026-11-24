import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from redis import Redis


def connect():
    return psycopg.connect(
        host=os.getenv('POSTGRES_HOST', 'db'), port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.environ['POSTGRES_USER'], dbname=os.environ['POSTGRES_DB'],
        password=os.environ['POSTGRES_PASSWORD'], row_factory=dict_row, connect_timeout=4,
    )


cache = Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'), socket_timeout=3)


def migrate():
    with connect() as db:
        db.execute('SELECT pg_advisory_xact_lock(5209)')
        for path in sorted(Path('migrations').glob('*.sql')):
            db.execute(path.read_text())
