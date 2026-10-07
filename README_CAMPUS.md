# 校园译桥 CampusBridge

基于 LibreTranslate 源码仓库增加的中俄校园工作台。原项目和许可证保留，新增代码位于 `campus/`，不更改上游翻译算法。版本 1.0，2026-10-07。

## 立即运行

安装 Python 3.10 或更新版本后，在本仓库根目录执行：

```sh
python -m campus.server
```

打开 http://127.0.0.1:8765 。校园扩展只依赖 Python 标准库。先点击「填入术语示例」再点击「开始翻译」，可直接演示术语映射。三类双语模板也可离线使用。**这不代表任意文本机器翻译已安装。**

Windows 可双击 `start-campus.cmd`。如果 python 不在 PATH，可改用 `py -3 -m campus.server`。

## 接入真实翻译

在另一个 Python 虚拟环境中按上游 README 安装 LibreTranslate，或使用已安装的 Docker：

```sh
docker compose -f docker-compose.campus.yml up -d
```

首次下载镜像和语言模型需要联网，可能较慢；需准备数 GB 磁盘与内存并根据实际模型验证。镜像默认加载 zh、ru、en，英语可能作为中转语言。具体模型路径以 `/languages` 和实际翻译响应为准，不承诺直译。模型安装完成后可以在断网环境运行。

服务默认为 http://127.0.0.1:5000 。校园扩展的环境变量 `CAMPUS_LT_URL` 可指定自托管服务地址，`CAMPUS_LT_API_KEY` 可提供服务端 API key，`CAMPUS_PORT` 可更改工作台端口。密钥不得写入前端或提交 Git。设置远程地址会把正文发送到该地址，请仅配置受控服务。

## 已实现

- 36 条中文与俄语种子术语，4 个领域，支持搜索与双向精确匹配。
- 最长术语优先、俄文字词边界检查、人工保留词和课程编号保护。
- 术语优先可开关，未锁定文本调用真实 LibreTranslate `/translate`。
- 课程通知、教师答疑邮件、课件标题固定双语模板。
- HTML 双语对照导出，可浏览器打开打印；内容经过 HTML 转义。
- 同源请求检查、正文长度限制、默认仅本机监听、不记录正文。
- 页面提供当前源码下载，保留 AGPL-3.0。

## 术语维护

编辑 `campus/terms.json`，保留唯一 id、zh、ru、domain、status、source 和 version 字段。保存后接口立即读取，无需重启。本版本全部种子词均未经过学校审定；正式使用前应由学科教师与俄语教师联合核定并补充可靠出处。词形匹配是精确匹配，不包含俄语词形还原。锁定名词后分段翻译可能损失上下文及变格，适合专业词核对和标题，整句需复核。用户保留词优先于术语。

## 测试

```sh
python -m unittest campus.test_campus -v
```

测试覆盖术语映射、边界、模板、HTTP 输入与跨站保护。模拟引擎测试验证调用约定，不能证明真实模型翻译质量。端到端模型、Docker 首次下载与俄语专家质量评测需在部署机执行。

## 发布边界

本服务器是本机演示服务器，不直接暴露公网。学校多用户部署需增加认证、访问控制、HTTPS、配额和运维监控。未实现浏览器插件、PDF/OCR、复杂文档版式保留、审批后台或翻译记忆库。

修改版沿用 AGPL-3.0。通过网络向用户提供修改版服务时，应向这些用户显著提供该版本的对应源码；非商业使用不是自动豁免。页面自带源码下载，但正式部署仍需确认源码包含部署版本及其构建资料；不要把密钥、用户数据或模型授权文件混入发布包。模型及词库数据另行核查许可。

## GitHub 提交

当前交付来自用户提供的源码 ZIP，没有上游 Git 历史，也不是 GitHub fork。请先在 GitHub 对 LibreTranslate/LibreTranslate 执行 Fork，然后克隆自己的 fork，把本交付新增的 campus 目录、README_CAMPUS.md、start-campus.cmd、docker-compose.campus.yml 以及 README.md 的校园入口合并到克隆中，再提交和推送。保留其余上游文件，以免覆盖 fork 更新。最后提交自己的 fork 链接和 commit SHA。不要将原仓库链接冒充个人 fork 链接。本任务未创建 PR 或 Issue。

AI 辅助说明：代码、材料初稿由 OpenAI Codex 辅助生成；提交人应理解实现，核查术语与版权，并按比赛要求披露辅助使用情况。
