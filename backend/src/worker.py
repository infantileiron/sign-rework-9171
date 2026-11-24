import logging
import time
from pathlib import Path

from src.config.database import cache, connect
from src.constants.domain import METHOD, Status
from src.models import audit, reports
from src.services.comparison import compare
from src.services.reports import digest

log = logging.getLogger(__name__)


def execute_job():
    with connect() as db:
        job = reports.take_job(db)
        if not job:
            return False
        report_id = job['id']
        try:
            snapshot = job['snapshot']
            if snapshot['method'] != METHOD or digest(snapshot) != job['fingerprint']:
                raise ValueError('快照校验失败，请重新创建比选')
            result = compare(snapshot)
        except ValueError as error:
            reports.finish_job(db, report_id, Status.FAILED, None, str(error))
            audit.record(db, None, 'report.fail', report_id)
        except Exception:
            log.exception('Report %s failed', report_id)
            reports.finish_job(db, report_id, Status.FAILED, None, '计算失败，请重新创建比选')
            audit.record(db, None, 'report.fail', report_id)
        else:
            reports.finish_job(db, report_id, Status.SUCCEEDED, result, None)
            audit.record(db, None, 'report.complete', report_id)
        return True


def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            cache.ping()
            completed = execute_job()
            Path('/tmp/heartbeat').touch()
            if not completed:
                time.sleep(0.7)
        except Exception:
            log.exception('Worker loop failed, pending jobs will be retried')
            time.sleep(2)


if __name__ == '__main__':
    main()
