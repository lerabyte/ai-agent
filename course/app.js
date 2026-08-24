(() => {
  "use strict";

  const STORAGE_KEY = "agent-lab-course-progress-v1";
  const TOTAL_LESSONS = 6;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const lessonCards = [...document.querySelectorAll(".lesson-card")];
  const progressBar = document.querySelector("#course-progress-bar");
  const progressMeter = document.querySelector("#course-progress");
  const progressPercent = document.querySelector("#progress-percent");
  const headerProgressBar = document.querySelector("#header-progress-bar");
  const headerProgressLabel = document.querySelector("#header-progress-label");
  const continueButton = document.querySelector("#continue-button");

  const defaultState = { completed: [] };

  function configureHostedMarkdownLinks() {
    if (!window.location.hostname.toLowerCase().endsWith(".github.io")) return;

    const owner = window.location.hostname.slice(0, -".github.io".length);
    const pathParts = window.location.pathname.split("/").filter(Boolean);
    const courseIndex = pathParts.indexOf("course");
    const repository = courseIndex > 0 ? pathParts[0] : `${owner}.github.io`;

    document.querySelectorAll("a[data-repo-path]").forEach((link) => {
      const repositoryPath = link.dataset.repoPath
        .split("/")
        .map((part) => encodeURIComponent(part))
        .join("/");

      link.href = `https://github.com/${encodeURIComponent(owner)}/${encodeURIComponent(repository)}/blob/main/${repositoryPath}`;
      link.title = "Open the rendered Markdown file on GitHub";
    });
  }

  function loadProgress() {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (!stored || !Array.isArray(stored.completed)) return { ...defaultState };

      const completed = stored.completed
        .map(Number)
        .filter((lesson) => Number.isInteger(lesson) && lesson >= 1 && lesson <= TOTAL_LESSONS);

      return { completed: [...new Set(completed)] };
    } catch {
      return { ...defaultState };
    }
  }

  let courseState = loadProgress();

  function saveProgress() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(courseState));
    } catch {
      // The course still works when browser storage is unavailable.
    }
  }

  function renderProgress() {
    const count = courseState.completed.length;
    const percent = Math.round((count / TOTAL_LESSONS) * 100);

    progressBar.style.width = `${percent}%`;
    headerProgressBar.style.width = `${percent}%`;
    progressPercent.textContent = `${percent}%`;
    headerProgressLabel.textContent = `${count} / ${TOTAL_LESSONS}`;
    progressMeter.setAttribute("aria-valuenow", String(percent));

    lessonCards.forEach((card) => {
      const lesson = Number(card.dataset.lesson);
      const complete = courseState.completed.includes(lesson);
      const button = card.querySelector(".complete-button");
      const label = card.querySelector(".complete-label");

      card.classList.toggle("is-complete", complete);
      button.setAttribute("aria-pressed", String(complete));
      label.textContent = complete ? "Completed" : "Mark complete";
    });

    continueButton.textContent = count === TOTAL_LESSONS ? "Take the quiz" : "Continue course";
  }

  document.querySelectorAll(".complete-button").forEach((button) => {
    button.addEventListener("click", () => {
      const lesson = Number(button.closest(".lesson-card").dataset.lesson);
      const complete = courseState.completed.includes(lesson);

      courseState.completed = complete
        ? courseState.completed.filter((item) => item !== lesson)
        : [...courseState.completed, lesson].sort((a, b) => a - b);

      saveProgress();
      renderProgress();
    });
  });

  continueButton.addEventListener("click", () => {
    const nextCard = lessonCards.find((card) => !courseState.completed.includes(Number(card.dataset.lesson)));

    if (!nextCard) {
      document.querySelector("#quiz").scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth" });
      return;
    }

    nextCard.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "center" });
    window.setTimeout(() => nextCard.querySelector("a").focus({ preventScroll: true }), reducedMotion ? 0 : 500);
  });

  document.querySelector("#reset-progress").addEventListener("click", () => {
    const shouldReset = window.confirm("Reset all six lesson checkmarks?");
    if (!shouldReset) return;

    courseState = { ...defaultState };
    saveProgress();
    renderProgress();
  });

  document.querySelectorAll(".outcome-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") === "true";
      const outcomePanel = document.getElementById(button.getAttribute("aria-controls"));

      button.setAttribute("aria-expanded", String(!expanded));
      outcomePanel.hidden = expanded;
    });
  });

  const copyStatus = document.querySelector("#copy-status");

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.setAttribute("readonly", "");
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.select();
    const copied = document.execCommand("copy");
    textArea.remove();

    if (!copied) throw new Error("Copy was blocked");
  }

  document.querySelectorAll(".copy-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const originalLabel = button.textContent;
      try {
        await copyText(button.dataset.copy);
        button.textContent = "Copied";
        button.classList.add("is-copied");
        copyStatus.textContent = `Copied: ${button.dataset.copy}`;
      } catch {
        button.textContent = "Select";
        copyStatus.textContent = "Copy was blocked. Select the command manually.";
      }

      window.setTimeout(() => {
        button.textContent = originalLabel;
        button.classList.remove("is-copied");
      }, 1600);
    });
  });

  const simulatorForm = document.querySelector("#simulator-form");
  const simulatorPrompt = document.querySelector("#simulator-prompt");
  const runLoopButton = document.querySelector("#run-loop-button");
  const stageCards = [...document.querySelectorAll(".stage-card")];
  const stageConnectors = [...document.querySelectorAll(".stage-connector")];
  const terminalOutput = document.querySelector("#terminal-output");
  const terminalStatus = document.querySelector("#terminal-status");
  const stagePrompt = document.querySelector("#stage-prompt");
  const stageResult = document.querySelector("#stage-result");
  const stageAnswer = document.querySelector("#stage-answer");
  let simulationId = 0;

  const delay = (milliseconds) =>
    new Promise((resolve) => window.setTimeout(resolve, reducedMotion ? 12 : milliseconds));

  function resetSimulator() {
    stageCards.forEach((card, index) => {
      card.classList.remove("is-active", "is-done");
      card.querySelector(".stage-state").textContent = index === 0 ? "READY" : "WAITING";
    });
    stageConnectors.forEach((connector) => connector.classList.remove("is-active"));
    terminalOutput.replaceChildren();
    stageResult.textContent = "--:--:--";
    stageAnswer.textContent = "Waiting for result";
  }

  function appendTrace(time, source, message, className) {
    const line = document.createElement("div");
    const timestamp = document.createElement("span");
    const sourceLabel = document.createElement("span");
    const messageText = document.createTextNode(` ${message}`);

    timestamp.className = "terminal-time";
    timestamp.textContent = `[${time}] `;
    sourceLabel.className = className;
    sourceLabel.textContent = source;

    line.append(timestamp, sourceLabel, messageText);
    terminalOutput.appendChild(line);
  }

  function activateStage(index) {
    stageCards.forEach((card, cardIndex) => {
      const done = cardIndex < index;
      const active = cardIndex === index;
      card.classList.toggle("is-done", done);
      card.classList.toggle("is-active", active);
      card.querySelector(".stage-state").textContent = done ? "DONE" : active ? "RUNNING" : "WAITING";
    });

    if (index > 0) stageConnectors[index - 1].classList.add("is-active");
  }

  simulatorForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = "What time is it right now?";

    const currentSimulation = ++simulationId;
    resetSimulator();
    stagePrompt.textContent = prompt;
    terminalStatus.textContent = "RUNNING";
    runLoopButton.disabled = true;
    runLoopButton.textContent = "Tracing…";
    simulatorPrompt.disabled = true;

    const nowStamp = () => new Date().toLocaleTimeString([], { hour12: false });

    activateStage(0);
    appendTrace(nowStamp(), "USER     →", prompt, "terminal-model");
    await delay(720);
    if (currentSimulation !== simulationId) return;

    activateStage(1);
    appendTrace(nowStamp(), "MODEL    →", "requests get_current_time()", "terminal-model");
    await delay(800);
    if (currentSimulation !== simulationId) return;

    activateStage(2);
    appendTrace(nowStamp(), "PYTHON   →", "validates request, then runs function", "terminal-python");
    await delay(780);
    if (currentSimulation !== simulationId) return;

    const localTime = new Date().toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
    });
    activateStage(3);
    stageResult.textContent = localTime;
    appendTrace(nowStamp(), "TOOL     →", `returns “${localTime}”`, "terminal-result");
    await delay(780);
    if (currentSimulation !== simulationId) return;

    activateStage(4);
    const finalAnswer = `The current time is ${localTime}.`;
    stageAnswer.textContent = finalAnswer;
    appendTrace(nowStamp(), "MODEL    →", finalAnswer, "terminal-model");
    await delay(520);

    stageCards[4].classList.remove("is-active");
    stageCards[4].classList.add("is-done");
    stageCards[4].querySelector(".stage-state").textContent = "DONE";
    terminalStatus.textContent = "COMPLETE";
    runLoopButton.disabled = false;
    runLoopButton.textContent = "Replay fixed trace";
    simulatorPrompt.disabled = false;
  });

  const quizCards = [...document.querySelectorAll(".quiz-card")];
  const quizScore = document.querySelector("#quiz-score");
  const quizSummary = document.querySelector("#quiz-summary");

  const feedbackByQuestion = {
    1: "localhost routes the client to a service running on this computer.",
    2: "Python executes approved functions; the model only requests them.",
    3: "A normal loop ends when the model returns a final answer with no new tool call.",
    4: "An approved registry maps each requested tool name to one Python function.",
    5: "A structured error becomes information the model can use to choose a better next step.",
    6: "Python must require write approval and keep the resolved path inside the allowed workspace.",
  };

  function updateQuizScore() {
    const answered = quizCards.filter((card) => card.querySelector("input:checked"));
    const correct = quizCards.filter((card) => card.classList.contains("is-correct"));
    quizScore.textContent = `${correct.length} / ${quizCards.length}`;

    if (answered.length === quizCards.length) {
      quizSummary.textContent =
        correct.length === quizCards.length
          ? "Perfect trace. You understand the model → Python → result flow."
          : `${correct.length} correct. Review the highlighted explanations and try again.`;
    } else {
      quizSummary.textContent = `${answered.length} of ${quizCards.length} answered.`;
    }
  }

  quizCards.forEach((card) => {
    card.addEventListener("change", () => {
      const selected = card.querySelector("input:checked");
      const correct = selected.value === card.dataset.answer;
      const question = Number(card.dataset.question);
      const feedback = card.querySelector(".quiz-feedback");

      card.classList.toggle("is-correct", correct);
      card.classList.toggle("is-wrong", !correct);
      feedback.textContent = correct ? `Correct — ${feedbackByQuestion[question]}` : `Not quite — ${feedbackByQuestion[question]}`;
      updateQuizScore();
    });
  });

  document.querySelector("#reset-quiz").addEventListener("click", () => {
    document.querySelector("#quiz-form").reset();
    quizCards.forEach((card) => {
      card.classList.remove("is-correct", "is-wrong");
      card.querySelector(".quiz-feedback").textContent = "";
    });
    quizScore.textContent = `0 / ${quizCards.length}`;
    quizSummary.textContent = "Choose an answer to get instant feedback.";
  });

  configureHostedMarkdownLinks();
  renderProgress();
})();
