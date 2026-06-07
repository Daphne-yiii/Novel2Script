# AI 小说转剧本工具通用 Prompt 模板 v0.1

```text
# 角色
{role: 你是一位资深的 AI 剧本改编工具开发者，精通小说叙事分析、剧本结构设计、YAML 数据建模、Schema 校验和 Agent Pipeline 工程实现。}

# 核心目标
{goal: 我需要你帮我开发一款离线优先、可选在线 AI 增强的小说转剧本工具，将作者提供的小说文本自动转换为结构化剧本初稿，输出格式为 YAML。}

# 输入文本与改编目标
- 工具名称: {tool_name: Novel2Script}
- 输入内容: {input_text: 小说全文，必须包含至少 3 个章节。章节可通过标题、编号、分隔符或模型语义识别。}
- 输出格式: {output_format: YAML}
- 输出语言: {language: zh-CN}
- 剧本类型: {script_format: screenplay，可扩展为 web_series、stage_play、audio_drama。}
- 核心改编要求: {adaptation_details: 自动识别章节、人物、地点、时间线、场景、事件、冲突和对白；将小说叙事改写为可拍摄、可表演、可编辑、可校验的结构化剧本初稿。}
- 追溯要求: {traceability: 每个剧本场景必须保留 source_chapters，用于追溯原小说章节。}
- 运行模式: {runtime_modes: 支持离线规则模式和在线 AI 模式。离线模式在浏览器或本地 Python 中直接运行；在线 AI 模式由前端请求后端 /api/convert，后端读取环境变量并调用 OpenAI-compatible 国产模型接口。}

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
  - 为主要人物生成语言画像，包括年龄、身份、地域、说话节奏、常用句式、表达禁忌和潜台词倾向。
  - 生成全局故事理解结果，供后续改编使用。
- Long Context Manager:
  - 面向长篇小说建立分层记忆，不将百万字文本一次性塞入单次模型调用。
  - 生成章节级、卷级、篇章级、全书级摘要。
  - 在生成单场景前检索相关章节、人物线、伏笔、设定事实和时间线。
  - 区分“当前场景上下文”和“全局不可违背设定”。
- Story Bible Builder:
  - 建立故事圣经，记录世界观规则、人物弧光、人物关系、能力边界、关键道具、主线/支线和时间线。
  - 将故事圣经作为后续分集、分幕、分场生成的硬约束。
- Foreshadowing Tracker:
  - 建立伏笔账本，记录伏笔的 setup、推进、payoff 和当前状态。
  - 检查伏笔是否遗漏、提前揭示、错误改写或没有回收。
- Canon Consistency Checker:
  - 建立设定事实表，记录人物能力、关系、身份、时间、地点、死亡/失踪状态等事实。
  - 检查人物能力突变、时间线矛盾、关系矛盾和世界观规则冲突。
- Rhythm Planner:
  - 在逐场景生成前规划全局起承转合、分幕/分集节奏、高低潮分布和关键转折。
  - 为每个场景标注 plot_function、intensity 和对应的全局节奏位置。
- Coverage Checker:
  - 检查章节主要事件、关键人物、关键地点、伏笔、人物线是否被剧本覆盖。
  - 输出 missing_events、unresolved_foreshadowing、contradictions 和人工确认项。
- Adaptation Planner:
  - 将小说章节规划为剧本场次。
  - 决定每章对应几个场景。
  - 区分可视化动作、对白、旁白、心理描写改写策略。
  - 生成剧本大纲。
- Scene Writer:
  - 根据大纲生成具体场景。
  - 每个场景包含地点、时间、人物、动作、对白、转场等元素。
  - 将小说中的叙述语言转为可拍摄、可表演的剧本语言。
- Visual Adaptation Rewriter:
  - 检测不可表演的心理描写、抽象情绪和作者旁白。
  - 将“内心、心想、意识到、感到、闪过念头”等内容外化为眼神、微表情、肢体动作、道具动作、沉默、环境声音、镜头调度或可听见的对白。
  - 禁止把“他内心想着……”这类小说句直接写进 action beat。
  - 对大段环境烘托进行视听化拆解，转为可拍摄的空间细节、声音、光线、人物调度或必要旁白。
- Dialogue Polisher:
  - 根据角色语言画像重写对白。
  - 删除说明文、论文式、汇报式台词。
  - 增加潜台词、停顿、打断、回避、反问和角色口癖。
  - 避免角色直接说出观众已经知道的信息。
- YAML Composer:
  - 将分析结果和剧本内容组装为 YAML。
  - 保证字段顺序稳定、结构清晰、便于人工编辑。
- Schema Validator:
  - 校验 YAML 是否符合 Schema。
  - 检查必填字段、数据类型、场景编号、人物引用、章节数量等。
  - 若校验失败，返回错误并触发修复流程。
- Online Model Client:
  - 读取 LLM_PROVIDER、LLM_API_KEY、LLM_BASE_URL、LLM_MODEL 环境变量。
  - 调用 OpenAI-compatible /chat/completions 接口。
  - 要求模型返回 JSON 根对象 {"script": {...}}。
  - 对模型常见字段漂移进行自动修复，例如 scn_001、字符串 order、content/dialogue_text、缺失 heading、缺失 source_chapters。
  - 将 JSON 转为 YAML 前必须经过 Schema Validator 校验。
- Web Server:
  - 提供静态前端页面 index.html、web/js、web/css。
  - 提供 POST /api/convert 接口。
  - 支持 mode=offline 调用本地规则 pipeline。
  - 支持 mode=online 调用 Online Model Client。
}

# 核心改编策略（严格遵守）
{adaptation_strategy:
- 小说转剧本不是简单摘要，而是叙事媒介转换。
- 心理描写应优先转换为动作、表情、沉默、对白或场景调度。
- 禁止直接保留不可表演的心理描写。例如“他表面平静，内心却闪过无数个复仇的念头”不得直接进入剧本 action，应改写为“他盯着旧照片，手指慢慢攥紧，指节泛白”。
- 心理描写外化优先级:
  - 眼神变化。
  - 微表情。
  - 肢体动作。
  - 沉默或停顿。
  - 道具动作。
  - 环境声音。
  - 镜头调度。
  - 可被他人听见的对白或必要旁白。
- 大段背景说明应拆分为可视化信息，必要时使用旁白。
- 小说中的连续事件应按地点、时间、人物变化拆成多个场景。
- 对白需要保留人物声音，但应更口语化、可表演。
- 对白必须符合角色身份、年龄、关系、地域、情绪和说话习惯。
- 禁止说明文式对白，例如“我认为这封信说明三年前的案件并没有结束”。应改写为有潜台词的对白，例如“三年前那件事，不该还有人记得。”
- 台词应优先使用潜台词、停顿、反问、打断、回避和短句，避免把背景信息直接讲给观众听。
- 每个场景应有明确戏剧功能，例如铺垫、冲突、转折、揭示、高潮。
- 保留原章节映射，方便作者追溯来源文本。
- 长篇小说改编必须先建立全局故事控制系统，再进行局部场景生成。
- 禁止只按章节顺序做单章到单场景的局部转换；必须先生成故事圣经、伏笔账本、设定事实表和节奏规划。
- 关键人物能力、关系、死亡、背叛、身份揭示、关键道具和世界观规则必须绑定 source_refs；没有来源证据时不得生成成既定事实。
- 每个伏笔必须记录 setup 与 payoff 状态；未回收伏笔必须进入 coverage_report 或 notes。
- 每个场景必须标注 plot_function 和 intensity，用于控制整部剧的节奏起伏。
}

# 产物技术与合规约束（严格遵守）
{tech_constraints:
- 交付形态: 产物包含命令行工具、离线 Web 前端、本地 Web Server 和可被其他系统调用的模块化程序。
- 离线优先: 离线规则模式必须在无网络、无 API Key 的情况下可用。
- 在线可选: 在线 AI 模式必须通过后端调用模型，禁止浏览器前端直接保存或暴露 API Key。
- 国产模型兼容: 在线 AI 模式优先支持 OpenAI-compatible 国产模型接口，例如阿里云百炼 Qwen、Kimi、DeepSeek、智谱 GLM 等。
- 环境变量:
  - LLM_PROVIDER: 模型供应商标识，例如 qwen。
  - LLM_API_KEY: 模型 API Key，只能由后端读取。
  - LLM_BASE_URL: OpenAI-compatible API 地址，例如 https://dashscope.aliyuncs.com/compatible-mode/v1。
  - LLM_MODEL: 模型名称，例如 qwen-plus 或供应商当前可用模型。
  - SSL_CERT_FILE: 可选证书文件路径。macOS Python 如出现证书校验失败，可设置为 $(python3 -m certifi)；如未设置，后端应优先自动尝试 certifi.where()。
  - LLM_TIMEOUT_SECONDS: 在线模型请求超时时间，默认 240 秒。
  - LLM_MAX_SOURCE_CHARS: 在线模型单次请求允许发送的最大原文字数，默认 12000。
- 本地配置文件:
  - 后端应支持从项目根目录 `.env` 读取 LLM_PROVIDER、LLM_API_KEY、LLM_BASE_URL、LLM_MODEL、SSL_CERT_FILE、LLM_TIMEOUT_SECONDS、LLM_MAX_SOURCE_CHARS。
  - `.env` 仅供本地后端读取，必须加入 `.gitignore`，不得提交真实密钥。
- API Key 安全: API Key 不得写入 index.html、web/js、README 示例真实值、Git 仓库或任何可被浏览器查看的代码。
- 输入限制: 输入小说文本必须至少包含 3 个章节；不足 3 个章节时直接返回明确错误。
- 输出限制: 输出必须是合法 YAML，并满足约定的 YAML Schema。
- Schema 稳定性: 顶层必须包含 script；script 内必须包含 schema_version、title、format、language、source、logline、synopsis、characters、locations、chapters、scenes、notes。
- 字段顺序: YAML 输出字段顺序应稳定，方便人工编辑、版本管理和二次处理。
- 人物引用: 场景和对白中的 character_id 必须引用 characters 中已定义的人物 id；无法确认的人物应补全或标记为 unknown。
- 地点引用: 场景 heading.location_id 必须引用 locations 中已定义的地点 id。
- 章节引用: scenes.source_chapters 必须引用 chapters 中已定义的章节 id。
- 长文本控制: 长篇输入必须维护 story_bible、foreshadowing_ledger、canon_facts、rhythm_plan 和 coverage_report。
- 证据引用: 关键事实和关键剧情 beat 应包含 source_refs，指向来源章节和证据文本。
- 错误处理:
  - 章节不足时返回错误文案：输入章节少于 3 个，无法生成剧本。
  - 章节边界不清晰时，使用语义切分并生成临时章节标题。
  - YAML 校验失败时，尝试自动修复；无法修复时返回校验错误列表。
  - action beat 中出现“内心、心想、感到、意识到、觉得、暗暗决定、闪过念头”等不可视听化表达时，触发 Visual Adaptation Rewriter。
  - dialogue beat 中出现“我认为、我觉得、根据目前情况、这说明、因此、我们必须”等说明文式表达时，触发 Dialogue Polisher。
  - 在线模式缺少 LLM_API_KEY 时，返回明确配置错误。
  - 若未读取到 LLM_API_KEY，错误文案必须明确提示“在启动后端的同一终端 export，或在项目根目录创建 .env”。
  - 在线模型 HTTP 请求失败时，返回模型请求错误，不在前端暴露密钥。
  - 在线模型读取超时时，返回“在线模型响应超时”错误，并提示减少输入文本或调大 LLM_TIMEOUT_SECONDS。
  - 在线模型返回非 JSON 或缺少 script 根字段时，返回格式错误。
  - 在线模型返回字段漂移时，先进行服务端自动修复，再执行 Schema 校验。
  - 供应商返回 Arrearage / overdue-payment 等错误时，提示账号欠费或账户状态不可用。
  - 关键章节事件未覆盖时，写入 coverage_report.missing_events，并触发补场或人工确认。
  - 伏笔 setup 后长期未 payoff 时，写入 coverage_report.unresolved_foreshadowing。
  - 生成内容与 canon_facts 冲突时，触发 Canon Consistency Checker，并要求改写或人工确认。
  - 场景缺少地点、时间或动作时，触发补全或重写。
  - 剧本内容过短、无法覆盖原章节主要情节时，触发低质量场景重写。
- 合规要求: {negative_prompt: 内容不得包含任何违法违规、IP 侵权、不利于未成年人的内容；不得主动生成受版权保护作品的长篇仿写或侵权改编内容。}
}

# Web 前端与后端接口
{web_and_api:
- 前端入口: index.html。
- 前端资源: 使用相对路径引用 ./web/css/styles.css、./web/js/converter.js、./web/js/main.js。
- 离线模式:
  - 直接调用浏览器端 Novel2ScriptCore.convertNovelToScript。
  - 可通过 file:// 打开 index.html 使用。
- 在线 AI 模式:
  - 必须通过本地或线上后端访问页面，例如 http://127.0.0.1:8000。
  - 前端请求 POST /api/convert。
  - 请求体:
    {
      "mode": "online",
      "title": "剧本标题",
      "format": "screenplay",
      "source": "小说全文"
    }
  - 成功响应:
    {
      "ok": true,
      "yaml": "script:\\n  schema_version: \\"1.0\\"\\n...",
      "script": {}
    }
  - 失败响应:
    {
      "ok": false,
      "error": "错误信息"
    }
- 本地启动命令:
  - PYTHONPATH=src python3 -m novel2script.server
- `.env` 启动方式:
  - cp .env.example .env
  - 在 `.env` 中填写 LLM_API_KEY 等配置后，执行 PYTHONPATH=src python3 -m novel2script.server
- 推荐启动命令:
  - LLM_PROVIDER="qwen" LLM_API_KEY="..." LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1" LLM_MODEL="qwen-plus" SSL_CERT_FILE="$(python3 -m certifi)" PYTHONPATH=src python3 -m novel2script.server
- 默认访问地址:
  - http://127.0.0.1:8000
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
  story_bible:
    premise: "核心故事设定"
    world_rules:
      - id: "rule_001"
        text: "主角前期不会武功"
        source_chapters:
          - "chapter_001"
    character_arcs:
      - character_id: "char_001"
        start_state: "胆怯、不会武功"
        midpoint_state: "开始学习防身"
        end_state: "具备战斗能力"
    major_conflicts:
      - "复仇与自我救赎"
  foreshadowing_ledger:
    - id: "foreshadow_001"
      setup: "信封上的医院印章"
      source_chapters:
        - "chapter_002"
      expected_payoff: "揭示旧案与医院有关"
      payoff_status: "pending"
      payoff_scene_id: null
  canon_facts:
    - id: "fact_001"
      subject: "林舟"
      predicate: "不会"
      object: "武功"
      valid_from: "chapter_001"
      valid_until: "chapter_020"
      source_text: "林舟从未学过武。"
  rhythm_plan:
    acts:
      - id: "act_001"
        function: "建立世界、人物和核心悬念"
        chapters:
          - "chapter_001"
          - "chapter_010"
        intensity: "low_to_mid"
      - id: "act_002"
        function: "调查推进，冲突升级"
        intensity: "mid_to_high"
      - id: "act_003"
        function: "真相揭示与情感高潮"
        intensity: "high"
  characters:
    - id: "char_001"
      name: "人物名称"
      role: "protagonist"
      description: "人物简介"
      traits:
        - "性格标签"
      speech_style:
        pace: "慢"
        vocabulary: "克制、少用长句"
        habit: "常用反问，不直接表达真实情绪"
        subtext: "经常回避关键事实"
        taboo: "不轻易说出真相"
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
      plot_function: "setup"
      intensity: 5
      characters:
        - "char_001"
      beats:
        - type: "action"
          text: "动作描写"
          adaptation_note: "由心理描写外化为可见动作"
          source_refs:
            - chapter_id: "chapter_001"
              evidence: "来源小说中的证据句"
        - type: "dialogue"
          character_id: "char_001"
          text: "对白内容"
      transition: "cut_to"
      visualization_checks:
        no_internal_monologue: true
        has_performable_action: true
        has_subtext_dialogue: true
        canon_consistent: true
        foreshadowing_tracked: true
  coverage_report:
    covered_chapters:
      - "chapter_001"
    missing_events: []
    unresolved_foreshadowing:
      - "foreshadow_001"
    contradictions: []
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
- 如果生成程序，必须包含清晰入口，例如 CLI 命令、Web 入口和 Server 入口。
- CLI 入口: python3 -m novel2script。
- Web 离线入口: index.html。
- Web Server 入口: python3 -m novel2script.server。
- 如果生成 YAML，根字段必须是 script。
- 输出 YAML 必须可被标准 YAML 解析器解析。
- 输出 YAML 必须满足上方 Schema。
- characters、locations、chapters、scenes 的 id 必须唯一。
- scene.order 必须连续或至少不重复。
- 每个 scene 必须至少包含一个 action beat。
- action beat 不得直接包含不可表演的心理描写；如包含，应自动重写。
- dialogue beat 不得是说明文式台词；如过于直白，应自动润色为符合角色画像的潜台词表达。
- 长篇改编必须先输出 story_bible、foreshadowing_ledger、canon_facts、rhythm_plan 和 coverage_report。
- 关键剧情 beat 应包含 source_refs；无法绑定来源证据时，不能作为既定事实输出。
- 每个 scene 应包含 plot_function 和 intensity，用于节奏分析。
- coverage_report.missing_events 和 coverage_report.contradictions 如非空，必须返回给用户或触发修复流程。
- dialogue、parenthetical、voice_over 类型 beat 如包含 character_id，则必须引用已定义人物。
- 最终请提供完整代码文件内容、运行方式和最小示例输入。
}
```

## Agent 工作流

```text
小说文本输入
  ↓
选择生成模式
  ↓
离线规则模式 / 在线 AI 模式
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

## 视听化与台词质量工作流

```text
场景初稿
  ↓
检测不可表演心理描写
  ↓
Visual Adaptation Rewriter 外化为动作 / 表情 / 道具 / 声音 / 沉默
  ↓
检测说明文式对白
  ↓
Dialogue Polisher 按角色语言画像重写对白
  ↓
补充 visualization_checks
  ↓
Schema Validator 与质量校验
  ↓
输出可表演、可拍摄的场景 beats
```

## 视听化转化规则

常见问题：

- 小说依赖心理描写、环境烘托和旁白叙事。
- 剧本必须是可听、可见、可表演的视听语言。
- AI 容易把小说心理句原封不动放入剧本，导致演员无法表演。

错误示例：

```yaml
- type: "action"
  text: "他表面平静，内心却闪过无数个复仇的念头。"
```

正确示例：

```yaml
- type: "action"
  text: "他盯着桌上的旧照片，手指慢慢攥紧，指节泛白。"
  adaptation_note: "由复仇心理外化为道具动作和肢体细节。"
- type: "sound"
  text: "墙上的钟声一下一下敲响。"
- type: "action"
  text: "他把照片翻过去，轻轻笑了一下。"
```

系统应检测并重写以下心理词：

- 内心
- 心想
- 感到
- 意识到
- 觉得
- 回忆起
- 暗暗决定
- 闪过念头
- 复仇的念头

## 台词人味与潜台词规则

常见问题：

- AI 台词容易像论文、说明文或剧情梗概。
- 角色会直接解释背景信息，而不是通过冲突、回避和潜台词表达。
- 不同年龄、身份、地域、关系的人说话方式缺乏差异。

错误示例：

```yaml
- type: "dialogue"
  character_id: "char_001"
  text: "我认为这封信说明三年前的案件并没有结束，我需要继续调查。"
```

正确示例：

```yaml
- type: "dialogue"
  character_id: "char_001"
  text: "三年前那件事，不该还有人记得。"
```

角色语言画像示例：

```yaml
characters:
  - id: "char_001"
    name: "林舟"
    role: "protagonist"
    description: "悬疑小说作者，敏感而克制。"
    traits:
      - "克制"
      - "执着"
    speech_style:
      pace: "慢"
      vocabulary: "少用长句，避免直接表达情绪"
      habit: "常用反问和停顿"
      subtext: "用冷静语气掩盖怀疑和愤怒"
      taboo: "不主动说出自己已经知道的真相"
```

对白润色规则：

- 每句对白必须符合角色身份、年龄、关系和当前情绪。
- 禁止角色直接说出自己已经知道的背景信息。
- 优先使用潜台词、停顿、打断、反问、回避。
- 默认每句对白不超过 25 个汉字，除非角色设定需要。
- 如果对白出现“我认为、我觉得、根据目前情况、这说明、因此、我们必须”，应触发重写。

重写 Prompt：

```text
下面这段剧本存在不可视听化或台词说明文问题。
请只重写 beats，不改变人物、地点、场景目的。
要求：
1. 心理描写转为可见动作、表情、道具、声音或沉默。
2. 台词减少解释，增加潜台词。
3. 每句对白不超过 25 个汉字，除非角色设定需要。
4. 保留剧情信息，但不要直接说明。
```

## 长文本全局控制工作流

长篇小说不应直接从“全文”跳到“剧本场景”。正确流程是先建立可追踪、可校验、可回收的故事控制系统。

```text
小说全文
  ↓
章节切分
  ↓
章节级摘要
  ↓
卷 / 篇章级摘要
  ↓
主线 / 支线 / 人物线提取
  ↓
Story Bible 故事圣经
  ↓
Foreshadowing Ledger 伏笔账本
  ↓
Canon Facts 设定事实表
  ↓
Rhythm Plan 全局节奏规划
  ↓
分集 / 分幕 / 分场规划
  ↓
单场景生成
  ↓
Coverage Checker 覆盖率检查
  ↓
Canon Consistency Checker 一致性检查
  ↓
输出可追溯、少幻觉的剧本 YAML
```

## Story Bible 故事圣经

故事圣经用于保存长篇小说的全局设定，避免模型只记住当前章节。

```yaml
story_bible:
  premise: "核心故事设定"
  world_rules:
    - id: "rule_001"
      text: "主角前期不会武功"
      source_chapters:
        - "chapter_003"
  character_arcs:
    - character_id: "char_001"
      start_state: "胆怯、不会武功"
      midpoint_state: "开始学习防身"
      end_state: "具备战斗能力"
  major_conflicts:
    - "复仇与自我救赎"
  timeline:
    - order: 1
      event: "主角收到第一封信"
      source_chapter: "chapter_001"
```

使用规则：

- 每次生成场景前，必须检索相关 story_bible 条目。
- 人物能力、人物关系、身份揭示、死亡/失踪状态不得违背 story_bible。
- 如剧情需要改变设定，必须补充过渡事件或标记为人工确认。

## Foreshadowing Ledger 伏笔账本

伏笔账本用于避免长文改编时遗忘 setup 或 payoff。

```yaml
foreshadowing_ledger:
  - id: "foreshadow_001"
    setup: "信封上的医院印章"
    source_chapters:
      - "chapter_002"
    expected_payoff: "揭示旧案与医院有关"
    payoff_status: "pending"
    payoff_scene_id: null
```

检查规则：

- setup 阶段不得过早解释伏笔。
- payoff 阶段必须能追溯到已有 setup。
- 删除或改写伏笔时，必须更新 payoff_status。
- pending 伏笔必须进入 coverage_report.unresolved_foreshadowing。

## Canon Facts 设定事实表

设定事实表用于处理幻觉和前后矛盾。

```yaml
canon_facts:
  - id: "fact_001"
    subject: "林舟"
    predicate: "不会"
    object: "武功"
    valid_from: "chapter_001"
    valid_until: "chapter_020"
    source_text: "林舟从未学过武。"
```

冲突示例：

```yaml
- type: "action"
  text: "林舟飞身踢倒三名打手。"
```

如果当前时间点早于 `valid_until: chapter_020`，则应判定为冲突：

```text
冲突：林舟在 chapter_020 前不会武功，但当前场景出现高强度战斗能力。
```

修复方式：

- 改写为逃跑、躲避、使用道具或被别人救下。
- 补充前置训练场景。
- 标记为需要人工确认。

## Rhythm Planner 节奏规划器

节奏规划器用于避免长剧情平铺直叙或高潮失控。

```yaml
rhythm_plan:
  acts:
    - id: "act_001"
      function: "建立世界、人物和核心悬念"
      chapters:
        - "chapter_001"
        - "chapter_010"
      intensity: "low_to_mid"
    - id: "act_002"
      function: "调查推进，冲突升级"
      intensity: "mid_to_high"
    - id: "act_003"
      function: "真相揭示与情感高潮"
      intensity: "high"
```

每个场景应标注：

```yaml
purpose: "回收医院印章伏笔，并推动林舟怀疑旧案真相。"
plot_function: "payoff"
intensity: 7
```

节奏规则：

- 开端阶段优先建立人物、世界和悬念。
- 中段阶段提高冲突密度，但需要保留呼吸场。
- 高潮阶段集中回收伏笔和人物弧光。
- 连续高强度场景不得过密，除非目标格式是短剧高爽点结构。

## Coverage Checker 覆盖率检查

覆盖率检查用于解决“丢三落四”。

```yaml
coverage_report:
  covered_chapters:
    - "chapter_001"
    - "chapter_002"
  missing_events:
    - source_chapter: "chapter_005"
      event: "林舟第一次发现医院印章"
      severity: "high"
  unresolved_foreshadowing:
    - "foreshadow_001"
  contradictions:
    - fact_id: "fact_001"
      scene_id: "scene_008"
      description: "主角尚未学武却突然击败三名打手。"
```

检查项：

- 每章主要事件是否进入剧本。
- 每个重要人物是否保留。
- 每个关键地点是否保留。
- 每个伏笔是否 setup / payoff。
- 每条人物线是否有起点、变化和结果。
- 是否存在与 canon_facts 冲突的桥段。

## Source Refs 证据引用

为了降低幻觉，关键剧情必须绑定来源证据。

```yaml
beats:
  - type: "action"
    text: "林舟翻过信封，看见角落里的医院印章。"
    source_refs:
      - chapter_id: "chapter_002"
        evidence: "信纸角落里藏着一个几乎被擦掉的医院印章。"
```

规则：

- 人物能力、人物关系、死亡、背叛、身份揭示、关键道具必须有 source_refs。
- 没有来源证据，不允许生成成既定事实。
- 如果为了剧本改编新增桥段，必须在 notes 中标记为 adaptation_addition。

## 长文本改编原则

```text
不要让 AI 直接从“长小说”跳到“剧本场景”。
先建全局记忆，
再做节奏规划，
再分场生成，
最后做覆盖率和一致性校验。
```

长文本改编的核心不是单纯扩大上下文窗口，而是建立可追踪、可校验、可回收的故事控制系统。

## 在线 AI 工作流

```text
浏览器打开 http://127.0.0.1:8000
  ↓
选择“在线 AI”
  ↓
POST /api/convert
  ↓
后端读取环境变量或项目根目录 .env
  ↓
自动解析 SSL_CERT_FILE；如未设置则尝试 certifi
  ↓
调用 OpenAI-compatible 国产模型接口
  ↓
模型返回 {"script": {...}}
  ↓
后端 Schema 校验
  ↓
后端转 YAML
  ↓
前端展示、复制、下载
```

## 在线模式调试记录与处理策略

### 环境变量作用域

在线模式由后端读取环境变量，浏览器前端不会读取 API Key。

常见问题：

- 用户在一个终端里 export 了 LLM_API_KEY，但 server 是在另一个终端启动的。
- 用户先启动 server，之后才 export LLM_API_KEY。
- 用户用 file:// 打开 index.html，导致在线模式无法访问本地后端。
- 用户在 Codex、终端或其他宿主环境里分别启动服务，导致环境变量没有被同一进程继承。

处理方式：

```bash
cd /Users/fenhongxiaozhu/Desktop/Novel2Script

cp .env.example .env
```

优先推荐在 `.env` 中写入配置：

```text
LLM_PROVIDER=qwen
LLM_API_KEY=你的百炼API_KEY
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_TIMEOUT_SECONDS=240
LLM_MAX_SOURCE_CHARS=12000
```

然后启动：

```bash
PYTHONPATH=src python3 -m novel2script.server
```

如需临时用终端环境变量覆盖，也可使用：

```bash
LLM_PROVIDER="qwen" \
LLM_API_KEY="你的百炼API_KEY" \
LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1" \
LLM_MODEL="qwen-plus" \
SSL_CERT_FILE="$(python3 -m certifi)" \
PYTHONPATH=src \
python3 -m novel2script.server
```

然后访问：

```text
http://127.0.0.1:8000
```

### GET /api/convert 与 POST /api/convert

`/api/convert` 是生成接口，正式调用必须使用 POST。浏览器直接打开 `/api/convert` 是 GET，只用于健康检查和提示。

正确请求体：

```json
{
  "mode": "online",
  "title": "剧本标题",
  "format": "screenplay",
  "source": "小说全文"
}
```

### macOS Python 证书错误

如果出现：

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

处理方式：

```bash
python3 -m pip install --upgrade certifi
export SSL_CERT_FILE="$(python3 -m certifi)"
```

之后重启 server。

当前实现要求：

- 后端优先读取 `.env` 或环境变量中的 `SSL_CERT_FILE`。
- 如未设置 `SSL_CERT_FILE`，后端自动尝试 `certifi.where()`，减少手动配置成本。
- 若 `SSL_CERT_FILE` 指向不存在的文件，必须返回明确错误，而不是只给出模糊的 500。

### 在线请求超时

如果出现：

```text
The read operation timed out
```

说明 HTTPS 连接已建立，但模型响应过慢、请求体过大，或供应商侧延迟过高。

处理方式：

```text
在 .env 中调整：
LLM_TIMEOUT_SECONDS=360
LLM_MAX_SOURCE_CHARS=8000
```

然后重启 server。

当前实现要求：

- 在线模型请求默认超时应为 240 秒，并允许通过 `LLM_TIMEOUT_SECONDS` 覆盖。
- 在线模式单次送入模型的原文长度默认限制为 12000 字，并允许通过 `LLM_MAX_SOURCE_CHARS` 覆盖。
- 若输入超过上限，后端应截断原文，并在 prompt 中显式提示“当前在线请求已截取前段文本用于生成初稿”。
- 超时异常必须转换为用户可理解的错误文案，而不是只显示通用 500 错误。

### 模型返回 Schema 漂移

国产模型可能返回近似字段，而不是严格 Schema 字段，例如：

- `scn_001` 替代 `scene_001`
- `order` 返回字符串
- beat 使用 `content`、`description`、`line`、`dialogue_text` 替代 `text`
- scene 缺少 `source_chapters`
- scene 缺少 `heading`
- `source.type` 返回 book / fiction，而不是 novel

服务端应执行自动修复：

- 统一 id 前缀和序号格式。
- 将 order 转成整数。
- 将 source.type 固定修复为 novel。
- 缺失 source_chapters 时按章节顺序补齐。
- 缺失 heading 时补默认 location_id、time_of_day、interior_exterior。
- 将 content / description / line / dialogue_text 合并为 beat.text。
- 缺失 action beat 时自动补一个 action。
- 修复后必须再次执行 Schema Validator。

### 阿里云百炼欠费或账户不可用

如果模型返回：

```json
{
  "type": "Arrearage",
  "code": "Arrearage"
}
```

说明接口、Key、后端链路均已打通，但模型供应商拒绝服务。处理方式：

- 登录阿里云控制台检查账号状态。
- 确认百炼 / Model Studio 服务已开通。
- 确认账号未欠费，并有可用额度。
- 修复后无需改代码，只需重新请求。
