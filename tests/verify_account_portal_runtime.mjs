#!/usr/bin/env node
/**
 * Executes the real public-site account-entry code with a minimal DOM.
 * Every endpoint is fictional and no network or form submission is possible.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = fs.readFileSync(path.join(root, 'assets/site.js'), 'utf8');
const registerUrl = 'https://app.example.invalid/register';
const loginUrl = 'https://app.example.invalid/login';

function render(config) {
  const entries = [];
  let onReady;
  const primaryCta = { insertAdjacentElement: (_position, element) => entries.push(element) };
  const nav = {
    querySelector(selector) {
      if (selector === '[data-account-portal]') return null;
      if (selector === '.nav-cta, .button-primary') return primaryCta;
      return null;
    },
    append: (...elements) => entries.push(...elements),
  };
  const document = {
    addEventListener(event, handler) { if (event === 'DOMContentLoaded') onReady = handler; },
    createElement() {
      return {
        dataset: {},
        insertAdjacentElement: (_position, element) => entries.push(element),
      };
    },
    querySelectorAll(selector) { return selector === '.nav' ? [nav] : []; },
  };
  const window = {
    DEAL_ALLIANCE_SITE_CONFIG: config,
    location: { origin: 'https://www.dealalliancehub.com' },
    setTimeout() {},
  };
  vm.runInNewContext(source, { document, window, URL, crypto: { randomUUID: () => 'fake-request-id' } });
  assert.equal(typeof onReady, 'function', 'site script must register a DOM-ready handler');
  onReady();
  return entries.map((entry) => ({ text: entry.textContent, href: entry.href, kind: entry.dataset.accountPortal }));
}

const valid = {
  accountPortalRegisterUrl: registerUrl,
  accountPortalLoginUrl: loginUrl,
  accountPortalAllowedOrigins: ['https://app.example.invalid'],
  accountPortalMode: 'enabled',
};

assert.deepEqual(render({ ...valid, accountPortalMode: 'disabled' }), []);
assert.deepEqual(render({ ...valid, accountPortalLoginUrl: '' }), []);
assert.deepEqual(render({ ...valid, accountPortalAllowedOrigins: ['https://other.example.invalid'] }), []);
assert.deepEqual(render({ ...valid, accountPortalRegisterUrl: 'http://app.example.invalid/register' }), []);
assert.deepEqual(render({ ...valid, accountPortalRegisterUrl: 'https://app.example.invalid/register?token=must-not-be-public' }), []);
assert.deepEqual(render({ ...valid, accountPortalLoginUrl: 'https://app.example.invalid/login#session' }), []);
assert.deepEqual(render({ ...valid, accountPortalRegisterUrl: 'https://app.example.invalid/reset-password' }), []);
assert.deepEqual(render({ ...valid, accountPortalLoginUrl: 'https://user:password@app.example.invalid/login' }), []);
assert.deepEqual(
  render(valid).sort((a, b) => a.kind.localeCompare(b.kind)),
  [
    { text: '登入我的工具', href: loginUrl, kind: 'login' },
    { text: '建立帳號', href: registerUrl, kind: 'register' },
  ],
);

console.log('PASS_ACCOUNT_PORTAL_RUNTIME disabled=hidden incomplete=hidden invalid_origin=hidden http=hidden sensitive_url=hidden approved_https_clean_paths=two_links fake_urls_only=true');
