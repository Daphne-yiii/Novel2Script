# AI 小说转剧本工具通用 Prompt 模板 v0.1

以下模板可直接复制给 AI Agent，用于生成或实现“小说文本转结构化剧本 YAML”的工具。

## 通用 Prompt 模板（可直接复制）

```text
# 角色
{role: 你是一位资深的 AI 剧本改编工具开发者，精通小说叙事分析、剧本结构设计、YAML 数据建模、Schema 校验和 Agent Pipeline 工程实现。}

# 核心目标
{goal: 我需要你帮我开发一款纯本地运行的 AI 辅助小说转剧本工具，将作者提供的小说文本自动转换为结构化剧本初稿，输出格式为 YAML。}

# 输入文本与改编目标
- 工具名称: {tool_name: Novel2Script}
- 输入内容: {input_text: 小说全文，必须包含至少 3 个章节。章节可通过标题、编号、分隔符或模型语义识别。}
- 输出格式: {output_format: YAML}
- 输出语言: {language: zh-CN}
- 剧本类型: {script_format: screenplay，可扩展为 web_series、stage_play、audio_drama。}
- 核心改编要求: {adaptation_details: 自动识别章节、人物、地点、时间线、场景、事件、冲突和对白；将小说叙事改写为可拍摄、可表演、可编辑、可校验的结构化剧本初稿。}
- 追溯要求: {traceability: 每个剧本场景必须保留 source_chapters，用于追溯原小说章节。}

# Agent Pipeline 与模块职责
{pipeline:
- Input Parser:
  - 接收小说文本。
  - 清洗空白字符、非法符号、重复段落。
  - 尝试识别章节边界。
  - 校验章节数量不少于 3。
- Chapter Segmenter:
  - 将小说拆分为章节对象。
  - 每章保留标题、顺序、正文、摘要。
  - 对无法明确识别标题的章节生成临时标题。
- Story Analyzer:
  - 提取人物、地点、时间线、主要事件、情绪基调、冲突关系。
  - 生成全局故事理解结果，供后续改编使用。
- Adaptation Planner:
  - 将小说章节规划为剧本场次。
  - 决定每章对应几个场景。
  - 区分可视化动作、对白、旁白、心理描写改写策略。
  - 生成剧本大纲。
- Scene Writer:
  - 根据大纲生成具体场景。
  - 每个场景包含地点、时间、人物、动作、对白、转场等元素。
  - 将小说中的叙述语言转为可拍摄、可表演的剧本语言。
- YAML Composer:
  - 将分析结果和剧本内容组装为 YAML。
  - 保证字段顺序稳定、结构清晰、便于人工编辑。
- Schema Validator:
  - 校验 YAML 是否符合 Schema。
  - 检查必填字段、数据类型、场景编号、人物引用、章节数量等。
  - 若校验失败，返回错误并触发修复流程。
}

# 核心改编策略（严格遵守）
{adaptation_strategy:
- 小说转剧本不是简单摘要，而是叙事媒介转换。
- 心理描写应优先转换为动作、表情、沉默、对白或场景调度。
- 大段背景说明应拆分为可视化信息，必要时使用旁白。
- 小说中的连续事件应按地点、时间、人物变化拆成多个场景。
- 对白需要保留人物声音，但应更口语化、可表演。
- 每个场景应有明确戏剧功能，例如铺垫、冲突、转折、揭示、高潮。
- 保留原章节映射，方便作者追溯来源文本。
}

# 产物技术与合规约束（严格遵守）
{tech_constraints:
- 交付形态: 产物可以为命令行工具、Web 工具或可被其他系统调用的模块化程序。
- 本地运行: 优先支持纯本地运行；如接入 AI 模型，应将模型调用封装为可替换模块。
- 输入限制: 输入小说文本必须至少包含 3 个章节；不足 3 个章节时直接返回明确错误。
- 输出限制: 输出必须是合法 YAML，并满足约定的 YAML Schema。
- Schema 稳定性: 顶层必须包含 script；script 内必须包含 schema_version、title、format、language、source、logline、synopsis、characters、locations、chapters、scenes、notes。
- 字段顺序: YAML 输出字段顺序应稳定，方便人工编辑、版本管理和二次处理。
- 人物引用: 场景和对白中的 character_id 必须引用 characters 中已定义的人物 id；无法确认的人物应补全或标记为 unknown。
- 地点引用: 场景 heading.location_id 必须引用 locations 中已定义的地点 id。
- 章节引用: scenes.source_chapters 必须引用 chapters 中已定义的章节 id。
- 错误处理:
  - 章节不足时返回错误文案：输入章节少于 3 个，无法生成剧本。
  - 章节边界不清晰时，使用语义切分并生成临时章节标题。
  - YAML 校验失败时，尝试自动修复；无法修复时返回校验错误列表。
  - 场景缺少地点、时间或动作时，触发补全或重写。
  - 剧本内容过短、无法覆盖原章节主要情节时，触发低质量场景重写。
- 合规要求: {negative_prompt: 内容不得包含任何违法违规、IP 侵权、不利于未成年人的内容；不得主动生成受版权保护作品的长篇仿写或侵权改编内容。}
}

# YAML Schema 输出结构
{yaml_schema:
script:
  schema_version: "1.0"
  title: "作品标题"
  format: "screenplay"
  language: "zh-CN"
  source:
    type: "novel"
    chapter_count: 3
  logline: "一句话故事梗概"
  synopsis: "完整故事摘要"
  characters:
    - id: "char_001"
      name: "人物名称"
      role: "protagonist"
      description: "人物简介"
      traits:
        - "性格标签"
  locations:
    - id: "loc_001"
      name: "地点名称"
      description: "地点简介"
  chapters:
    - id: "chapter_001"
      title: "第一章"
      order: 1
      summary: "章节摘要"
  scenes:
    - id: "scene_001"
      order: 1
      source_chapters:
        - "chapter_001"
      heading:
        location_id: "loc_001"
        time_of_day: "night"
        interior_exterior: "interior"
      purpose: "该场景的戏剧功能"
      characters:
        - "char_001"
      beats:
        - type: "action"
          text: "动作描写"
        - type: "dialogue"
          character_id: "char_001"
          text: "对白内容"
      transition: "cut_to"
  notes: []
}

# Beat 类型定义
{beat_types:
- action: 动作、场面调度、可视化叙事。
- dialogue: 角色对白，必须包含 character_id。
- parenthetical: 表演提示，通常依附于某个角色。
- voice_over: 旁白或内心独白转写，通常包含 character_id。
- sound: 音效。
- transition: 场景内转场提示。
}

# 输出结构与验证口径
{output_structure:
- 输出一个完整、可运行、可校验的项目或模块。
- 如果生成程序，必须包含清晰入口，例如 CLI 命令、main 函数或 Web 入口。
- 如果生成 YAML，根字段必须是 script。
- 输出 YAML 必须可被标准 YAML 解析器解析。
- 输出 YAML 必须满足上方 Schema。
- characters、locations、chapters、scenes 的 id 必须唯一。
- scene.order 必须连续或至少不重复。
- 每个 scene 必须至少包含一个 action beat。
- dialogue、parenthetical、voice_over 类型 beat 如包含 character_id，则必须引用已定义人物。
- 最终请提供完整代码文件内容、运行方式和最小示例输入。
}
```

## Agent 工作流

```text
小说文本输入
  ↓
文本清洗与章节识别
  ↓
章节数量校验
  ↓
故事分析
  ↓
人物 / 地点 / 时间线提取
  ↓
剧本改编规划
  ↓
逐场景生成
  ↓
YAML 组装
  ↓
Schema 校验
  ↓
输出结构化剧本初稿
```
