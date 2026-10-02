# 《心理统计枕边书》双语版项目架构说明
# Psychological Statistics for the Unhurried People (Multilingual Edition)

本项目采用**一体化多语言架构（Single Root Quarto Project with Part-Divided Multilingual Chapters）**构建，兼顾中英文双语独立排版、独立目录、独立搜索、独立交叉引用以及本地 KaTeX 公式渲染。

---

## 目录结构

```text
Psych_Stats_Unhurried_Multilingual/
├── _quarto.yml            # 根目录全局配置文件（激活 RStudio 原生 Build / Publish）
├── Psych_Stats_Unhurried_Multilingual.Rproj  # RStudio 项目文件
├── index.qmd              # 根目录双语首页（序言 + 中英导航）
├── cover.png              # 封面
├── references.bib         # 参考文献
├── katex/                 # 本地内嵌 KaTeX 引擎
├── lang-switch.js         # 语言智能切换与章节同步脚本（右上角悬浮胶囊按钮）
├── rsconnect/             # Posit Cloud 部署凭据与配置
│
├── zh/                    # 中文版章节目录 (lang: zh)
│   ├── _metadata.yml      # 目录元数据 (声明中文语言与本地化)
│   ├── chap1.qmd ~ 4.qmd  # 中文章节
│   ├── data/              # R 运行数据环境 (chapter2_env.RData 等)
│   └── images/            # 插图素材
│
└── en/                    # 英文版章节目录 (lang: en)
    ├── _metadata.yml      # 目录元数据 (声明英文语言与本地化)
    ├── index.qmd          # 英文版 Preface
    ├── chap1.qmd ~ 4.qmd  # 英文版精译章节
    ├── data/              # R 运行数据环境
    └── images/            # 插图素材
```

---

## 语言切换与章节同步机制

- **屏幕右上角悬浮胶囊按钮**：
  - 无论滚动到哪一页，右上角始终展示 `[ 🌐 English ]` / `[ 🌐 中文版 ]` 按钮；
  - 在第 2 章点击即可自动跳转到英文版对应第 2 章，保留锚点定位；
  - 自动在浏览器中记忆语言偏好。

---

## 在 RStudio 中原生编译与一键发布

由于项目根目录直接配置了标准的 `_quarto.yml` 和 `rsconnect`：

1. **一键编译（Render Book）**：
   在 RStudio 右上角 **`Build` 选项卡** 中，点击 **`Render Book`** 按钮（或直接点编辑器上方的 `Render`）；
2. **一键发布（Publish）**：
   直接点击 RStudio 工具栏上的 **蓝色原生「Publish...」按钮**，RStudio 会调出官方发布面板，一键更新发布至 Posit Cloud Connect！
