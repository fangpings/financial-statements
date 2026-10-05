# 读懂美国上市公司财报

从商业交易到经营判断。面向没有会计基础的读者，学习寻找原始披露、理解报表与附注、复算数字，并独立完成一家公司的财务分析。

从[全书目录](textbook/README.md)开始，或直接阅读[第 01 章](textbook/01-questions.md)。教材按八篇组织，共 36 章、6 份附录、146 道基础分章练习及推理答案，另有随堂推演、进阶实作和八份分篇综合作业。扩写版补齐交易分录、多期余额与现金勾稽、附注带读、对照情景及毕业分析底稿。编写与资料核查日期为 2026-10-04。

这是可直接用 Markdown 阅读器阅读的教材。真实案例以各章指定的历史财年及申报版本为准；虚构企业“北辰设备”及其他教学假设均明确标注。范围以美国国内上市公司的 US GAAP 报表为主，外国发行人及 IFRS 差异见附录 E。

本轮逐篇补写的内容与复核范围见[审阅记录](reviews/README.md)。想先检查教学深度，可以读[收入确认](textbook/11-revenue.md)、[租赁](textbook/17-leases.md)或[完整年报带读](textbook/35-guided-report.md)。

配套数据位于 [data](data/README.md)。运行以下命令，复核贯穿案例、毕业项目数据和教材内部链接：

```sh
python3 tools/check_book.py
python3 tools/accounting_lab.py
```

上述程序仅使用 Python 标准库，无需账号或网络。真实原始资料链接需联网打开。与相邻教材的衔接见[附录 F](textbook/appendix-f-connections.md)。

## 网页阅读与本地预览

网页使用与 `us-econ`、`cn-econ`、`mmt` 相同的 VitePress 方案，提供八篇导航、中文全文搜索、明暗主题和折叠答案。Markdown 源文件仍可直接阅读；网站构建时会把相邻仓库的本地链接转换为它们的 GitHub Pages 地址。

需要 Node.js 22 和 Python 3.9 或更新版本：

```sh
npm ci
npm run check
npm run dev
```

生成及预览静态站点：

```sh
npm run build
npm run check:site
npm run preview
```

构建产物位于 `.vitepress/dist/`，不纳入 Git。预览地址为 `http://127.0.0.1:4173/financial-statements/`。

## 首次发布到 GitHub Pages

目标仓库为 `fangpings/financial-statements`，预计站点地址为 `https://fangpings.github.io/financial-statements/`。配置已准备好，远程仓库与线上部署尚未完成。本次环境禁止写入 `.git`，且无法解析 GitHub/npm 域名；本地构建使用从相邻 `mmt` 仓库复制的同版本依赖和锁文件进行验证。正常联网环境应使用上面的 `npm ci` 从锁文件安装。

在可写入 `.git`、能访问 GitHub 的终端中进入本目录，先确认 `gh auth status` 已登录目标账号；需要时运行 `gh auth login`。若目标远程仓库尚不存在，执行：

```sh
git init -b main
git add .
git commit -m "Add financial statements textbook and GitHub Pages site"
gh repo create fangpings/financial-statements --public --source=. --remote=origin --push
gh api --method POST repos/fangpings/financial-statements/pages -f build_type=workflow
gh workflow run pages.yml --repo fangpings/financial-statements
gh run list --repo fangpings/financial-statements --workflow pages.yml
```

若远程仓库已存在，先核对其内容，再配置 `origin`；不要强制推送覆盖。若 Pages 已启用，可在仓库 **Settings → Pages → Source** 选择 **GitHub Actions**，无需重复创建 Pages。首次推送可能在 Pages 启用前触发一次失败，启用后手动运行工作流即可。

后续推送到 `main` 会自动进行教材校验、网站构建及 Pages 发布。工作流见 `.github/workflows/pages.yml`，站点配置见 `.vitepress/config.mts`。若改用其他仓库名，请同步调整配置中的 `base`。部署方式参考 [VitePress 官方说明](https://vitepress.dev/guide/deploy)。
