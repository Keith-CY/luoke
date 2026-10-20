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
- **形态**：签名公证的 .app，不常驻；由主控的空闲任务拉起检查。bundle id 建议 `ai.luoke.audit`。
- **只做 macOS**，最低 26.2。
- **现状**：2026-10-20 立项，私有仓库已建，还没有代码。进度见 `luoke-audit/STATUS.md`。

## 对外提供

**给 agent：MCP 工具**（agent 工具协议版本 1），在 `~/.luoke-audit/run/agent.sock` 上提供：

| 工具 | 只读 | 做什么 |
|---|---|---|
| `audit_status` | 是 | 上一轮什么时候查的、查到多少、病毒库日期、哪些项没扫描及原因 |
| `audit_findings` | 是 | 按类别、严重度列发现，每条带依据和建议动作；给一张结果卡片 |
| `audit_scan_now` | 是 | 请主控尽快跑一轮（用户在对话里说"查一下"）；不改动用户的东西 |
| `audit_plan` | 是 | 对选中的发现出一份方案（删哪些、换成克隆哪些、清哪些缓存），给一张确认卡片；要管理员权限的几项单独标出"会请你输入 Mac 的密码" |
| `audit_apply` | 否（列进 `actions`） | 执行用户在卡片上点了的方案；删除一律移到废纸篓。要管理员权限的部分弹 macOS 标准的授权对话框，用户不碰终端 |
| `audit_ignore` | 否（列进 `actions`） | 把一条发现或一类标成"不用管" |
| `audit_autoclean` | 否（列进 `actions`） | 用户同意（或收回）"会重建的缓存以后自动清" |

**outbox** `luoke://luoke-audit/outbox`：
- `security`（urgent）：病毒库报毒、新出现的未签名常驻项这类；
- `space`（normal）：空间明显在被某个来源吃掉，或可用空间低于门槛；
- `findings`（low）：一轮查完的摘要；
- `needs-access`（normal）：要用户给完全磁盘访问，带去系统设置的说明；
- `auto-done`（normal）：自动清了会重建的缓存（工具协议 §8a），带撤销不了的说明（缓存删了只能等工具重建）。

**配件清单**（草案）：

```json
{"contract": 1, "accessory": "luoke-audit", "bundle_id": "ai.luoke.audit", "name": "螺壳体检",
 "type": "app", "entry": [], "resident": false, "memory": true, "ui_element": true,
 "tasks": [{"name": "luoke-audit.explain", "kind": "generate", "main": true},
           {"name": "luoke-audit.identify", "kind": "generate", "main": false}],
 "jobs": [{"name": "scan", "exec": ["…"], "min_interval_minutes": 1440, "uses_model": true, "memory_mb": 1500, "timeout_minutes": 60},
          {"name": "update", "exec": ["…"], "min_interval_minutes": 1440, "uses_model": false, "memory_mb": 200, "timeout_minutes": 20}],
 "data": ["~/.luoke-audit"], "min_macos": "26.2",
 "capabilities": {"protocol": 1, "socket": "~/.luoke-audit/run/agent.sock", "reports": ["…"], "actions": ["…"]}}
```

**评测集**（交给 luoke-core）：`luoke-audit.explain`（发现归纳成人话：准确、不夸大、给的动作能执行）、`luoke-audit.identify`（只给路径、bundle id、大小、时间，说出可能是什么）。全部用合成的假用户目录。

## 依赖

| 依赖 | 用来做什么 | 现状 |
|---|---|---|
| luoke-core | 空闲任务 `scan`、`update`；生成任务 `luoke-audit.explain`、`luoke-audit.identify`；安装、升级、卸载 | 待开 issue |
| luoke-agent | 唯一的提醒出口：调 MCP 工具、画卡片、转达 outbox | 工具协议版本 1 已有；本工具的接口待商定 |
| luoke-mem | 写"发生了什么"（用户清了哪类、忽略了哪类、自动清了什么） | 用主控里那份 `luoke_mem` |
| luoke-search | 待谈：共用文件元信息 | 待开 issue |
| macOS | FSEvents、`getattrlist`（克隆标记）、Security（验签名）、Spotlight 元数据、`sfltool` / `launchctl`（常驻项） | 系统自带 |
| ClamAV、YARA | 特征扫描（不是模型），随本工具打包、锁定版本；病毒库由 freshclam 从上游更新 | 只进不出（顶层 ADR 0016 修订） |

## 对别的项目的需求

**对 luoke-core**（待开 issue）：
1. 登记两个空闲任务：`scan`（每天一次，跑 ClamAV 时约 1 GB 内存）、`update`（每天一次，freshclam，只下载）。
2. 用 `jobs` 的 `exec` 直接起本工具自己签名的程序，并让 macOS 把它记在本工具名下（TCC 的"负责的 app"是 `ai.luoke.audit`，不是主控），这样完全磁盘访问只授给本工具。
3. 两个生成任务，都走 background：`explain` 每轮 1–3 次、每次约 2–4k token；`identify` 按需、每次几条。

**对 luoke-agent**（待开 issue）：照工具协议接上面的 MCP 工具、卡片和 outbox；`audit_autoclean` 的确认卡片要写清只限会重建的缓存（顶层 ADR 0016 修订）。

**对 luoke-search**（待开 issue）：两边都要遍历文件、都用 FSEvents，谈能不能共用文件元信息（大小、时间、改动），各自只存自己要的。

## 在记忆里读写什么

- **写**：只写"发生了什么"：用户清了哪类、忽略了哪类、自动清了什么、多大。目录清单、文件内容、哈希不写。
- **读**：第一版不读。以后可以读记忆归纳的习惯（例如"这类缓存用户总是清"）来排序。

## 要守的底线

- **不带模型**（ADR 0018）：要模型只找主控；主控不在时照样查，只是没有人话归纳。
- **数据不出本机**（ADR 0013）：数据目录 `~/.luoke-audit/`（目录只有本账户能读），排除出 Time Machine；往外只下载病毒库，不上传任何东西。
- **凭证不存值**：找到的密码、密钥、令牌只记位置和类型。
- **只读，改动只来自用户的点按**（工具协议 §5）；删除移到废纸篓；会重建的缓存是唯一能在确认一次后自动清的（顶层 ADR 0016 修订）。
- **要管理员权限的，用户不碰终端**：点了以后弹 macOS 标准的授权对话框，一次一授权，不装常驻的 root 辅助程序。提权执行的是本工具自己签名的程序加方案编号（先验签名，再逐项核对路径、inode、大小，不跟随符号链接），不是拼出来的命令。
- **不主动找用户**（ADR 0014）：只经 agent 的 outbox。
- **跑得轻**：外部命令带超时和资源上限、低优先级、增量扫描，用户回来就让路。
