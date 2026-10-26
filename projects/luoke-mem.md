# 螺壳记忆 luoke-mem

- 仓库：[`luoke-mem/`](../luoke-mem)；设计：`luoke-mem/DESIGN.md`
- 本页由 luoke-mem 的会话维护。

## 是什么

螺壳工具共用的本机记忆：一个 SQLite 文件 `~/.luoke/mem.db`（目录 700、文件 600，位置可以用 `LUOKE_HOME` 换）。它记下各工具写来的"发生了什么"（记录，可以带原文），并且是唯一下结论的地方：关于用户的理解——关于你、关注的话题、不感兴趣、处理习惯、常用说法——都由它归纳，每条带依据和把握程度（顶层 [ADR 0014](../docs/adr/0014-who-does-what.md)、[0015](../docs/adr/0015-how-memory-thinks.md)）。

记忆归用户，不归任何一个工具。本机就是边界（[ADR 0013](../docs/adr/0013-the-machine-is-the-boundary.md)）：任何工具、agent 都读得到全部记录、理解和依据原文；删别的工具写的、清空，只在记忆自己的界面里做。记忆打在主控里，打开方式是 `luoke://memory`。

现状 0.25.9（beta1 用 0.25.8）。

## 对外提供

- **Python 库 `luoke_mem`**：只用标准库，Python 3.9 起。各配件优先用主控里那一份（见下「和使用方定下的」）。
  - 写：`record`（库在写入前遮掉凭证）、`state`、`propose`、`conclude`（按"什么记录能推出什么理解"的表定档）、`confirm`、`reject`、`revise`、`later`、`was`（以前是，现在不是）、`redate`（改正本工具记录的时间）。
  - 读：`notes`（默认给比较确定以上；`confidence=[...]` 按档读；每条带 `confidence`、`data`、`auto`、`fresh`）、`note`（全部依据的原文和 `data`）、`records`（默认本工具的，`tool=` 别的工具的，`tool=None` 全部）、`context`、`counts`、`recent`。
  - 合并和拆开：同一机构的事实是一条（话题「机构:<名>」）；`merged(nid)` 列出并进来的说法，`WholeMemory.split(nid)` 拆出来。
  - 删：`forget`（单条理解）、`forget_records`（本工具的一部分记录，可以留下被引用的）、`forget_tool()`（本工具写的全部）。删别的工具写的、`forget_all` 只在 `WholeMemory`（记忆自己的界面和命令行）里。
  - 想问的和建议（给 agent 和工具页面）：`asks(tool=...)` 读，`reply(id, choice, text)` 交回（yes / no / past / revise / later / answer；建议是 useful / useless / never）。
  - 凭证和敏感：`mask_secrets(text)`（别名 `mask`）、`find_secrets(text)`；`sensitive_kinds(text)` 标健康、法律纠纷、宗教政治，这三类推出来的要用户点头才算（`CONFIRM_KINDS`）。`allowed()`、`ask(类别)`、`withheld()`、`never_kept()`、`sensitive()` 留着给旧调用方，不再限制什么。
  - 给用户看的名字：`KIND_NAMES`、`TOOL_NAMES`、`CONFIDENCE_NAMES`、`CATEGORY_NAMES`、`action_name()`。
- **理解的类别**：`fact` 关于你、`interest` 关注的话题、`dislike` 不感兴趣、`preference` 处理习惯、`term` 常用说法、`taste` 精选的口味（邮件助手挑精选用，不算关于你）。三档：猜测 / 比较确定 / 确定；会变的太久没有新依据是"以前的事"（`status='past'`）。
- **处理习惯**：`data={account, sender, category, action, name}`（加标签带 `label`，filter 带 `filter`）；`auto` 只在"确定"、有类别、动作能撤回（`AUTO_ACTIONS`：archive、read、label、filter）时为真。删除、标垃圾、退订只做成建议（[ADR 0016](../docs/adr/0016-acting-for-the-user.md)）。
- **整份记忆的界面**：本机网页，`luoke://memory`（`?note=N` 打开到一条，`?view=recent` 打开"最近记下的"）。概览、猜测、以前的事、各类理解、全部依据（含工具存的内容）、确认 / 不对 / 现在还是 / 修改 / 忘掉、按来源忘掉、清空。只监听 127.0.0.1，校验令牌、Host、Origin。`luoke_mem.ui.ensure(path) -> url` 给用数据副本开发时用。
- **配件清单**：`luoke-mem/packaging/accessory.json`，主控原样拷进自己的 .app，读 tasks、jobs、commands。
  - 任务：`luoke-mem.typing`（从打字归纳常用说法和话题）、`luoke-mem.topics`（从邮件助手的记录和原文归纳话题、口味、不感兴趣），都是后台生成任务；评测 `bench/run_typing.py`、`bench/run_topics.py`。
  - 空闲任务：`learn`（归纳、反刍：重新定档、以前的事、习惯、想问的、建议）。
  - 命令：`forget-tool <工具> [--dry-run]`。
- **命令行**：`python3 -m luoke_mem [--path P] ui | sources | forget-tool <工具> [--dry-run] | learn [--force] [--again] [--hub S] | app [--note N] [--view recent]`。
- **多个进程同时读写**：WAL 模式加等待锁；忘掉的从文件里也抹掉（`secure_delete`，清空预写日志）。
- **版本和兼容**：schema 只加不改，`user_version` 只升不降，旧的库容得下新的列、类别和状态（DESIGN「版本和兼容」）。

## 依赖

- 只用标准库。
- **螺壳（luoke-core）**：在后台生成任务里用模型（`luoke-mem.typing`、`luoke-mem.topics`），在空闲时拉起 `learn`；主控在 `GET /tasks` 里报自己那份 luoke_mem 的路径。没有主控时只是不归纳，记忆照常读写。

## 使用方

- **luoke-mail**：写记录（发出的邮件、机构来信、订阅的打开和原文、精选的打开和反馈、标签、亲手的处理、改过的建议、规则做的、撤回），读理解和确定的习惯，页面上显示和它有关的想问的和建议。见 [luoke-mail.md](luoke-mail.md)。
- **luoke-ime**：个人化组件写上屏记录（带前文，标成第三方），读常用说法和别的理解做联想。见 [luoke-ime.md](luoke-ime.md)。
- **luoke-agent**：读想问的和建议（`asks`），卡片上列依据原文（`note()["cites"]`），把回答交回（`reply`）。见 [luoke-agent.md](luoke-agent.md)。
- **luoke-audit**（螺壳体检，beta1 之后接入）：写清了什么、忽略了什么、自动清了什么、报毒怎么处理的、自动清缓存的开关；第一版不读。见 [luoke-audit.md](luoke-audit.md)。
- **luoke-core**：把 luoke_mem 打进主控、处理 `luoke://memory`、调度 `learn`、跑评测；卸载别的配件时，用户勾了"同时从记忆里忘掉"才调 `forget-tool`。见 [luoke-core.md](luoke-core.md)。

## 和使用方定下的

- **用主控里那份 luoke_mem**：主控 `GET /tasks` 的答复顶层有 `"luoke_mem": {"path", "version"}`（只有打着记忆的主控才报）。邮件助手、agent 每次新起进程时问一次，插到 `sys.path` 最前面再导入，问不到就用自带的兜底那份；输入法的个人化组件跑在主控的 Python 上，直接导入，没有主控就不写记忆。兜底那份只要不比主控里钉住的新。
- **luoke-mail**：
  - 记录：`mail-read` 每个发件人每月一条，带 `count`、`opened`（只数用户自己打开的）、`category`、`mails`（这个月打开过的最新 3 封 {subject, date, text}；事务邮件不带正文），同一 `ref` 再写一条带原文的就替掉旧的那条；`digest-open`、`digest-feedback` 带 `source`、`text`；`sent-mail` 带用户自己写的部分 `text`；`mail-acted` 带 `action`、`label`、`category`、`where`（here / elsewhere）、`count`、`name`；`mail-override` 带 `from`、`to`；`mail-auto`（规则做的，`by=rule`）和 `mail-undo-auto`（带习惯的 `note_id`，算反证）。每条带 `account`、`sender`、`by`、`happened_at`（真实时间）。写进去的文字先过 `mask_secrets`。
  - 机构来信推出的事实，话题写「机构:<完整机构名>」，同一机构的不同说法都用它，由记忆并成一条。从邮件原文里抽事实（发出的邮件、机构来信）是邮件助手的观察，照旧调 `conclude` / `propose`，由记忆的表定档；话题、不感兴趣、习惯由记忆归纳。精选读 `notes(kinds=["taste", "interest"])`；自动执行读 `notes(kinds=["preference"], confidence=["sure"])` 里 `auto` 为真的；页面上的想问的和建议读 `asks(tool="luoke-mail")`。
- **luoke-ime**：`ime-commit`（用户 / 陈述，`data.app`，`data.context` 是光标前的前文、标成 `third_party`）、`ime-correction`、`ime-forget`（不要的候选）。按应用、按时间段删用 `forget_records`；用户设了保留期就 `forget_records(..., keep_cited=True)`。常用说法由记忆归纳，只数用户自己打的。
- **luoke-agent**：想问的、建议从 `asks()` 读，依据从 `note(about_note)["cites"]` 读，回答一律 `reply`；习惯建议（`action.capability == "habit"`）给"好 / 不用 / 别再提"。
- **luoke-audit**（luoke-mem#7 商定，beta1 之后实现）：体检是 Swift 程序，用螺壳的 Python 起 `python -m luoke_mem record --tool luoke-audit`，标准输入一行一条 JSON（字段同 `record()`），标准输出一行对一行回 `{"id"}` 或 `{"error"}`；没给 `sensitive` 就由命令标。topic：`audit-cleaned`（user / receipt）、`audit-ignored`（user / statement）、`audit-auto-cleaned`（system / activity，`by=rule`）、`audit-malware`（user / receipt）、`audit-autoclean`（user / statement）。不记路径。「螺壳体检」四个字不算健康。
- **用户对理解说的话归记忆**：`state`、`confirm`、`reject`、`revise`、`later`、`was`、`reply` 记在 luoke-mem 名下，`data` 是 `{"via": 调用的工具}`；卸载某个工具时，用户确认过、否定过、亲口写的留着。
- **升版通知**：luoke-mem 升版时告诉用到它的会话，说清接口有没有变；接口只加不改，主控换了新库，旧的调用照样能用。

## 对别的项目的需求

- **luoke-mail**：ADR 0015 说的"必要时向工具要更多原文"还没有通道；beta1 之后商定一个读取接口（比如按发件人取最近几封的正文）。
