# 螺壳 luoke-core

- 仓库：[`luoke-core/`](../luoke-core)；设计：`luoke-core/docs/DESIGN.md`，v1 范围和接口细节：`luoke-core/docs/V1.md`
- 本页由 luoke-core 的会话维护。

## 是什么

螺壳工具共用的本地 AI 主控：一个菜单栏程序，管本机所有模型推理（加载、内存、功耗、排队），按实验室发布的配方决定用什么模型做什么任务；配方里的每个选择都有实测证据。它同时是螺壳工具的安装器和更新器。模型的推理和权重归主控（顶层 ADR 0014、0018）。

## 对外提供

**给配件（螺壳的工具）**
- **任务层**：本账户的 Unix socket（`~/Library/Application Support/luoke-core/run/hub.sock`），接入参考 `luoke_core/client.py`。
  - 生成：OpenAI 兼容、一律流式，按 `X-Luoke-Priority` 分"用户在等"和"后台"。
  - 打分、联想、续写：专用模型直连，按配件保留前缀快照。专用模型的工作进程空闲 10 分钟停、下次用到再起（重起期间答 `not_ready`，`retry_after` 2 秒）；内存不够时不起（`retry_after` 30 秒）。
  - 嵌入：`POST /tasks/<任务>/v1/embed`，后台批和用户在等的查询走专用模型自己的通道。
  - `GET /tasks`：本档能用的任务、参数、状态，以及只用来显示的 `model_name`（`combo` 不解析）；顶层的 `luoke_mem` 给出主控里那份记忆库的位置。
  - 预热、常驻声明、退出通知；被挡回时有统一的原因码和 `retry_after` / `retry_after_ms`（V1 §2）。
- **配件接入契约**（DESIGN §11、V1 §8）：打包与身份、用模型的方式、评测集、数据与升级、界面与安全。
- **空闲任务**：配件在清单 `jobs` 里登记"空闲时跑"的命令，主控在安静时刻拉起、用户回来时让它收尾（V1 §8）。
- **主控自带的 Python 可以借**：`螺壳.app/Contents/Resources/python/bin/python3`（改名前装的是 `螺壳主控.app`；装在 `/Applications` 或 `~/Applications`，ADR 0012）（python-build-standalone 3.12，同一个 Team 签名）；契约 1 内路径和 bundle id `ai.luoke.core` 不变，换大版本前先写进这里并通知用它的配件（V1 §8）。
- **配件用主控里那份 luoke_mem**：`GET /tasks` 顶层 `"luoke_mem": {"path", "version"}` 给出 site-packages 的位置；工具每次新起进程时问一次、插到 `sys.path` 最前面再 import，主控不在就用自带的兜底那份（兜底那份不比钉住的新）。
- **`GET /accessories`**：装了哪些配件及其清单里的公开字段（含 `capabilities`）。
- **打包脚本** `tools/package_python_app.py`：配件清单 + 包目录 → 自带 Python 的 .app（V1 §8）。

**记忆（luoke-mem）打在主控里**
- 主控 .app 自带 luoke-mem 的代码和清单（`Contents/Resources/memory/luoke-accessory.json`），配件标识仍是 `luoke-mem`；它的任务、空闲任务、`forget-tool` 都用主控自带的 Python 跑。主控进程本身不读记忆。
- 打开记忆界面：`open luoke://memory`；跳到某一条 `luoke://memory?note=<编号>`；打开到「最近记下的」`luoke://memory?view=recent`。
- 判断记忆在不在：Swift 看 `luoke://memory` 有没有应用能打开；Python 看主控 .app 里的那份清单在不在。
- 主控升级、退出前请主控 Python 跑着的 `-m luoke_mem` 进程退出；luoke_mem 收到 SIGTERM 要干净退出。

**给用户**
- 安装、升级（新的安装器原地升级，旧版留作回退；菜单「检查更新…」按渠道查新版；升级只往新换、不往回降）、配件回到上一版（菜单「配件回到上一版…」，按那一版当时的验证认它）、装完输入法引导添加输入源、卸载（只删配件清单里和它自己的标识绑定的数据位置，记忆文件永远不删；可选从记忆里忘掉它写的东西）。
- 首次运行：按清单下载引擎包和本档模型，先复用本机已有的同名模型（逐文件核哈希、只读克隆）；大内存机器可选「省空间」。
- **给高级用户的本机端点**（顶层 ADR 0014 修订）：设置 → 高级，默认关。OpenAI 兼容的 `/v1/models`、`/v1/chat/completions`，只听 127.0.0.1；模型是主控这一档的底座和用户自己登记的本机模型（`user/<名字>`）。命令行 `luoke launch pi` 一键配好 pi。给用户自己的工具用，配件照旧走任务层（V1 §2b）。

**配方与评测**
- 配方：模型清单、引擎包、各档底座、任务表与任务参数、已验证版本、依据（DESIGN §3）。
- 发布前评测：每个任务在各硬件档上按评测集打分；哪一档开着由支持台账定——连过 3 遍才开，失败一遍就关（顶层 ADR 0017，V1 §10b）。

## 依赖

- 推理引擎：钉住版本、不改代码的 oMLX，打成引擎包，由实验室重签公证（ADR 0001）。
- 模型由实验室量化、托管在 ModelScope 和 Hugging Face；安装包和引擎包发在 GitHub 的 luoke-releases。
- 记忆：luoke-mem（打进主控的那份按发布钉住的提交）。

## 使用方

- luoke-mail：后台批量分拣和其他邮件任务、单次调用。
- luoke-ime：重排打分、联想、续写；个人化组件借主控的 Python。
- luoke-mem：归纳任务（typing、topics），空闲任务 learn。
- luoke-agent：常驻配件，对话和简报任务，`GET /accessories`。
- digup：嵌入。

## 对别的项目的需求

- 每个工具在自己的注册页写清要主控提供哪些任务、调用方式（生成、打分、嵌入）、延迟要求；每个任务交评测集，没有评测集的任务不进配方；随模型变化的数值（门槛、上限、是否思考等）写进配方，不写死在工具里（DESIGN §3、§7、§11）。
- 工具不注册自己的登录项（由系统拉起的配件，例如输入法，是例外），不点名模型，不提供选模型的界面；安装路径由配件类型决定，发布后不变（DESIGN §11）。
- 后台请求按硬件档限制输入长度、配件分段提交；被 `busy` / `paused` 挡回时按 `retry_after`（有 `retry_after_ms` 就按它）重试，主控不排队（DESIGN §6）。
- 配件的代码改了、要换装的，同时升清单里的版本号：主控按版本号判断要不要升级。
- **主控改名「螺壳」（主人 10-23 定，PR luoke-core#26 的提案）**：internal-1024 起更新程序和安装器认「螺壳.app」和「螺壳主控.app」两个名字，internal-1024-2 起主控叫 `螺壳.app`，internal-1025-3 起装在 `/Applications`（`~/Applications` 里的也认，luoke-core ADR 0012）。bundle id `ai.luoke.core`、数据目录 `~/Library/Application Support/luoke-core`、socket、命令 `luoke` 都不变。配件里写死了主控位置的，要在 internal-1026 之前改成两个名字都认：最好按 bundle id 找（Swift：`NSWorkspace.shared.urlForApplication(withBundleIdentifier: "ai.luoke.core")`），Python 先试 `螺壳.app` 再试 `螺壳主控.app`。已接：luoke-mail 0.17.17（c5a4379）、luoke-ime 0.1.14（9dcbc8b），都是两个名字都认。给用户看的文字里的「螺壳主控」随各自的版本改成「螺壳」。
