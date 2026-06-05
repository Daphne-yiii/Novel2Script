(function (global) {
  "use strict";

  const VALID_FORMATS = new Set(["screenplay", "web_series", "stage_play", "audio_drama"]);
  const VALID_BEAT_TYPES = new Set([
    "action",
    "dialogue",
    "parenthetical",
    "voice_over",
    "sound",
    "transition"
  ]);

  function convertNovelToScript(sourceText, options = {}) {
    const cleanedText = parseInput(sourceText);
    const chapters = segmentChapters(cleanedText);
    if (chapters.length < 3) {
      throw new Error("输入章节少于 3 个，无法生成剧本。");
    }

    const analysis = analyzeStory(cleanedText, chapters);
    const plan = planAdaptation(chapters, analysis);
    const scenes = writeScenes(chapters, analysis, plan);
    const script = composeScript(chapters, analysis, scenes, options);
    const errors = validateScript(script);
    if (errors.length > 0) {
      throw new Error("YAML Schema 校验失败：" + errors.join("；"));
    }
    return script;
  }

  function parseInput(text) {
    const cleaned = cleanText(String(text || ""));
    if (!cleaned) {
      throw new Error("输入文本为空。");
    }
    return cleaned;
  }

  function cleanText(text) {
    return text
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, "")
      .split("\n")
      .map((line) => line.trim())
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function segmentChapters(text) {
    let rawChapters = findTitledChapters(text);
    if (rawChapters.length < 3) {
      rawChapters = splitBySeparators(text);
    }
    if (rawChapters.length < 3) {
      rawChapters = semanticChunk(text, 3);
    }
    return rawChapters.map((chapter, index) => ({
      id: idFor("chapter", index + 1),
      title: chapter.title || `临时章节 ${index + 1}`,
      order: index + 1,
      text: chapter.body,
      summary: summarizeText(chapter.body, 2, 160)
    }));
  }

  function findTitledChapters(text) {
    const pattern = /^(第[一二三四五六七八九十百千万零〇两\d]+[章节回部卷][^\n]*|Chapter\s+\d+[^\n]*|\d+[.、]\s*[^\n]{1,40})$/gim;
    const matches = Array.from(text.matchAll(pattern));
    if (matches.length < 3) {
      return [];
    }

    const chapters = [];
    matches.forEach((match, index) => {
      const start = match.index + match[0].length;
      const end = index + 1 < matches.length ? matches[index + 1].index : text.length;
      const body = text.slice(start, end).trim();
      if (body) {
        chapters.push({ title: match[1].trim(), body });
      }
    });
    return chapters;
  }

  function splitBySeparators(text) {
    const parts = text
      .split(/^\s*(?:-{3,}|\*{3,}|={3,})\s*$/gm)
      .map((part) => part.trim())
      .filter(Boolean);
    if (parts.length < 3) {
      return [];
    }
    return parts.map((body, index) => ({ title: `临时章节 ${index + 1}`, body }));
  }

  function semanticChunk(text, targetCount) {
    const paragraphs = text.split(/\n\s*\n/g).map((part) => part.trim()).filter(Boolean);
    if (paragraphs.length < targetCount) {
      return [];
    }

    const chunkSize = Math.max(1, Math.floor(paragraphs.length / targetCount));
    const chunks = [];
    for (let index = 0; index < targetCount; index += 1) {
      const start = index * chunkSize;
      const end = index < targetCount - 1 ? (index + 1) * chunkSize : paragraphs.length;
      const chunk = paragraphs.slice(start, end);
      if (chunk.length > 0) {
        chunks.push({ title: `临时章节 ${index + 1}`, body: chunk.join("\n\n") });
      }
    }
    return chunks;
  }

  function analyzeStory(text, chapters) {
    const characters = extractCharacters(text);
    const locations = extractLocations(text);
    return {
      characters,
      locations,
      timeline: chapters.map((chapter) => chapter.summary),
      majorEvents: chapters.map((chapter) => chapter.summary).filter(Boolean),
      tone: inferTone(text),
      conflicts: inferConflicts(text, characters)
    };
  }

  function extractCharacters(text) {
    const candidates = new Map();
    const patterns = [
      /(?:^|[。！？!?，,\n])\s*([\u4e00-\u9fa5]{2,6})(?:低声|轻声|沉声)?(?:说|问|喊|叫|回答|道)/g,
      /“[^”]{1,80}”\s*([\u4e00-\u9fa5]{2,6})(?:低声|轻声|沉声)?(?:说|问|喊|叫|回答|道)/g,
      /(?:^|[。！？!?，,\n])\s*([\u4e00-\u9fa5]{2,4})(?:走进|推开|看着|望向|站在|坐在|回到|停住)/g
    ];
    const stopwords = new Set([
      "他们",
      "她们",
      "我们",
      "你们",
      "有人",
      "孩子",
      "声音",
      "雨水",
      "时候",
      "这里",
      "那里",
      "窗外",
      "街道",
      "房间",
      "书店"
    ]);

    patterns.forEach((pattern) => {
      for (const match of text.matchAll(pattern)) {
        const normalized = normalizeCharacterName(match[1]);
        if (normalized && !stopwords.has(normalized)) {
          candidates.set(normalized, (candidates.get(normalized) || 0) + 1);
        }
      }
    });

    let ranked = Array.from(candidates.entries())
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "zh-Hans"))
      .slice(0, 8);
    if (ranked.length === 0) {
      ranked = [["unknown", 1]];
    }

    return ranked.map(([name], index) => {
      const displayName = name === "unknown" ? "未知人物" : name;
      return {
        id: idFor("char", index + 1),
        name: displayName,
        role: index === 0 ? "protagonist" : "supporting",
        description: `${displayName}，由小说文本自动识别或补全的人物。`,
        traits: inferTraits(text, displayName)
      };
    });
  }

  function normalizeCharacterName(name) {
    let normalized = String(name || "").trim();
    normalized = normalized.replace(/(低声|轻声|沉声|忽然|终于)$/g, "");
    normalized = normalized.replace(/^(那个|这个|一名|一个)/g, "");
    const invalidFragments = ["知道", "像是", "早就", "街", "窗", "雨", "信", "房", "门", "医院", "柜台", "外"];
    if (normalized.length < 2 || invalidFragments.some((fragment) => normalized.includes(fragment))) {
      return "";
    }
    if (/(的|了|着|过|没有|不是)$/.test(normalized)) {
      return "";
    }
    return normalized;
  }

  function inferTraits(text, name) {
    const pattern = new RegExp(`.{0,20}${escapeRegExp(name)}.{0,30}`, "g");
    const windows = Array.from(text.matchAll(pattern)).map((match) => match[0]).join(" ");
    const traits = [];
    [
      ["沉默", "克制"],
      ["犹豫", "谨慎"],
      ["追问", "执着"],
      ["冷笑", "冷静"],
      ["害怕", "敏感"],
      ["怒", "冲动"]
    ].forEach(([keyword, trait]) => {
      if (windows.includes(keyword) && !traits.includes(trait)) {
        traits.push(trait);
      }
    });
    return traits.length > 0 ? traits : ["待细化"];
  }

  function extractLocations(text) {
    const keywords = ["书店", "房间", "街道", "巷子", "办公室", "学校", "医院", "车站", "屋里", "门口", "客厅", "厨房"];
    const found = keywords.filter((keyword) => text.includes(keyword));
    const names = found.length > 0 ? found : ["主要场景"];
    return names.slice(0, 8).map((name, index) => ({
      id: idFor("loc", index + 1),
      name,
      description: `${name}，由小说文本自动识别或补全的场景空间。`
    }));
  }

  function inferTone(text) {
    if (["雨", "信", "失踪", "旧案", "秘密", "沉默"].some((keyword) => text.includes(keyword))) {
      return "悬疑克制";
    }
    if (["笑", "阳光", "热闹", "欢呼"].some((keyword) => text.includes(keyword))) {
      return "明亮轻快";
    }
    return "写实叙事";
  }

  function inferConflicts(text, characters) {
    const conflicts = [];
    if (["信", "秘密", "真相", "旧案"].some((keyword) => text.includes(keyword))) {
      conflicts.push("人物追寻真相与未知阻力之间的冲突。");
    }
    if (["沉默", "没有回答", "犹豫"].some((keyword) => text.includes(keyword))) {
      conflicts.push("人物之间因隐瞒和试探产生的关系冲突。");
    }
    if (conflicts.length === 0) {
      const protagonist = characters[0] ? characters[0].name : "主角";
      conflicts.push(`${protagonist}的目标与现实阻碍之间的冲突。`);
    }
    return conflicts;
  }

  function planAdaptation(chapters, analysis) {
    return {
      scenes: chapters.map((chapter, index) => {
        const order = index + 1;
        return {
          id: idFor("scene", order),
          order,
          sourceChapters: [chapter.id],
          locationId: chooseLocationForChapter(chapter.text, analysis.locations).id,
          timeOfDay: inferTimeOfDay(chapter.text),
          interiorExterior: inferInteriorExterior(chapter.text),
          purpose: inferScenePurpose(order, chapters.length),
          characterIds: analysis.characters.slice(0, 3).map((character) => character.id),
          rewriteStrategy: inferRewriteStrategy(chapter.text)
        };
      })
    };
  }

  function chooseLocationForChapter(text, locations) {
    return locations.find((location) => text.includes(location.name)) || locations[0];
  }

  function inferTimeOfDay(text) {
    if (["夜", "晚上", "深夜", "凌晨"].some((keyword) => text.includes(keyword))) {
      return "night";
    }
    if (["清晨", "早晨", "上午"].some((keyword) => text.includes(keyword))) {
      return "morning";
    }
    if (["傍晚", "黄昏"].some((keyword) => text.includes(keyword))) {
      return "evening";
    }
    return "day";
  }

  function inferInteriorExterior(text) {
    if (["房间", "屋里", "书店", "办公室", "客厅", "厨房"].some((keyword) => text.includes(keyword))) {
      return "interior";
    }
    if (["街", "路", "巷", "雨中", "门外"].some((keyword) => text.includes(keyword))) {
      return "exterior";
    }
    return "interior";
  }

  function inferScenePurpose(order, total) {
    if (order === 1) {
      return "建立故事开端，交代人物处境与核心悬念。";
    }
    if (order === total) {
      return "推动阶段性揭示，为后续冲突或结局留下明确方向。";
    }
    return "推进调查与人物关系，制造新的冲突或转折。";
  }

  function inferRewriteStrategy(text) {
    const strategy = ["保留章节主事件", "转写为可拍摄动作"];
    if (["想起", "心里", "觉得", "意识到"].some((keyword) => text.includes(keyword))) {
      strategy.push("将心理描写转为动作、表情或停顿");
    }
    if (text.includes("“") && text.includes("”")) {
      strategy.push("保留并口语化关键对白");
    }
    if (text.length > 220) {
      strategy.push("压缩背景说明，必要时转为旁白");
    }
    return strategy;
  }

  function writeScenes(chapters, analysis, plan) {
    const chaptersById = Object.fromEntries(chapters.map((chapter) => [chapter.id, chapter]));
    return plan.scenes.map((scenePlan) => {
      const chapter = chaptersById[scenePlan.sourceChapters[0]];
      return writeScene(scenePlan, chapter, analysis.characters);
    });
  }

  function writeScene(scenePlan, chapter, characters) {
    const dialogues = extractDialogues(chapter.text);
    const beats = [
      {
        type: "action",
        text: rewriteAsAction(chapter.summary, scenePlan.rewriteStrategy)
      }
    ];

    dialogues.slice(0, 3).forEach((dialogue, index) => {
      const speaker = guessSpeaker(chapter.text, dialogue, characters);
      beats.push({
        type: "dialogue",
        character_id: speaker.id,
        text: dialogue
      });
      if (index === 0) {
        beats.push({
          type: "action",
          text: "短暂的沉默改变了场景里的气氛，人物关系开始变得紧张。"
        });
      }
    });

    if (beats.length === 1) {
      beats.push({
        type: "action",
        text: "人物用动作和停顿承接原文叙事，场景保持可拍摄的外部行为。"
      });
    }

    return {
      id: scenePlan.id,
      order: scenePlan.order,
      source_chapters: scenePlan.sourceChapters,
      heading: {
        location_id: scenePlan.locationId,
        time_of_day: scenePlan.timeOfDay,
        interior_exterior: scenePlan.interiorExterior
      },
      purpose: scenePlan.purpose,
      characters: scenePlan.characterIds,
      beats,
      transition: "cut_to"
    };
  }

  function extractDialogues(text) {
    return Array.from(text.matchAll(/“([^”]{1,120})”/g))
      .map((match) => match[1].replace(/\s+/g, " ").trim())
      .filter(Boolean);
  }

  function rewriteAsAction(summary, rewriteStrategy) {
    if (!summary) {
      return "场景展开，人物进入关键情境。";
    }
    if (rewriteStrategy.includes("将心理描写转为动作、表情或停顿")) {
      return `画面呈现：人物通过停顿和细微动作带出情绪。${summary}`;
    }
    return `画面呈现：${summary}`;
  }

  function guessSpeaker(text, dialogue, characters) {
    const dialogueIndex = text.indexOf(`“${dialogue}”`);
    const context = text.slice(Math.max(0, dialogueIndex - 20), dialogueIndex + dialogue.length + 30);
    return characters.find((character) => context.includes(character.name)) || characters[0];
  }

  function composeScript(chapters, analysis, scenes, options) {
    const title = String(options.title || "").trim() || inferTitle(chapters);
    const format = VALID_FORMATS.has(options.format) ? options.format : "screenplay";
    return {
      schema_version: "1.0",
      title,
      format,
      language: "zh-CN",
      source: {
        type: "novel",
        chapter_count: chapters.length
      },
      logline: buildLogline(analysis),
      synopsis: chapters.map((chapter) => chapter.summary).filter(Boolean).join(" "),
      characters: analysis.characters,
      locations: analysis.locations,
      chapters: chapters.map((chapter) => ({
        id: chapter.id,
        title: chapter.title,
        order: chapter.order,
        summary: chapter.summary
      })),
      scenes,
      notes: [
        "当前版本使用浏览器本地规则引擎生成剧本初稿，适合作为 AI 或人工二次打磨的结构化底稿。",
        `故事基调：${analysis.tone}。`
      ]
    };
  }

  function inferTitle(chapters) {
    const firstTitle = chapters[0].title;
    if (firstTitle.startsWith("第") || firstTitle.startsWith("临时章节")) {
      const firstSentence = summarizeText(chapters[0].text, 1, 80);
      return (firstSentence.slice(0, 12) || "未命名剧本").replace(/[，。！？；：]+$/g, "");
    }
    return firstTitle.slice(0, 30);
  }

  function buildLogline(analysis) {
    const protagonist = analysis.characters[0] ? analysis.characters[0].name : "主角";
    const conflict = analysis.conflicts[0] || "逐渐升级的冲突";
    return `${protagonist}在连续事件中追寻真相，并面对${conflict}`;
  }

  function validateScript(script) {
    const errors = [];
    [
      "schema_version",
      "title",
      "format",
      "language",
      "source",
      "logline",
      "synopsis",
      "characters",
      "locations",
      "chapters",
      "scenes",
      "notes"
    ].forEach((field) => {
      if (!(field in script)) {
        errors.push(`缺少顶层字段 script.${field}`);
      }
    });

    if (!VALID_FORMATS.has(script.format)) {
      errors.push("script.format 不是合法取值");
    }
    if (!script.source || script.source.type !== "novel") {
      errors.push("script.source.type 必须为 novel");
    }
    if (!Array.isArray(script.chapters) || script.chapters.length < 3) {
      errors.push("script.chapters 至少需要 3 个章节");
    }

    const characterIds = collectIds(script.characters, "characters", errors);
    const locationIds = collectIds(script.locations, "locations", errors);
    const chapterIds = collectIds(script.chapters, "chapters", errors);
    const sceneIds = collectIds(script.scenes, "scenes", errors);
    void sceneIds;

    if (!Array.isArray(script.scenes) || script.scenes.length === 0) {
      errors.push("script.scenes 至少需要 1 个场景");
      return errors;
    }

    const sceneOrders = new Set();
    script.scenes.forEach((scene) => {
      if (typeof scene.order !== "number") {
        errors.push(`${scene.id}.order 必须是整数`);
      } else if (sceneOrders.has(scene.order)) {
        errors.push(`${scene.id}.order 重复`);
      } else {
        sceneOrders.add(scene.order);
      }

      validateSceneRefs(scene, chapterIds, characterIds, locationIds, errors);
      validateBeats(scene, characterIds, errors);
    });
    return errors;
  }

  function collectIds(items, label, errors) {
    const ids = new Set();
    if (!Array.isArray(items)) {
      errors.push(`script.${label} 必须是数组`);
      return ids;
    }

    items.forEach((item) => {
      if (!item || typeof item !== "object") {
        errors.push(`script.${label} 内元素必须是对象`);
        return;
      }
      if (!item.id) {
        errors.push(`script.${label} 内元素缺少 id`);
        return;
      }
      if (ids.has(item.id)) {
        errors.push(`script.${label} 存在重复 id: ${item.id}`);
      }
      ids.add(item.id);
    });
    return ids;
  }

  function validateSceneRefs(scene, chapterIds, characterIds, locationIds, errors) {
    if (!Array.isArray(scene.source_chapters) || scene.source_chapters.length === 0) {
      errors.push(`${scene.id}.source_chapters 不能为空`);
    } else {
      scene.source_chapters.forEach((chapterId) => {
        if (!chapterIds.has(chapterId)) {
          errors.push(`${scene.id} 引用了未定义章节 ${chapterId}`);
        }
      });
    }

    if (!scene.heading || typeof scene.heading !== "object") {
      errors.push(`${scene.id}.heading 必须是对象`);
      return;
    }
    if (!locationIds.has(scene.heading.location_id)) {
      errors.push(`${scene.id}.heading.location_id 引用了未定义地点`);
    }
    if (!scene.heading.time_of_day) {
      errors.push(`${scene.id}.heading.time_of_day 不能为空`);
    }
    if (!["interior", "exterior"].includes(scene.heading.interior_exterior)) {
      errors.push(`${scene.id}.heading.interior_exterior 不是合法取值`);
    }

    (scene.characters || []).forEach((characterId) => {
      if (!characterIds.has(characterId)) {
        errors.push(`${scene.id} 引用了未定义人物 ${characterId}`);
      }
    });
  }

  function validateBeats(scene, characterIds, errors) {
    if (!Array.isArray(scene.beats) || scene.beats.length === 0) {
      errors.push(`${scene.id}.beats 不能为空`);
      return;
    }
    let hasAction = false;
    scene.beats.forEach((beat, index) => {
      if (!VALID_BEAT_TYPES.has(beat.type)) {
        errors.push(`${scene.id}.beats[${index + 1}].type 不是合法取值`);
      }
      if (beat.type === "action") {
        hasAction = true;
      }
      if (!beat.text) {
        errors.push(`${scene.id}.beats[${index + 1}].text 不能为空`);
      }
      if (["dialogue", "parenthetical", "voice_over"].includes(beat.type) && !characterIds.has(beat.character_id)) {
        errors.push(`${scene.id}.beats[${index + 1}] 引用了未定义人物 ${beat.character_id}`);
      }
    });
    if (!hasAction) {
      errors.push(`${scene.id}.beats 至少需要一个 action`);
    }
  }

  function dumpYaml(data) {
    return dumpValue(data, 0).trimEnd() + "\n";
  }

  function dumpValue(value, indent) {
    if (Array.isArray(value)) {
      return dumpList(value, indent);
    }
    if (value && typeof value === "object") {
      return dumpObject(value, indent);
    }
    return `${" ".repeat(indent)}${formatScalar(value)}\n`;
  }

  function dumpObject(data, indent) {
    const prefix = " ".repeat(indent);
    return Object.entries(data).map(([key, value]) => {
      if (Array.isArray(value)) {
        return value.length > 0 ? `${prefix}${key}:\n${dumpList(value, indent + 2).trimEnd()}` : `${prefix}${key}: []`;
      }
      if (value && typeof value === "object") {
        return `${prefix}${key}:\n${dumpObject(value, indent + 2).trimEnd()}`;
      }
      return `${prefix}${key}: ${formatScalar(value)}`;
    }).join("\n") + "\n";
  }

  function dumpList(items, indent) {
    const prefix = " ".repeat(indent);
    return items.map((item) => {
      if (Array.isArray(item)) {
        return `${prefix}-\n${dumpList(item, indent + 2).trimEnd()}`;
      }
      if (item && typeof item === "object") {
        const entries = Object.entries(item);
        if (entries.length === 0) {
          return `${prefix}- {}`;
        }
        const [firstKey, firstValue] = entries[0];
        const rest = Object.fromEntries(entries.slice(1));
        const firstLine = formatInlineObjectEntry(firstKey, firstValue, indent + 2);
        const restText = entries.length > 1 ? "\n" + dumpObject(rest, indent + 2).trimEnd() : "";
        return `${prefix}- ${firstLine}${restText}`;
      }
      return `${prefix}- ${formatScalar(item)}`;
    }).join("\n") + "\n";
  }

  function formatInlineObjectEntry(key, value, indent) {
    if (Array.isArray(value)) {
      return value.length > 0 ? `${key}:\n${dumpList(value, indent).trimEnd()}` : `${key}: []`;
    }
    if (value && typeof value === "object") {
      return `${key}:\n${dumpObject(value, indent).trimEnd()}`;
    }
    return `${key}: ${formatScalar(value)}`;
  }

  function formatScalar(value) {
    if (value === null || value === undefined) {
      return "null";
    }
    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
    if (typeof value === "number") {
      return String(value);
    }
    return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, "\\\"").replace(/\n/g, "\\n").replace(/\t/g, "\\t")}"`;
  }

  function summarizeText(text, maxSentences, maxChars) {
    const normalized = String(text || "").replace(/\s+/g, "");
    const sentences = normalized.match(/[^。！？!?]+[。！？!?]?/g) || [];
    const summary = sentences.slice(0, maxSentences).join("");
    return (summary || normalized).slice(0, maxChars);
  }

  function idFor(prefix, order) {
    return `${prefix}_${String(order).padStart(3, "0")}`;
  }

  function escapeRegExp(text) {
    return String(text).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  const api = {
    convertNovelToScript,
    dumpYaml,
    validateScript,
    _internal: {
      cleanText,
      segmentChapters,
      analyzeStory,
      planAdaptation,
      writeScenes
    }
  };

  global.Novel2ScriptCore = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
