/*
 * Local-only activation artifact. The default public build never imports this
 * file. It contains navigation targets only: no credentials, token, session,
 * payment, artifact, entitlement, or receiver data.
 */
window.DEAL_ALLIANCE_SITE_CONFIG = Object.freeze({
  waitlistEndpoint: "",
  waitlistAllowedOrigins: [],
  waitlistMode: "disabled",
  // The public site gives people one durable instruction. The App then owns
  // login, registration, roles, and the My Tools projection.
  // Owner-only entry: App owns authentication and role projection.  Do not
  // present a public registration affordance from this artifact.
  accountPortalRegisterUrl: "",
  accountPortalLoginUrl: "https://app.dealalliancehub.com/",
  accountPortalAllowedOrigins: ["https://app.dealalliancehub.com"],
  accountPortalMode: "login_only",
  monthlySubscriptionBoundary: Object.freeze({
    mode: "login_only_candidate",
    title: "訂閱與試用說明",
    trial: "新帳號可先使用 7 天試用；試用期間不會默默扣款。",
    consent: "正式開通前，會請你明確同意：單項工具依各月費每月自動續訂；六選五月繳方案每月 NT$999 自動續訂；六選五年繳方案一次付清 NT$9,990，並於每年自動續訂。",
    cancellation: "取消後不會再續扣，並可繼續使用到當次已付費週期結束；不是直接切到日曆月底。",
    closed: "目前尚未開放線上付款或下載；可用狀態請以成交聯盟 App 顯示為準。"
  }),
  commercialOffer: Object.freeze({
    mode: "login_only_candidate",
    source: "DA-COMMERCIAL-PRICING-20260906",
    title: "工具與方案",
    individualTitle: "單項工具月費（含稅）",
    products: Object.freeze([
      Object.freeze({id: "contact_converter", name: "通訊錄轉檔", monthly: "NT$199／月", note: "使用既有通訊錄轉檔功能；不新增功能。"}),
      Object.freeze({id: "smart_close", name: "智能成交助手", monthly: "NT$199／月"}),
      Object.freeze({id: "line_macos", name: "LINE 群發 macOS", monthly: "NT$499／月"}),
      Object.freeze({id: "line_windows", name: "LINE 群發 Windows", monthly: "NT$499／月", note: "Windows 版仍在完成正式交付；目前不提供下載或立即可用承諾。"}),
      Object.freeze({id: "birthday_sms", name: "生日簡訊群發", monthly: "NT$299／月"}),
      Object.freeze({id: "bulk_sms", name: "一般簡訊群發", monthly: "NT$299／月"})
    ]),
    bundleTitle: "六選五組合方案（含稅）",
    bundleMonthly: "月繳 NT$999",
    bundleAnnual: "年繳 NT$9,990",
    bundleTerms: "六項工具任選五項；月繳方案每月 NT$999 自動續訂；年繳方案一次付清 NT$9,990，並於每年自動續訂。取消後不再續扣，仍可使用至當次已付費週期結束。",
    fixedPriceTerms: "六選五組合採固定方案價，不依所選五項單項月費加總調整；即使單項月費加總低於 NT$999，月繳方案仍固定每月 NT$999，年繳方案仍固定一次付清 NT$9,990，並於每年自動續訂。",
    selectionTerms: "不論月繳或年繳，每個依訂閱日起算的月週期，可一次重新選整組五項；確認後立即生效，費用不變。",
    deviceTerms: "每個帳號合計可使用 2 台裝置，不是每項工具各 2 台。",
    availabilityTerms: "Windows 版尚未開放下載或立即使用；可用狀態請以成交聯盟 App 顯示為準。",
    ctaState: "closed"
  }),
  publicBetaActivationMode: "owner_approved_candidate_only",
  paymentMode: "disabled",
  publicGeneralDownloadMode: "disabled",
  privacyVersion: "PENDING_PRIVACY_REVIEW"
});
