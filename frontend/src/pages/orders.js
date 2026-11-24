import {api} from '../api/studio.js';
import {intakeFields, intakeValues, heading, numeric, panelTitle, stat, empty} from '../components/common/ui.js';
import {formSubmit} from '../hooks/interaction.js';
import {canEdit, crewName, studio} from '../stores/studio.js';
import {esc, fixed, timecode} from '../utils/format.js';

function table() {
  const rows = studio.orders.filter(row => !studio.orderFilter || row.crew === studio.orderFilter);
  if (!rows.length) return empty('该组暂无结算工单。请切换分组，或录入已结算的历史工单。');
  return `<div class="table-wrap"><table><thead><tr><th>编号 / 视频</th><th>摄制组</th><th>成片 / 分钟</th><th>镜头</th><th>换景</th><th>返工 / h</th>${canEdit() ? '<th>操作</th>' : ''}</tr></thead><tbody>${rows.map(row => `
    <tr><td><small class="mono row-code">${esc(row.code)}</small><strong>${esc(row.title)}</strong></td>
    <td>${esc(crewName(row.crew))}</td><td class="mono" title="${fixed(row.minutes)} 分钟">${timecode(row.minutes)} <small>${fixed(row.minutes)}</small></td>
    <td class="mono">${row.shots}</td><td class="mono">${row.switches}</td><td class="mono actual">${fixed(row.hours)}</td>
    ${canEdit() ? `<td><button class="plain" data-edit="${esc(row.code)}">修订</button></td>` : ''}</tr>`).join('')}</tbody></table></div>`;
}

function editor(root, rerender, order) {
  const dialog = root.querySelector('#order-dialog');
  dialog.innerHTML = `<form id="order-form"><div class="panel-head"><h2>${order ? '修订工单' : '录入结算工单'}</h2><button class="plain" type="button" data-close>关闭</button></div>
    <label>工单号<input name="code" required pattern="[A-Z][A-Z0-9\\-]{2,19}" value="${esc(order?.code)}" placeholder="QY-0609" ${order ? 'readonly' : ''}></label>
    <label>视频名称<input name="title" required maxlength="90" value="${esc(order?.title)}" placeholder="轮渡服务｜无障碍乘船指引"></label>
    <label>摄制组<select name="crew" required>${studio.crews.map(crew => `<option value="${crew.code}" ${crew.code === order?.crew ? 'selected' : ''}>${esc(crew.name)}</option>`).join('')}</select></label>
    <div class="fields">${intakeFields(order)}</div>
    ${numeric('实际返工工时（h）', 'hours', {min:0,max:200,step:'any',value:order?.hours})}
    <p class="error" role="alert"></p><button class="accent" type="submit">保存工单</button>
  </form>`;
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  formSubmit(dialog.querySelector('form'), async form => {
    const data = {...intakeValues(form), title:form.get('title'), crew:form.get('crew'), hours:Number(form.get('hours'))};
    if (!order) data.code = form.get('code');
    await api.saveOrder(data, order?.code);
    [studio.orders, studio.crews] = await Promise.all([api.orders(), api.crews()]);
    dialog.close();
    rerender();
  });
  dialog.showModal();
}

export function ordersPage(root, rerender) {
  root.innerHTML = `${heading('历史结算', '工单样本', '按摄制组整理历史结算。每条工单保留接单参数与实际返工工时。', canEdit() ? '<button id="new-order" class="accent">录入结算工单</button>' : '')}
    <div class="metrics">${stat('结算工单', studio.orders.length, '条')}${stat('有样本摄制组', studio.crews.filter(c => c.samples).length, '组')}${stat('实际返工合计', fixed(studio.orders.reduce((sum,row) => sum+row.hours,0), 1), 'h')}</div>
    <div class="split"><section class="panel">${panelTitle('结算台账', `<label class="inline">按组查看<select id="crew-filter"><option value="">全部摄制组</option>${studio.crews.map(crew => `<option value="${crew.code}" ${crew.code === studio.orderFilter ? 'selected' : ''}>${esc(crew.name)}</option>`).join('')}</select></label>`)}${table()}</section>
    <aside class="panel roster">${panelTitle('摄制组名册')}<p class="subtle section-note">整组划分训练与测试样本。</p><ul>${studio.crews.map(crew => `<li><span class="mono">${crew.code}</span><b>${esc(crew.name)}</b><span class="mono">${crew.samples} 条</span></li>`).join('')}</ul><a class="text-link" href="#/plans">查看候选特征 →</a></aside></div>
    <dialog id="order-dialog"></dialog>`;
  root.querySelector('#crew-filter').onchange = event => { studio.orderFilter = event.target.value; rerender(); };
  root.querySelector('#new-order')?.addEventListener('click', () => editor(root, rerender));
  root.querySelectorAll('[data-edit]').forEach(button => button.onclick = () => editor(root, rerender, studio.orders.find(row => row.code === button.dataset.edit)));
}
