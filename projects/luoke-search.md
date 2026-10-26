# 螺壳深度搜索 luoke-search

- 仓库：`luoke-search/`（登记合并后由 luoke-top 挂成子模块）；进度：`luoke-search/STATUS.md`；术语：`luoke-search/CONTEXT.md`
- 本页由 luoke-search 的会话维护。

## 是什么

本机的深度搜索：给 Mac 上用户选的文件夹和照片图库建索引，按字词和按意思找回来。想不起东西放在哪、只记得内容的时候用。

- **第一版搜**：
  - 文档：txt、md、rtf、doc、docx、odt、html、xlsx、pptx、csv、tsv（含 GBK 编码的文字文件）；
  - PDF：一页一页读，扫描件按页 OCR；
  - 截图：认出截图，读里面的字；
  - 图片、视频（关键帧和音轨）、录音；
  - 照片图库：经 PhotoKit 读"照片"里的照片和视频，要用户允许。
  - 不搜代码。
- **第二步**：记忆里的记录和依据原文、打字记录（都经记忆读）、邮件（要邮件助手给读取接口）。都从已有组件读，深度搜索自己只存向量和关键词，不重复存原文。
- **没有自己的界面**：没有菜单栏图标、窗口、快捷键面板。用户在螺壳里问（对话由螺壳的后台组件 agent 负责），比如"上个月拍的那张白板照片""合同里写押金的那页"，agent 调深度搜索，把结果画成卡片：标题、命中的片段、出处（第几页、第几秒），点一下在 Mac 上打开。要用户定的事（搜哪些文件夹、要不要照片图库）也由 agent 的卡片来问。
- **对外叫法**（顶层 CONTEXT「对外怎么叫」，10-25）：名字「螺壳深度搜索」；用户入口写"在螺壳里"，按意思搜的推理由"螺壳"提供。下文的"主控"只用于讲内部分工。
- **形态**：一个常驻的后台 .app（不出现在程序坞），由螺壳（luoke-core）安装、在登录时拉起；同一个可执行文件也是命令行 `luoke-search`。bundle id `ai.luoke.search`（已定）。
- **只做 macOS**，最低 26.2。
- **首发**：不在 v1 首发里，跟着 agent（v1.x）出。图片和声音的向量要等主控换上带新 mlx-vlm 的引擎包；在那之前图片、视频、录音只能按文件名和 OCR 的字找，所以有了图片和声音再发布。
- **和 digup 的关系**：从头写。原来基于开源 DigUp（MIT）的 digup 不登记；顶层 ADR 0018「digup 的嵌入」一节由本项目接手，任务改名为 `luoke-search.embed`。
- **现状**：2026-10-20 立项，第一版代码已在 main（2026-10-21）：读文档、PDF 和扫描件、截图、图片、录音、视频和照片图库，按字词和按意思搜，给 agent 的 MCP 和命令行，常驻服务和 .app。进度见 `luoke-search/STATUS.md`。

## 对外提供

**给 agent：MCP 工具**（agent 工具协议版本 1）。在 `~/.luoke-search/run/agent.sock` 上提供；`luoke-search mcp` 在标准输入输出上提供同一组工具。

| 工具 | 只读 | 做什么 |
|---|---|---|
| `search_query` | 是 | 参数 `query`，可选 `kinds`（文档、PDF、截图、图片、视频、录音、照片）、`since` / `until`、`limit`。答复：结果列表（编号、类型、标题、出处、页码或时刻、命中片段、为什么对得上、分数）、`partial`（还在建索引或缺向量时为真，附一句说明），加一张 A2UI 结果卡片 |
| `search_open` | 是 | 按结果编号在 Mac 上打开，跳到那一页或那一刻；或在访达里显示 |
| `search_status` | 是 | 索引了多少、还在等什么、主控能不能算向量 |
| `search_settings` | 是 | 看现在的设置；给出要改的，就出一张确认卡片（方案） |
| `search_settings_apply` | 否（列进 `actions`） | 执行用户在卡片上点了的方案：搜哪些文件夹、跳过哪些、要不要照片图库、用电池时建不建索引 |
| `search_open_system_settings` | 是 | 打开 macOS 系统设置里对应的隐私页（给"要你允许"那张卡片上的按钮用） |

**outbox** `luoke://luoke-search/outbox`，只报两类事，不推搜索结果：
- `needs-access`（normal）：要用户允许读某个文件夹或照片图库，带去系统设置的说明；
- `index-ready`（low）：第一遍索引建好了。

**命令行** `luoke-search`：`index`、`search`、`open`、`status`、`settings`、`eval`、`mcp`，和 MCP 工具一一对应，`--json` 的输出和 MCP 的答复同一个格式。`--index` 指定索引目录，`LUOKE_HUB_SOCKET` 指定主控，开发和测试不碰正式的索引和正在用的主控。

**配件清单**（草案）：

```json
{"contract": 1, "accessory": "luoke-search", "bundle_id": "ai.luoke.search", "name": "螺壳深度搜索",
 "type": "app", "entry": [], "resident": true, "memory": false, "ui_element": true,
 "tasks": [{"name": "luoke-search.embed", "kind": "embed", "main": true}],
 "data": ["~/.luoke-search"], "min_macos": "26.2",
 "capabilities": {"protocol": 1, "socket": "~/.luoke-search/run/agent.sock", "reports": ["…"], "actions": ["…"]}}
```

**评测集**（交给 luoke-core）：
- 参考向量集：9 条参考输入和标准向量（文字 5、截图 / 照片 / 视频帧各 1、声音 1），从 digup 原样拷来，文件不改。主控算的向量对它余弦 ≥ 0.999 是及格线（ADR 0018）。
- 检索评测：全部是合成语料和题目。起点是 digup 的四组（中文 51 题、文档格式 11 题、英文 31 题、孟加拉文和阿拉伯文 43 题）；新加照片图库的题、带时间范围的口语问题、"语料里没有答案"的题。

## 依赖

| 依赖 | 用来做什么 | 现状 |
|---|---|---|
| luoke-core | 嵌入任务 `luoke-search.embed`（`POST /tasks/luoke-search.embed/v1/embed`）、`GET /tasks`；安装、在登录时拉起常驻 | 接口已有（原 `digup.embed`，ADR 0018）；改名和分档前要补的见下（luoke-core#16） |
| luoke-agent | 唯一的入口：调 MCP 工具、画结果卡片、转达 outbox | 工具协议版本 1 已有；本工具的接口待商定 |
| luoke-mem | 第二步：读记录和依据原文 | 第一版不用 |
| luoke-mail | 第二步：搜全部邮件 | 待商定 |
| macOS | Vision（OCR）、PDFKit、AVFoundation、PhotoKit、FSEvents | 系统自带 |

## 对别的项目的需求

**对 luoke-core**（[luokelabs/luoke-core#16](https://github.com/luokelabs/luoke-core/issues/16)）：
1. 任务 `digup.embed` 改名为 `luoke-search.embed`，接口不变：`/v1/embed`、`vector_space`、`lane_busy`、`retry_after_ms`，以后图片和声音的 `inputs`。
2. 分到某一档之前补上（luoke-core 已同意）：起嵌入进程之前查 `fits_memory`、`wired_gb` 按实测写进配方、闲时停、内存压力下停、参数变了重启。
3. 图片和声音：换上带新 mlx-vlm 的引擎包以后打开；参考向量集里 4 条媒体向量也要余弦 ≥ 0.999。
4. 量和延迟：
   - 查询：每问一句一条，`user-waiting`，≤ 64 字；端到端 p90 在 100 ms 以内（M1）。M3 Pro 测试机实测 p50 11.1 ms、p90 11.3 ms。
   - 建索引：`background`。第一次几千到几万个请求，每个最多 32 段；之后只有改动的文件，每分钟几个。
   - 嵌入进程的内存（M3 Pro 测试机实测）：只有文字约 0.8–1.0 GB；开了图片和声音 2.2–3.9 GB（phys_footprint）。

**对 luoke-agent**（[luokelabs/luoke-agent#1](https://github.com/luokelabs/luoke-agent/issues/1)）：照工具协议接上面的 MCP 工具、结果卡片和 outbox。

**待谈**：
- **拒答门槛**：语料里没有答案时，现在多半仍会给出不相干的结果（digup 的 10 道这类题里 9 道是这样）。先在这类题上有评测数字、定下门槛，再开档。在那之前，答复里不说"有把握"，agent 不把弱结果当答案说。
- **邮件读取接口**：搜全部邮件要邮件助手给一个读取接口（例如按时间范围列出邮件、按编号取正文）。第二步时在 luoke-mail 开 issue 商定；在那之前不碰邮件。
- **和 agent**：谁判断"这一问要搜"；手机上要什么（片段多长、要不要缩略图、原件怎么取）；A2UI 组件目录里没有图片组件，缩略图怎么办。

## 在记忆里读写什么

- **第一版**：不读也不写。搜索词不写进记忆。
- **第二步**：读各工具的记录和依据原文（经 `luoke_mem`，ADR 0013 允许），在自己的索引里存向量和关键词，引用记录编号；不写记录和理解，不复制原文。记忆下结论，深度搜索找回原话和原件，两边不重叠。

## 要守的底线

- **不带模型**（ADR 0018）：向量只找主控要；主控不在或不提供时只按字词搜，不退回自带的模型。OCR 用系统的 Vision。
- **数据不出本机**（ADR 0013）：索引在 `~/.luoke-search/`（目录只有本账户能读），排除出 Time Machine；向主控只送文字、图片和声音的字节，不送路径。
- **凭证出去时遮**（ADR 0013，10-22 修订）：名字像密码、密钥、证书的文件不读；读到的文件里的完整证件号、卡号等原样进本机索引、原样送主控算向量，拿完整号码能搜到；结果、卡片、片段、标题交给 agent 时再遮：卡号、证件号只留后四位，密码、验证码、密钥整串遮。outbox 里不放凭证。
- **日志只记元数据**：不记搜索词、片段和文件内容。
- **只读用户的文件**：不改、不移动、不上传。
- **不主动找用户**（ADR 0014）：只经 agent 的 outbox 报两类事；改设置只在用户在卡片上点了以后（工具协议 §5）。
- 开发时把 MCP 接到用云端模型的客户端上，搜到的片段会离开本机，所以这样用时只对着合成的测试语料。
