/* Fail-closed public-site runtime configuration. Never put secrets here. */
window.DEAL_ALLIANCE_SITE_CONFIG = Object.freeze({
  waitlistEndpoint: "",
  waitlistAllowedOrigins: [],
  waitlistMode: "disabled",
  // Account credentials never belong to the public site. These are approved
  // private-account destinations; the public site only provides navigation.
  accountPortalRegisterUrl: "https://app.dealalliancehub.com/register",
  accountPortalLoginUrl: "https://app.dealalliancehub.com/login",
  accountPortalAllowedOrigins: ["https://app.dealalliancehub.com"],
  accountPortalMode: "enabled",
  privacyVersion: "PENDING_PRIVACY_REVIEW"
});
