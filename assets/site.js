document.addEventListener('DOMContentLoaded', () => {
  const config = window.DEAL_ALLIANCE_SITE_CONFIG || {};
  const endpointIsAllowed = () => {
    if (!config.waitlistEndpoint || config.waitlistMode !== 'enabled') return false;
    let endpoint;
    try { endpoint = new URL(config.waitlistEndpoint, window.location.origin); } catch (_error) { return false; }
    if (endpoint.protocol !== 'https:' && endpoint.origin !== window.location.origin) return false;
    const allowed = Array.isArray(config.waitlistAllowedOrigins) ? config.waitlistAllowedOrigins : [];
    return endpoint.origin === window.location.origin || allowed.includes(endpoint.origin);
  };

  document.querySelectorAll('[data-local-waitlist]').forEach((form) => {
    const result = form.querySelector('.local-result');
    const contact = form.querySelector('[name="contact"]');
    const consent = form.querySelector('[name="consent"]');
    const remoteEnabled = endpointIsAllowed();
    form.dataset.mode = remoteEnabled ? 'enabled' : 'local-only';
    if (contact) {
      contact.required = remoteEnabled;
      contact.type = remoteEnabled ? 'email' : 'text';
      contact.placeholder = remoteEnabled ? '例如：name@example.com' : '正式端點啟用後才會送出';
    }
    if (consent) consent.required = remoteEnabled;

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      result.classList.add('show');
      if (!remoteEnabled) {
        result.textContent = '目前仍是本機候選版：未送出任何資料，也沒有建立候補名單。';
        return;
      }
      if (!form.reportValidity()) return;
      const clientRequestId = crypto.randomUUID ? crypto.randomUUID() : `local-${Date.now()}`;
      const payload = {
        topic: form.elements.topic.value,
        contact: form.elements.contact.value.trim(),
        consent: form.elements.consent.checked,
        source: 'official-site-waitlist',
        client_request_id: clientRequestId
      };
      result.textContent = '正在送出，請稍候。';
      try {
        const response = await fetch(config.waitlistEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(payload),
          credentials: 'omit', redirect: 'error', referrerPolicy: 'strict-origin-when-cross-origin'
        });
        const body = await response.json();
        if (response.status !== 202 || body.ok !== true || body.status !== 'received' || !body.request_id) throw new Error('invalid-readback');
        result.textContent = `已收到你的候補／洽詢（編號 ${String(body.request_id).slice(0, 12)}）。`;
        form.reset();
      } catch (_error) {
        result.textContent = '目前無法完成送出，資料未被視為成功收件；請稍後再試。';
      }
    });
  });
});
