const assert = require("node:assert");
const core = require("../web/js/converter.js");

const sample = `第一章 雨夜
林舟推开旧书店的门，雨水从伞尖落下。
“有人来过吗？”林舟问。

第二章 追问
林舟回到房间，反复看那封没有署名的信。
“这不是巧合。”林舟低声说。

第三章 旧案
清晨，林舟来到医院门口，终于看见信中提到的名字。
“你终于来了。”女人说。`;

const script = core.convertNovelToScript(sample, { title: "雨夜来信", format: "screenplay" });
const yaml = core.dumpYaml({ script });

assert.equal(script.title, "雨夜来信");
assert.equal(script.source.chapter_count, 3);
assert.equal(script.scenes.length, 3);
assert.deepEqual(core.validateScript(script), []);
assert.ok(yaml.startsWith("script:\n"));
assert.ok(yaml.includes('schema_version: "1.0"'));

console.log("web converter tests passed");
