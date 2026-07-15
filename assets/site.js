document.addEventListener('DOMContentLoaded', () => {
  const config = window.DEAL_ALLIANCE_SITE_CONFIG || {};

  const accountPortalUrlIsAllowed = (value, requiredPath) => {
    if (!value || config.accountPortalMode !== 'enabled') return false;
    let portal;
    try { portal = new URL(value, window.location.origin); } catch (_error) { return false; }
    if (portal.protocol !== 'https:') return false;
    if (portal.username || portal.password || portal.search || portal.hash || portal.pathname !== requiredPath) return false;
    const allowed = Array.isArray(config.accountPortalAllowedOrigins) ? config.accountPortalAllowedOrigins : [];
    return allowed.includes(portal.origin);
  };

  if (!accountPortalUrlIsAllowed(config.accountPortalRegisterUrl, '/register') || !accountPortalUrlIsAllowed(config.accountPortalLoginUrl, '/login')) return;
  document.querySelectorAll('.nav').forEach((nav) => {
    if (nav.querySelector('[data-account-portal]')) return;
    const register = document.createElement('a');
    register.href = config.accountPortalRegisterUrl;
    register.className = 'button button-primary nav-account-entry';
    register.dataset.accountPortal = 'register';
    register.textContent = '建立帳號';
    const login = document.createElement('a');
    login.href = config.accountPortalLoginUrl;
    login.className = 'button button-ghost nav-account-entry';
    login.dataset.accountPortal = 'login';
    login.textContent = '登入我的工具';
    const primaryCta = nav.querySelector('.nav-cta, .button-primary');
    if (primaryCta) {
      primaryCta.insertAdjacentElement('beforebegin', register);
      register.insertAdjacentElement('beforebegin', login);
    } else {
      nav.append(login, register);
    }
  });
});
