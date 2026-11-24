import csv
import hashlib
import io
import json

from src.constants.domain import METHOD
from src.models import audit, orders, plans, reports
from src.services.comparison import validate_sample
from src.utils.errors import Problem


def digest(snapshot):
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def enqueue(db, plan_id, holdout, actor):
    samples = orders.list_orders(db)
    plan = plans.get_plan(db, plan_id)
    validate_sample(samples, holdout)
    snapshot = {'orders': samples, 'plan': {key: plan[key] for key in ('id', 'name', 'alpha', 'features')},
                'holdout': holdout, 'method': METHOD}
    report = reports.create_report(db, snapshot, digest(snapshot), actor)
    audit.record(db, actor, 'report.queue', report['id'])
    return report


def require_result(report):
    if not report['result']:
        raise Problem(409, '报告尚无可用结果')
    return report['result']


def rows_csv(report):
    result = require_result(report)
    buffer = io.StringIO()
    buffer.write('\ufeff')
    writer = csv.writer(buffer)
    writer.writerow(['report_id', 'snapshot_sha256', 'method', 'plan_id', 'alpha', 'features', 'selected_model',
                     'partition', 'test_crew', 'train_crews', 'order', 'actual_h', 'lasso_h', 'median_h'])
    plan = report['plan']
    prefix = [report['id'], report['fingerprint'], report['method'], plan['id'], plan['alpha'],
              '|'.join(plan['features']), result['winner']]
    partitions = [('development', fold) for fold in result['folds']] + [('holdout', result['holdout'])]
    for partition, fold in partitions:
        for row in fold['predictions']:
            writer.writerow([*prefix, partition, fold['crew'], '|'.join(fold['train_crews']), row['code'],
                             *(f'{row[key]:.8f}' for key in ('actual', 'lasso', 'baseline'))])
    return buffer.getvalue()
