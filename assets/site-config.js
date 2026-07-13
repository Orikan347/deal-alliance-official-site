/* Fail-closed public-site runtime configuration. Never put secrets here. */
window.DEAL_ALLIANCE_SITE_CONFIG = Object.freeze({
  waitlistEndpoint: "",
  waitlistAllowedOrigins: [],
  waitlistMode: "disabled",
  // Account credentials never belong to the public site. The entry is only
  // rendered after the backend owner supplies an approved HTTPS origin.
  accountPortalRegisterUrl: "",
  accountPortalLoginUrl: "",
  accountPortalAllowedOrigins: [],
  accountPortalMode: "disabled",
  privacyVersion: "PENDING_PRIVACY_REVIEW"
});
