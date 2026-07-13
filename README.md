# 成交聯盟官方網站候選 v1

作品 ID：ORI-WEB-DA-OFFICIAL-MVP-20260713-V1  
階段：PENDING_USER_ACCEPTANCE  
狀態：LOCAL_FUNCTIONAL_CANDIDATE_ONLY  
最後檢查：2026-07-13

這是成交聯盟公開官方網站的本機功能測試候選版。包含首頁、關於、解決方案、六項工具詳情、公開資源、FAQ、候補／洽詢、隱私邊界、使用條款、搜尋空狀態與 404。Codex 已用去識別化假資料完成瀏覽器端測試；目前等待使用者親自驗收核心流程。

正式工具仍是候補／洽詢狀態；四個工具頁提供的只是瀏覽器本機假資料示範，不登入、不呼叫正式 API、不保存、不發送。

公開正式來源已由主窗口確認為 `https://www.dealalliancehub.com`。這只更新本機候選的公開來源 metadata，不代表已部署或已可公開瀏覽。

候補收件契約已建立，但 `assets/site-config.js` 預設為 `disabled` 且沒有端點。只有正式 HTTPS 端點、Origin 白名單、隱私版本、保存／刪除規則與 receiver readback 全部核准後，才可切換為啟用。

## 本機開啟

進入此資料夾後執行：python3 -m http.server 4173

開啟：http://127.0.0.1:4173/

## 可重跑驗收

執行：python3 tests/verify_site.py

安全標頭契約：python3 tests/verify_headers_contract.py

候補假 receiver：python3 tests/verify_waitlist_contract.py

正式發布／監控／回滾契約：python3 tests/verify_release_contract.py

公開部署後只讀驗收（需 DNS／HTTPS 已就緒）：python3 tests/verify_public_release.py

GitHub Pages 發布工作流程目前只允許手動觸發：`.github/workflows/pages-manual-release.yml`；未取得主窗口發布核准前不會執行。

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

此候選站不可自行部署、送出候補資料、開啟登入、付款或執行正式發送。使用者驗收完成後，才進入正式授權、簽章、公證、乾淨安裝與部署 Gate。
