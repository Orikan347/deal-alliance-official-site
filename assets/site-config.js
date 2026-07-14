/* Fail-closed public-site runtime configuration. Never put secrets here. */
window.DEAL_ALLIANCE_SITE_CONFIG = Object.freeze({
  waitlistEndpoint: "",
  waitlistAllowedOrigins: [],
  waitlistMode: "disabled",
  // Account credentials never belong to the public site. The entry is only
  // rendered only for the staging origin that passed the deidentified
  // lifecycle Gate. This remains a candidate-site link until deployment.
  accountPortalRegisterUrl: "https://app.dealalliancehub.com/register",
  accountPortalLoginUrl: "https://app.dealalliancehub.com/login",
  accountPortalAllowedOrigins: ["https://app.dealalliancehub.com"],
  accountPortalMode: "enabled",
  privacyVersion: "PENDING_PRIVACY_REVIEW"
});
