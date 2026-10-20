# 螺壳系统文档（atlas）

整个系统的结构、组件、接口、数据流、运行与发布。按项目文档的方式写，内容对照代码核对。

- 源文件：`shell.html`（外壳和样式）、`pages/*.html`（每页一个片段，第一行是 `<!-- id | nav | group -->`，页面顺序在 `build.py` 的 `PAGES`）。
- 生成：`python3 atlas/build.py` → `index.html`（Artifact 用）和 `site/index.html`（完整网页）。
- 发布：`sh atlas/publish.sh` 把 `site/` 推到公开仓库 `luokelabs/luoke-atlas`，GitHub Pages 地址 https://luokelabs.github.io/luoke-atlas/ 。只有生成的网页公开，源文件留在私有的顶层仓库。
- 公开前检查：不写密钥、令牌、个人邮箱、主机名和用户数据。
- 由 luoke-top 维护；各项目会话发现写错了，告诉 luoke-top。
