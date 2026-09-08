const CFG = window.APP_CONFIG || {};

if (CFG.SUPABASE_URL && CFG.SUPABASE_ANON_KEY) {
  const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
  const authClient = createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
  });

  const $ = id => document.getElementById(id);
  const loginBtn = $('loginBtn');
  const accountBtn = $('accountBtn');
  const accountOverlay = $('accountOverlay');

  async function refreshAccountUI() {
    const { data } = await authClient.auth.getSession();
    const signedIn = !!data.session;
    if (accountBtn) accountBtn.classList.toggle('hidden', !signedIn);
  }

  async function passwordLogin(event) {
    event.preventDefault();
    event.stopImmediatePropagation();

    const email = $('emailInput')?.value.trim() || '';
    const password = $('passwordInput')?.value || '';
    const msg = $('loginMsg');

    if (!email || !password) {
      msg.textContent = '请输入邮箱和密码。';
      return;
    }

    loginBtn.disabled = true;
    msg.textContent = '正在登录…';

    const { error } = await authClient.auth.signInWithPassword({ email, password });

    if (error) {
      const text = (error.message || '').toLowerCase();
      if (text.includes('invalid login credentials')) {
        msg.textContent = '邮箱或密码不正确。如果还没有设置密码，请先在已登录的电脑端点“账号”设置密码。';
      } else if (text.includes('email not confirmed')) {
        msg.textContent = '这个邮箱还没有完成确认。';
      } else {
        msg.textContent = `登录失败：${error.message}`;
      }
      loginBtn.disabled = false;
      return;
    }

    msg.textContent = '登录成功，正在进入…';
    location.reload();
  }

  if (loginBtn) {
    // Capture phase prevents the old Magic-Link onclick in app.js from firing.
    loginBtn.addEventListener('click', passwordLogin, true);
  }

  if (accountBtn) {
    accountBtn.addEventListener('click', async () => {
      const { data } = await authClient.auth.getSession();
      if (!data.session) {
        location.reload();
        return;
      }
      $('accountMsg').textContent = '';
      $('newPasswordInput').value = '';
      accountOverlay.classList.remove('hidden');
    });
  }

  $('closeAccountBtn')?.addEventListener('click', () => accountOverlay.classList.add('hidden'));

  $('savePasswordBtn')?.addEventListener('click', async () => {
    const pwd = $('newPasswordInput').value;
    const msg = $('accountMsg');
    if (pwd.length < 8) {
      msg.textContent = '建议使用至少 8 位密码。';
      return;
    }

    $('savePasswordBtn').disabled = true;
    msg.textContent = '正在保存…';
    const { error } = await authClient.auth.updateUser({ password: pwd });
    $('savePasswordBtn').disabled = false;

    if (error) {
      msg.textContent = `保存失败：${error.message}`;
      return;
    }

    msg.textContent = '密码已保存。现在手机可以直接用“邮箱 + 这个密码”登录。';
  });

  $('signOutBtn')?.addEventListener('click', async () => {
    await authClient.auth.signOut();
    location.reload();
  });

  accountOverlay?.addEventListener('click', e => {
    if (e.target === accountOverlay) accountOverlay.classList.add('hidden');
  });

  authClient.auth.onAuthStateChange(() => refreshAccountUI());
  await refreshAccountUI();
}
