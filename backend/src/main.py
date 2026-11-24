import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from scripts.seed_demo import seed
from src.config.database import cache, connect, migrate
from src.middlewares.http import problem_handler, request_identity, response_policy, validation_handler
from src.routes import reports, studio
from src.utils.errors import Problem


@asynccontextmanager
async def lifespan(app):
    migrate()
    if os.getenv('SEED_DEMO', 'true').lower() == 'true':
        try:
            seed()
        except Exception:
            logging.exception('Demo seed failed')
    yield


app = FastAPI(title='桥语手语 · 视频返工工时比选', lifespan=lifespan)
app.add_exception_handler(Problem, problem_handler)
app.add_exception_handler(RequestValidationError, validation_handler)
app.middleware('http')(request_identity)
app.middleware('http')(response_policy)
app.include_router(studio.router)
app.include_router(reports.router)


@app.get('/health')
def health():
    try:
        with connect() as db:
            db.execute('SELECT 1 FROM reports LIMIT 1')
        cache.ping()
    except Exception as exc:
        raise Problem(503, '数据库或缓存不可用') from exc
    return {'status': 'ok'}
