# 死靈試煉 Buff 管理器

死靈試煉 Buff 管理器以 SoloPlay 為前提，同時支援 Realms 聯機會話。透過天賦樹介面選擇 Buff，Realms 中的選擇上限與校驗規則由房主控制。本模組獨立載入並儲存設定，無需天賦點管理器。

## 功能

- 在天賦樹介面的列表中選擇原版死靈試煉 Buff。
- 根據原版 Buff 池、流派、職業、技能與天賦要求篩選可用項。
- 選擇上限可設為 1–64 項，預設 32 項。
- 分別設定本地和 Realms 作用域，Realms 客機受主機規則約束。
- 支援英文、簡體中文、繁體中文，Buff 名稱使用遊戲翻譯。

任務本身為死靈試煉時，開啟預配置 Buff 也會關閉該局的原版獎勵抽選。

總開關預設關閉，其下本地和 Realms 作用域預設開啟。選擇上限指選中的條目數量，不代表單個 Buff 可以無限疊層，也不保證每種配裝都能使用全部 Buff。

## 依賴與安裝

需要 Darktide Mod Loader、Darktide Mod Framework 和 SoloPlay。使用 Realms 聯機時還需安裝 Realms，SoloPlay 仍為前提。天賦點管理器和兩款浩劫模組均為可選配套。

## Vortex 安裝

- 退出遊戲，在 Vortex 中管理 Darktide，並先安裝上方列出的依賴。
- 從本模組 Files 頁面下載安裝 ZIP，在 Vortex 中選擇 Install From File（從檔案安裝）匯入，然後啟用模組並點選 Deploy Mods（部署模組）。
- 開啟 Load Order（載入順序），啟用 MortisBuffManager 並將其排在 SoloPlay 後，保留其他模組。
- 啟動遊戲，進入“Mod 選項 → 死靈試煉 Buff 管理器”，開啟總開關以使用預配置 Buff。

## 手動安裝

- 退出遊戲，並按各依賴的說明完成前置安裝。
- 開啟 Darktide 遊戲目錄；Steam 中可透過“屬性 → 已安裝檔案 → 瀏覽”進入。
- 進入遊戲的 mods 資料夾，將本 ZIP 內的 MortisBuffManager 資料夾解壓到此處，確認最終路徑為 mods/MortisBuffManager。
- 編輯 mods/mod_load_order.txt，在 SoloPlay 後另起一行加入 MortisBuffManager，保留其他條目。
- 儲存檔案並啟動遊戲，進入“Mod 選項 → 死靈試煉 Buff 管理器”並開啟總開關。

使用拆分版前請停用舊的 TalentAndMortisManager。本模組載入遊戲自身提供的死靈資源，不在包內分發提取的遊戲美術素材。

## 框架開關

Darktide Mod Framework 提供模組啟用／禁用開關。本模組另有預設關閉的功能總開關，兩者都開啟時功能才會生效。關閉框架開關會停止更新並執行清理，不改動已儲存的功能設定。

## 使用方法

開啟 Mod 選項 → 死靈試煉 Buff 管理器，開啟自訂 Buff，選擇本地或 Realms 作用域並設定上限。進入天賦樹，用死靈 Buff 選擇控制元件勾選符合資格的條目。更換職業、技能、天賦或流派後，應重新檢查可用列表。

Realms 客機需要相同模組才能提交自己的選擇，最終接受的條目由主機上限和校驗規則決定。隊伍應使用相同版本。

## 限制與相容性

在靈能室、本地單人等受支援場景，以及由主機授權的 Realms 會話中生效。不承諾在官方匹配中獲得 Buff 或永久進度。

資格篩選遵循可用的原版資料，不保證所有 Buff 都能同時組合。替換死靈選擇、任務 Buff 管理或相同天賦樹控制元件的模組可能衝突。

已透過程式碼與模擬檢查，本版尚未新增實機測試。更改遊戲語言後請重啟。

## 2.0.1 更新

- 完善英文、簡體中文、繁體中文設定文字。
- 說明文件移入自身目錄，消除四個獨立 Vortex 包之間同名根目錄說明檔案造成的衝突。

## 致謝

從原 TalentAndMortisManager 拆分。Solo Play 與 Realms：deluxghost。原版死靈系統、Buff 定義及引用素材：Fatshark。遊戲原始碼查閱：Aussiemon/Darktide-Source-Code。本模組為獨立社群專案。
