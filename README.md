# Novel2Script

Novel2Script 是一个“小说文本 -> 结构化剧本 YAML”的最小可运行实现。当前版本根据 `docs/technical-design-v0.1.md` 的 Agent Pipeline 设计，用规则引擎完成章节识别、人物/地点提取、场景生成、YAML 组装和 Schema 校验。

## 功能

- 提供纯离线 Web 前端，直接打开 `index.html` 即可使用。
- 支持至少 3 个章节的中文小说文本输入。
- 自动识别章节标题，章节不清晰时尝试分隔符或语义分块。
- 提取基础人物、地点、时间线、主要事件、冲突和对白。
- 将章节改写为可编辑的剧本 YAML 初稿。
- 校验章节数量、人物引用、地点引用、场景顺序和 beat 类型。

## 程序结构

当前实现按 `docs/technical-design-v0.1.md` 中的 Agent Pipeline 拆分：

- `input_parser.py`: 清洗输入文本并处理空输入错误。
- `chapter_segmenter.py`: 识别章节标题、分隔符或语义分块，生成章节对象。
- `story_analyzer.py`: 提取人物、地点、时间线、主要事件、故事基调和冲突。
- `adaptation_planner.py`: 将章节规划为剧本场景，并生成改写策略。
- `scene_writer.py`: 根据场景规划生成动作、对白和转场。
- `composer.py`: 按稳定字段顺序组装 script 数据。
- `validator.py`: 校验 Schema、引用关系、场景顺序和 beat 类型。
- `yaml_writer.py`: 输出不依赖第三方库的 YAML 文本。

前端文件：

- `index.html`: 离线 Web 入口。
- `web/js/converter.js`: 浏览器端小说转剧本规则引擎。
- `web/js/main.js`: 页面交互、复制、下载和本地草稿保存。
- `web/css/styles.css`: 响应式界面样式。

## 快速开始

打开前端界面：

```bash
open index.html
```

直接用源码运行：

```bash
PYTHONPATH=src python3 -m novel2script examples/sample_novel.txt
```

写入文件：

```bash
PYTHONPATH=src python3 -m novel2script examples/sample_novel.txt -o output.yaml --title 雨夜来信
```

安装为命令行工具：

```bash
python3 -m pip install -e .
novel2script examples/sample_novel.txt -o output.yaml
```

## 输入格式

输入应是 UTF-8 文本，至少包含 3 个章节。章节可使用类似格式：

```text
第一章 雨夜
……

第二章 追问
……

第三章 旧案
……
```

也支持 `Chapter 1`、`1. 标题`、`---` 等边界形式；如果边界不明确，程序会尝试按段落拆成临时章节。

## 输出结构

输出根字段为 `script`，结构遵循 `docs/yaml-schema-v0.1.md`：

```yaml
script:
  schema_version: "1.0"
  title: "雨夜来信"
  format: "screenplay"
  language: "zh-CN"
  source:
    type: "novel"
    chapter_count: 3
  characters: []
  locations: []
  chapters: []
  scenes: []
  notes: []
```

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
node tests/test_web_converter.js
```

## 当前边界

v0.1 是规则版原型，不调用远程 AI 模型。它适合验证数据结构、CLI 流程和 Schema 约束；后续可以将 `Story Analyzer`、`Adaptation Planner`、`Scene Writer` 替换为真正的 LLM Agent。
