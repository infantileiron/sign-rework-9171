from enum import StrEnum


class Role(StrEnum):
    OWNER = 'owner'
    ANALYST = 'analyst'
    VIEWER = 'viewer'


class Status(StrEnum):
    QUEUED = 'queued'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    PUBLISHED = 'published'


FEATURES = {'minutes': '成片分钟', 'shots': '镜头数', 'switches': '背景切换'}
METHOD = 'logo-lasso-v1'
