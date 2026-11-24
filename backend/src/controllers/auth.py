import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.database import cache, connect
from src.utils.errors import Problem
from src.utils.security import password_hash, verify


bearer = HTTPBearer(auto_error=False)
secret = os.environ['JWT_SECRET']
issuer = 'sign-rework'
dummy = password_hash('unused', '0' * 32)


def login(request: Request, email, password):
    client = request.client.host if request.client else 'unknown'
    window = int(datetime.now(timezone.utc).timestamp()) // 60
    key = f'login:{client}:{window}'
    with cache.pipeline() as tx:
        count, _ = tx.incr(key).expire(key, 120).execute()
    if count > 40:
        raise Problem(429, '登录请求过多，请一分钟后重试')
    with connect() as db:
        row = db.execute('SELECT * FROM accounts WHERE email=%s', (email.lower(),)).fetchone()
    valid = verify(password, row['password_hash'] if row else dummy)
    if not row or not valid:
        raise Problem(401, '邮箱或密码错误')
    user = {key: row[key] for key in ('email', 'display_name', 'role')}
    token = jwt.encode({'sub': row['email'], 'iss': issuer,
                        'exp': datetime.now(timezone.utc) + timedelta(hours=8)}, secret, algorithm='HS256')
    return {'token': token, 'user': user}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise Problem(401, '请先登录')
    try:
        claims = jwt.decode(credentials.credentials, secret, algorithms=['HS256'], issuer=issuer,
                            options={'require': ['exp', 'sub', 'iss']})
    except jwt.InvalidTokenError as exc:
        raise Problem(401, '登录已失效，请重新登录') from exc
    with connect() as db:
        user = db.execute('SELECT email, display_name, role FROM accounts WHERE email=%s', (claims['sub'],)).fetchone()
    if not user:
        raise Problem(401, '登录已失效，请重新登录')
    return user


def allow(*roles):
    def check(user=Depends(current_user)):
        if user['role'] not in roles:
            raise Problem(403, '此操作需要对应的工作台权限')
        return user
    return check
