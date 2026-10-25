# 螺壳 luoke

螺壳是实验室出品的一组本地 AI 工具。它们都只在你的电脑上运行，不经过任何云服务；它们一边帮你做事，一边把你自己的东西（你写的邮件、你打的字、你的网站）整理成一份只在本机的记忆，让每个工具、以及以后你自己的个人 agent，都更懂你。

这个仓库放顶层文档（各项目怎么分工、怎么协作、共用哪些词），各项目作为子模块挂在下面，每个项目仍是自己的仓库。

**第一次拿代码**：

```bash
git clone --recurse-submodules https://github.com/luokelabs/luoke.git
cd luoke
git submodule foreach 'git switch main && git pull'
```

各项目仓库现在是私有的，团队以外的人拿到的只有顶层文档。第三行让每个项目停在 main 的最新提交上，不然子模块会停在顶层记下的那个提交（"detached HEAD"），改动容易落在旧代码上。之后每次更新：顶层 `git pull`，再跑一遍第三行。

在哪个项目里改，就在那个项目目录里提交、推那个项目的仓库，和单独克隆时一样。顶层记下的各项目提交由 `luoke-top` 在每天的内部版（`internal-MMDD`）和里程碑（beta、公开发布）时更新并打标签，用来还原"那一版是哪几份代码"，平时顶层 `git status` 里显示项目有新提交是正常的。

| 项目 | 是什么 | 现状 | 注册页 |
|---|---|---|---|
| [luoke-core](luoke-core) | 螺壳（主控）：用户装的应用；本机所有模型推理、配方与评测、各应用的安装和更新 | 0.1.0 开发版，每天两版内部版；beta1 10-29 出 | [projects/luoke-core.md](projects/luoke-core.md) |
| [luoke-mem](luoke-mem) | 螺壳记忆：各应用共用的本机记忆 `~/.luoke/mem.db`，入口在螺壳里 | 0.25，打包在螺壳里 | [projects/luoke-mem.md](projects/luoke-mem.md) |
| [luoke-mail](luoke-mail) | 邮件助手：用本机模型整理整个邮箱 | 0.18，首发主打之一 | [projects/luoke-mail.md](projects/luoke-mail.md) |
| [luoke-ime](luoke-ime) | 输入法：只管按键和上屏，候选交给可以随手写的引擎 | 0.1.19，首发主打之一（要 macOS 26） | [projects/luoke-ime.md](projects/luoke-ime.md) |
| [luoke-agent](luoke-agent) | agent：螺壳的后台组件，唯一主动找用户的出口，以后并进螺壳（先 Mac，再手机） | 开发版（过渡形态）在作者机器上试用，不进首发（v1.x） | [projects/luoke-agent.md](projects/luoke-agent.md) |
| [luoke-community](luoke-community) | 螺壳实验室的官网和螺壳社区 | 封闭测试 11-02 开始，官网在做 | [projects/luoke-community.md](projects/luoke-community.md) |
| [luoke-search](luoke-search) | 深度搜索：给本机文件和照片建索引，按字词和意思找回来；没有自己的界面，入口在螺壳 | 立项，第一版在写，跟 agent（v1.x）出 | [projects/luoke-search.md](projects/luoke-search.md) |
| [luoke-audit](luoke-audit) | 体检：空闲时只读地查这台 Mac 的垃圾和安全问题，规则判断、模型只讲，经螺壳提醒 | 立项，第一版在写 | [projects/luoke-audit.md](projects/luoke-audit.md) |

- [顶层设计](ARCHITECTURE.md)：分工、数据怎么流、项目之间的约定
- [术语](CONTEXT.md)：跨项目共用的词
- [顶层决定记录](docs/adr/)：涉及不止一个项目的决定
- [新增一个组件](docs/new-component.md)：团队成员加新组件的流程
- [系统文档](https://luokelabs.github.io/luoke-atlas/)：各组件现在怎么工作、接口和文件位置
- 各项目的进度看它自己的 `STATUS.md`
