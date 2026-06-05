# 剧本 YAML Schema 文档 v0.1

## 1. Schema 设计目标

该 YAML Schema 的目标是让 AI 生成的剧本具备以下能力：

- 结构稳定：方便程序读取、校验和导出。
- 人类可编辑：作者可以直接打开 YAML 修改内容。
- 可追溯：每个场景能追溯到原小说章节。
- 可扩展：未来可支持分集剧、短剧、电影剧本、舞台剧等格式。
- 适合 AI 二次处理：字段明确，便于后续润色、续写、分镜或导出。

## 2. 顶层结构

```yaml
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
  characters: []
  locations: []
  chapters: []
  scenes: []
  notes: []
```

## 3. 字段定义

### script.schema_version

```yaml
schema_version: "1.0"
```

说明：Schema 版本号。

设计原因：后续 Schema 升级时可以兼容旧剧本，例如从电影剧本扩展到短剧分集结构。

### script.title

```yaml
title: "雨夜来信"
```

说明：剧本标题。

设计原因：剧本是独立创作成果，需要拥有自己的标题，可能与原小说标题不同。

### script.format

```yaml
format: "screenplay"
```

可选值：

- screenplay
- web_series
- stage_play
- audio_drama

设计原因：不同剧本类型的场景组织方式不同，提前保留扩展空间。

### script.source

```yaml
source:
  type: "novel"
  chapter_count: 5
```

说明：记录来源文本信息。

设计原因：本工具的关键约束是“3 个章节以上小说文本”，因此必须保留章节数量和来源类型。

### script.characters

```yaml
characters:
  - id: "char_001"
    name: "林舟"
    role: "protagonist"
    description: "年轻小说家，敏感而克制。"
    traits:
      - "谨慎"
      - "执着"
```

字段说明：

- id：人物唯一标识。
- name：人物名称。
- role：人物功能，如主角、反派、配角。
- description：人物简介。
- traits：性格标签。

设计原因：场景对白需要引用人物。使用 id 可以避免同名、别名或改名造成混乱。

### script.locations

```yaml
locations:
  - id: "loc_001"
    name: "旧书店"
    description: "街角一间潮湿昏暗的旧书店。"
```

设计原因：剧本高度依赖空间。地点独立建模后，可用于场景统计、拍摄计划和分镜生成。

### script.chapters

```yaml
chapters:
  - id: "chapter_001"
    title: "第一章 雨夜"
    order: 1
    summary: "林舟在雨夜收到一封没有署名的信。"
```

设计原因：保留小说章节映射，方便作者检查 AI 是否遗漏原文情节。

### script.scenes

```yaml
scenes:
  - id: "scene_001"
    order: 1
    source_chapters:
      - "chapter_001"
    heading:
      location_id: "loc_001"
      time_of_day: "night"
      interior_exterior: "interior"
    purpose: "引出神秘信件，建立悬疑基调。"
    characters:
      - "char_001"
    beats:
      - type: "action"
        text: "林舟推开旧书店的门，雨水顺着伞尖滴落。"
      - type: "dialogue"
        character_id: "char_001"
        text: "有人来过吗？"
      - type: "action"
        text: "柜台后的老人没有回答，只把一封信推到他面前。"
    transition: "cut_to"
```

场景字段说明：

- id：场景唯一标识。
- order：场景顺序。
- source_chapters：来源章节 ID。
- heading：场景头。
- purpose：该场景的戏剧功能。
- characters：出场人物 ID。
- beats：场景内的动作、对白、旁白等内容。
- transition：转场方式。

设计原因：剧本的最小叙事单位是场景，而场景内部由动作和对白推进。beats 比纯文本更适合后续编辑、重排和导出。

## 4. Beat 类型定义

```yaml
beats:
  - type: "action"
    text: "她停在门口，没有立刻进去。"

  - type: "dialogue"
    character_id: "char_002"
    text: "你终于来了。"

  - type: "parenthetical"
    character_id: "char_002"
    text: "压低声音"

  - type: "voice_over"
    character_id: "char_001"
    text: "那天以后，我再也没有见过他。"
```

可选 type：

- action
- dialogue
- parenthetical
- voice_over
- sound
- transition

设计原因：剧本不是普通 prose。将动作、对白、旁白、音效分开，可以支持后续导出为标准剧本格式。

## 5. 最小合法 YAML 示例

```yaml
script:
  schema_version: "1.0"
  title: "示例剧本"
  format: "screenplay"
  language: "zh-CN"
  source:
    type: "novel"
    chapter_count: 3
  logline: "一名年轻作者在三封信中发现失踪多年的真相。"
  synopsis: "主角收到神秘来信，逐步揭开过去事件，并最终面对真相。"
  characters:
    - id: "char_001"
      name: "林舟"
      role: "protagonist"
      description: "年轻作者。"
      traits:
        - "敏感"
  locations:
    - id: "loc_001"
      name: "旧书店"
      description: "潮湿安静的街角书店。"
  chapters:
    - id: "chapter_001"
      title: "第一章"
      order: 1
      summary: "林舟收到第一封信。"
    - id: "chapter_002"
      title: "第二章"
      order: 2
      summary: "林舟开始调查信件来源。"
    - id: "chapter_003"
      title: "第三章"
      order: 3
      summary: "林舟发现信件与旧案有关。"
  scenes:
    - id: "scene_001"
      order: 1
      source_chapters:
        - "chapter_001"
      heading:
        location_id: "loc_001"
        time_of_day: "night"
        interior_exterior: "interior"
      purpose: "建立悬疑开端。"
      characters:
        - "char_001"
      beats:
        - type: "action"
          text: "林舟走进旧书店，收起被雨打湿的伞。"
        - type: "dialogue"
          character_id: "char_001"
          text: "这封信是谁留下的？"
      transition: "cut_to"
  notes: []
```

## 6. Schema 设计原因总结

该 Schema 选择“人物、地点、章节、场景、beat”五类核心结构，是因为小说改编剧本时最重要的问题不是生成文本，而是建立可控的改编结构。

- chapters 解决来源追溯问题。
- characters 解决人物一致性问题。
- locations 解决场景空间管理问题。
- scenes 解决剧本叙事组织问题。
- beats 解决动作、对白、旁白的可编辑问题。
- schema_version 解决长期演进问题。
