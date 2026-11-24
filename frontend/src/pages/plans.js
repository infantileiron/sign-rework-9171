import {api} from '../api/studio.js';
import {empty, heading, numeric, panelTitle} from '../components/common/ui.js';
import {features} from '../constants/domain.js';
import {formSubmit} from '../hooks/interaction.js';
import {canEdit, studio} from '../stores/studio.js';
import {esc} from '../utils/format.js';

export function plansPage(root, rerender) {
  root.innerHTML = `${heading('模型配置', '候选特征', '只使用接单时可知的三个字段。每次保存都会建立可复跑的特征版本。', '<a class="button" href="#/runs">去按组验证 →</a>')}
    <div class="split ${canEdit() ? 'editor-split' : ''}"><section class="panel">${panelTitle('版本库', `<span class="mono subtle">${studio.plans.length} 个版本</span>`)}
    ${studio.plans.length ? `<div class="versions">${studio.plans.map(plan => `<article>
      <span class="row-code mono">V${String(plan.id).padStart(2,'0')}</span><h3>${esc(plan.name)}</h3>
      <div class="feature-track">${plan.features.map(key => `<span>${features[key]}</span>`).join('')}</div><div class="mono subtle">α = ${plan.alpha}</div>
    </article>`).join('')}</div>` : empty('暂无候选版本，需要由分析员先选择接单特征。')}
    </section>${canEdit() ? `<aside class="panel">${panelTitle('新建特征版本')}<form id="plan-form" class="panel-form">
    <label>版本名<input name="name" required maxlength="64" placeholder="例：时长＋镜头 · v3"></label>
    ${numeric('正则强度 α', 'alpha', {min:.001,max:100,step:'any',value:.1})}
    <fieldset><legend>接单特征</legend>${Object.entries(features).map(([key,label]) => `<label class="check"><input type="checkbox" name="features" value="${key}" checked>${label}</label>`).join('')}</fieldset>
    <p class="subtle">α 越大，越容易压缩弱特征的系数。实际工时只用于训练目标和误差核对。</p>
    <p class="error" role="alert"></p><button type="submit" class="accent">保存新版本</button></form></aside>` : ''}</div>`;
  formSubmit(root.querySelector('#plan-form'), async data => {
    await api.savePlan({name:data.get('name'), alpha:Number(data.get('alpha')), features:data.getAll('features')});
    studio.plans = await api.plans();
    rerender();
  });
}
