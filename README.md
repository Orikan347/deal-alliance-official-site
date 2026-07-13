# 成交聯盟官方網站候選 v1

作品 ID：ORI-WEB-DA-OFFICIAL-MVP-20260713-V1  
階段：PENDING_RELEASE_SECURITY
狀態：PUBLIC_RELEASE_ARTIFACT_OUT_OF_SYNC_PENDING_REGISTRATION
最後檢查：2026-07-13

這是成交聯盟公開官方網站的可維護候選來源。包含首頁、關於、解決方案、六項工具詳情、公開資源、FAQ、候補／洽詢、隱私邊界、使用條款、搜尋空狀態與 404。Codex 已用去識別化假資料完成核心流程、候補 receiver 與帳號入口的安全測試；使用者核心流程驗收與後台 HTTPS 假帳號 E2E 仍待完成。

正式工具仍是候補／洽詢狀態；四個工具頁提供的只是瀏覽器本機假資料示範，不登入、不呼叫正式 API、不保存、不發送。

公開正式來源為 `https://www.dealalliancehub.com`。目前公開站基礎路由已存在，但最新唯讀 Gate 顯示正式首頁尚未同步 `site-config.js` 的帳號入口 bootstrap；在從本來源重建並受控發布 `dist/`、重新取得公開 PASS 前，不可把候選中的入口／`llms.txt` 修正稱為已上線。

候補收件契約已建立，但 `assets/site-config.js` 預設為 `disabled` 且沒有端點。只有正式 HTTPS 端點、Origin 白名單、隱私版本、保存／刪除規則與 receiver readback 全部核准後，才可切換為啟用。

## 本機開啟

進入此資料夾後執行：python3 -m http.server 4173

開啟：http://127.0.0.1:4173/

## 可重跑驗收

執行：python3 tests/verify_site.py

安全標頭契約：python3 tests/verify_headers_contract.py

候補假 receiver：python3 tests/verify_waitlist_contract.py

正式發布／監控／回滾契約：python3 tests/verify_release_contract.py

帳號入口 runtime（使用 `example.invalid` 假網址）：`<bundled-node> tests/verify_account_portal_runtime.mjs`

公開部署後只讀驗收（需 DNS／HTTPS 已就緒）：python3 tests/verify_public_release.py

發布 artifact 由 `scripts/build-public.sh` 從本來源重建 `dist/`；它不會把 tests、契約或交接文件放進公開輸出。GitHub Pages 發布工作流程目前只允許手動觸發：`.github/workflows/pages-manual-release.yml`；未取得主窗口發布核准前不會執行。

工具狀態對照包含在：python3 tests/verify_site.py

## 發佈前必做

1. `site.config.json`、canonical、sitemap、OG、JSON-LD 與 `llms.txt` 已統一使用 `https://www.dealalliancehub.com`；正式部署前仍需以公開 HTTPS 做 readback。
2. 由品牌負責人確認公開文案、工具名稱與實際開放狀態。
3. 以正式 staging 驗證 HTTP、行動版、分享卡、Schema Validator、Rich Results Test、Search Console 與外部 crawler。

完整網站設計與上線 Gate：`網站完整規劃藍圖_2026-07-13.md`。

正式推播前的主窗口交接文件：`公開推播前交接清單_2026-07-13.md`。

## 本輪驗收範圍

- sitemap 共 15 個公開頁：主頁、About、Solutions、Tools、六項工具詳情、Resources、FAQ、候補／洽詢、Privacy、Terms。
- 保護／空狀態路由：`/404.html`、`/search/`；不進 sitemap。
- 工具目錄共六項：四項 `WAITLIST_ONLY`，一項 `WAITLIST_ONLY` 的本機流程示範，及一項 `NOT_ENABLED` 預留工具。
- 可由使用者親自測試的本機示範：聯絡人轉換成功／錯誤、Smart Close 整理、簡訊預覽、LINE 流程預覽；全部只使用假資料。
- 驗收報告：`驗收報告_2026-07-13.md`。
- 假收件契約驗收：`python3 tests/verify_waitlist_contract.py`；只使用 `example.invalid` 假資料與本機 fake receiver。

此候選站不可自行部署、送出候補資料、開啟登入、付款或執行正式發送。帳號入口與候補 receiver 預設均為 `disabled`／空 URL；後台 HTTPS 與去識別化跨系統 E2E 通過後才可受控啟用純導向連結。
