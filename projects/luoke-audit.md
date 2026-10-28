# 螺壳体检 luoke-audit

- 仓库：`luoke-audit/`（登记合并后由 luoke-top 挂成子模块）；进度：`luoke-audit/STATUS.md`；术语：`luoke-audit/CONTEXT.md`
- 本页由 luoke-audit 的会话维护。

## 是什么

定期在空闲时只读地查一遍这台 Mac，找出垃圾和安全问题，说清是谁造成的、删了有什么风险，经 agent 告诉用户；删不删由用户点。

- **原则**：是不是垃圾、能不能删、风险多高，由确定的规则决定；模型只做归纳和解释（经主控）。能用元信息（大小、时间、属主、签名、链接数）判断的就不读内容，需要内容时（重复文件的哈希、散落的密钥）在本机读，内容不进日志和记忆。扫描失败记成"没扫描"，不算没有发现。
- **第一版查**：
  - 垃圾：空间去向和每天的增长、是谁在产生（例如测试每次运行都在临时目录留下一份构建、会话工具的临时目录越积越多）、会重建的缓存、卸载后的残留、很久没动的项目（删前查 git：未推送提交、未提交改动、stash）。
  - 安全：常驻项（指向不存在的程序、未签名、用户可写）、进程异常（孤儿、成批堆积、来自已删除的应用）、权限授予（应用已不在还拿着完全磁盘访问等）、FileVault / 防火墙 / SIP / Gatekeeper / 自动更新 / 锁屏、ClamAV 和 YARA 扫下载目录和常驻项指向的程序。
- **第二版**：重复文件（APFS 克隆、硬链接不算；首选把多余的换成克隆，不丢数据）、过期文件（多个信号同时成立，默认 6 个月）、散落的密钥（只记位置和类型，不存值）、一键清理、过期软件。
- **界面**：自己的报告页（用户主动打开），分"放心删 / 要确认 / 仅供参考"，每条写依据。主动提醒只经 agent。
- **形态**：签名公证的「螺壳体检.app」（bundle id `ai.luoke.audit`），随包带 ClamAV 和 YARA。里面两个程序：
  - `luoke-audit`：用户给「完全磁盘访问」的就是它；扫描、出方案、执行方案都在它里面，由主控的空闲任务拉起，**从不开 socket**。
  - `luoke-audit-serve`：只管给 agent 的 socket，**不拿完全磁盘访问、不碰用户的文件**，每个请求交给 `luoke-audit mcp` 去做；由主控当常驻配件起（见下面对 luoke-core 的需求 4）。
- **只做 macOS**，最低 26.2。
- **现状**（2026-10-28）：
  - **已合**：
    - 检查引擎（19 条规则）、给 agent 的 MCP、增量扫描（FSEvents）、两个生成任务的提示词（照 ADR 0019 放在 `prompts/`）和评测（两种底座上硬性条目全过）；
    - 拆成两个程序、打包签名、性能基准；
    - 四类不用点就清，能放回，评测挑错为 0；
    - 要密码的删除（系统目录里的卸载残留），经 agent 或在终端里；
    - 配件清单的 `service`、`permissions`、`listing`，以及三种资源；
    - 写记忆；
    - 每一轮在 outbox 里只放一件（清理结果和体检结果合成一张卡片）。
  - **还没做**：
    - 体检自己的窗口（全部明细的文件夹树、规则编辑）；
    - 旧版 Homebrew 的删除（现在只报）。
  - **等别人**：进配方、常驻起 `luoke-audit-serve`（luoke-core#17、luoke-core#27，beta1 之后）。
  - 进度见 `luoke-audit/STATUS.md`。

## 对外提供

**给 agent：MCP 工具**（agent 工具协议版本 1），由 `luoke-audit-serve` 在 `~/.luoke-audit/run/agent.sock` 上提供：

| 工具 | 只读 | 做什么 |
|---|---|---|
| `audit_status` | 是 | 上一轮什么时候查的、查到多少、病毒库日期、哪些项没扫描及原因 |
| `audit_findings` | 是 | 按结论（放心删 / 要确认 / 仅供参考）、类别列发现，每条带依据和建议动作；给一张结果卡片 |
| `audit_scan_now` | 是 | 请主控尽快跑一轮（用户在对话里说"查一下"）；不改动用户的东西 |
| `audit_plan` | 是 | 对选中的发现出方案（删哪些、换成克隆哪些、清哪些缓存），给一张确认卡片；系统目录里要密码的几项是单独一份方案、单独一个按钮（「移到废纸篓（要输入密码）」） |
| `audit_apply` | 否（列进 `actions`） | 执行用户在卡片上点了的方案；删除一律移到废纸篓。要密码的那份：弹 macOS 的授权对话框，由单独签名的 `luoke-audit-admin` 以管理员身份做 |
| `audit_ignore` | 否（列进 `actions`） | 把一条发现标成"不用管" |
| `audit_restore` | 否（列进 `actions`） | 放回：清理记录里的一条（`c-…`），或一次清理的整批（`p-…` / `auto-…`）；原位置有同名的就放在旁边 |
| `audit_autoclean` | 否（列进 `actions`） | 开或关不用点就清的四类，参数 `{"on": true/false}`（旧的 `enable` 照旧认） |
| `audit_reveal` | 是 | 在访达里选中一条发现指的文件（只在 Mac 上） |
| `audit_open_settings` | 是 | 打开系统设置里对应的隐私与安全性页面（只在 Mac 上） |
| `outbox_ack` | 是 | agent 告诉体检某件事已经说过、答过或放下了 |

**outbox** `luoke://luoke-audit/outbox`（也认相对 id `outbox`）：
- `security`（urgent）：病毒库报毒、新出现的没人担保的常驻项；
- `space`（normal）：可用空间低于门槛；
- `needs-access`（normal）：要用户给完全磁盘访问，带去系统设置的说明；
- 每一轮最多一件（luoke-agent#2，10-27、10-28），编号 `round/<这一轮开始的时间>`：
  - 有自动清了的：`auto-done`（normal，工具协议 §8a）。卡片上半部是清了的，[放回]（整批，缓存是直接删的、放不回）、[以后别自动清]；下半部是要你决定的。agent 还没说过的（它说过以后回 `outbox_ack shown`），带进下一轮那件，最多一周；
  - 没有自动清了的、有要你决定的：`findings`（low），这一轮的摘要和清理方案；
  - 只剩仅供参考的：不放。

**资源**（luoke-agent#3，相对 id）：`summary`（`{"count", "text"}`）、`permissions`（`fda`、`auto`、`admin` 的状态）、`page/overview`、`page/cleaned`（A2UI 基础页）。

**配件清单**（`packaging/luoke-accessory.json`，打包时去掉草案标记）：

```json
{"contract": 1, "accessory": "luoke-audit", "bundle_id": "ai.luoke.audit", "name": "螺壳体检", "version": "0.1.0",
 "type": "app", "entry": [], "resident": false, "resident_exec": "luoke-audit-serve", "resident_command": ["--this-mac"],
 "memory": true, "ui_element": true, "min_macos": "26.2",
 "tasks": [{"name": "luoke-audit.explain", "kind": "generate", "main": false},
           {"name": "luoke-audit.identify", "kind": "generate", "main": false}],
 "jobs": [{"name": "scan", "exec": "luoke-audit", "command": ["scan", "--this-mac", "--autoclean"], "min_interval_minutes": 1440,
           "uses_model": false, "memory_mb": 1500, "allow_battery": false, "timeout_minutes": 60},
          {"name": "update", "exec": "luoke-audit", "command": ["update", "--this-mac"], "min_interval_minutes": 1440,
           "uses_model": false, "memory_mb": 800, "allow_battery": false, "timeout_minutes": 20}],
 "data": ["~/.luoke-audit"],
 "capabilities": {"protocol": 1, "socket": "~/.luoke-audit/run/agent.sock",
                  "reports": [ …上面五类… ],
                  "actions": [ …上面四个会改动东西的… ],
                  "service": {"summary": true, "pages": [{"id": "overview", "title": "概览"}, {"id": "cleaned", "title": "清理记录"}]},
                  "permissions": [{"id": "fda", "kind": "system", "tcc": "SystemPolicyAllFiles", "title": "完全磁盘访问", "facts": [ … ], "without": "degrade"},
                                  {"id": "auto", "kind": "delegate", "title": "不用点就清 4 类", "on": "audit_autoclean"},
                                  {"id": "admin", "kind": "each-time", "title": "删除系统目录里的东西（要 Mac 的密码）"}],
                  "listing": {"tagline": "找出吃空间的和可疑的，替你清掉不会丢东西的", "category": "系统"}}}
```

`resident` 先留 false：主控还不认 `resident_exec`，旧主控按 `resident: true` 会在登录时打开主程序。怎么配合由 luoke-core 定（luoke-core#17）。

**评测集**（交给 luoke-core）：`luoke-audit.explain`（发现归纳成人话：准确、不夸大、给的动作能执行）、`luoke-audit.identify`（只给路径、bundle id、大小、时间，说出可能是什么）。全部用合成的假用户目录。

提示词（`prompts/`，ADR 0019 的格式）用 explain 第 4 版、identify 第 5 版，温度 0。32 GB 档 qwen3.5-9b-4bit、128 GB 档 gemma-4-26b-8bit 上硬性条目都全过（各跑 3 遍）。接进主控的改动在 luoke-core#27（草稿，beta1 之后合）。

## 依赖

| 依赖 | 用来做什么 | 现状 |
|---|---|---|
| luoke-core | 空闲任务 `scan`、`update`；生成任务 `luoke-audit.explain`、`luoke-audit.identify`；常驻起 `luoke-audit-serve`；安装、升级、卸载 | 需求已提（luoke-core#17）；生成任务进配方在 luoke-core#27（beta1 之后合）；常驻起 `luoke-audit-serve` 已在 #17 商定（清单加 `resident_exec` / `resident_command`），beta1 之后接 |
| luoke-agent | 唯一的提醒出口：调 MCP 工具、画卡片、转达 outbox | 已商定（luoke-agent#2），10-23 对着测过、全对上；正式接在 beta1 之后 |
| luoke-mem | 写"发生了什么"（用户清了哪类、忽略了哪类、自动清了什么） | 写哪些已定（见下）；写入口已在 luoke-mem 0.26.0 做好（luoke-mem#7，命令行 `record`），跟 luoke-core#27 一起进下一个大版本 |
| luoke-search | 共用文件元信息 | 10-21 定先各做各的（luoke-search#12 已关）；以后要共用，另加只读接口 |
| macOS | FSEvents、`getattrlistbulk`（遍历）、`getattrlist`（克隆标记）、Security（验签名）、Spotlight 元数据、`launchctl`（常驻项；`sfltool` 会弹管理员密码框，不用） | 系统自带 |
| ClamAV、YARA | 特征扫描（不是模型），随本工具打包、锁定版本；病毒库由 freshclam 从上游更新 | 只进不出（顶层 ADR 0016 修订） |

## 对别的项目的需求

**对 luoke-core**（luoke-core#17）：
1. 登记两个空闲任务：`scan`（每天一次，跑 ClamAV 时约 1 GB 内存；没有新文件的那天不起 ClamAV）、`update`（每天一次，freshclam 下载后逐个试载新的库文件，约 700 MB 内存）。
2. 用 `jobs` 的 `exec` 直接起本工具自己签名的程序，并让 macOS 把它记在本工具名下（TCC 的"负责的 app"是 `ai.luoke.audit`，不是主控），这样完全磁盘访问只授给本工具。
3. 两个生成任务，都走 background：`explain` 每轮 1–3 次、每次约 2–4k token；`identify` 按需、每次几条。
4. 常驻起 `luoke-audit-serve`（Chen Yu 10-26 定由主控起）：照常驻配件的规矩，登录时拉起、异常退出重启、卸载时停。起的时候也让它自己负责（disclaim），不算在主控或 `luoke-audit` 名下。清单已加 `resident_exec` / `resident_command`（luoke-core 10-26 同意）；有它时怎么定常驻，请 luoke-core 定。
5. `GET /tasks` 的 `luoke_mem` 里给出螺壳自带 Python 的路径（写记忆用，见下）。

**对 luoke-agent**（luoke-agent#2、#3）：照工具协议接上面的 MCP 工具、卡片、outbox 和资源；四类按规则挑出的项不用点就清、事后能放回（顶层 ADR 0016 的 10-27 修订，规则评测挑错为 0）。要密码那份方案的选项绑在 `/admin_choices`。

**对 luoke-mem**（luoke-mem#7）：
1. 给没有 Python 可调的程序一个写入口：已做（luoke-mem 0.26.0），`<螺壳的 python> -m luoke_mem record --tool luoke-audit`。本工具已经接上（luoke-audit#35）：只认螺壳 Team 签名的那份 Python，起它时让它自己负责（disclaim），不沾本工具的完全磁盘访问；进配方之前主控答 403，写不进去。
2. 本工具写五种记录（见下），不写路径。
3. 「体检」在健康关键词里：已改，「螺壳体检」不算健康，「体检报告」照常算。

**对 luoke-search**（luoke-search#12）：两边都要遍历文件、都用 FSEvents，谈能不能共用文件元信息（大小、时间、改动），各自只存自己要的。

## 在记忆里读写什么

- **写**：只写"发生了什么"：用户清了哪类、忽略了哪类、自动清了什么、多大。目录清单、文件内容、哈希不写。Chen Yu 10-26 定：记用户清了哪类、几项、多大；忽略了哪类或哪个应用；自动清了什么；病毒怎么处理的（文件名和病毒名）；自动清缓存的开关。不记路径，保留期跟着记忆自己的规则走。
- **五种记录**（luoke-mem#7 定）：

  | topic | speaker / kind | 什么时候写 |
  |---|---|---|
  | `audit-cleaned` | `user` / `receipt` | 用户处理了体检给的清理方案 |
  | `audit-ignored` | `user` / `statement` | 用户说「以后别提」 |
  | `audit-auto-cleaned` | `system` / `activity` | 按规则自动清了，`data` 带 `"by": "rule"`，不拿来归纳习惯 |
  | `audit-malware` | `user` / `receipt` | 用户处理了报毒的文件（`action` 是 `ignore` 也写） |
  | `audit-autoclean` | `user` / `statement` | 用户开或关自动清理 |

  `happened_at` 写真实的本地时间；「先不动」不写。
- **读**：第一版不读。以后可以读记忆归纳的习惯（例如"这类缓存用户总是清"）来排序。

## 要守的底线

- **不带模型**（ADR 0018）：要模型只找主控；主控不在时照样查，只是没有人话归纳。
- **数据不出本机**（ADR 0013）：数据目录 `~/.luoke-audit/`（目录只有本账户能读），排除出 Time Machine；往外只下载病毒库，不上传任何东西。
- **凭证不存值**：找到的密码、密钥、令牌只记位置和类型。
- **只读，改动只来自用户的点按**（工具协议 §5）；删除移到废纸篓。例外是四类不用点就清（顶层 ADR 0016 的 10-27 修订）：会重建的缓存直接删；装好了的应用的安装包、下载里别处还有一份的重复文件、测试工具留下的临时文件夹移进废纸篓，能放回；放回过的那类不再自动清，用户能整个关掉。只在主控定时起的那一轮做。
- **要管理员权限的**（Chen Yu 10-26、10-27 定）：经 agent，点了以后弹 macOS 的授权对话框，一次一授权，不装常驻的 root 辅助程序。root 那一侧先把单独签名的 `luoke-audit-admin` 拷进只有 root 能写的文件夹，按发布签名（Developer ID、Team NJQ5W3T9K5）核对这份拷贝，再用空环境跑；它按和扫描同一个判定重新判定每一项，只动 root 拥有的、不跟随符号链接、核对 inode。第一版只做系统目录里的卸载残留。想自己在终端里做的：`luoke-audit system --this-mac` 列出来，`--trash a0,a1` 移到废纸篓（Chen Yu 10-26、10-28 定）。不加 sudo 跑本程序，它只把同一步交给 `sudo -k`，在终端里每次问密码；root 跑的和密码框那条路是同一段命令，和卡片上是同一份方案。
- **权限分开**：拿完全磁盘访问的 `luoke-audit` 从不开 socket；开 socket 的 `luoke-audit-serve` 不拿完全磁盘访问，也不碰用户的文件。
- **不主动找用户**（ADR 0014）：只经 agent 的 outbox。
- **跑得轻**：外部命令带超时和资源上限、低优先级、增量扫描，用户回来就让路。
