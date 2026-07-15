# 成交聯盟官方網站候選 v1

作品 ID：ORI-WEB-DA-OFFICIAL-MVP-20260713-V1  
階段：PENDING_USER_ACCEPTANCE
狀態：PENDING_USER_ACCEPTANCE_PRODUCT_PLATFORM_REWRITE
最後檢查：2026-07-15

這是成交聯盟公開官方網站的可維護候選來源。包含首頁、關於、解決方案、四項已查核工具詳情、公開資源、FAQ、開放資訊、隱私邊界、使用條款、搜尋空狀態與 404。生涯運數計算器保留在候選來源中，但不會進入公開網站產物、導覽或 sitemap；「跟進節奏工具」因找不到獨立產品來源，也不會公開。帳號入口只有純導向 CTA：`https://app.dealalliancehub.com/register` 與 `/login`，不收集、傳遞或儲存帳密／session，仍待使用者驗收與正式發行安全 Gate。

四項工具目前都只顯示誠實的開放狀態，不提供假表單、假下載或假互動示範；不登入、不呼叫正式 API、不保存、不發送。

公開正式來源為 `https://www.dealalliancehub.com`，根網域會導向 `www`。既有技術版本已讀回 HTTPS、帳號 CTA runtime 與安全標頭；但 2026-07-15 的工具產品文案 revision `PRODUCT_PLATFORM_20260715` 尚未被正式來源讀回，不能宣稱本輪內容已上線。帳號入口只允許 `https://app.dealalliancehub.com` 的精確 `/register`、`/login` 路徑；該獨立 app 的註冊／登入表單已可公開開啟，並具私有頁安全標頭。官網本身不接觸帳密；Email 驗證、試用權益與完整 lifecycle 的公開讀回仍待完成，因此尚不能稱為正式可營運服務。

候補收件功能未啟用，現階段只提供「工具開放資訊」說明。只有正式 HTTPS 端點、Origin 白名單、隱私版本、保存／刪除規則與 receiver readback 全部核准後，才可新增可提交的表單。

## 本機開啟

進入此資料夾後執行：`python3 -m http.server 4173`

開啟：[http://127.0.0.1:4173/](http://127.0.0.1:4173/)

**不要直接用 `file://` 開 `index.html`。** 網站的樣式、帳號 CTA 與導覽腳本使用網站根路徑載入；直接開檔會讓它們失效，看起來像未完成頁面。

## 可重跑驗收

執行：python3 tests/verify_site.py

安全標頭契約：python3 tests/verify_headers_contract.py

候補假 receiver：python3 tests/verify_waitlist_contract.py

正式發布／監控／回滾契約：python3 tests/verify_release_contract.py

正式可營運前資料／法務／客服防呆：python3 tests/verify_operational_readiness.py

最終目標完成度稽核：python3 tests/verify_goal_readiness.py

帳號入口 runtime（含假網址、官網同源與相對路徑拒絕；只允許唯一 app CTA）：`<bundled-node> tests/verify_account_portal_runtime.mjs`

公開部署後只讀驗收（需 DNS／HTTPS 已就緒）：python3 tests/verify_public_release.py

帳號 app 私有頁只讀驗收（不輸入或送出帳密；確認 credential form 僅存在 app 同源）：`python3 tests/verify_account_portal_public.py`

發布 artifact 由 `scripts/build-public.sh` 從本來源重建 `dist/`；它不會把 tests、契約或交接文件放進公開輸出。正式受控發布目標是 Cloudflare Pages，production branch 為 `agent/official-site-v1`；未取得主窗口發布核准前不會執行。歷史 GitHub Pages URL 只作備援／歷史證據，不能當作正式 canonical 或本輪發布證據。

工具狀態對照包含在：python3 tests/verify_site.py

## 發佈前必做

1. `site.config.json`、canonical、sitemap、OG、JSON-LD 與 `llms.txt` 已統一使用 `https://www.dealalliancehub.com`；正式部署前仍需以公開 HTTPS 做 readback。
2. 由品牌負責人確認公開文案、工具名稱與實際開放狀態。
3. 以正式公開來源驗證 HTTP、行動版、分享卡、Schema Validator、Rich Results Test、Search Console 與外部 crawler；帳號端另完成去識別 Email 驗證／試用 lifecycle readback。
4. 正式把網站稱為「可營運服務」前，owner 必須提供並核准：營運主體、公開客服、隱私聯絡人、隱私／條款版本與生效日、服務地區／準據法，以及首批具作者、來源與日期的公開資源。這些未補齊前，技術候選只能維持 `PENDING_USER_ACCEPTANCE`。

完整網站設計與上線 Gate：`網站完整規劃藍圖_2026-07-13.md`。

逐項完成真相與主窗口順序：`正式營運完成度矩陣_2026-07-14.md`。

Owner 可直接填寫的公開資料表：`公開營運資料確認表_待Owner填寫.md`。

監控設定與回滾演練清單：`公開監控與回滾演練清單_2026-07-14.md`。

正式推播前的主窗口交接文件：`公開推播前交接清單_2026-07-13.md`。

## 本輪驗收範圍

- sitemap 共 13 個公開頁：主頁、About、Solutions、Tools、四項已查核工具詳情、Resources、FAQ、工具開放資訊、Privacy、Terms。
- 保護／空狀態路由：`/404.html`、`/search/`；不進 sitemap。
- 工具目錄目前公開四項，全部維持 `WAITLIST_ONLY`；生涯運數計算器與沒有來源的跟進節奏工具均不出現在公開 artifact。
- 可由使用者親自驗收的候選流程：辨識目前耗時的成交工作、閱讀工具與安全邊界、查看目前開放狀態、純導向至帳號入口；網站不假裝工具已可在瀏覽器內使用。
- 現行工具產品定位與驗收：`產品定位重寫總規劃_2026-07-15.md`、`驗收報告_2026-07-15_工具產品定位重寫.md`。舊的「內容來源重建」報告已停用，不可當作公開文案依據。

此候選站不可自行部署、送出候補資料、建立帳號、付款或執行正式發送。候補 receiver 仍為 `disabled`／空 URL；官網候選只啟用兩個已驗證的純導向連結，帳密只會在獨立 app 同源頁面處理。公開 Email 驗證／試用 lifecycle、隱私規則與 release security Gate 完整通過前，不可稱為正式可營運服務。
