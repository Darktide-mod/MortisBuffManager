# MortisBuffManager

本目录是此模组唯一的活动工程。源码、版本、检查和发布资料由本项目单独维护。

- `src/MortisBuffManager/`：安装源码；这是 ZIP 中唯一的顶层文件夹。
- `tests/`：本项目的回归检查。
- `tools/`：本项目的发布与离线 UI 渲染工具。
- `publishing/`：中英功能正文、英文简介与更新日志，以及内部发布配置。
- `release/`：每个新发布目录仅有独立安装 ZIP 与三份提交文案。
- `build/`：可重新生成的测试与渲染中间文件，不用于上传。

在本目录执行 `./Test.ps1` 运行检查；执行 `./Release.ps1` 单独检查并发布；执行 `./Release.ps1 -Check` 校验现有发布。也可使用 Python 运行 `tests/run.py` 和 `tools/release.py`。

测试与发布不读取其他三个模组的工程。

[安装 ZIP](release/4.6.2/MortisBuffManager-4.6.2.zip) · [中英 BBCode](release/4.6.2/description.bbcode.txt) · [完整发布流程](发布流程.md)

开发依赖默认位于工作区 `dev-support/`：LuaJIT Python 运行库、原版游戏 Lua 与 DMF/SoloPlay 测试素材。可通过 `DARKTIDE_DEV_SUPPORT`、`DARKTIDE_SOURCE`、`DARKTIDE_TEST_RUNTIME` 环境变量指定位置；项目可单独迁出。发布脚本与产品源码没有共享维护目录。

当前功能版本为 4.6.2。天赋页采用「可入池」「DIY」「已选择」「不可入池」四个带数量标签，支持公共／职业／流派分类、搜索和滚轮浏览。天赋列表与详情分别滚动；预选通过勾选与金色显示，原生／DIY 点数独立计算。实际切换流派会移除新配置下不可入池的原生及 DIY 预选，浏览标签与分类不改变选择。

闪击资格按官方角色配装解析，修复基础与升级闪击同时保存在天赋树时误判的问题，恢复执法官强化手雷、流氓强化闪光雷及适配的手雷再生／额外投掷奖励。已检查 7 职业、26 闪击分支、109 配装组合。

修复 Realms Loadout 旧共享窗口切页时重复关闭的异常；日志已确认重复关闭报错，闪烁改善仍待游戏内验证。

已复核当前安装的 Realms Loadout 0.5.1 共享窗口，并加入旧筛选状态迁移检查。

仅生成发布产物，不更新本地安装。核查时本机仍为 4.6.0；必须单独安装本模组 ZIP，更新 HCM 不会替换死灵 UI。实机与联机验收待完成。

正式版移除 Debug 入口及临时诊断采集，并清除旧诊断开关。保留每轮路线 Buff＋公共／职业抽选、固定 10 次进度奖励及竞争次数限制；Realms 使用 v10 奖励协议，房主与客机建议统一使用本版。

入口：`/mortisbuffs`，也可在本 mod 的 DMF 设置中绑定快捷键。

兼容 Talent Point Manager 和 Realms Loadout，二者均为可选安装；本 mod 独立管理设置、Buff 选择及奖励。

包的安装、版本、依赖、Lua 与资源接口见 [包规范](docs/diy/PACKAGES.zh-CN.md)。

外部资源接口与示例见 [资源指南](docs/diy/ASSETS.zh-CN.md)。使用外部图形时需要 SimpleAssets v2；普通词条不受影响。
