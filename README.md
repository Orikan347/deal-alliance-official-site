# 成交聯盟官方網站候選 v1

作品 ID：ORI-WEB-DA-OFFICIAL-MVP-20260713-V1  
狀態：LOCAL_CANDIDATE_ONLY  
最後檢查：2026-07-13

這是成交聯盟公開官方網站的本機靜態候選版。內容只提供首頁、關於、解決方案、工具、公開資源、FAQ、候補／洽詢、隱私邊界、使用條款與 404；沒有登入、付款、學生資料、管理設定、授權邏輯或真實表單送出。

## 本機開啟

進入此資料夾後執行：python3 -m http.server 4173

開啟：http://127.0.0.1:4173/

## 可重跑驗收

執行：python3 tests/verify_site.py

## 發佈前必做

1. 在 site.config.json 確認正式 HTTPS 網域，並替換所有 official-domain-pending.invalid canonical／sitemap／schema URL。
2. 由品牌負責人確認公開文案、工具名稱與實際開放狀態。
3. 以正式 staging 驗證 HTTP、行動版、分享卡、Schema Validator、Rich Results Test、Search Console 與外部 crawler。

完整網站設計與上線 Gate：`網站完整規劃藍圖_2026-07-13.md`。

正式推播前的主窗口交接文件：`公開推播前交接清單_2026-07-13.md`。

## 本輪驗收範圍

- 公開索引路由：`/`、`/about/`、`/solutions/`、`/tools/`、`/tools/follow-up-rhythm/`、`/resources/`、`/faq/`、`/waitlist/`、`/privacy/`、`/terms/`。
- 保護／空狀態路由：`/404.html`、`/search/`；不進 sitemap。
- 所有工具與候補 CTA 仍是 `WAITLIST_ONLY` 或公開說明，不可購買、下載、試用、登入或啟用。
- 驗收報告：`驗收報告_2026-07-13.md`。

此候選站不可自行部署、送出候補資料、開啟登入、付款或下載。
