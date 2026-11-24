import {api} from '../api/studio.js';
import {empty, heading, panelTitle, status} from '../components/common/ui.js';
import {formSubmit} from '../hooks/interaction.js';
import {canEdit, crewName, studio} from '../stores/studio.js';
import {esc} from '../utils/format.js';

export function reportList(reports) {
  return reports.length ? `<div class="table-wrap"><table><thead><tr><th>记录</th><th>特征版本</th><th>独立留出组</th><th>状态</th><th>报告</th></tr></thead><tbody>
  ${reports.map(item => `<tr><td class="mono">#${item.id}</td><td>${esc(item.plan_name)}</td><td>${esc(crewName(item.holdout))}</td><td>${status(item.status)}</td><td><a class="text-link" href="#/reports/${item.id}">打开 →</a></td></tr>`).join('')}
  </tbody></table></div>` : empty('暂无可查看的比选记录。分析员可提交版本，业务负责人审核后发布给观察员。');
}

function preview(root, selected) {
  const included = studio.crews.filter(crew => crew.samples);
  root.querySelector('#partition-preview').innerHTML = `<div class="partition-strip">${included.map(crew => `<div class="${crew.code === selected ? 'held' : ''}"><span class="mono">${crew.code}</span><strong>${esc(crew.name)}</strong><small>${crew.samples} 条 · ${crew.code === selected ? '独立留出' : '开发'}</small></div>`).join('')}</div>
    <p class="subtle">开发组各做一折验证，同一摄制组的工单始终一起划分。独立留出组只用于最终评估。</p>`;
}

export function runsPage(root) {
  const groups = studio.crews.filter(crew => crew.samples > 0);
  const ready = groups.length >= 3 && groups.every(crew => crew.samples >= 2) && studio.plans.length > 0;
  root.innerHTML = `${heading('组间泛化', '按组交叉验证', '比较 Lasso 与训练折中位数基线，按开发组平均绝对误差选型。')}
    ${canEdit() ? `<div class="split run-split"><section class="panel">${panelTitle('提交比选任务')}<form id="run-form" class="panel-form">
      <label>特征版本<select name="plan_id" required>${studio.plans.map(plan => `<option value="${plan.id}">${esc(plan.name)} · α ${plan.alpha}</option>`).join('')}</select></label>
      <label>独立留出组<select name="holdout" required>${groups.map(crew => `<option value="${crew.code}" ${crew.code === 'G06' ? 'selected' : ''}>${esc(crew.name)} · ${crew.samples} 条</option>`).join('')}</select></label>
      <p class="subtle">任务提交时冻结工单、特征版本和留出组。</p>
      ${ready ? '' : '<p class="subtle">需要一个特征版本及至少 3 个摄制组，每组至少 2 条工单。</p>'}
      <p class="error" role="alert"></p><button class="accent" type="submit" ${ready ? '' : 'disabled'}>锁定样本并运行</button>
    </form></section><section class="panel preview">${panelTitle('样本分区预览')}<div id="partition-preview"></div></section></div>` : ''}
    <section class="panel history">${panelTitle('运行记录')}${reportList(studio.reports)}</section>`;
  const form = root.querySelector('#run-form');
  if (!form) return;
  const choice = form.elements.holdout;
  preview(root, choice.value);
  choice.onchange = () => preview(root, choice.value);
  formSubmit(form, async data => {
    const report = await api.run({plan_id:Number(data.get('plan_id')), holdout:data.get('holdout')});
    studio.reports = [report, ...studio.reports];
    location.hash = `/reports/${report.id}`;
  });
}
