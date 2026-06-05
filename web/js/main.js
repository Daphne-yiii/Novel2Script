(function () {
  "use strict";

  const sampleNovel = `第一章 雨夜

林舟推开旧书店的门，雨水顺着伞尖滴落。柜台后的老人抬起眼，像是早就知道他会来。

“有人来过吗？”林舟问。

老人没有回答，只把一封没有署名的信推到他面前。信封潮湿，边缘却没有被雨水泡软。

第二章 追问

林舟回到房间，反复看那封信。窗外的街道被雨水照得发白，他忽然想起三年前那个同样潮湿的夜晚。

“这不是巧合。”林舟低声说。

他把信纸摊在桌上，发现角落里藏着一个几乎被擦掉的医院印章。

第三章 旧案

清晨，林舟来到医院门口。来往的人群从他身边经过，没有人注意到他握紧的手。

“你终于来了。”一个女人说。

林舟停住脚步。女人递给他第二封信，旧案的轮廓终于从沉默里浮出水面。`;

  const state = {
    yaml: "",
    script: null
  };

  const elements = {};

  document.addEventListener("DOMContentLoaded", () => {
    try {
      bindElements();
      restoreDraft();
      bindEvents();
      if (!elements.sourceInput.value.trim()) {
        elements.sourceInput.value = sampleNovel;
      }
      setStatus("离线就绪", "ok");
      setMessage("粘贴小说后生成结构化 YAML。");
    } catch (error) {
      showFatalError(error);
    }
  });

  function bindElements() {
    [
      "convertForm",
      "statusPill",
      "sampleButton",
      "clearButton",
      "copyButton",
      "downloadButton",
      "titleInput",
      "formatInput",
      "sourceInput",
      "yamlOutput",
      "summaryText",
      "chapterCount",
      "characterCount",
      "sceneCount",
      "messageBox"
    ].forEach((id) => {
      elements[id] = document.getElementById(id);
    });
  }

  function bindEvents() {
    elements.convertForm.addEventListener("submit", (event) => {
      event.preventDefault();
      generateYaml();
    });
    elements.sampleButton.addEventListener("click", () => {
      elements.sourceInput.value = sampleNovel;
      elements.titleInput.value = "雨夜来信";
      persistDraft();
      setMessage("示例文本已填入。");
    });
    elements.clearButton.addEventListener("click", () => {
      elements.sourceInput.value = "";
      elements.yamlOutput.textContent = "";
      state.yaml = "";
      state.script = null;
      updateMetrics(null);
      toggleResultActions(false);
      setStatus("等待输入", "");
      setMessage("已清空。");
      persistDraft();
    });
    elements.copyButton.addEventListener("click", copyYaml);
    elements.downloadButton.addEventListener("click", downloadYaml);
    elements.titleInput.addEventListener("input", persistDraft);
    elements.formatInput.addEventListener("change", persistDraft);
    elements.sourceInput.addEventListener("input", persistDraft);
  }

  function generateYaml() {
    try {
      setStatus("生成中", "");
      const script = window.Novel2ScriptCore.convertNovelToScript(elements.sourceInput.value, {
        title: elements.titleInput.value,
        format: elements.formatInput.value
      });
      const yaml = window.Novel2ScriptCore.dumpYaml({ script });
      state.script = script;
      state.yaml = yaml;
      elements.yamlOutput.textContent = yaml;
      elements.summaryText.textContent = `${script.title} / ${script.format}`;
      updateMetrics(script);
      toggleResultActions(true);
      setStatus("校验通过", "ok");
      setMessage("YAML 已生成。");
      persistDraft();
    } catch (error) {
      state.script = null;
      state.yaml = "";
      elements.yamlOutput.textContent = "";
      updateMetrics(null);
      toggleResultActions(false);
      setStatus("生成失败", "error");
      setMessage(error && error.message ? error.message : "哎呀，出错了，请重启试试吧~", true);
    }
  }

  async function copyYaml() {
    if (!state.yaml) {
      return;
    }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(state.yaml);
      } else {
        fallbackCopy(state.yaml);
      }
      setMessage("已复制到剪贴板。");
    } catch (error) {
      fallbackCopy(state.yaml);
      setMessage("已复制到剪贴板。");
    }
  }

  function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "readonly");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  function downloadYaml() {
    if (!state.yaml) {
      return;
    }
    try {
      const blob = new Blob([state.yaml], { type: "text/yaml;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const title = sanitizeFileName(state.script ? state.script.title : "script");
      link.href = url;
      link.download = `${title || "script"}.yaml`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setMessage("YAML 文件已下载。");
    } catch (error) {
      setMessage("哎呀，出错了，请重启试试吧~", true);
    }
  }

  function updateMetrics(script) {
    elements.chapterCount.textContent = script ? script.chapters.length : "0";
    elements.characterCount.textContent = script ? script.characters.length : "0";
    elements.sceneCount.textContent = script ? script.scenes.length : "0";
  }

  function toggleResultActions(enabled) {
    elements.copyButton.disabled = !enabled;
    elements.downloadButton.disabled = !enabled;
  }

  function setStatus(text, tone) {
    elements.statusPill.textContent = text;
    elements.statusPill.classList.toggle("is-ok", tone === "ok");
    elements.statusPill.classList.toggle("is-error", tone === "error");
  }

  function setMessage(text, isError) {
    elements.messageBox.textContent = text;
    elements.messageBox.classList.toggle("is-error", Boolean(isError));
  }

  function persistDraft() {
    try {
      localStorage.setItem("novel2script.title", elements.titleInput.value);
      localStorage.setItem("novel2script.format", elements.formatInput.value);
      localStorage.setItem("novel2script.source", elements.sourceInput.value);
    } catch (error) {
      return;
    }
  }

  function restoreDraft() {
    try {
      const title = localStorage.getItem("novel2script.title");
      const format = localStorage.getItem("novel2script.format");
      const source = localStorage.getItem("novel2script.source");
      if (title) {
        elements.titleInput.value = title;
      }
      if (format) {
        elements.formatInput.value = format;
      }
      if (source) {
        elements.sourceInput.value = source;
      }
    } catch (error) {
      return;
    }
  }

  function sanitizeFileName(text) {
    return String(text || "").replace(/[\\/:*?"<>|]/g, "").trim().slice(0, 40);
  }

  function showFatalError(error) {
    document.body.innerHTML = "";
    const message = document.createElement("div");
    message.className = "app-shell";
    message.textContent = "哎呀，出错了，请重启试试吧~";
    document.body.appendChild(message);
    console.error(error);
  }
})();
