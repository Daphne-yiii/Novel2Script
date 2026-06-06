# AI 小说转剧本工具通用 Prompt 模板 v0.1

以下模板可直接复制给 AI Agent，用于生成或实现“小说文本转结构化剧本 YAML”的工具。

## 通用 Prompt 模板（可直接复制）

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
  - SSL_CERT_FILE: macOS Python 如出现证书校验失败，可设置为 $(python3 -m certifi)。
- API Key 安全: API Key 不得写入 index.html、web/js、README 示例真实值、Git 仓库或任何可被浏览器查看的代码。
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
  - action beat 中出现“内心、心想、感到、意识到、觉得、暗暗决定、闪过念头”等不可视听化表达时，触发 Visual Adaptation Rewriter。
  - dialogue beat 中出现“我认为、我觉得、根据目前情况、这说明、因此、我们必须”等说明文式表达时，触发 Dialogue Polisher。
  - 在线模式缺少 LLM_API_KEY 时，返回明确配置错误。
  - 在线模型 HTTP 请求失败时，返回模型请求错误，不在前端暴露密钥。
  - 在线模型返回非 JSON 或缺少 script 根字段时，返回格式错误。
  - 在线模型返回字段漂移时，先进行服务端自动修复，再执行 Schema 校验。
  - 供应商返回 Arrearage / overdue-payment 等错误时，提示账号欠费或账户状态不可用。
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
      characters:
        - "char_001"
      beats:
        - type: "action"
          text: "动作描写"
          adaptation_note: "由心理描写外化为可见动作"
        - type: "dialogue"
          character_id: "char_001"
          text: "对白内容"
      transition: "cut_to"
      visualization_checks:
        no_internal_monologue: true
        has_performable_action: true
        has_subtext_dialogue: true
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

## 在线 AI 工作流

```text
浏览器打开 http://127.0.0.1:8000
  ↓
选择“在线 AI”
  ↓
POST /api/convert
  ↓
后端读取 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
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

处理方式：

```bash
cd /Users/fenhongxiaozhu/Desktop/Novel2Script

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
