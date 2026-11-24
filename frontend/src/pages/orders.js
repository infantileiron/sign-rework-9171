import {api} from '../api/studio.js';
import {empty, heading, intakeFields, intakeValues, numeric, panelTitle, stat} from '../components/common/ui.js';
import {formSubmit} from '../hooks/interaction.js';
import {canEdit, crewName, settlementOf, studio} from '../stores/studio.js';
import {esc, fixed, timecode} from '../utils/format.js';

const stateLabel = {aligned: '已对齐', waiting: '等待对齐', unsettled: '未补流水'};
const reasonLabel = {matched: '已对上', missing: '流水没到', unbalanced: '分摊对不上'};

function stateChip(state) {
  return `<span class="settle-state ${esc(state)}">${esc(stateLabel[state] ?? state)}</span>`;
}

function table() {
  const rows = studio.orders.filter(row => !studio.orderFilter || row.crew === studio.orderFilter);
  if (!rows.length) return empty('该组暂无结算工单。请切换分组，或录入已结算的历史工单。');
  return `<div class="table-wrap"><table><thead><tr><th>编号 / 视频</th><th>摄制组</th><th>成片 / 分钟</th><th>镜头</th><th>换景</th><th>返工 / h</th><th>结算</th><th>操作</th></tr></thead><tbody>${rows.map(row => {
    const detail = settlementOf(row.code);
    const state = detail?.state ?? 'unsettled';
    const serials = detail?.serials ?? [];
    return `
    <tr><td><small class="mono row-code">${esc(row.code)}</small><strong>${esc(row.title)}</strong></td>
    <td>${esc(crewName(row.crew))}</td><td class="mono" title="${fixed(row.minutes)} 分钟">${timecode(row.minutes)} <small>${fixed(row.minutes)}</small></td>
    <td class="mono">${row.shots}</td><td class="mono">${row.switches}</td><td class="mono actual">${fixed(row.hours)}</td>
    <td>${stateChip(state)}${serials.length ? `<button class="plain serial-count" data-ledger="${esc(row.code)}">${serials.length} 笔流水</button>` : ''}</td>
    <td>${canEdit() ? `<button class="plain" data-edit="${esc(row.code)}">修订</button>` : `<button class="plain" data-ledger="${esc(row.code)}">流水</button>`}</td></tr>`;
  }).join('')}</tbody></table></div>`;
}

function ledgerRows(detail) {
  if (!detail?.serials.length) return empty('这张工单还没有登记流水。结算补录后，这里会列出用过的流水。');
  return `<div class="table-wrap"><table><thead><tr><th>流水号</th><th>本单分摊 h</th><th>记工原数 h</th><th>共用工单</th><th>对账</th></tr></thead><tbody>${detail.serials.map(row => `
    <tr><td class="mono">${esc(row.serial)}</td><td class="mono">${fixed(row.allocated)}</td>
    <td class="mono">${row.ledger === null ? '—' : fixed(row.ledger)}</td>
    <td>${row.shared_with.length ? row.shared_with.map(esc).join('、') : '<span class="muted">仅本单</span>'}</td>
    <td><span class="serial-chip ${esc(row.reason)}">${esc(reasonLabel[row.reason])}</span></td></tr>`).join('')}</tbody></table></div>`;
}

function waitingBlock(detail) {
  if (!detail || detail.state !== 'waiting') return '';
  return `<div class="waiting-note"><p><b>整组等待切换</b>　共用流水的工单要一起对齐才会切换样本，间接相连的也算。</p>
    <ul>${detail.component_waiting.map(item => `<li><span class="mono">${esc(item.serial)}</span>${esc(reasonLabel[item.reason])} · ${item.orders.map(esc).join('、')}</li>`).join('')}</ul></div>`;
}

function ledgerDialog(root, rerender, order) {
  const dialog = root.querySelector('#ledger-dialog');
  const detail = settlementOf(order.code);
  const missing = detail?.component_waiting?.filter(item => item.reason === 'missing') ?? [];
  dialog.innerHTML = `<div class="panel-head"><h2>${esc(order.code)} · 结算流水</h2><button class="plain" type="button" data-close>关闭</button></div>
    <div class="ledger-summary">${stateChip(detail?.state ?? 'unsettled')}
      <span>现用样本 <b class="mono">${order.hours === null ? '—' : fixed(order.hours)} h</b></span>
      <span>本单分摊合计 <b class="mono">${detail?.pending_hours == null ? '—' : fixed(detail.pending_hours)} h</b></span></div>
    ${ledgerRows(detail)}
    ${missing.length ? `<div class="missing-note"><b>没到的流水</b><p>${missing.map(item => esc(item.serial)).join('、')} 尚未出现在记工台账，等待补传。</p></div>` : ''}
    ${waitingBlock(detail)}
    <p class="subtle">已对齐的组会用分摊后的工时进入比选；未对齐期间仍用旧样本。</p>`;
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  dialog.showModal();
}

function editor(root, rerender, order) {
  const dialog = root.querySelector('#order-dialog');
  const settled = Boolean(order && settlementOf(order.code)?.serials.length);
  dialog.innerHTML = `<form id="order-form"><div class="panel-head"><h2>${order ? '修订工单' : '录入结算工单'}</h2><button class="plain" type="button" data-close>关闭</button></div>
    <label>工单号<input name="code" required pattern="[A-Z][A-Z0-9\\-]{2,19}" value="${esc(order?.code)}" placeholder="QY-0609" ${order ? 'readonly' : ''}></label>
    <label>视频名称<input name="title" required maxlength="90" value="${esc(order?.title)}" placeholder="轮渡服务｜无障碍乘船指引"></label>
    <label>摄制组<select name="crew" required>${studio.crews.map(crew => `<option value="${crew.code}" ${crew.code === order?.crew ? 'selected' : ''}>${esc(crew.name)}</option>`).join('')}</select></label>
    <div class="fields">${intakeFields(order)}</div>
    ${numeric('实际返工工时（h）', 'hours', {min:0,max:200,step:'any',value:order?.hours})}
    ${settled ? '<p class="subtle">这张工单的工时由结算单分摊决定。如需改动，请在「结算补录」中调整流水分摊。</p>' : ''}
    <p class="error" role="alert"></p><button class="accent" type="submit">保存工单</button>
  </form>`;
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  formSubmit(dialog.querySelector('form'), async form => {
    const data = {...intakeValues(form), title:form.get('title'), crew:form.get('crew'), hours:Number(form.get('hours'))};
    if (!order) data.code = form.get('code');
    await api.saveOrder(data, order?.code);
    [studio.orders, studio.crews, studio.settlement] = await Promise.all([api.orders(), api.crews(), api.settlements()]);
    dialog.close();
    rerender();
  });
  dialog.showModal();
}

const workLogRow = () => `<div class="entry-row"><input name="log-serial" placeholder="流水号，例 JS-0001" pattern="[A-Z0-9][A-Z0-9\\-]{1,39}">
  <input name="log-hours" type="number" min="0.01" max="100000" step="any" placeholder="记工原数 h"><button type="button" class="plain" data-drop>移除</button></div>`;

const allocRow = () => `<div class="entry-row"><select name="alloc-order">${studio.orders.map(row => `<option value="${esc(row.code)}">${esc(row.code)} · ${esc(row.title)}</option>`).join('')}</select>
  <input name="alloc-serial" placeholder="流水号" pattern="[A-Z0-9][A-Z0-9\\-]{1,39}"><input name="alloc-hours" type="number" min="0" max="200" step="any" placeholder="分摊 h"><button type="button" class="plain" data-drop>移除</button></div>`;

function settlementEditor(root, rerender) {
  const dialog = root.querySelector('#settlement-dialog');
  dialog.innerHTML = `<form id="settlement-form"><div class="panel-head"><h2>结算补录</h2><button class="plain" type="button" data-close>关闭</button></div>
    <label>结算单号<input name="sheet_no" required maxlength="64" placeholder="JS-0609"></label>
    <fieldset><legend>按工单分摊（多张工单共用一笔流水时合计要等于记工原数）</legend><div id="alloc-rows">${allocRow()}</div><button class="plain" type="button" id="add-alloc">＋ 添加分摊</button></fieldset>
    <p class="subtle">结算单上的流水号若还没补传记工，会显示为「没到的流水」；这组工单继续用旧样本，整组对齐后一次性切换。</p>
    <p class="error" role="alert"></p><button class="accent" type="submit">保存结算单</button>
  </form>`;
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  const form = dialog.querySelector('form');
  const bindDrop = container => container.querySelectorAll('[data-drop]').forEach(button =>
    button.onclick = () => button.closest('.entry-row').remove());
  bindDrop(form);
  dialog.querySelector('#add-alloc').onclick = () => { form.querySelector('#alloc-rows').insertAdjacentHTML('beforeend', allocRow()); bindDrop(form); };
  formSubmit(form, async data => {
    const allocations = data.getAll('alloc-serial')
      .map((serial, index) => ({order: data.getAll('alloc-order')[index], serial: serial.trim(),
                                hours: Number(data.getAll('alloc-hours')[index])}))
      .filter(row => row.serial);
    if (!allocations.length) throw new Error('至少登记一笔工单分摊');
    studio.settlement = await api.saveSettlement({sheet_no: data.get('sheet_no'), allocations});
    [studio.orders, studio.crews] = await Promise.all([api.orders(), api.crews()]);
    dialog.close();
    rerender();
  });
  dialog.showModal();
}

function reconciliation() {
  const waiting = studio.settlement.waiting_orders ?? [];
  const missing = studio.settlement.missing_serials ?? [];
  const unbalanced = studio.settlement.unbalanced_serials ?? [];
  if (!waiting.length && !missing.length && !unbalanced.length) {
    return `<p class="subtle section-note">所有结算流水已对上，样本按最近一次切换进入比选。</p>`;
  }
  return `<div class="reconcile-summary">
    ${missing.length ? `<div><span>没到的流水</span><p class="mono">${missing.map(esc).join('、')}</p></div>` : ''}
    ${unbalanced.length ? `<div><span>分摊对不上</span><p class="mono">${unbalanced.map(esc).join('、')}</p></div>` : ''}
    ${waiting.length ? `<div><span>等待切换工单</span><p>${waiting.map(code => `<button class="plain text-link" data-ledger="${esc(code)}">${esc(code)}</button>`).join('、')}</p></div>` : ''}
    <p class="subtle">这些工单所在组仍使用旧样本；同组流水全部对上后一次性切换。</p></div>`;
}

function ledgerUpload(root, rerender) {
  const dialog = root.querySelector('#ledger-upload-dialog');
  dialog.innerHTML = `<form id="ledger-upload-form"><div class="panel-head"><h2>记工流水补传</h2><button class="plain" type="button" data-close>关闭</button></div>
    <p class="subtle">按流水号补传记工原数。重传同一流水只覆盖原数，不会重复计入工时；已用这笔流水的工单会随之重新对账。</p>
    <fieldset><legend>记工流水</legend><div id="upload-rows">${workLogRow()}</div><button class="plain" type="button" id="add-upload">＋ 添加流水</button></fieldset>
    <p class="error" role="alert"></p><button class="accent" type="submit">补传流水</button>
  </form>`;
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  const form = dialog.querySelector('form');
  const bindDrop = () => form.querySelectorAll('[data-drop]').forEach(button =>
    button.onclick = () => button.closest('.entry-row').remove());
  bindDrop();
  dialog.querySelector('#add-upload').onclick = () => {
    form.querySelector('#upload-rows').insertAdjacentHTML('beforeend', workLogRow()); bindDrop();
  };
  formSubmit(form, async data => {
    const entries = data.getAll('log-serial')
      .map((serial, index) => ({serial: serial.trim(), hours: Number(data.getAll('log-hours')[index])}))
      .filter(row => row.serial);
    if (!entries.length) throw new Error('至少登记一笔记工流水');
    studio.settlement = await api.saveWorkLogs(entries);
    [studio.orders, studio.crews] = await Promise.all([api.orders(), api.crews()]);
    dialog.close();
    rerender();
  });
  dialog.showModal();
}

export function ordersPage(root, rerender) {
  const waiting = studio.settlement.waiting_orders ?? [];
  root.innerHTML = `${heading('历史结算', '工单样本', '按摄制组整理历史结算。结算流水按工单分摊，对账通过后才进入比选样本。',
    canEdit() ? '<div class="page-actions"><button id="ledger-upload" class="button">记工补传</button><button id="settlement" class="button">结算补录</button><button id="new-order" class="accent">录入结算工单</button></div>' : '')}
    <div class="metrics">${stat('结算工单', studio.orders.length, '条')}${stat('等待对齐', waiting.length, '条')}${stat('没到流水', (studio.settlement.missing_serials ?? []).length, '笔')}</div>
    <div class="split"><section class="panel">${panelTitle('结算台账', `<label class="inline">按组查看<select id="crew-filter"><option value="">全部摄制组</option>${studio.crews.map(crew => `<option value="${crew.code}" ${crew.code === studio.orderFilter ? 'selected' : ''}>${esc(crew.name)}</option>`).join('')}</select></label>`)}${table()}</section>
    <aside class="panel roster">${panelTitle('摄制组名册')}<p class="subtle section-note">整组划分训练与测试样本。</p><ul>${studio.crews.map(crew => `<li><span class="mono">${crew.code}</span><b>${esc(crew.name)}</b><span class="mono">${crew.samples} 条</span></li>`).join('')}</ul><a class="text-link" href="#/plans">查看候选特征 →</a></aside></div>
    <section class="panel history">${panelTitle('结算对账')}${reconciliation()}</section>
    <dialog id="order-dialog"></dialog><dialog id="ledger-dialog"></dialog><dialog id="settlement-dialog"></dialog><dialog id="ledger-upload-dialog"></dialog>`;
  root.querySelector('#crew-filter').onchange = event => { studio.orderFilter = event.target.value; rerender(); };
  root.querySelector('#new-order')?.addEventListener('click', () => editor(root, rerender));
  root.querySelector('#settlement')?.addEventListener('click', () => settlementEditor(root, rerender));
  root.querySelector('#ledger-upload')?.addEventListener('click', () => ledgerUpload(root, rerender));
  root.querySelectorAll('[data-edit]').forEach(button => button.onclick = () => editor(root, rerender, studio.orders.find(row => row.code === button.dataset.edit)));
  root.querySelectorAll('[data-ledger]').forEach(button => button.onclick = () =>
    ledgerDialog(root, rerender, studio.orders.find(row => row.code === button.dataset.ledger)));
}
