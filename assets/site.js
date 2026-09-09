document.addEventListener('DOMContentLoaded', () => {
  const interactiveControlSelector = [
    '.button',
    '.brand',
    '.nav-links a',
    '.choice-list a',
    '.card-link',
    '.text-link',
    '.faq summary',
    'button',
    '[role="button"]'
  ].join(',');
  const findInteractiveControl = (target) => {
    if (!target || typeof target.closest !== 'function') return null;
    return target.closest(interactiveControlSelector);
  };
  const controlIsDisabled = (control) => (
    control.matches(':disabled')
    || control.getAttribute('aria-disabled') === 'true'
    || control.getAttribute('aria-busy') === 'true'
    || control.classList.contains('is-disabled')
  );
  const clearPressedControls = () => {
    document.querySelectorAll('.is-pressed').forEach((control) => {
      if (control.matches(interactiveControlSelector)) control.classList.remove('is-pressed');
    });
  };

  document.querySelectorAll(interactiveControlSelector).forEach((control) => {
    control.dataset.interactionFeedback = 'ready';
  });
  document.addEventListener('pointerdown', (event) => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    const control = findInteractiveControl(event.target);
    if (!control || controlIsDisabled(control)) return;
    control.classList.add('is-pressed');
  });
  document.addEventListener('pointerup', clearPressedControls);
  document.addEventListener('pointercancel', clearPressedControls);
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const control = findInteractiveControl(event.target);
    if (!control || controlIsDisabled(control)) return;
    control.classList.add('is-pressed');
  });
  document.addEventListener('keyup', clearPressedControls);
  document.addEventListener('focusout', (event) => {
    findInteractiveControl(event.target)?.classList.remove('is-pressed');
  });
  document.addEventListener('click', (event) => {
    const control = findInteractiveControl(event.target);
    if (!control || !controlIsDisabled(control)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    control.classList.remove('is-pressed');
  }, true);

  let feedbackSequence = 0;
  const safeSupportFallback = (value) => {
    if (value !== '/support/') return '';
    try {
      const fallback = new URL(value, window.location.origin);
      return fallback.origin === window.location.origin && fallback.pathname === '/support/' ? fallback.pathname : '';
    } catch (_error) {
      return '';
    }
  };
  const showControlFeedback = ({control, type, message, fallbackHref = ''} = {}) => {
    if (!(control instanceof Element) || !control.matches(interactiveControlSelector)) return false;
    if (!['busy', 'success', 'error'].includes(type) || typeof message !== 'string' || !message.trim()) return false;
    let feedback = control.dataset.controlFeedbackId && document.getElementById(control.dataset.controlFeedbackId);
    if (!feedback) {
      feedbackSequence += 1;
      feedback = document.createElement('p');
      feedback.id = `official-site-control-feedback-${feedbackSequence}`;
      control.dataset.controlFeedbackId = feedback.id;
      control.insertAdjacentElement('afterend', feedback);
    }
    feedback.className = `control-feedback control-feedback--${type}`;
    feedback.setAttribute('role', type === 'error' ? 'alert' : 'status');
    feedback.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
    feedback.replaceChildren(document.createTextNode(message.trim()));
    const safeFallback = type === 'error' ? safeSupportFallback(fallbackHref) : '';
    if (safeFallback) {
      const separator = document.createTextNode(' ');
      const link = document.createElement('a');
      link.href = safeFallback;
      link.textContent = '查看帳號與客服說明';
      feedback.append(separator, link);
    }
    control.setAttribute('aria-describedby', feedback.id);
    if (type === 'busy') control.setAttribute('aria-busy', 'true');
    else control.removeAttribute('aria-busy');
    return true;
  };
  if (typeof window.addEventListener === 'function') {
    window.addEventListener('dealalliance:control-feedback', (event) => showControlFeedback(event.detail));
  }
  window.DealAllianceControlFeedback = Object.freeze({show: showControlFeedback});

  const canonicalAppRoot = 'https://app.dealalliancehub.com/';
  const entryTimeouts = new WeakMap();
  const addEntryFeedback = () => {
    document.querySelectorAll('a[href]').forEach((link) => {
      if (link.href === canonicalAppRoot) link.dataset.accountPortal = link.dataset.accountPortal || 'my-tools';
    });
  };
  const clearEntryTimeout = (control) => {
    const timeout = entryTimeouts.get(control);
    if (timeout) window.clearTimeout(timeout);
    entryTimeouts.delete(control);
  };
  const navigationWillStayOnPage = (event) => (
    event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0
  );
  addEntryFeedback();
  document.addEventListener('click', (event) => {
    const control = findInteractiveControl(event.target);
    if (!control || navigationWillStayOnPage(event) || controlIsDisabled(control)) return;
    const href = control.getAttribute('href');
    if (href !== canonicalAppRoot) return;
    clearEntryTimeout(control);
    showControlFeedback({control, type: 'busy', message: '正在開啟成交聯盟 App…'});
    const sourceUrl = window.location.href;
    const timeout = window.setTimeout(() => {
      entryTimeouts.delete(control);
      if (document.visibilityState === 'visible' && window.location.href === sourceUrl) {
        showControlFeedback({
          control,
          type: 'error',
          message: '目前無法開啟成交聯盟 App。請檢查網路後再試，',
          fallbackHref: '/support/'
        });
      }
    }, 3000);
    entryTimeouts.set(control, timeout);
  });

  const config = window.DEAL_ALLIANCE_SITE_CONFIG || {};

  const accountPortalUrlIsAllowed = (value) => {
    if (!value || !['enabled', 'login_only'].includes(config.accountPortalMode)) return false;
    let portal;
    try { portal = new URL(value, window.location.origin); } catch (_error) { return false; }
    if (portal.protocol !== 'https:') return false;
    if (portal.username || portal.password || portal.search || portal.hash || portal.pathname !== '/') return false;
    const allowed = Array.isArray(config.accountPortalAllowedOrigins) ? config.accountPortalAllowedOrigins : [];
    return allowed.includes(portal.origin);
  };

  const registrationOpen = config.accountPortalMode === 'enabled';
  if (!accountPortalUrlIsAllowed(config.accountPortalLoginUrl)) return;
  if (registrationOpen && !accountPortalUrlIsAllowed(config.accountPortalRegisterUrl)) return;
  document.querySelectorAll('.nav').forEach((nav) => {
    if (nav.querySelector('[data-account-portal]')) return;
    const login = document.createElement('a');
    login.href = config.accountPortalLoginUrl;
    login.className = 'button button-ghost nav-account-entry';
    login.dataset.accountPortal = 'my-tools';
    login.textContent = '登入我的工具';
    const primaryCta = nav.querySelector('.nav-cta, .button-primary');
    if (primaryCta) {
      primaryCta.insertAdjacentElement('beforebegin', login);
    } else {
      nav.append(login);
    }
    if (registrationOpen) {
      const register = document.createElement('a');
      register.href = config.accountPortalRegisterUrl;
      register.className = 'button button-primary nav-account-entry';
      register.dataset.accountPortal = 'get-started';
      register.textContent = '建立帳號';
      login.insertAdjacentElement('afterend', register);
    }
  });

  document.querySelectorAll('[data-account-entry]').forEach((guide) => {
    guide.href = config.accountPortalLoginUrl;
    guide.hidden = false;
  });
  addEntryFeedback();

  const subscriptionBoundary = config.monthlySubscriptionBoundary || {};
  const canRenderSubscriptionBoundary = config.accountPortalMode === 'login_only'
    && subscriptionBoundary.mode === 'login_only_candidate'
    && ['title', 'trial', 'consent', 'cancellation', 'closed'].every((key) => (
      typeof subscriptionBoundary[key] === 'string' && subscriptionBoundary[key].trim()
    ));
  const boundaryPaths = new Set(['/', '/tools/', '/refund/']);
  if (canRenderSubscriptionBoundary && boundaryPaths.has(window.location.pathname)) {
    document.querySelectorAll('main').forEach((main) => {
      if (main.querySelector('[data-monthly-subscription-boundary]')) return;
      const section = document.createElement('section');
      section.className = 'section section-cream';
      section.dataset.monthlySubscriptionBoundary = 'login-only-candidate';
      const container = document.createElement('div');
      container.className = 'container';
      const notice = document.createElement('div');
      notice.className = 'notice';
      const title = document.createElement('strong');
      title.textContent = subscriptionBoundary.title;
      const copy = document.createElement('span');
      copy.textContent = ` ${subscriptionBoundary.trial} ${subscriptionBoundary.consent} ${subscriptionBoundary.cancellation} ${subscriptionBoundary.closed}`;
      notice.append(title, copy);
      container.append(notice);
      section.append(container);
      main.prepend(section);
    });
  }

  const commercialOffer = config.commercialOffer || {};
  const commercialProductIds = [
    'contact_converter', 'smart_close', 'line_macos', 'line_windows', 'birthday_sms', 'bulk_sms'
  ];
  const commercialProducts = Array.isArray(commercialOffer.products) ? commercialOffer.products : [];
  const canRenderCommercialOffer = config.accountPortalMode === 'login_only'
    && commercialOffer.mode === 'login_only_candidate'
    && accountPortalUrlIsAllowed(config.accountPortalLoginUrl)
    && commercialProducts.length === commercialProductIds.length
    && commercialProducts.every((product, index) => (
      product && product.id === commercialProductIds[index]
      && typeof product.name === 'string' && product.name.trim()
      && typeof product.monthly === 'string' && product.monthly.trim()
    ))
    && commercialOffer.ctaState === 'closed'
    && ['title', 'individualTitle', 'bundleTitle', 'bundleMonthly', 'bundleAnnual', 'bundleTerms', 'fixedPriceTerms', 'selectionTerms', 'deviceTerms', 'availabilityTerms'].every((key) => (
      typeof commercialOffer[key] === 'string' && commercialOffer[key].trim()
    ));
  const commercialPaths = new Set(['/', '/tools/']);
  if (canRenderCommercialOffer && commercialPaths.has(window.location.pathname)) {
    document.querySelectorAll('main').forEach((main) => {
      if (main.querySelector('[data-monthly-commercial-offer]')) return;
      const section = document.createElement('section');
      section.className = 'section section-paper';
      section.dataset.monthlyCommercialOffer = 'login-only-candidate';
      section.dataset.commercialOfferCta = 'closed';
      const container = document.createElement('div');
      container.className = 'container';
      const heading = document.createElement('div');
      heading.className = 'section-heading';
      const headingCopy = document.createElement('div');
      const title = document.createElement('h2');
      title.textContent = commercialOffer.title;
      const individualTitle = document.createElement('p');
      individualTitle.className = 'section-kicker';
      individualTitle.textContent = commercialOffer.individualTitle;
      headingCopy.append(individualTitle, title);
      const summary = document.createElement('p');
      summary.textContent = commercialOffer.bundleTerms;
      heading.append(headingCopy, summary);
      const grid = document.createElement('div');
      grid.className = 'grid grid-3';
      commercialProducts.forEach((product) => {
        const card = document.createElement('article');
        card.className = 'card';
        card.dataset.commercialSku = product.id;
        const name = document.createElement('h3');
        name.textContent = product.name;
        const monthly = document.createElement('p');
        const price = document.createElement('strong');
        price.textContent = product.monthly;
        monthly.append(price);
        card.append(name, monthly);
        if (typeof product.note === 'string' && product.note.trim()) {
          const note = document.createElement('p');
          note.textContent = product.note;
          card.append(note);
        }
        grid.append(card);
      });
      const bundle = document.createElement('div');
      bundle.className = 'notice';
      const bundleTitle = document.createElement('strong');
      bundleTitle.textContent = commercialOffer.bundleTitle;
      const bundleCopy = document.createElement('p');
      bundleCopy.textContent = `${commercialOffer.bundleMonthly}；${commercialOffer.bundleAnnual}。${commercialOffer.bundleTerms}`;
      const fixedPrice = document.createElement('p');
      fixedPrice.textContent = commercialOffer.fixedPriceTerms;
      const selection = document.createElement('p');
      selection.textContent = commercialOffer.selectionTerms;
      const devices = document.createElement('p');
      devices.textContent = commercialOffer.deviceTerms;
      const availability = document.createElement('p');
      availability.textContent = commercialOffer.availabilityTerms;
      bundle.append(bundleTitle, bundleCopy, fixedPrice, selection, devices, availability);
      container.append(heading, grid, bundle);
      section.append(container);
      const boundary = main.querySelector('[data-monthly-subscription-boundary]');
      if (boundary) boundary.insertAdjacentElement('afterend', section);
      else main.prepend(section);
    });
  }

  document.querySelectorAll('.fine-print').forEach((finePrint) => {
    if (finePrint.querySelector('[data-service-guides]')) return;
    const guides = document.createElement('span');
    guides.dataset.serviceGuides = 'true';
    guides.innerHTML = '<a href="/support/">帳號與客服說明</a>　<a href="/refund/">付款與退款說明</a>';
    finePrint.append(guides);
  });
});
