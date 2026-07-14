# 成交聯盟官方網站候選 v1

作品 ID：ORI-WEB-DA-OFFICIAL-MVP-20260713-V1  
階段：PENDING_USER_ACCEPTANCE
狀態：PUBLIC_RELEASE_LIVE_ACCOUNT_PORTAL_PENDING
最後檢查：2026-07-14

這是成交聯盟公開官方網站的可維護候選來源。包含首頁、關於、解決方案、五項公開工具詳情、公開資源、FAQ、候補／洽詢、隱私邊界、使用條款、搜尋空狀態與 404。生涯運數計算器保留在候選來源中，但不會進入公開網站產物、導覽或 sitemap。候補 receiver 仍安全停用；後台 staging 的去識別帳號／OAuth／權益 lifecycle 已通過，因此候選版已接上兩個純導向 CTA：`https://app.dealalliancehub.com/register` 與 `/login`。它們不收集、傳遞或儲存帳密／session，仍待使用者驗收與正式發行安全 Gate。

正式工具仍是候補／洽詢狀態；四個工具頁提供的只是瀏覽器本機假資料示範，不登入、不呼叫正式 API、不保存、不發送。

公開正式來源為 `https://www.dealalliancehub.com`，根網域會導向 `www`。現行 live 19 條路由、SEO/GEO metadata、`llms.txt`、公開安全標頭與帳號入口 bootstrap 已以 HTTPS GET-only Gate 讀回；下一次受控發布候選後將為 18 條路由，且不再公開生涯運數計算器。候選設定僅允許 `https://app.dealalliancehub.com`，並只接受精確的 `/register`、`/login` 路徑；尚未受控發布，不能稱為正式公開註冊。

候補收件契約已建立，但 `assets/site-config.js` 預設為 `disabled` 且沒有端點。只有正式 HTTPS 端點、Origin 白名單、隱私版本、保存／刪除規則與 receiver readback 全部核准後，才可切換為啟用。

## 本機開啟

進入此資料夾後執行：python3 -m http.server 4173

開啟：http://127.0.0.1:4173/

## 可重跑驗收

執行：python3 tests/verify_site.py

安全標頭契約：python3 tests/verify_headers_contract.py

候補假 receiver：python3 tests/verify_waitlist_contract.py

正式發布／監控／回滾契約：python3 tests/verify_release_contract.py

正式可營運前資料／法務／客服防呆：python3 tests/verify_operational_readiness.py

最終目標完成度稽核：python3 tests/verify_goal_readiness.py

帳號入口 runtime（含假網址拒絕與核准 staging CTA）：`<bundled-node> tests/verify_account_portal_runtime.mjs`

公開部署後只讀驗收（需 DNS／HTTPS 已就緒）：python3 tests/verify_public_release.py

帳號 staging 私有頁只讀驗收（不送出帳密）：`python3 tests/verify_account_portal_public.py --resolve-ip <公開 DNS IPv4>`

發布 artifact 由 `scripts/build-public.sh` 從本來源重建 `dist/`；它不會把 tests、契約或交接文件放進公開輸出。GitHub Pages 發布工作流程目前只允許手動觸發：`.github/workflows/pages-manual-release.yml`；未取得主窗口發布核准前不會執行。

工具狀態對照包含在：python3 tests/verify_site.py

## 發佈前必做

1. `site.config.json`、canonical、sitemap、OG、JSON-LD 與 `llms.txt` 已統一使用 `https://www.dealalliancehub.com`；正式部署前仍需以公開 HTTPS 做 readback。
2. 由品牌負責人確認公開文案、工具名稱與實際開放狀態。
3. 以正式 staging 驗證 HTTP、行動版、分享卡、Schema Validator、Rich Results Test、Search Console 與外部 crawler。
4. 正式把網站稱為「可營運服務」前，owner 必須提供並核准：營運主體、公開客服、隱私聯絡人、隱私／條款版本與生效日、服務地區／準據法，以及首批具作者、來源與日期的公開資源。這些未補齊前，技術候選只能維持 `PENDING_USER_ACCEPTANCE`。

完整網站設計與上線 Gate：`網站完整規劃藍圖_2026-07-13.md`。

逐項完成真相與主窗口順序：`正式營運完成度矩陣_2026-07-14.md`。

正式推播前的主窗口交接文件：`公開推播前交接清單_2026-07-13.md`。

## 本輪驗收範圍

- sitemap 共 14 個公開頁：主頁、About、Solutions、Tools、五項公開工具詳情、Resources、FAQ、候補／洽詢、Privacy、Terms。
- 保護／空狀態路由：`/404.html`、`/search/`；不進 sitemap。
- 工具目錄目前公開五項，全部維持 `WAITLIST_ONLY`；生涯運數計算器已依 owner 指示隱藏，不出現在公開 artifact。
- 可由使用者親自測試的本機示範：聯絡人轉換成功／錯誤、Smart Close 整理、簡訊預覽、LINE 流程預覽；全部只使用假資料。
- 驗收報告：`驗收報告_2026-07-13.md`。
- 假收件契約驗收：`python3 tests/verify_waitlist_contract.py`；只使用 `example.invalid` 假資料與本機 fake receiver。

此候選站不可自行部署、送出候補資料、建立帳號、付款或執行正式發送。候補 receiver 仍為 `disabled`／空 URL；帳號入口僅在候選來源啟用兩個已驗證的純導向 staging 連結。staging E2E 通過後仍必須經使用者驗收、正式帳號流程／隱私規則與 release security Gate，才可受控發布。
