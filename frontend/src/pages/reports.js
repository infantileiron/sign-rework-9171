import {api} from '../api/studio.js';
import {coefficients, foldDetails, maeBars, predictions} from '../components/results.js';
import {empty, heading, intakeFields, intakeValues, panelTitle, status} from '../components/common/ui.js';
import {features, models} from '../constants/domain.js';
import {buttonAction, formSubmit} from '../hooks/interaction.js';
import {waitForReport} from '../hooks/poll.js';
import {crewName, studio} from '../stores/studio.js';
import {esc, fixed} from '../utils/format.js';
import {reportList} from './runs.js';

function resultView(report) {
  const result = report.result;
  const holdout = result.holdout;
  const scale = Math.max(0.01, ...Object.values(result.macro_mae), ...Object.values(holdout.mae));
  return `<div class="split result-split">
    <section class="panel selected">${panelTitle('开发组比选', '<span class="caps">逐组验证</span>')}
      <div class="panel-body"><p class="model-lead">${models[result.winner]}</p><p class="subtle">${result.folds.length} 折等权平均 MAE 决定入选模型。误差越小越好。</p>${maeBars(result.macro_mae, scale)}</div>
    </section>
    <section class="panel independent">${panelTitle('独立留出组', '<span class="caps">最终评估</span>')}
      <div class="panel-body"><p class="model-lead">${esc(crewName(holdout.crew))}</p><p class="subtle">${holdout.test_samples} 条留出工单 · ${holdout.train_samples} 条开发组工单重训</p>${maeBars(holdout.mae, scale)}</div>
    </section>
  </div>
  <div class="split result-split details-split">
    <section class="panel">${panelTitle('Lasso 系数', '<span class="caps">开发组重训</span>')}
      <div class="panel-body">${coefficients(holdout.fit)}<p class="subtle">${result.winner === 'baseline' ? '本次排期使用中位数基线。' : ''}零系数表示该特征在本次拟合中未保留。系数表达关联强度，实际排期还需审核。</p></div>
    </section>
    <section class="panel">${panelTitle('开发组逐折误差', '<span class="caps">Lasso / 基线</span>')}
      ${result.folds.map(foldDetails).join('')}
    </section>
  </div>
  <div class="split result-split details-split">
    <section class="panel">${panelTitle('新片工时试估')}
      <form id="estimate-form" class="panel-form"><p class="subtle">用本报告入选模型估算。超出开发样本范围的特征会标记外推。</p><div class="fields">${intakeFields({minutes:5.5,shots:22,switches:2})}</div>
      <div class="form-actions"><button type="submit" class="accent">估算工时</button><output id="estimate-value" aria-live="polite"></output></div><p class="error" role="alert"></p></form>
    </section>
    <section class="panel">${panelTitle('留出组逐工单核对')}${predictions(holdout.predictions)}</section>
  </div>`;
}

function showReport(root, report, reload) {
  const result = report.result;
  const showPublish = report.status === 'succeeded' && studio.user.role === 'owner';
  root.innerHTML = `${heading('排期解释', `比选报告 <em class="mono">#${report.id}</em>`, `${esc(report.plan.name)} · α ${report.plan.alpha} · ${report.sample_count} 条快照工单`,
    `<div class="page-actions"><a class="button" href="#/reports">返回报告</a>${result ? '<button id="download" class="button">导出 CSV</button>' : ''}${showPublish ? '<button id="publish" class="accent">复核并发布</button>' : ''}</div>`)}
    <div class="snapshot">${status(report.status)}<span title="${esc(report.fingerprint)}">快照 <code>${esc(report.fingerprint.slice(0,16))}</code></span><span>${report.plan.features.map(key => features[key]).join(' / ')}</span></div>
    <p id="report-error" role="alert" class="error">${esc(report.error)}</p>
    ${result ? resultView(report) : empty(report.status === 'queued' ? '已冻结样本，计算进程将自动处理。页面会刷新进度。' : '本次计算未产生结果。可调整 α 或特征方案后重新提交。')}`;
  const msg = root.querySelector('#report-error');
  const download = root.querySelector('#download');
  if (download) download.onclick = () => buttonAction(download, msg, async () => {
    const file = await api.export(report.id);
    const url = URL.createObjectURL(file);
    const link = Object.assign(document.createElement('a'), {href:url, download:`sign-rework-${report.id}.csv`});
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  const publish = root.querySelector('#publish');
  if (publish) publish.onclick = () => buttonAction(publish, msg, async () => {
    await api.publish(report.id);
    reload();
  });
  formSubmit(root.querySelector('#estimate-form'), async data => {
    const output = root.querySelector('#estimate-value');
    output.textContent = '';
    const result = await api.estimate(report.id, intakeValues(data));
    if (!output.isConnected) return;
    const warning = result.outside_range.length ? ` · 外推：${result.outside_range.map(key => features[key]).join('、')}` : '';
    output.textContent = `${fixed(result.hours)} h · ${models[result.model]}${warning}`;
  });
}

export function reportsPage(root, id, reload) {
  if (!id) {
    root.innerHTML = `${heading('发布与复核', '排期解释', '查阅模型系数、独立组误差和逐工单预测，使用已审核结果安排新片返工。')}
      <section class="panel">${panelTitle('比选报告')}${reportList(studio.reports)}</section>`;
    return;
  }
  root.innerHTML = empty('正在读取比选报告…');
  return waitForReport(signal => api.report(id, signal), report => {
    studio.reports = studio.reports.some(item => item.id === report.id)
      ? studio.reports.map(item => item.id === report.id ? report : item) : [report, ...studio.reports];
    showReport(root, report, reload);
  }, error => {
    root.innerHTML = `<section class="panel">${empty(error.message)}<div class="panel-body"><button id="retry" class="button">重试</button> <a class="text-link" href="#/reports">返回报告</a></div></section>`;
    root.querySelector('#retry').onclick = reload;
  });
}
