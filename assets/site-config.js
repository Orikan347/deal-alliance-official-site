/* Fail-closed public-site runtime configuration. Never put secrets here. */
window.DEAL_ALLIANCE_SITE_CONFIG = Object.freeze({
  waitlistEndpoint: "",
  waitlistAllowedOrigins: [],
  waitlistMode: "disabled",
  // Account destinations stay hidden until real remote registration and
  // login lifecycle verification pass. Never send a visitor to a 404 or a
  // staging explanation page.
  accountPortalRegisterUrl: "",
  accountPortalLoginUrl: "",
  accountPortalAllowedOrigins: [],
  accountPortalMode: "disabled",
  privacyVersion: "PENDING_PRIVACY_REVIEW"
});
