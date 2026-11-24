import logging
from uuid import uuid4

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.utils.errors import Problem


log = logging.getLogger(__name__)


async def request_identity(request, call_next):
    request.state.request_id = uuid4().hex
    try:
        response = await call_next(request)
    except Exception:
        log.exception('Request %s failed', request.state.request_id)
        response = JSONResponse({'message': '服务暂不可用，请稍后重试'}, status_code=500)
    response.headers['X-Request-ID'] = request.state.request_id
    return response


async def response_policy(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


async def problem_handler(request, error: Problem):
    return JSONResponse({'message': error.message}, status_code=error.status)


async def validation_handler(request, error: RequestValidationError):
    issue = error.errors()[0]
    location = '.'.join(str(part) for part in issue['loc'][1:])
    labels = {'code': '工单号', 'title': '视频名称', 'crew': '摄制组', 'minutes': '成片分钟',
              'shots': '镜头数', 'switches': '背景切换', 'hours': '实际返工工时', 'name': '版本名',
              'alpha': '正则强度 α', 'features': '候选特征', 'holdout': '留出组', 'plan_id': '特征方案'}
    if issue['type'] == 'value_error':
        message = str(issue['ctx']['error'])
    else:
        message = f'{labels.get(location, location or "提交内容")}格式或范围有误，请检查输入'
    return JSONResponse({'message': message}, status_code=422)
