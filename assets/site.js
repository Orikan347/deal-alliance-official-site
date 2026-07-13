document.addEventListener('DOMContentLoaded', () => {
  const config = window.DEAL_ALLIANCE_SITE_CONFIG || {};
  const accountPortalUrlIsAllowed = (value) => {
    if (!value || config.accountPortalMode !== 'enabled') return false;
    let portal;
    try { portal = new URL(value, window.location.origin); } catch (_error) { return false; }
    if (portal.protocol !== 'https:' && portal.origin !== window.location.origin) return false;
    const allowed = Array.isArray(config.accountPortalAllowedOrigins) ? config.accountPortalAllowedOrigins : [];
    return portal.origin === window.location.origin || allowed.includes(portal.origin);
  };
  const renderAccountPortalEntry = () => {
    if (!accountPortalUrlIsAllowed(config.accountPortalRegisterUrl) || !accountPortalUrlIsAllowed(config.accountPortalLoginUrl)) return;
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
  };
  renderAccountPortalEntry();

  const addResetControl = (container) => {
    if (container.querySelector('[data-demo-reset]')) return container.querySelector('[data-demo-reset]');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button button-secondary';
    button.dataset.demoReset = '';
    button.textContent = '清除／取消';
    container.querySelector('.demo-controls')?.append(button);
    return button;
  };
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
    if (!form.querySelector('button[type="reset"]')) {
      const reset = document.createElement('button');
      reset.type = 'reset';
      reset.className = 'button button-secondary';
      reset.textContent = '清除／取消';
      form.querySelector('button[type="submit"]')?.insertAdjacentElement('afterend', reset);
    }
    form.dataset.mode = remoteEnabled ? 'enabled' : 'local-only';
    if (contact) {
      contact.required = remoteEnabled;
      contact.type = remoteEnabled ? 'email' : 'text';
      contact.placeholder = remoteEnabled ? '例如：name@example.com' : '正式端點啟用後才會送出';
    }
    // Consent is required even for the local-only path so the candidate does
    // not teach a visitor that a future waitlist submission can skip consent.
    if (consent) consent.required = true;

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      result.classList.add('show');
      if (consent && !consent.checked) {
        result.textContent = '請先勾選同意，才能送出候補／洽詢。';
        return;
      }
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
    form.addEventListener('reset', () => {
      window.setTimeout(() => { result.textContent = ''; result.classList.remove('show'); }, 0);
    });
  });

  document.querySelectorAll('[data-demo="contact-converter"]').forEach((demo) => {
    const input = demo.querySelector('[data-demo-input]');
    const output = demo.querySelector('[data-demo-output]');
    const button = demo.querySelector('[data-demo-run]');
    const download = demo.querySelector('[data-demo-download]');
    let vcard = '';
    addResetControl(demo);
    button.addEventListener('click', () => {
      const rows = input.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
      const invalid = rows.findIndex((row) => {
        const parts = row.split(',').map((part) => part.trim());
        return parts.length !== 3 || !parts[0] || !parts[1] || !parts[2] || !parts[2].includes('@');
      });
      if (invalid >= 0) {
        vcard = '';
        output.textContent = `第 ${invalid + 1} 行格式不正確；請使用：姓名,電話,email`;
        download.hidden = true;
        return;
      }
      const cards = rows.slice(0, 20).map((row) => {
        const [name = '', phone = '', email = ''] = row.split(',').map((part) => part.trim());
        return ['BEGIN:VCARD', 'VERSION:3.0', `FN:${name || '未命名測試聯絡人'}`, phone && `TEL:${phone}`, email && `EMAIL:${email}`, 'END:VCARD'].filter(Boolean).join('\n');
      });
      vcard = cards.join('\n');
      output.textContent = cards.length ? `已在本機產生 ${cards.length} 筆 VCF 預覽；沒有上傳或保存。` : '請輸入假資料，每行格式：姓名,電話,email';
      download.hidden = !cards.length;
    });
    download.addEventListener('click', () => {
      if (!vcard) return;
      const blob = new Blob([vcard], { type: 'text/vcard;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url; anchor.download = 'deal-alliance-demo.vcf'; anchor.click();
      URL.revokeObjectURL(url);
    });
    demo.querySelector('[data-demo-reset]')?.addEventListener('click', () => {
      input.value = '';
      vcard = '';
      output.textContent = '已清除本機示範結果。';
      download.hidden = true;
    });
  });

  document.querySelectorAll('[data-demo="smart-close"]').forEach((demo) => {
    const input = demo.querySelector('[data-demo-input]');
    const output = demo.querySelector('[data-demo-output]');
    addResetControl(demo);
    demo.querySelector('[data-demo-run]').addEventListener('click', () => {
      const text = input.value.trim();
      const name = (text.match(/(?:我是|叫|客戶是)([\u4e00-\u9fff]{2,4})/) || [])[1] || '測試客戶';
      output.textContent = text ? `本機示範結果\n對象：${name}\n已確認：${text.slice(0, 80)}\n下一步：補上一個可確認的時間與責任人。\n（未呼叫 AI、未保存內容）` : '請輸入一段去識別化對話，再執行本機示範。';
    });
    demo.querySelector('[data-demo-reset]')?.addEventListener('click', () => {
      input.value = '';
      output.textContent = '已清除本機示範結果。';
    });
  });

  document.querySelectorAll('[data-demo="sms-preview"]').forEach((demo) => {
    const name = demo.querySelector('[data-demo-name]');
    const message = demo.querySelector('[data-demo-message]');
    const output = demo.querySelector('[data-demo-output]');
    addResetControl(demo);
    const render = () => { output.textContent = `收件人：${name.value || '測試聯絡人'}\n內容：${message.value || '請輸入一段測試訊息'}\n\n這只是預覽，沒有發送。`; };
    demo.querySelector('[data-demo-run]').addEventListener('click', render);
    render();
    demo.querySelector('[data-demo-reset]')?.addEventListener('click', () => {
      name.value = '';
      message.value = '';
      output.textContent = '已取消並清除本機預覽。';
    });
  });

  document.querySelectorAll('[data-demo="line-preview"]').forEach((demo) => {
    const input = demo.querySelector('[data-demo-input]');
    const output = demo.querySelector('[data-demo-output]');
    addResetControl(demo);
    demo.querySelector('[data-demo-run]').addEventListener('click', () => {
      const steps = input.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).slice(0, 10);
      output.textContent = steps.length ? `本機流程預覽\n${steps.map((step, index) => `${index + 1}. ${step}`).join('\n')}\n\n這只是流程預覽，沒有登入 LINE 或發送訊息。` : '請每行輸入一個去識別化流程步驟。';
    });
    demo.querySelector('[data-demo-reset]')?.addEventListener('click', () => {
      input.value = '';
      output.textContent = '已取消並清除流程預覽。';
    });
  });
});
