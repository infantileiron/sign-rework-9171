import {api, loadStudio} from '../api/studio.js';
import {formSubmit} from '../hooks/interaction.js';
import {session} from '../stores/session.js';
import {studio} from '../stores/studio.js';

export function login(root, enter, expired = false) {
  root.innerHTML = `<main class="login-page">
    <section class="login-hero">
      <div class="identity"><i class="mark" aria-hidden="true">Ⅲ</i><span>桥语手语<small>制作工作台</small></span></div>
      <div><p class="eyebrow">制作运营 / 排期评估</p><h1>视频返工<br>工时比选</h1><p class="description">用结算工单估计新片返工工时，保留整支摄制组检验排期偏差。</p></div>
      <div class="login-timeline" aria-hidden="true">
        <div class="ruler"><span>00:00:00</span><span>00:02:00</span><span>00:04:00</span><span>00:06:00</span></div>
        <div class="track"><b>V1</b><i>成片时长</i><i>镜头数</i><i>背景切换</i></div>
        <div class="track secondary"><b>QA</b><i>开发组交叉验证</i><i>留出组</i></div>
      </div>
    </section>
    <section class="login-side"><form id="login-form">
      <h2>登录工作台</h2>
      <div class="demo-roles" aria-label="填入演示账号"><button type="button" data-role="analyst">分析员</button><button type="button" data-role="owner">业务负责人</button><button type="button" data-role="viewer">观察员</button></div>
      <label>邮箱<input name="email" type="email" autocomplete="username" placeholder="analyst@bridge.test" required></label>
      <label>密码<input name="password" type="password" autocomplete="current-password" required></label>
      <p class="error" role="alert">${expired ? '登录已失效，请重新登录。' : ''}</p>
      <button class="accent" type="submit">登录</button>
    </form></section>
  </main>`;
  const form = root.querySelector('#login-form');
  form.querySelectorAll('[data-role]').forEach(button => button.onclick = () => {
    form.elements.email.value = `${button.dataset.role}@bridge.test`;
    form.elements.password.value = 'Qiaoyu2026!';
  });
  formSubmit(form, async data => {
    const result = await api.login(Object.fromEntries(data));
    session.set(result.token);
    try { await loadStudio(); }
    catch (error) { session.clear(); throw error; }
    studio.user = result.user;
    enter();
  });
}
