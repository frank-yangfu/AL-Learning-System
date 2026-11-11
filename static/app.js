/* AL 自学系统 —— 前端逻辑（原生 JS，零依赖） */
(function () {
  "use strict";

  const EMOTION_COLOR = {
    curiosity: "#3b82f6", confusion: "#f59e0b", frustration: "#ef4444",
    excitement: "#ec4899", satisfaction: "#22c55e", boredom: "#6b7280",
    anxiety: "#a855f7", neutral: "#14b8a6",
  };
  const MASTERY_LABEL = { 0: "未测", 1: "未掌握", 2: "了解", 3: "熟悉", 4: "掌握" };
  // 三关递进的掌握度测评：每关标题 / 名称 / 过关标准
  const MASTERY_GATES = [
    { n: 1, key: "说出来", name: "理解", crit: "能用大白话说清核心意思，并举一个贴切的生活例子。" },
    { n: 2, key: "做出来", name: "应用", crit: "能独立做对一道基础题，步骤正确、方法用对、答案正确。" },
    { n: 3, key: "讲明白", name: "迁移", crit: "能迁移到新情境，或把知识点讲得让完全不懂的人也听懂。" },
  ];

  const state = {
    token: localStorage.getItem("al_token") || "",
    username: localStorage.getItem("al_user") || "",
    roles: [],
    currentRole: null,
    sessionId: null,
    messages: [],
    busy: false,
    selectedCourse: null,
    _lesson: null,         // 当前打开的课程详细讲义
    _lessonTopic: null,    // 讲义对应的可选项知识点（用于“选择这门课”）
    curriculum: null,
    curMeta: null,
    _courseStage: null,
    // 课后测试（自测模式）：出题→学生独立作答→按正确率+用时评估→未掌握则再学
    testMode: false,
    testQids: [],
    testAnswers: {},          // { qid: answer_index }
    testTimes: {},            // { qid: 秒 }
    testStart: 0,
    _testTimerId: null,
    curLang: "zh-CN",        // 当前语音识别 / 朗读语言
    voiceMode: false,        // 语音对话模式：导师回复自动朗读
    recognizing: false,      // 是否正在语音识别
    // 🗣️ 语音朗读调节（平板上可调音色，告别机械嗓音）
    ttsVoice: localStorage.getItem("al_tts_voice") || "",       // 指定嗓音名；空=自动优选本机最自然嗓音
    ttsRate: parseFloat(localStorage.getItem("al_tts_rate")) || 0.95,
    ttsPitch: parseFloat(localStorage.getItem("al_tts_pitch")) || 1.02,
    ttsVolume: parseFloat(localStorage.getItem("al_tts_volume")) || 1.0,
    ttsStyle: localStorage.getItem("al_tts_style") || "natural",
    ttsEngine: localStorage.getItem("al_tts_engine") || "cloud",  // 朗读引擎：cloud/browser/auto；默认云端最稳
    // 电脑语音服务器地址（华为等手机出厂没有 TTS 引擎、也装不了语音包，只能靠电脑出声）
    // 形如 "192.168.1.5:8000"（不写端口默认补 8000），留空表示不使用
    ttsServer: localStorage.getItem("al_tts_server") || "",
    lastBotText: "",         // 导师上一条回复（供朗读）
    _finalTranscript: "",
    // 精准学
    precUnits: [],
    precSubject: "",
    precGrade: "",
    precGraph: null,
    precDiag: null,           // {diag_id, questions:[{qid,stem,options,topic_id,topic_title}]}
    precDiagAnswers: {},
    precPractice: null,       // 当前练习 {questions:[{qid,stem,options,idx}], total}
    _practiceAnswers: {},     // 练题作答 { qid: answer_index }
    _practiceCourse: "",      // 当前练习的知识点 id（断点续学要用）
    _practiceTier: "",        // 当前练习层级：基础/提升/拓展
    precProgress: null,       // 学习进度总览 {dist, mastery_pct, coverage_pct, by_subject...}
    _precLastPanel: "",       // 上次打开的精准学面板：diag / practice / mistakes
    _diagMeta: null,          // 本次诊断元信息 {scope, weak_before, weak_total, covered}
    _lastDiagResult: null,    // 上一次诊断/再测结果（用于前后对比展示）
    _mistakeCache: {},        // 错题本当前列表 { id: mistake }
    _redoPick: {},            // 错题重做已选答案 { mistake_id: option_index }
    _redoOpen: null,          // 当前展开重做的错题 id
    _lastView: "home",        // 上次所在视图（断点续学）
    _pendingResume: null,     // 待恢复的断点快照
    resume: null,             // 服务端/本地断点快照
    _resumeTimer: null,
    // 🗣️ 口语练习
    speechSentences: [],
    speechIdx: 0,
    speechResults: [],
    speechBusy: false,
    // 🏠 学习机模式
    childName: localStorage.getItem("al_child_name") || "",
    childAvatar: localStorage.getItem("al_child_avatar") || "🐱",
    parentPin: localStorage.getItem("al_parent_pin") || "",
    dailyMaxMin: parseInt(localStorage.getItem("al_daily_max") || "30", 10),
    todaySec: 0,              // 今日已学习秒数
    _timerHandle: null,       // 学习计时器句柄
    _lockSeconds: 0,          // 锁屏倒计时秒数
    _lockTimerHandle: null,
    _lastTick: 0,             // 上次计时时间戳
    _fromLauncher: false,     // 是否从桌面进入
  };
  let recognition = null;    // Web Speech 语音识别实例
  let _explainCtx = { problem: "", full: "", prev: "" };  // 当前讲解上下文（供追问/换讲法/朗读）

  // ---------- 断网/弱网提示 ----------
  const OFFLINE_BAR_ID = "offline-bar";
  function _initOfflineBar() {
    const bar = document.createElement("div");
    bar.id = OFFLINE_BAR_ID;
    bar.textContent = "⚠️ 当前网络不可用，请检查网络连接后刷新页面";
    bar.style.cssText = "position:fixed;top:0;left:0;right:0;background:#f59e0b;color:#fff;text-align:center;" +
      "padding:6px 12px;font-size:13px;z-index:99999;display:none;";
    document.body.appendChild(bar);
    window.addEventListener("online", () => bar.style.display = "none");
    window.addEventListener("offline", () => bar.style.display = "block");
    if (!navigator.onLine) bar.style.display = "block";
  }
  _initOfflineBar();

  async function exportMyData() {
    const btn = document.getElementById('export-data-btn');
    if (btn) btn.disabled = true;
    try {
      const data = await api('GET', '/api/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'al-learning-export-' + new Date().toISOString().slice(0,10) + '.json';
      a.click();
      toast('已导出 ' + (data.mastery?.length || 0) + ' 条掌握记录');
    } catch (e) {
      toast('导出失败：' + (e.message || e));
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // ---------- 工具 ----------
  function el(id) { return document.getElementById(id); }
  function toast(msg) {
    const t = el("toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove("show"), 2200);
  }
  async function api(method, path, body) {
    const opt = { method, headers: { "Content-Type": "application/json" } };
    if (state.token) opt.headers["Authorization"] = "Bearer " + state.token;
    if (body) opt.body = JSON.stringify(body);
    let res;
    try {
      res = await fetch(path, opt);
    } catch (e) {
      // 网络层失败：服务器不可达，或页面来源不对（file:// 双击打开 / 预览面板跨域）
      throw new Error("无法连接服务器（" + (e && e.message ? e.message : "网络错误") +
        "）。请确认：① 后端已在 " + location.origin + " 运行；② 用浏览器在地址栏直接打开 " + location.origin +
        "（不要双击打开 index.html 文件，也不要在文件预览面板里操作）；③ 若从平板/其他设备访问，确认电脑防火墙已放行端口。");
    }
    let data = {};
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) throw new Error(data.error || ("请求失败 " + res.status));
    return data;
  }

  // ---------- 🔊 音效引擎（Web Audio 合成，零外部文件，离线可用） ----------
  const _SFX = {
    _ctx: null,
    _get() {
      try {
        if (!this._ctx) {
          const AC = window.AudioContext || window.webkitAudioContext;
          if (!AC) return null;
          this._ctx = new AC();
        }
        if (this._ctx.state === "suspended") this._ctx.resume();
        return this._ctx;
      } catch (e) { return null; }
    },
    _tone(ctx, freq, t0, dur, type, vol) {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = type || "sine"; o.frequency.value = freq;
      g.gain.setValueAtTime(0, t0);
      g.gain.linearRampToValueAtTime(vol || 0.12, t0 + 0.015);
      g.gain.exponentialRampToValueAtTime(0.001, t0 + dur);
      o.connect(g); g.connect(ctx.destination);
      o.start(t0); o.stop(t0 + dur + 0.05);
    },
    play(kind) {
      const ctx = this._get(); if (!ctx) return;
      const t = ctx.currentTime;
      try {
        if (kind === "correct") { this._tone(ctx, 880, t, 0.12, "sine", 0.10); }
        else if (kind === "wrong") { this._tone(ctx, 220, t, 0.18, "triangle", 0.08); }
        else if (kind === "combo") { [660, 880, 1100].forEach((f, i) => this._tone(ctx, f, t + i * 0.07, 0.12, "sine", 0.10)); }
        else if (kind === "claim") { [523, 659, 784, 1047].forEach((f, i) => this._tone(ctx, f, t + i * 0.08, 0.16, "sine", 0.11)); }
        else if (kind === "buy") { [784, 988, 1319].forEach((f, i) => this._tone(ctx, f, t + i * 0.09, 0.18, "sine", 0.11)); }
        else if (kind === "milestone") { [392, 523, 659, 784, 1047].forEach((f, i) => this._tone(ctx, f, t + i * 0.1, 0.28, "triangle", 0.12)); }
        else if (kind === "tap") { this._tone(ctx, 1200, t, 0.05, "sine", 0.05); }
      } catch (e) {}
    }
  };
  window._AL_SFX = _SFX;

  // ---------- 认证 ----------
  const UI = {
    switchTab(tab) {
      el("tab-login").classList.toggle("active", tab === "login");
      el("tab-register").classList.toggle("active", tab === "register");
      el("auth-pass").setAttribute("autocomplete", tab === "login" ? "current-password" : "new-password");
    },
    async auth() {
      const username = el("auth-user").value.trim();
      const password = el("auth-pass").value;
      if (!username || !password) return toast("请输入用户名和密码");
      const isReg = el("tab-register").classList.contains("active");
      try {
        const r = isReg
          ? await api("POST", "/api/register", { username, password })
          : await api("POST", "/api/login", { username, password });
        state.token = r.token; state.username = r.username;
      localStorage.setItem("al_token", r.token); localStorage.setItem("al_user", r.username);
      const b = document.getElementById('export-data-btn'); if (b) b.style.display = 'block';
        localStorage.setItem("al_token", r.token);
        localStorage.setItem("al_user", r.username);
        await this.enter();
      } catch (e) { toast(e.message); }
    },
    logout() {
      state.token = ""; localStorage.removeItem("al_token"); localStorage.removeItem("al_user");
      showLauncher();
    },
    // ---------- 🏠 学习机：设置向导 ----------
    pinNext(inp, nextId) {
      if (inp.value.length >= 1 && nextId) {
        const next = el(nextId);
        if (next && next.tagName === "INPUT") next.focus();
        else if (next && next.tagName === "BUTTON") next.focus();
      }
    },
    setupStep1() {
      const name = el("setup-name").value.trim();
      if (!name) return toast("先告诉老师你叫什么名字吧！");
      state.childName = name;
      state.childAvatar = document.querySelector(".av-opt.selected")?.dataset?.av || "🐱";
      el("setup-step-1").hidden = true;
      el("setup-step-2").hidden = false;
      el("sp-1").focus();
    },
    setupStep2() {
      const p1 = el("sp-1").value;
      const p2 = el("sp-2").value;
      const p3 = el("sp-3").value;
      const p4 = el("sp-4").value;
      const pin = p1 + p2 + p3 + p4;
      if (pin.length < 4) {
        el("setup-pin-error").hidden = false;
        return;
      }
      el("setup-pin-error").hidden = true;
      state.parentPin = pin;
      // 持久化孩子档案
      localStorage.setItem("al_child_name", state.childName);
      localStorage.setItem("al_child_avatar", state.childAvatar);
      localStorage.setItem("al_parent_pin", state.parentPin);
      localStorage.setItem("al_daily_max", "30");
      // 加入多孩子列表
      let children = [];
      try { children = JSON.parse(localStorage.getItem("al_children") || "[]"); } catch(e) {}
      if (!children.find(c => c.name === state.childName)) {
        children.push({ name: state.childName, avatar: state.childAvatar });
        localStorage.setItem("al_children", JSON.stringify(children));
      }
      el("setup-wizard").hidden = true;
      toast("🎉 设置完成！开始学习吧！");
      showLauncher();
      syncProfile();
      // 触发后台登录
      bootLogin();
    },
    // 头像选择
    initAvatarPicker() {
      document.querySelectorAll(".av-opt").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".av-opt").forEach(b => b.classList.remove("selected"));
          btn.classList.add("selected");
          state.childAvatar = btn.dataset.av;
        });
      });
    },

    // ---------- 🏠 学习桌面入口 ----------
    continueLearn() {
      // 进入学习页
      this.enterApp("learn");
    },
    goCourseSquare() {
      // 跳转到「自学」页（年级/科目/章节 三级浏览 + 直接出学习内容）
      this.enterApp("selfstudy");
    },
    goTodayPractice() {
      this.enterApp("precision");
    },
    goAchievement() {
      this.openAchievement();
    },
    async openAchievement() {
      el("achievement-modal").hidden = false;
      const body = el("achieve-body");
      body.innerHTML = `<div class="achieve-stars"><div class="as-count">...</div><div class="as-label">加载中</div></div>`;
      try {
        const [stars, ach] = await Promise.all([
          api("GET", "/api/stars"),
          api("GET", "/api/achievements"),
        ]);
        const badges = ach.badges || [];
        const unlocked = badges.filter(b => b.unlocked).length;
        body.innerHTML = `
          <div class="achieve-stars">
            <div class="as-count">⭐ ${stars.total || 0}</div>
            <div class="as-label">今日 +${stars.today || 0} · 共获得</div>
          </div>
          <div class="achieve-grid">
            ${badges.map(b => `
              <div class="achieve-card ${b.unlocked ? 'unlocked' : 'locked'}">
                <div class="ac-icon">${esc(b.icon)}</div>
                <div class="ac-title">${esc(b.title)}</div>
                <div class="ac-desc">${esc(b.desc)}</div>
                <div class="ac-status ${b.unlocked ? 'done' : 'wait'}">${b.unlocked ? '✅ 已解锁' : '🔒 未解锁'}</div>
              </div>
            `).join("")}
          </div>
          <p style="text-align:center;font-size:12px;color:var(--muted);margin-top:12px">已解锁 ${unlocked}/${badges.length}</p>
        `;
      } catch (e) {
        body.innerHTML = `<p class="r-empty">加载失败：${esc(e.message)}</p>`;
      }
    },
    closeAchievement() {
      el("achievement-modal").hidden = true;
    },
    async awardStars(source, points) {
      try {
        const r = await api("POST", "/api/stars/award", { source, points });
        if (r.awarded) {
          // 更新桌面星星数
          const starEl = el("stat-stars");
          if (starEl) {
            const cur = parseInt(starEl.textContent) || 0;
            starEl.textContent = cur + points;
          }
          // 检查成就是否解锁
          this.checkAchievements();
        }
      } catch (e) { /* 静默 */ }
    },
    async checkAchievements() {
      try {
        const [stars, ach] = await Promise.all([
          api("GET", "/api/stars"),
          api("GET", "/api/achievements"),
        ]);
        const badges = ach.badges || [];
        const toUnlock = [];
        // 检查条件
        const totalStars = stars.total || 0;
        const unlockedIds = new Set(badges.filter(b => b.unlocked).map(b => b.id));

        // stars_50: 累计50星
        if (totalStars >= 50 && !unlockedIds.has("stars_50")) toUnlock.push("stars_50");

        // 测评相关掌握度
        if (!unlockedIds.has("first_mastery") || !unlockedIds.has("master_5")) {
          const m = await api("GET", "/api/report/daily");
          const mastered = m.mastery ? m.mastery.mastered : 0;
          if (mastered > 0 && !unlockedIds.has("first_mastery")) toUnlock.push("first_mastery");
          if (mastered >= 5 && !unlockedIds.has("master_5")) toUnlock.push("master_5");
        }

        // 自学进度相关成就（基于本地进度 al_ss_progress）
        if (!unlockedIds.has("first_selfstudy") && state._ssVisited) toUnlock.push("first_selfstudy");
        const ssMap = this._ssLoadProgress();
        const ssIds = Object.keys(ssMap);
        const ssLearned = ssIds.filter(id => (ssMap[id].status || 0) >= 1).length;
        const ssMastered = ssIds.filter(id => (ssMap[id].status || 0) >= 2).length;
        if (ssLearned >= 1 && !unlockedIds.has("first_selfstudy")) toUnlock.push("first_selfstudy");
        if (ssLearned >= 10 && !unlockedIds.has("selfstudy_10")) toUnlock.push("selfstudy_10");
        if (ssLearned >= 50 && !unlockedIds.has("selfstudy_50")) toUnlock.push("selfstudy_50");
        if (ssMastered >= 10 && !unlockedIds.has("selfstudy_master_10")) toUnlock.push("selfstudy_master_10");
        // 满分小能手：记录一次满分即解锁
        if (!unlockedIds.has("quiz_perfect") && state._ssQuizPerfect) toUnlock.push("quiz_perfect");

        for (const bid of toUnlock) {
          const r = await api("POST", "/api/achievements/unlock", { badge_id: bid });
          if (r.unlocked) {
            const badge = badges.find(b => b.id === bid);
            this.showUnlockToast(badge?.icon || "🏆", badge?.title || "成就解锁", badge?.desc || "");
          }
        }
      } catch (e) { /* 静默 */ }
    },
    showUnlockToast(icon, title, desc) {
      const t = el("unlock-toast");
      el("unlock-icon").textContent = icon;
      el("unlock-title").textContent = "🏆 " + title;
      el("unlock-desc").textContent = desc;
      t.style.display = "block";
      setTimeout(() => { t.style.display = "none"; }, 3500);
    },

    // ---------- ⭐ 激励引擎（每日任务 / 连胜，纯星星无交易） ----------
    renderGamify() {
      if (!window.AL_GAMIFY) return;
      const g = window.AL_GAMIFY, s = g.state();
      // 连胜条
      const bar = el("streak-bar");
      if (bar) {
        if (s.streak.cur > 0) {
          bar.style.display = "flex";
          const wk = g.week();
          bar.innerHTML =
            `<div class="streak-flame">🔥</div>` +
            `<div class="streak-info"><b>${s.streak.cur} 天连胜</b>` +
            `<span>${s.streak.best > s.streak.cur ? "最佳 " + s.streak.best + " 天" : "再接再厉！"}</span></div>` +
            `<div class="streak-week">${wk.map(d =>
              `<span class="sw-dot ${d.active ? "on" : ""}" title="${d.date}"></span>`).join("")}</div>`;
        } else {
          bar.style.display = "none";
        }
      }
      // 每日任务卡
      const box = el("daily-tasks");
      if (box) {
        const doneN = s.tasks.items.filter(i => i.claimed).length;
        box.style.display = "flex";
        box.innerHTML =
          `<div class="dt-head"><div class="dt-icon">🎯</div>` +
          `<div class="dt-label">每日任务 <span class="dt-sub">${doneN}/${s.tasks.items.length} 已完成</span></div>` +
          `<span class="dt-wallet">⭐ ${s.tasks.items.reduce((a, i) => a + (i.claimed ? i.stars : 0), 0)} 今日已得</span></div>` +
          `<div class="dt-list">` + s.tasks.items.map((it, i) => {
            const pct = Math.min(100, Math.round(it.progress / it.goal * 100));
            const ready = !it.claimed && it.progress >= it.goal;
            return `<div class="dt-item ${it.claimed ? "claimed" : ready ? "ready" : ""}">
              <span class="dt-ico">${it.icon}</span>
              <div class="dt-mid"><div class="dt-title">${esc(it.title)}</div>
                <div class="dt-bar"><span style="width:${pct}%"></span></div></div>
              <div class="dt-right">${it.claimed
                ? `<span class="dt-done">✓ 已领</span>`
                : ready
                  ? `<button class="btn small dt-claim" onclick="UI.claimTask(${i})">领 ${it.stars}⭐</button>`
                  : `<span class="dt-gem">+${it.stars}⭐</span>`}</div>
            </div>`;
          }).join("") + `</div>`;
      }
      // 连胜里程碑庆祝（一次一个）
      const ms = window.AL_GAMIFY.takeMilestone();
      if (ms) this.showMilestone(ms.day, ms.stars);
    },
    claimTask(idx) {
      if (!window.AL_GAMIFY) return;
      const r = window.AL_GAMIFY.claim(idx);
      if (r) {
        this._ssXpToast("⭐ 任务完成", `「${r.title}」 +${r.stars} 星星`);
        _SFX.play("claim");
        this.renderGamify();
      }
    },
    showMilestone(day, stars) {
      const t = el("milestone-toast");
      if (!t) return;
      el("ms-title").textContent = `🔥 连胜 ${day} 天！`;
      el("ms-desc").textContent = `奖励 +${stars} ⭐ 星星，继续保持！`;
      t.style.display = "flex";
      _SFX.play("milestone");
      setTimeout(() => { t.style.display = "none"; }, 4000);
    },

    // ---------- 🌈 课外读物（离线内置，含阅读理解） ----------
    _storiesCache: null,
    async _loadStories() {
      if (this._storiesCache) return this._storiesCache;
      const load = f => api("GET", "offline/stories/" + f).catch(() => ({ stories: [] }));
      const [m, c] = await Promise.all([load("stories_math.json"), load("stories_chinese.json")]);
      this._storiesCache = (m.stories || []).concat(c.stories || []);
      return this._storiesCache;
    },
    async openStories() {
      el("stories-modal").hidden = false;
      const body = el("stories-body");
      body.innerHTML = `<p class="r-empty">加载中…</p>`;
      const list = await this._loadStories();
      if (!list.length) { body.innerHTML = `<p class="r-empty">暂无读物</p>`; return; }
      const groups = [["math", "🔢 数学故事"], ["chinese", "✍️ 语文故事"]];
      body.innerHTML = groups.map(([sub, label]) => {
        const items = list.filter(s => s.subject === sub);
        if (!items.length) return "";
        return `<div class="st-group-label">${label}</div>` + items.map(s => {
          const done = this._storyState(s.id).quizDone;
          return `<div class="st-row" onclick="UI.openStory('${s.id}')">
            <span class="st-emoji">${s.emoji}</span>
            <div class="st-mid"><div class="st-title">${esc(s.title)}</div>
              <div class="st-meta">${s.level === "1-3" ? "🌱 1-3 年级" : "🌿 4-6 年级"} · 约 ${s.minutes} 分钟</div></div>
            ${done ? `<span class="st-done">✓</span>` : `<span class="st-go">→</span>`}
          </div>`;
        }).join("");
      }).join("");
    },
    closeStories() { el("stories-modal").hidden = true; },
    _storyState(id) {
      try {
        const m = JSON.parse(localStorage.getItem("al_stories_v1") || "{}");
        return m[id] || {};
      } catch (e) { return {}; }
    },
    _markStory(id, patch) {
      let m = {};
      try { m = JSON.parse(localStorage.getItem("al_stories_v1") || "{}"); } catch (e) {}
      m[id] = Object.assign({}, m[id] || {}, patch, { ts: Date.now() });
      localStorage.setItem("al_stories_v1", JSON.stringify(m));
      // 阅读进度同样要跟账号走（record_key 前缀 story:，与知识点进度共用一张表）
      if (state.token) {
        const rec = {};
        rec["story:" + id] = { status: (m[id] && m[id].done) ? 2 : 1, ts: m[id].ts };
        api("POST", "/api/study/records", { records: rec }).catch(() => {});
      }
    },
    openStory(id) {
      const s = (this._storiesCache || []).find(x => x.id === id);
      if (!s) return;
      state._story = { s, answered: {}, correct: {} };
      el("story-read-title").textContent = `${s.emoji} ${s.title}`;
      el("story-read-modal").hidden = false;
      this._ssRenderStory();
    },
    closeStory() { el("story-read-modal").hidden = true; },
    _ssRenderStory() {
      const st = state._story; if (!st) return;
      const body = el("story-read-body");
      const allAnswered = st.s.quiz.every((q, qi) => st.answered[qi] !== undefined);
      body.innerHTML =
        `<div class="story-cover">${st.s.cover ? `<img src="${esc(st.s.cover)}" alt="">` : st.s.emoji}</div>` +
        st.s.paras.map(p => `<p class="story-para">${esc(p)}</p>`).join("") +
        `<div class="st-quiz-head">📝 读一读，答一答（全对奖 3 ⭐）</div>` +
        st.s.quiz.map((q, qi) => {
          const picked = st.answered[qi];
          const isRight = picked !== undefined && picked === q.answer;
          return `<div class="stq-item ${picked === undefined ? "" : isRight ? "right" : "wrong"}">
            <div class="stq-q">${qi + 1}. ${esc(q.q)}</div>
            <div class="stq-opts">` + q.options.map((o, oi) => {
              if (picked === undefined) return `<button class="stq-opt" onclick="UI.answerStory(${qi}, ${oi})">${esc(o)}</button>`;
              let cls = "stq-opt";
              if (oi === q.answer) cls += " right";
              else if (oi === picked) cls += " wrong";
              return `<button class="${cls}" disabled>${esc(o)}</button>`;
            }).join("") + `</div>` +
            (picked !== undefined ? `<div class="stq-why">${isRight ? "✅" : "❌"} ${esc(q.why)}</div>` : ``) +
          `</div>`;
        }).join("") +
        (allAnswered
          ? `<div class="st-finish">${this._storyState(st.s.id).quizDone ? "📖 读完啦，可以再读一遍" : "🎉 全部答完！奖励已发放"}</div>`
          : ``);
    },
    answerStory(qi, oi) {
      const st = state._story; if (!st || st.answered[qi] !== undefined) return;
      st.answered[qi] = oi;
      this._ssOnAnswer(oi === st.s.quiz[qi].answer);
      const allRight = st.s.quiz.every((q, i) => st.answered[i] === q.answer);
      const allAnswered = st.s.quiz.every((q, i) => st.answered[i] !== undefined);
      if (allAnswered) {
        this._markStory(st.s.id, { quizDone: true, allRight });
        if (allRight && !st.rewarded) {
          st.rewarded = true;
          this.awardStars("story_quiz", 3);
          try { if (window.AL_GAMIFY) window.AL_GAMIFY.track("learned", 1); } catch (e) {}
          this._ssXpToast("🌈 读物完成", "+3 ⭐ 星星");
        }
        this.checkAchievements();
      }
      this._ssRenderStory();
    },

    // ---------- 📸 拍照搜题 ----------
    openOCR() {
      el("ocr-modal").hidden = false;
      el("ocr-result").style.display = "none";
      el("ocr-status").style.display = "none";
      el("ocr-preview").style.display = "none";
      el("ocr-camera-btn").style.display = "";
      const v = el("ocr-video");
      if (v) { try { v.srcObject && v.srcObject.getTracks().forEach(t => t.stop()); } catch(e) {} v.style.display = "none"; }
    },
    closeOCR() {
      el("ocr-modal").hidden = true;
      const v = el("ocr-video");
      if (v) { try { v.srcObject && v.srcObject.getTracks().forEach(t => t.stop()); } catch(e) {} }
    },
    async startCamera() {
      const v = el("ocr-video");
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        v.srcObject = stream;
        v.style.display = "block";
        v.play();
        el("ocr-camera-btn").style.display = "none";
        // 3秒后自动拍照
        setTimeout(() => this.captureFromVideo(v, stream), 3000);
        el("ocr-status").style.display = "block";
        el("ocr-status").innerHTML = `<span class="spinner"></span>准备拍照，请对准题目…`;
      } catch (e) {
        toast("无法打开摄像头：" + e.message);
      }
    },
    captureFromVideo(video, stream) {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0);
      // 停止摄像头
      stream.getTracks().forEach(t => t.stop());
      video.style.display = "none";
      // 显示预览
      const img = el("ocr-img");
      img.src = canvas.toDataURL("image/jpeg");
      el("ocr-preview").style.display = "block";
      // 进行 OCR
      this.runOCR(canvas.toDataURL("image/jpeg"));
    },
    uploadImage() {
      el("ocr-file-input").click();
    },
    onImageSelected(event) {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = el("ocr-img");
        img.src = e.target.result;
        el("ocr-preview").style.display = "block";
        this.runOCR(e.target.result);
      };
      reader.readAsDataURL(file);
    },
    async runOCR(imageData) {
      const status = el("ocr-status");
      const result = el("ocr-result");
      status.style.display = "block";
      status.innerHTML = `<span class="spinner"></span>正在识别文字…（首次加载需下载识别模型）`;
      result.style.display = "none";
      try {
        if (typeof Tesseract === "undefined") {
          status.innerHTML = "❌ Tesseract.js 未加载，请检查网络连接";
          return;
        }
        const { data } = await Tesseract.recognize(imageData, 'chi_sim+eng', {
          logger: (m) => {
            if (m.status === "recognizing text") {
              status.innerHTML = `<span class="spinner"></span>识别中… ${Math.round(m.progress * 100)}%`;
            }
          }
        });
        const text = (data.text || "").trim();
        if (!text) {
          status.innerHTML = "未识别到文字，请重新拍照或上传清晰的图片";
          return;
        }
        status.style.display = "none";
        result.style.display = "block";
        // 把识别结果回填到输入框，方便学生稍作修改后再讲
        const ta = el("ocr-text-input");
        if (ta && !ta.value.trim()) ta.value = text;
        this._lastOcrText = text;   // 供讲解按钮安全读取（避免内联字符串转义问题）
        // 在课程库中搜索匹配（作为补充入口）
        const matches = this.searchCourseForText(text);
        result.innerHTML = `
          <div class="ocr-text">${esc(text)}</div>
          <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn btn-primary" onclick="UI.explainProblem(UI._lastOcrText)">🔍 让 AL 老师讲这道题</button>
            <button class="btn" onclick="UI.sendOCRToChat('${esc(text)}')">💬 导师提问</button>
          </div>
          ${matches.length > 0 ? `
            <div class="ocr-match">📚 在课程中找到相关知识点：</div>
            ${matches.map(m => `<div style="padding:6px 0;font-size:14px">• <a href="#" onclick="UI.goStudy('${esc(m.id)}');UI.closeOCR();return false">${esc(m.title)}</a></div>`).join("")}
          ` : `
            <div class="ocr-match" style="color:var(--muted)">没匹配到课程知识点也没关系，AL 老师会直接讲这道题</div>
          `}
          <div style="margin-top:10px">
            <button class="btn ghost small" onclick="UI.openOCR()">🔄 重新拍照</button>
          </div>
        `;
      } catch (e) {
        status.innerHTML = "❌ 识别失败：" + esc(e.message);
      }
    },
    searchCourseForText(text) {
      // 在课程库中搜索匹配的文字
      const keywords = text.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, " ").split(/\s+/).filter(w => w.length >= 2);
      if (keywords.length === 0) return [];
      const matches = [];
      const seen = new Set();
      // 遍历所有课程
      const allTopics = [];
      // 先找已加载的 curriculum
      if (state.curriculum) {
        for (const stage of state.curriculum) {
          for (const subj of stage.subjects || []) {
            for (const grade of subj.grades || []) {
              for (const topic of grade.topics || []) {
                allTopics.push(topic);
              }
            }
          }
        }
      }
      if (allTopics.length === 0) return [];
      for (const topic of allTopics) {
        const title = topic.title || "";
        const subs = (topic.sub || []).join(" ");
        const text_lower = text.toLowerCase();
        const title_lower = title.toLowerCase();
        // 简单匹配：标题包含关键词或子内容匹配
        let score = 0;
        for (const kw of keywords) {
          if (title_lower.includes(kw.toLowerCase())) score += 3;
          if (subs.toLowerCase().includes(kw.toLowerCase())) score += 1;
        }
        if (score > 0 && !seen.has(topic.id)) {
          seen.add(topic.id);
          matches.push({ id: topic.id, title, score });
        }
      }
      matches.sort((a, b) => b.score - a.score);
      return matches.slice(0, 5);
    },
    sendOCRToChat(text) {
      this.closeOCR();
      // 把识别文字填入聊天输入框
      const input = el("chat-input");
      if (input) {
        input.value = "我拍到了一道题：" + text.slice(0, 200);
        input.focus();
        toast("已填入输入框，点发送即可提问");
      }
    },
    // ---------- 📖 题目解析（拍照/输入 → AL 老师讲透） ----------
    explainTyped() {
      const t = (el("ocr-text-input").value || "").trim();
      if (!t) return toast("请先拍照识别，或在下方输入/粘贴题目");
      this.explainProblem(t);
    },
    async explainProblem(text) {
      if (!text || !text.trim()) return toast("题目内容为空");
      this.closeOCR();
      const modal = el("explain-modal");
      const body = el("explain-body");
      const foot = el("explain-foot");
      modal.hidden = false;
      foot.style.display = "none";
      body.innerHTML = '<div class="ocr-status"><span class="spinner"></span> AL 老师正在读题、思考怎么讲…</div>';
      try {
        const r = await api("POST", "/api/problem/explain", { problem: text, lang: state.curLang || "zh" });
        this.renderExplain(r, text);
      } catch (e) {
        body.innerHTML = '<div class="ocr-status">❌ ' + esc(e.message) + '</div>';
      }
    },
    renderExplain(d, rawText) {
      const body = el("explain-body");
      const problem = (d.problem || rawText || "").trim();
      const steps = d.steps || [];
      const know = d.knowledge || [];
      const mistakes = d.common_mistakes || [];
      const mockTag = d.mock ? '<span class="explain-mock-tag">演示模式</span>' : '';
      let html = '<div class="explain-card">';
      html += '<div class="explain-sec"><h4>📝 题目</h4><div class="explain-problem">' + esc(problem) + '</div></div>';
      if (know.length) {
        html += '<div class="explain-sec"><h4>🎯 考查知识点</h4><div class="explain-kw">' +
          know.map(k => '<span class="chip">' + esc(k) + '</span>').join("") + '</div></div>';
      }
      if (d.analysis) {
        html += '<div class="explain-sec"><h4>💡 破题思路' + mockTag + '</h4><div class="explain-analysis">' + esc(d.analysis) + '</div></div>';
      }
      if (steps.length) {
        html += '<div class="explain-sec"><h4>🪜 解题步骤</h4><ol class="explain-steps">' +
          steps.map(s => '<li>' + esc(s) + '</li>').join("") + '</ol></div>';
      }
      if (d.answer) {
        html += '<div class="explain-sec"><h4>✅ 最终答案</h4><div class="explain-answer">' + esc(d.answer) + '</div></div>';
      }
      if (mistakes.length) {
        html += '<div class="explain-sec"><h4>⚠️ 易错提醒</h4><ul class="explain-mistakes">' +
          mistakes.map(m => '<li>' + esc(m) + '</li>').join("") + '</ul></div>';
      }
      if (d.practice) {
        html += '<div class="explain-sec"><h4>🏋️ 同类巩固题</h4><div class="explain-practice">' + esc(d.practice) + '</div></div>';
      }
      html += '</div>';
      html += '<div class="explain-actions">' +
        '<button class="btn small" onclick="UI.speakExplain()">🔊 朗读讲解</button>' +
        '<button class="btn small ghost" onclick="UI.explainReread()">🔄 换种讲法</button>' +
        '</div>';
      body.innerHTML = html;
      el("explain-foot").style.display = "flex";
      // 保存上下文：供追问 / 换讲法 / 朗读
      const full = [problem, d.analysis, steps.join("\n"), d.answer, d.practice].filter(Boolean).join("\n\n");
      _explainCtx.problem = problem;
      _explainCtx.full = full;
      _explainCtx.prev = full;
    },
    speakExplain() {
      if (!_explainCtx.full) return toast("还没有可朗读的讲解");
      unlockTTS();
      speak(_explainCtx.full);
    },
    closeExplain() {
      el("explain-modal").hidden = true;
      try { if (window.speechSynthesis) window.speechSynthesis.cancel(); } catch (e) {}
    },
    async explainFollowup() {
      const q = (el("explain-q").value || "").trim();
      if (!q) return toast("请先输入你的追问");
      const body = el("explain-body");
      const wrap = document.createElement("div");
      wrap.className = "explain-sec";
      const fid = "fu-" + Date.now();
      wrap.innerHTML = '<h4>🙋 你的追问</h4><div class="explain-follow">' + esc(q) + '</div>' +
        '<div class="explain-follow" id="' + fid + '"><span class="spinner"></span> AL 老师思考中…</div>';
      body.appendChild(wrap);
      body.scrollTop = body.scrollHeight;
      try {
        const r = await api("POST", "/api/problem/followup", {
          problem: _explainCtx.problem, prev: _explainCtx.prev, question: q, lang: state.curLang || "zh"
        });
        el(fid).innerHTML = esc(r.reply || "（暂无回复）");
        _explainCtx.prev += "\n问：" + q + "\n答：" + (r.reply || "");
        if (r.mock) { const t = document.createElement("span"); t.className = "explain-mock-tag"; t.textContent = "演示模式"; wrap.appendChild(t); }
      } catch (e) {
        el(fid).innerHTML = "❌ " + esc(e.message);
      }
      el("explain-q").value = "";
    },
    explainReread() {
      const q = el("explain-q");
      q.value = "请用完全不同的方式（换个生活比喻、把节奏放慢）把整道题再讲一遍，让零基础的人也能听懂。";
      this.explainFollowup();
    },
    async enterApp(view) {
      el("app-view").hidden = false;
      state._fromLauncher = true;
      state._lastTick = Date.now(); // 重置计时起点
      if (!state.token) {
        // 尝试静默登录（账号未必注册过：先 login，失败再 register，与 bootLogin 一致）
        try {
          const u = accountOfChild(state.childName);
          let r = null;
          try {
            r = await api("POST", "/api/login", { username: u, password: "al_child_default" });
          } catch (e0) {
            r = await api("POST", "/api/register", { username: u, password: "al_child_default" });
          }
          if (r) markAccountKnown(r.username);
          bindAccount(r.username);
          state.token = r.token; state.username = r.username;
      localStorage.setItem("al_token", r.token); localStorage.setItem("al_user", r.username);
      const b = document.getElementById('export-data-btn'); if (b) b.style.display = 'block';
          localStorage.setItem("al_token", r.token);
          localStorage.setItem("al_user", r.username);
        } catch (e) { /* 离线 */ }
      }
      if (state.token) {
        const tn = el("top-name");
        if (tn) tn.textContent = (state.username || state.childName) + " 同学";
        const ta = el("top-avatar");
        if (ta) ta.textContent = state.childAvatar || "🐱";
        await this.loadRoles();
      }
      this.go(view || "learn");
    },
    goHome() {
      // 返回孩子学习主页
      this.go("home");
    },

    // ---------- 🔒 家长验证 ----------
    openParentGate() {
      if (!state.parentPin) {
        // 未设置PIN → 引导设置
        el("app-view").hidden = true;
        el("setup-wizard").hidden = false;
        el("setup-step-1").hidden = true;
        el("setup-step-2").hidden = false;
        return;
      }
      el("parent-gate").hidden = false;
      el("pg-1").value = ""; el("pg-2").value = "";
      el("pg-3").value = ""; el("pg-4").value = "";
      el("pg-error").hidden = true;
      setTimeout(() => el("pg-1").focus(), 100);
    },
    checkPin() {
      const p1 = el("pg-1").value;
      const p2 = el("pg-2").value;
      const p3 = el("pg-3").value;
      const p4 = el("pg-4").value;
      const pin = p1 + p2 + p3 + p4;
      if (pin.length < 4) return;
      if (pin === state.parentPin) {
        el("parent-gate").hidden = true;
        hideLockScreen();  // 解锁成功，关闭锁屏
        this.showParentPanel();
      } else {
        el("pg-error").hidden = false;
        el("pg-1").value = ""; el("pg-2").value = "";
        el("pg-3").value = ""; el("pg-4").value = "";
        el("pg-1").focus();
      }
    },
    closeParentGate() {
      el("parent-gate").hidden = true;
      // 如果锁屏未解锁（PIN错误关闭弹窗），恢复锁屏
      if (state._lockSeconds > 0) {
        const lock = el("lock-screen");
        if (lock) lock.removeAttribute("hidden");
      }
    },
    showParentPanel() {
      const panel = el("parent-panel");
      if (!panel) return;
      panel.hidden = false;
      // 高亮当前时长选项
      document.querySelectorAll(".time-opt").forEach(btn => {
        btn.classList.toggle("active", parseInt(btn.dataset.min, 10) === state.dailyMaxMin);
      });
      // 今日报告
      const rp = el("parent-today-report");
      if (rp) {
        const min = Math.floor(state.todaySec / 60);
        rp.innerHTML = `<p style="font-size:15px;color:var(--ink)">今日已学习 <b>${min}</b> 分钟（上限 ${state.dailyMaxMin} 分钟）</p>`;
      }
      // 孩子列表
      this.renderChildList();
    },
    renderChildList() {
      const list = el("child-list");
      if (!list) return;
      let children = [];
      try { children = JSON.parse(localStorage.getItem("al_children") || "[]"); } catch(e) {}
      const active = localStorage.getItem("al_child_name") || "";
      if (children.length === 0) {
        list.innerHTML = `<p style="font-size:13px;color:var(--muted)">当前只有一个孩子</p>`;
        return;
      }
      list.innerHTML = children.map(c => `
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--line)">
          <span style="font-size:24px">${esc(c.avatar)}</span>
          <span style="flex:1;font-size:14px;font-weight:${c.name === active ? '700' : '400'}">${esc(c.name)} ${c.name === active ? '👈 当前' : ''}</span>
          ${c.name !== active ? `<button class="btn tiny ghost" onclick="UI.switchToChild('${esc(c.name)}')">切换</button>` : ''}
          <button class="btn tiny danger" onclick="UI.deleteChild('${esc(c.name)}')">删除</button>
        </div>
      `).join("");
    },
    closeParentPanel() {
      el("parent-panel").hidden = true;
    },
    // 家长面板：设置时长
    initTimeOptions() {
      document.querySelectorAll(".time-opt").forEach(btn => {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".time-opt").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          state.dailyMaxMin = parseInt(btn.dataset.min, 10);
          localStorage.setItem("al_daily_max", String(state.dailyMaxMin));
          toast("每日学习时长已设为 " + state.dailyMaxMin + " 分钟");
        });
      });
    },
    // 家长解锁锁屏
    unlockByParent() {
      // 先隐藏锁屏，让家长验证弹窗显示出来（锁屏 z-index 999 会盖住弹窗）
      const lock = el("lock-screen");
      if (lock) lock.setAttribute("hidden", "");
      this.openParentGate();
    },
    // 家长→设置页
    async showDashboard() {
      this.enterApp("dashboard");
      try {
        const d = await api("GET", "/api/dashboard");
        const s = d.summary || {};
        const recent = (d.sessions_recent||[]).map(r =>
          `<li style="padding:6px 0;border-bottom:1px solid #eee;display:flex;justify-content:space-between"><span>${r.d}</span><span style="color:#666">${r.cnt} 次</span></li>`
        ).join('') || '<li>暂无记录</li>';
        const topM = (d.top_mastered||[]).map(r =>
          `<li style="padding:4px 0;border-bottom:1px solid #eee">📘 ${r.course_id} · 掌握度 ${r.level}</li>`
        ).join('') || '<li>暂无</li>';
        const topW = (d.top_weak||[]).map(r =>
          `<li style="padding:4px 0;border-bottom:1px solid #eee">🔴 ${r.course_id} · 尝试 ${r.attempts} 次</li>`
        ).join('') || '<li>暂无</li>';
        const html = `
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin:16px 0">
            <div style="background:#fff;padding:16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.08);text-align:center">
              <div style="font-size:26px;font-weight:bold;color:#4f46e5">${s.total_courses||0}</div><div style="font-size:12px;color:#666">已学课程</div>
            </div>
            <div style="background:#fff;padding:16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.08);text-align:center">
              <div style="font-size:26px;font-weight:bold;color:#22c55e">${s.mastered||0}</div><div style="font-size:12px;color:#666">已掌握</div>
            </div>
            <div style="background:#fff;padding:16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.08);text-align:center">
              <div style="font-size:26px;font-weight:bold;color:#3b82f6">${s.familiar||0}</div><div style="font-size:12px;color:#666">熟悉</div>
            </div>
            <div style="background:#fff;padding:16px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.08);text-align:center">
              <div style="font-size:26px;font-weight:bold;color:#ef4444">${s.not_mastered||0}</div><div style="font-size:12px;color:#666">未掌握</div>
            </div>
          </div>
          <h3 style="margin-top:12px">📅 最近 7 天</h3>
          <ul style="list-style:none;padding:0">${recent}</ul>
          <h3 style="margin-top:12px">🌟 已掌握 Top10</h3>
          <ul style="list-style:none;padding:0;font-size:13px">${topM}</ul>
          <h3 style="margin-top:12px">⚠️ 待加强 Top10</h3>
          <ul style="list-style:none;padding:0;font-size:13px">${topW}</ul>
        `;
        const view = el("view-dashboard");
        if (view) view.innerHTML = html;
      } catch (e) { toast("加载看板失败：" + e.message); }
    },
    goSettings() {
      el("parent-panel").hidden = true;
      hideLockScreen();
      this.enterApp("settings");
      this.loadTtsUI();   // 同步语音朗读设置到控件
    },
    switchChild() {
      // 显示孩子列表让家长选择
      this.renderChildList();
      toast("👆 点击列表中的孩子名字即可切换");
    },
    switchToChild(name) {
      let children = [];
      try { children = JSON.parse(localStorage.getItem("al_children") || "[]"); } catch(e) {}
      const child = children.find(c => c.name === name);
      if (!child) return toast("未找到该孩子");
      // 保存当前孩子
      localStorage.setItem("al_child_name", child.name);
      localStorage.setItem("al_child_avatar", child.avatar);
      // 切换前：先把「当前孩子」的本地进度存进他自己的抽屉，避免串号
      saveScopeFor(localStorage.getItem("al_user") || "");
      state.childName = child.name;
      state.childAvatar = child.avatar;
      // 清除旧 token，重新登录
      state.token = "";
      localStorage.removeItem("al_token");
      localStorage.removeItem("al_user");
      el("parent-panel").hidden = true;
      toast("已切换到 " + child.name);
      // 重新引导登录
      bootLogin().then(() => {
        showLauncher();
        syncProfile();
        // 登录态就绪后，把该账号在服务端的学习进度拉回本地
        UI._ssLoadRemoteProgress().then(() => UI.renderMachineHome && UI.renderMachineHome(true));
      });
    },
    addChild() {
      const name = prompt("输入新孩子的名字：");
      if (!name || !name.trim()) return;
      const avatar = prompt("选一个头像 emoji（🐱 🐶 🐰 🐼 🦊 🐯）：", "🐱");
      let children = [];
      try { children = JSON.parse(localStorage.getItem("al_children") || "[]"); } catch(e) {}
      if (children.find(c => c.name === name.trim())) {
        return toast("同名孩子已存在");
      }
      children.push({ name: name.trim(), avatar: (avatar || "🐱").trim() });
      localStorage.setItem("al_children", JSON.stringify(children));
      // 切换到新孩子
      this.switchToChild(name.trim());
    },
    deleteChild(name) {
      let children = [];
      try { children = JSON.parse(localStorage.getItem("al_children") || "[]"); } catch(e) {}
      const active = localStorage.getItem("al_child_name");
      if (name === active) {
        // 不能删除当前孩子
        // 但家长可以删
      }
      if (!confirm(`删除「${name}」的学习记录吗？`)) return;
      children = children.filter(c => c.name !== name);
      localStorage.setItem("al_children", JSON.stringify(children));
      // 如果删除的是当前孩子，切到第一个
      if (name === active && children.length > 0) {
        this.switchToChild(children[0].name);
      } else if (children.length === 0) {
        // 没有孩子了，重新初始化
        localStorage.removeItem("al_child_name");
        localStorage.removeItem("al_child_avatar");
        localStorage.removeItem("al_token");
        localStorage.removeItem("al_user");
        state.token = "";
        el("parent-panel").hidden = true;
        location.reload();
      } else {
        this.renderChildList();
        toast("已删除");
      }
    },

    async enter() {
      if (el("login-view")) el("login-view").style.display = "none";
      el("app-view").hidden = false;
      const tn = el("top-name");
      if (tn) tn.textContent = (state.username || state.childName) + " 同学";
      const ta = el("top-avatar");
      if (ta) ta.textContent = state.childAvatar || "🐱";
      await this.loadRoles();
      this.go("learn");
    },

    // ---------- 路由 ----------
    go(view) {
      ["learn", "roles", "kg", "precision", "report", "settings", "home", "plan", "selfstudy", "dashboard", "companion"].forEach((v) => {
        const sec = el("view-" + v);
        if (sec) sec.classList.toggle("active", v === view);
        const nav = el("nav-" + v);
        if (nav) nav.classList.toggle("active", v === view);
      });
      // 底部 Tab
      document.querySelectorAll(".bottom-tab").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.view === view);
      });
      if (view === "roles") this.renderRoleList();
      if (view === "kg") this.renderKG();
      if (view === "precision") this.loadPrecUnits();
      if (view === "report") this.loadReport();
      if (view === "settings") this.loadSettings();
      if (view === "selfstudy") this.openSelfStudy();
      if (view === "dashboard") this.showDashboard();
      if (view !== "learn" && view !== "home") this.stopSilenceMonitor();
      else if (state.sessionId) this.startSilenceMonitor();
      this.closeSidebar();
      this.closeMore();
      if (view === "home") { this.renderResumeCard(); this.renderMachineHome && this.renderMachineHome(false); }
      if (view === "companion") { this.openCompanion && this.openCompanion(); }
      // 学伴球：进入应用内任意页面显示，全屏学伴页隐藏
      if (typeof updateCompanionFab === "function") updateCompanionFab(view);
      this.saveResumeSoon();
    },

    // ---------- ⏯ 断点续学：下次打开可以继续 ----------
    RESUME_KEY: "al_resume_v1",
    _resumeLabel(r) {
      const p = r.prec || {}, ss = r.ss || {};
      if (p.diag && (p.diag.questions || []).length) {
        const n = Object.keys(p.diag.answers || {}).length, t = p.diag.questions.length;
        return { title: "📋 继续未完成的诊断", sub: `${p.subject || ""} ${p.grade || ""} · 已答 ${n}/${t} 题` };
      }
      if (p.practice && (p.practice.questions || []).length) {
        const n = Object.keys(p.practice.answers || {}).length, t = p.practice.questions.length;
        return { title: "✏️ 继续未完成的练习", sub: `${p.practice.title || "分层练习"}${p.practice.tier ? " · " + p.practice.tier : ""} · 已答 ${n}/${t} 题` };
      }
      if (p.panel === "mistakes") return { title: "📕 继续复习错题本", sub: `${p.subject || ""} ${p.grade || ""}`.trim() };
      if (ss.cid) {
        const where = ss.seq ? `${ss.seq.name || ""} 第 ${(ss.seq.idx || 0) + 1} 章` : `${ss.subject || ""} · ${ss.grade || ""}`;
        return { title: "📚 继续自学：" + (ss.title || "上一章节"), sub: where };
      }
      if (p.subject) return { title: "📊 继续精准学", sub: `${p.subject} ${p.grade || ""}`.trim() };
      return null;
    },
    _resumeSnapshot() {
      const ss = state._ssChapterId ? {
        cid: state._ssChapterId,
        title: (state._ssLesson && state._ssLesson.title) || "",
        stage: state._ssStage, grade: state._ssGrade, subject: state._ssSubject,
        seq: state._ssSeqMode ? { name: state._ssSeqName, idx: state._ssSeqIdx } : null,
      } : null;
      const prec = (state.precSubject && state.precGrade) ? {
        subject: state.precSubject, grade: state.precGrade,
        panel: state._precLastPanel || "",
        mistakesFilter: state._mistakeFilter || "all",
        diag: state.precDiag ? {
          diag_id: state.precDiag.diag_id, questions: state.precDiag.questions,
          answers: state.precDiagAnswers || {}, meta: state._diagMeta || null,
        } : null,
        practice: state.precPractice ? {
          course_id: state._practiceCourse, title: (state._lesson && state._lesson.title) || "",
          tier: state._practiceTier, questions: state.precPractice.questions,
          answers: state._practiceAnswers || {},
        } : null,
      } : null;
      const snap = { v: 1, ts: new Date().toISOString(), view: state._lastView || "home", ss, prec };
      snap.label = this._resumeLabel(snap);
      return snap;
    },
    async saveResume(force) {
      try {
        const snap = this._resumeSnapshot();
        if (!snap.label) return;
        state.resume = snap;
        localStorage.setItem(this.RESUME_KEY, JSON.stringify(snap));
        if (!state.token) return;
        await api("POST", "/api/study/resume", { resume: snap }).catch(() => {});
      } catch (e) {}
    },
    saveResumeSoon() {
      if (state._resumeTimer) clearTimeout(state._resumeTimer);
      state._resumeTimer = setTimeout(() => { this.saveResume(); }, 700);
    },
    async loadResume() {
      let local = null, remote = null;
      try { local = JSON.parse(localStorage.getItem(this.RESUME_KEY) || "null"); } catch (e) {}
      try { const r = await api("GET", "/api/study/resume"); remote = r.resume; } catch (e) {}
      const pick = (remote && (!local || (remote.ts || "") > (local.ts || ""))) ? remote : local;
      state.resume = (pick && (pick.label || pick.view)) ? pick : null;
      if (!state.resume && pick) state.resume = pick;
      this.renderResumeCard();
    },
    _agoText(d) {
      const diff = (Date.now() - d.getTime()) / 1000;
      if (diff < 90) return "刚刚";
      if (diff < 3600) return Math.round(diff / 60) + " 分钟前";
      if (diff < 86400) return Math.round(diff / 3600) + " 小时前";
      return Math.round(diff / 86400) + " 天前";
    },
    renderResumeCard() {
      const box = el("resume-card");
      if (!box) return;
      const r = state.resume;
      const label = r && (r.label || this._resumeLabel(r));
      if (!label) { box.style.display = "none"; box.innerHTML = ""; return; }
      let ago = "";
      try { ago = this._agoText(new Date(r.ts)); } catch (e) {}
      box.style.display = "";
      box.innerHTML = `<div class="rs-main">
          <div class="rs-ico">⏯</div>
          <div class="rs-text">
            <div class="rs-title">${esc(label.title)}</div>
            <div class="rs-sub">${esc(label.sub || "")}${ago ? " · " + esc(ago) : ""}</div>
          </div>
          <button class="btn" onclick="UI.resumeGo()">继续学习 →</button>
        </div>`;
    },
    resumeGo() {
      const r = state.resume;
      if (!r) return;
      const hasPrec = r.prec && (r.prec.diag || r.prec.practice || r.prec.panel || r.prec.subject);
      if (hasPrec) { state._pendingResume = r; this.go("precision"); return; }
      if (r.ss && r.ss.cid) { state._pendingResume = r; this.go("selfstudy"); return; }
      this.go(r.view || "home");
    },
    async applyPendingResume() {
      const r = state._pendingResume;
      if (!r) return;
      state._pendingResume = null;
      const p = r.prec || {};
      // 1) 恢复学科 / 年级下拉
      const sSel = el("prec-subject"), gSel = el("prec-grade");
      if (sSel && p.subject && [...sSel.options].some(o => o.value === p.subject)) {
        sSel.value = p.subject; state.precSubject = p.subject; this.onPrecSubject();
      }
      if (gSel && p.grade && [...gSel.options].some(o => o.value === p.grade)) {
        gSel.value = p.grade; state.precGrade = p.grade; this.renderPrecGraph();
      }
      state._mistakeFilter = p.mistakesFilter || state._mistakeFilter || "all";
      // 2) 未完成的诊断 → 直接回到作答界面，并回填已选答案
      if (p.diag && (p.diag.questions || []).length) {
        state.precDiag = { diag_id: p.diag.diag_id, questions: p.diag.questions };
        state.precDiagAnswers = p.diag.answers || {};
        state._diagMeta = p.diag.meta || null;
        state._precLastPanel = "diag";
        el("prec-practice").style.display = "none";
        el("prec-mistakes").style.display = "none";
        el("prec-diag").style.display = "block";
        this.renderDiag(state.precDiag);
        this._restoreDiagPicks();
        toast("已恢复上次未完成的诊断，接着答吧 ✍️");
        return;
      }
      // 3) 未完成的练习 → 回到练习界面，保留已选答案
      if (p.practice && (p.practice.questions || []).length) {
        state.precPractice = { questions: p.practice.questions, total: p.practice.questions.length };
        state._practiceAnswers = p.practice.answers || {};
        state._practiceCourse = p.practice.course_id || "";
        state._practiceTier = p.practice.tier || "";
        state._precLastPanel = "practice";
        el("prec-diag").style.display = "none";
        el("prec-mistakes").style.display = "none";
        el("prec-practice").style.display = "block";
        this._renderPractice(state.precPractice, p.practice.tier, p.practice.title);
        toast("已恢复上次未完成的练习，接着做吧 ✏️");
        return;
      }
      // 4) 只是错题本 / 网页位置
      if (p.panel === "mistakes") { this.showMistakes(state._mistakeFilter); return; }
    },

    // ---------- 侧边栏抽屉（平板 / 手机） ----------
    toggleSidebar() {
      const sb = el("sidebar");
      if (!sb) return;
      const open = sb.classList.toggle("open");
      el("sidebar-mask").classList.toggle("show", open);
    },
    openSidebar() {
      const sb = el("sidebar");
      if (!sb) return;
      sb.classList.add("open");
      const m = el("sidebar-mask");
      if (m) m.classList.add("show");
    },
    closeSidebar() {
      const sb = el("sidebar");
      if (sb) sb.classList.remove("open");
      const m = el("sidebar-mask");
      if (m) m.classList.remove("show");
    },
    openMore() {
      const d = el("more-drawer");
      if (d) d.hidden = false;
    },
    closeMore() {
      const d = el("more-drawer");
      if (d) d.hidden = true;
    },

    // ---------- 角色 ----------
    async loadRoles() {
      state.roles = await api("GET", "/api/roles");
      const sel = el("learn-role");
      sel.innerHTML = state.roles.map(r => {
        const tag = r.lang === "en" ? "（英）" : "";
        const sys = r.user_id === 0 ? " · 系统" : "";
        return `<option value="${r.id}">${esc(r.name)}${tag}${sys}</option>`;
      }).join("");
      if (state.roles.length === 0) {
        el("chat-log").innerHTML = `<div class="empty">还没有学习角色，请先到「角色」页创建一个 🎭</div>`;
      } else {
        this.onRoleChange();
      }
    },
    onRoleChange() {
      const rid = parseInt(el("learn-role").value, 10);
      state.currentRole = state.roles.find(r => r.id === rid) || null;
      if (state.currentRole) {
        el("stage-badge").textContent = "关系阶段：" + STAGE_NAME(state.currentRole.relationship_stage);
        this.applyLangByRole(state.currentRole);
      }
      this.loadSessions();
    },
    applyLangByRole(role) {
      // 角色语言决定对话语言：英语外教 -> 英文语音，否则中文
      state.curLang = (role.lang === "en") ? "en-US" : "zh-CN";
      const mic = el("mic-btn");
      if (mic) mic.title = "点击开始/停止语音输入（" + state.curLang + "）";
    },
    async loadSessions() {
      this.stopAssess();
      const rid = state.currentRole && state.currentRole.id;
      if (!rid) return;
      const list = await api("GET", "/api/sessions?role_id=" + rid);
      const sel = el("learn-session");
      let html = `<option value="new">＋ 新建会话</option>`;
      list.forEach(s => {
        const cp = s.checkpoint ? " 📌" : "";
        const title = (s.title || "会话") + cp;
        html += `<option value="${s.id}">${esc(title)}（${s.message_count}条）</option>`;
      });
      sel.innerHTML = html;
      state.sessionId = null;
      el("chat-log").innerHTML = `<div class="empty">开始与「${esc(state.currentRole.name)}」的对话吧 ✨<br>它会用提问引导你思考，而不是直接给答案。</div>`;
      el("emotion-bar").style.display = "none";
      this.startSilenceMonitor();
    },
    onSessionChange() {
      const v = el("learn-session").value;
      if (v === "new") { state.sessionId = null; el("chat-log").innerHTML = ""; return; }
      this.loadMessages(parseInt(v, 10));
    },
    async loadMessages(sid) {
      state.sessionId = sid;
      this._lastUserMsgTime = Date.now();
      this._silenceHintShown = false;
      this.startSilenceMonitor();
      const msgs = await api("GET", "/api/sessions/" + sid);
      el("chat-log").innerHTML = "";
      msgs.forEach(m => appendBubble(m.role, m.content, false, m.emotion));
      scrollChat();
    },

    // ---------- 对话 ----------
    onKey(e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.send(); }
    },
    async send() {
      if (state.busy) return;
      if (state.testMode) return;   // 自测进行中，禁用聊天发送
      const rid = state.currentRole && state.currentRole.id;
      if (!rid) return toast("请先选择一个学习角色");
      const input = el("chat-input");
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      appendBubble("user", text, false);
      scrollChat();
      const typing = appendTyping();
      scrollChat();
      state.busy = true;
      try {
          const r = await api("POST", "/api/chat", {
            role_id: rid, session_id: state.sessionId, message: text,
            course_id: state.selectedCourse ? state.selectedCourse.id : null,
          });
          state.sessionId = r.session_id;
          this._lastUserMsgTime = Date.now();
          this._silenceHintShown = false;
          typing.remove();
          appendBubble("bot", r.reply, true, r.emotion, () => {
            this.showEmotion(r);
            if (r.stage) { state.currentRole.relationship_stage = r.stage_index; el("stage-badge").textContent = "关系阶段：" + r.stage; }
            this.refreshSessionSelect();
            state.lastBotText = r.reply;
            // 对话获得星星（每日限10次）
            this.awardStars("chat", 1);
            if (state.voiceMode) speak(r.reply);
          });
        scrollChat();
      } catch (e) {
        typing.remove();
        appendBubble("bot", "⚠️ " + e.message, false);
      } finally {
        state.busy = false;
      }
    },
    // ---------- 课后测试（自测模式） ----------
    // 流程：出题(5道选择) → 学生独立作答(计时) → 提交 → AL 按正确率+用时评估 →
    //       已掌握则鼓励；未掌握则给出「看AI讲解 / 重新测试 / 查看错题」再学习入口。
    async startAssess() {
      if (!state.selectedCourse) return toast("请先在「📚 浏览课程目录」中选择一个知识点，再开始课后测试");
      this.stopTestTimer();
      state.testMode = true;
      state.testQids = [];
      state.testAnswers = {};
      state.testTimes = {};
      state.testStart = Date.now();
      el("assess-banner").style.display = "flex";
      el("assess-topic").textContent = state.selectedCourse.title;
      el("assess-roadmap").style.display = "none";
      el("chat-log").style.display = "none";
      const composer = el("composer");
      if (composer) composer.style.display = "none";
      const box = el("test-panel");
      box.style.display = "block";
      const sc = state.selectedCourse || {};
      const subsLen = (sc.sub && sc.sub.length) || 0;
      // 与后端 _test_plan 一致：题量 = 子内容数（封顶 20），覆盖全部核心内容即可，不强制凑量
      const cnt = subsLen ? Math.min(subsLen, 20) : 5;
      box.innerHTML = `<div class="empty">📝 正在生成「${esc(state.selectedCourse.title)}」的课后自测题（约 ${cnt} 道，覆盖全部核心内容，请独立完成）…</div>`;
      try {
        const r = await api("POST", "/api/precision/test", { course_id: state.selectedCourse.id });
        state.testQids = r.questions.map(q => q.qid);
        this.renderTest(r);
        this.startTestTimer();
      } catch (e) {
        box.innerHTML = `<div class="empty">生成自测题失败：${esc(e.message)}</div>`;
      }
    },
    renderTest(r) {
      const labels = ["A", "B", "C", "D"];
      let html = `<div class="test-head">`;
      html += `<div class="test-sub">📋 课后自测 · ${esc(r.topic)}（共 ${r.total} 题，含选择题/填空题/计算题，请独立完成）</div>`;
      html += `<div class="test-progress" id="test-progress">已答 0/${r.total}</div>`;
      html += `</div>`;
      html += r.questions.map(q => {
        const typeLabel = q.type === "calc" ? "计算题" : q.type === "fill" ? "填空题" : "选择题";
        let body;
        if (q.type === "choice") {
          body = `<div class="choice-opts">` + (q.options || []).map((o, oi) => `
                <label class="choice-row"><span class="choice-lbl">${labels[oi] || oi}.</span>
                <span class="choice-txt">${plainMath(esc(o))}</span>
                <input type="radio" name="tq_${esc(q.qid)}" value="${oi}" onchange="UI.pickTest('${esc(q.qid)}',${oi})"></label>`).join("") + `</div>`;
        } else {
          body = `<div class="fill-wrap"><input type="text" class="fill-input" id="fi_${esc(q.qid)}" placeholder="把答案写在这里" autocomplete="off" oninput="UI.fillTest('${esc(q.qid)}', this.value)"><span class="fill-tip">${q.type === "calc" ? "写出计算过程或结果" : "在横线上填答案"}</span></div>`;
        }
        return `<div class="test-q" id="tq-${esc(q.qid)}">
          <div class="tq-no">${q.idx}.</div>
          <div class="tq-body">
            <span class="tq-type tq-${q.type}">${typeLabel}</span>
            <div class="tq-stem">${plainMath(esc(q.stem))}<span class="answer-blank">(　　)</span></div>
            ${body}
          </div>
        </div>`;
      }).join("");
      html += `<div class="btn-row"><button class="btn btn-primary" onclick="UI.submitTest()">📤 提交自测并看评估</button></div>`;
      html += `<div id="test-result"></div>`;
      el("test-panel").innerHTML = html;
      renderMath(el("test-panel"));
    },
    fillTest(qid, val) {
      if (state.testAnswers[qid] === undefined) {
        state.testTimes[qid] = Math.round((Date.now() - state.testStart) / 1000);
      }
      state.testAnswers[qid] = val;
      const done = state.testQids.filter(q => {
        const a = state.testAnswers[q];
        return a !== undefined && a !== "";
      }).length;
      const p = el("test-progress");
      if (p) p.textContent = `已答 ${done}/${state.testQids.length}`;
    },
    pickTest(qid, oi) {
      if (state.testAnswers[qid] === undefined) {
        // 首次作答时记录用时（秒）
        state.testTimes[qid] = Math.round((Date.now() - state.testStart) / 1000);
      }
      state.testAnswers[qid] = oi;
      const done = state.testQids.filter(q => state.testAnswers[q] !== undefined).length;
      const p = el("test-progress");
      if (p) p.textContent = `已答 ${done}/${state.testQids.length}`;
    },
    async submitTest() {
      const unanswered = state.testQids.filter(q => {
        const a = state.testAnswers[q];
        return a === undefined || a === "";
      });
      if (unanswered.length) return toast(`还有 ${unanswered.length} 道题没做，请全部作答后再提交`);
      this.stopTestTimer();
      const answers = state.testQids.map(qid => ({ qid, user_answer: state.testAnswers[qid] }));
      const total_time = Math.round((Date.now() - state.testStart) / 1000);
      el("test-panel").querySelectorAll("input[type=radio]").forEach(i => i.disabled = true);
      const fb = el("test-result");
      fb.innerHTML = `<div class="empty">📊 AL 正在根据你的正确率和做题时间评估掌握情况…</div>`;
      try {
        const r = await api("POST", "/api/precision/test/grade",
          { course_id: state.selectedCourse.id, answers, times: state.testTimes, total_time });
        this.showTestResult(r);
        if (state.selectedCourse) this.loadMastery(state.selectedCourse.id);
        this.awardStars("test", 3);
      } catch (e) {
        fb.innerHTML = `<div class="empty">评估失败：${esc(e.message)}</div>`;
      }
    },
    showTestResult(r) {
      const labels = ["A", "B", "C", "D"];
      const mm = String(Math.floor(r.total_time / 60)).padStart(2, "0");
      const ss = String(r.total_time % 60).padStart(2, "0");
      const cls = "mv-" + (r.level >= 4 ? "mastered" : r.level === 3 ? "familiar" : r.level === 2 ? "know" : "weak");
      let html = `<div class="test-result-card ${cls}">`;
      html += `<div class="tr-head">📊 自测结果：<b>${esc(r.verdict)}</b></div>`;
      html += `<div class="tr-metrics">`;
      html += `<span>✅ 正确率 <b>${r.correct_count}/${r.total}</b>（${r.accuracy}%）</span>`;
      html += `<span>⏱ 总用时 <b>${mm}:${ss}</b></span>`;
      html += `<span>🐢 平均 <b>${r.avg_time}</b> 秒/题</span>`;
      html += `</div>`;
      if (r.reason) html += `<div class="tr-reason">判定依据：${esc(r.reason)}</div>`;
      html += `<div class="tr-list">`;
      (r.results || []).forEach((res, i) => {
        if (res.error) return;
        const isChoice = (res.type === "choice" || typeof res.answer === "number");
        let ansShow, yourShow;
        const your = state.testAnswers[res.qid];
        if (isChoice) {
          ansShow = (typeof res.answer === "number") ? labels[res.answer] : String(res.answer);
          yourShow = (typeof your === "number") ? labels[your] : "未答";
        } else {
          ansShow = res.answer;
          yourShow = (your === undefined || your === "") ? "未答" : your;
        }
        const rc = res.correct ? "ok" : "bad";
        html += `<div class="tr-item ${rc}">`;
        html += `<div class="tri-h"><b>第 ${i + 1} 题</b> ${res.correct ? "✅ 答对" : "❌ 答错"}${res.time != null ? ` <span class="tri-time">用时 ${res.time}s</span>` : ""}</div>`;
        html += `<div class="tri-detail">你的答案：<b>${esc(yourShow)}</b> ｜ 正确答案：<b>${esc(ansShow)}</b></div>`;
        if (!res.correct && res.explanation) html += `<div class="tri-ex">💡 ${esc(res.explanation)}</div>`;
        html += `</div>`;
      });
      html += `</div>`;
      // 再学习区域
      if (r.level < 4) {
        html += `<div class="relearn-box">`;
        html += `<div class="rl-title">📚 还没完全掌握，AL 帮你再学一遍：</div>`;
        if (r.advice) html += `<div class="rl-advice">${esc(r.advice)}</div>`;
        if (r.relearn && r.relearn.length) {
          html += `<div class="rl-subs">重点回看：` + r.relearn.map(s => `<span class="rl-sub">${esc(s)}</span>`).join("") + `</div>`;
        }
        html += `<div class="btn-row">`;
        html += `<button class="btn ghost small" onclick="UI.openLessonById('${esc(r.course_id)}')">📖 看AI讲解</button>`;
        html += `<button class="btn ghost small" onclick="UI.startAssess()">🔄 重新测试</button>`;
        html += `<button class="btn ghost small" onclick="UI.goMistakes()">📕 查看错题本</button>`;
        html += `</div></div>`;
      } else {
        html += `<div class="relearn-box ok">🎉 已掌握！可以进入下一个知识点，或挑战更综合的题型。</div>`;
      }
      html += `</div>`;
      el("test-result").innerHTML = html;
      renderMath(el("test-result"));
    },
    goMistakes() {
      this.stopAssess();
      UI.go("precision");
      this.showMistakes();
    },
    startTestTimer() {
      this.stopTestTimer();
      state._testTimerId = setInterval(() => {
        const s = Math.round((Date.now() - state.testStart) / 1000);
        const t = el("test-timer");
        if (t) t.textContent = "⏱ " + String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
      }, 1000);
    },
    stopTestTimer() {
      if (state._testTimerId) { clearInterval(state._testTimerId); state._testTimerId = null; }
    },
    stopAssess() {
      this.stopTestTimer();
      state.testMode = false;
      state.testQids = [];
      state.testAnswers = {};
      state.testTimes = {};
      const b = el("assess-banner");
      if (b) b.style.display = "none";
      const road = el("assess-roadmap");
      if (road) road.style.display = "none";
      const panel = el("test-panel");
      if (panel) panel.style.display = "none";
      const log = el("chat-log");
      if (log) log.style.display = "block";
      const composer = el("composer");
      if (composer) composer.style.display = "";
      const t = el("test-timer");
      if (t) t.textContent = "⏱ 00:00";
    },
    async loadMastery(courseId) {
      if (!courseId) return;
      try {
        const m = await api("GET", "/api/mastery?course_id=" + encodeURIComponent(courseId));
        const badge = el("course-mastery");
        if (!badge) return;
        const lv = m.level || 0;
        badge.textContent = "掌握度：" + (MASTERY_LABEL[lv] || "未测");
        badge.className = "mastery-badge mv-" +
          (lv >= 4 ? "mastered" : lv === 3 ? "familiar" : lv === 2 ? "know" : lv === 1 ? "weak" : "untested");
        badge.style.display = "inline-block";
      } catch (e) { /* 忽略掌握度加载失败 */ }
    },

    // ---------- 📊 学情报告 ----------
    async loadReport() {
      this.switchReportTab("daily");
      try {
        const [daily, weekly, mastery, weak] = await Promise.all([
          api("GET", "/api/report/daily"),
          api("GET", "/api/report/weekly"),
          api("GET", "/api/report/mastery-summary"),
          api("GET", "/api/report/weak-areas"),
        ]);
        this.renderDaily(daily);
        this.renderWeekly(weekly);
        this.renderMasteryGrid(mastery);
        this.renderWeakList(weak);
      } catch (e) {
        // 离线兜底：用本地数据渲染同款报告（时长/掌握/星星全部本地可得）
        this.renderLocalReport();
      }
    },
    _localSevenDays() {
      const days = [];
      for (let i = 6; i >= 0; i--) {
        const d = new Date(); d.setHours(0, 0, 0, 0);
        d.setDate(d.getDate() - i);
        const sec = parseInt(localStorage.getItem("al_today_sec_" + d.getTime()) || "0", 10);
        days.push({ date: d.toISOString().slice(0, 10), seconds: sec,
          minutes: Math.round(sec / 60 * 10) / 10 });
      }
      return days;
    },
    renderLocalReport() {
      // 今日卡片（本地版）
      const cards = el("r-daily-cards");
      if (cards) {
        const map = this._ssLoadProgress();
        let mastered = 0, know = 0;
        Object.keys(map).forEach(k => {
          const s2 = (map[k] && map[k].status) || 0;
          if (s2 >= 2) mastered++; else if (s2 >= 1) know++;
        });
        const today = this._localSevenDays()[6];
        cards.innerHTML = `
          <div class="rcard"><div class="rc-v">${today.minutes}</div><div class="rc-l">今日学习(分)</div></div>
          <div class="rcard"><div class="rc-v">${mastered}</div><div class="rc-l">已掌握知识点</div></div>
          <div class="rcard"><div class="rc-v">${know}</div><div class="rc-l">学习中知识点</div></div>
          <div class="rcard"><div class="rc-v">${window.AL_GAMIFY ? window.AL_GAMIFY.state().streak.cur : 0}</div><div class="rc-l">连续学习(天)</div></div>`;
      }
      // 本周柱状图（本地版）
      const chart = el("r-weekly-chart");
      if (chart) {
        const days = this._localSevenDays();
        const max = Math.max(1, ...days.map(d => d.minutes));
        const total = days.reduce((a, d) => a + d.minutes, 0);
        chart.innerHTML =
          `<div class="wk-sum">本周共学习 <b>${Math.round(total)}</b> 分钟 · 学习 ${days.filter(d => d.seconds > 60).length} 天</div>` +
          `<div class="wk-bars">` + days.map(d => `
            <div class="wk-col" title="${d.date}">
              <div class="wk-v">${d.minutes}</div>
              <div class="wk-bar"><span style="height:${Math.round(d.minutes / max * 100)}%"></span></div>
              <div class="wk-d">${d.date.slice(5).replace("-", "/")}</div>
            </div>`).join("") + `</div>`;
      }
      // 掌握度（本地版：自学进度聚合）
      const mg = el("r-mastery-grid");
      if (mg) {
        const map = this._ssLoadProgress();
        let total = 0, done = 0, mastered = 0;
        Object.keys(map).forEach(k => {
          total++;
          const s2 = (map[k] && map[k].status) || 0;
          if (s2 >= 1) done++;
          if (s2 >= 2) mastered++;
        });
        mg.innerHTML = `<div class="rcard" style="grid-column:1/-1">
          <div class="rc-v">${mastered} / ${total || "—"}</div>
          <div class="rc-l">已掌握 / 已开始（自学进度）</div></div>`;
      }
      const wk = el("r-weekly-mastery"), wl = el("r-weak-list") || el("r-weak");
      if (wk) wk.innerHTML = `<p class="r-empty">离线模式：掌握度变化与薄弱项分析需要联网服务</p>`;
      if (wl) wl.innerHTML = `<p class="r-empty">离线模式：薄弱项分析需要联网服务</p>`;
    },
    switchReportTab(tab) {
      document.querySelectorAll(".rtab").forEach(t => t.classList.toggle("active", t.dataset.rtab === tab));
      document.querySelectorAll(".rpanel").forEach(p => p.classList.remove("active"));
      const rp = el("rpanel-" + tab);
      if (rp) rp.classList.add("active");
    },
    renderDaily(data) {
      const cards = el("r-daily-cards");
      if (!cards) return;
      const min = data.minutes || 0;
      const mLabels = ["未测", "未掌握", "了解", "熟悉", "掌握"];
      const m = data.mastery || {};
      cards.innerHTML = `
        <div class="r-card rc-time">
          <div class="rc-icon">⏱</div>
          <div class="rc-value">${Math.floor(min)}</div>
          <div class="rc-label">今日学习(分钟)</div>
        </div>
        <div class="r-card rc-msg">
          <div class="rc-icon">💬</div>
          <div class="rc-value">${data.msg_count || 0}</div>
          <div class="rc-label">对话消息</div>
        </div>
        <div class="r-card rc-mastery">
          <div class="rc-icon">✅</div>
          <div class="rc-value">${m.mastered || 0}</div>
          <div class="rc-label">已掌握(+${m.familiar || 0}熟悉)</div>
        </div>
        <div class="r-card rc-mistake">
          <div class="rc-icon">📕</div>
          <div class="rc-value">${data.mistake_count || 0}</div>
          <div class="rc-label">今日错题</div>
        </div>
      `;
      // 详细记录
      const detail = el("r-daily-detail");
      if (detail) {
        detail.innerHTML = `<div class="r-stats">
          <span>📝 会话数：<b>${data.session_count || 0}</b></span>
          <span>📊 已测评知识点：<b>${m.total_tested || 0}</b></span>
          <span>🎯 掌握：<b>${m.mastered || 0}</b> · 熟悉：${m.familiar || 0} · 了解：${m.know || 0}</span>
        </div>`;
      }
    },
    renderWeekly(data) {
      const chart = el("r-weekly-chart");
      if (!chart) return;
      const days = data.days || [];
      const maxMin = Math.max(...days.map(d => d.minutes), 1);
      const dayLabels = ["一", "二", "三", "四", "五", "六", "日"];
      // 今天星期几
      const today = new Date().getDay();
      chart.innerHTML = `<div class="r-bar-chart">` + days.map((d, i) => {
        const pct = (d.minutes / maxMin) * 100;
        const isToday = i === days.length - 1;
        const dow = (today - (days.length - 1 - i) + 7) % 7;
        const label = dayLabels[dow === 0 ? 6 : dow - 1] || "一";
        return `<div class="r-bar-col ${isToday ? 'today' : ''}">
          <div class="r-bar-value">${d.minutes.toFixed(1)}</div>
          <div class="r-bar" style="height:${Math.max(pct, 4)}%"></div>
          <div class="r-bar-label">${label}</div>
        </div>`;
      }).join("") + `</div>`;
      // 掌握度变化
      const masteryEl = el("r-weekly-mastery");
      if (masteryEl) {
        masteryEl.innerHTML = `<div class="r-stats">
          <span>📈 累计已掌握：<b>${data.total_mastered || 0}</b> / ${data.total_tested || 0} 个知识点</span>
        </div>`;
      }
    },
    renderMasteryGrid(data) {
      const grid = el("r-mastery-grid");
      if (!grid) return;
      const subjects = data.subjects || [];
      if (subjects.length === 0) {
        grid.innerHTML = `<p class="r-empty">还没有测评数据，开始学习吧！</p>`;
        return;
      }
      const lvLabel = {0:"未测", 1:"未掌握", 2:"了解", 3:"熟悉", 4:"掌握"};
      const lvClass = {0:"gray", 1:"red", 2:"yellow", 3:"blue", 4:"green"};
      grid.innerHTML = subjects.map(s => `
        <div class="r-subject-group">
          <h4>${esc(s.subject)}</h4>
          <div class="r-topic-grid">
            ${(s.topics || []).map(t => `
              <div class="r-topic-cell ${lvClass[t.level] || 'gray'}" 
                   onclick="UI.goStudy('${esc(t.course_id)}')" title="${esc(t.title)}">
                <div class="rt-label">${lvLabel[t.level] || '未测'}</div>
                <div class="rt-title">${esc(t.title.length > 10 ? t.title.slice(0, 10) + '…' : t.title)}</div>
              </div>
            `).join("")}
          </div>
        </div>
      `).join("");
    },
    renderWeakList(data) {
      const list = el("r-weak-list");
      if (!list) return;
      const areas = data.weak_areas || [];
      if (areas.length === 0) {
        list.innerHTML = `<div class="r-empty" style="color:var(--green)">🎉 没有薄弱项！所有已测评知识点都已掌握。</div>`;
        return;
      }
      list.innerHTML = areas.map(a => `
        <div class="r-weak-item">
          <div class="rw-subject">${esc(a.subject)}</div>
          <div class="rw-title">${esc(a.title)}</div>
          <div class="rw-status ${a.level <= 1 ? 'bad' : ''}">${esc(a.label)}</div>
          <button class="btn tiny ghost" onclick="UI.goStudy('${esc(a.course_id)}')">去学习</button>
        </div>
      `).join("");
    },
    goStudy(courseId) {
      // 跳转到学习页并选中该知识点
      if (!courseId) return;
      state.selectedCourse = { id: courseId, title: courseId };
      this.enterApp("learn");
      setTimeout(() => {
        // 尝试找到课程目录中的对应知识点
        toast("已跳转到学习页，请在课程目录中选择该知识点");
      }, 500);
    },

    // ================= 自学页（年级→科目→章节→学习内容） =================
    SS_PROGRESS_KEY: "al_ss_progress",
    openSelfStudy() {
      // 成就：标记进入过自学页
      if (!state._ssVisited) { state._ssVisited = true; this.checkAchievements(); }
      // 📊 进入自学页先与服务端对一次进度（换设备/清缓存后自动恢复）
      this._ssLoadRemoteProgress();
      if (!state._ssTree) {
        if (!state.curriculum) {
          api("GET", "/api/curriculum").then(res => {
            state.curriculum = res.curriculum || res;
            state.curMeta = { region: res.region, textbook: res.textbook, standard: res.standard };
            this._ssInitTree();
            this._applySSResumeIfAny();
          }).catch(e => toast(e.message));
        } else {
          this._ssInitTree();
          this._applySSResumeIfAny();
        }
      } else if (!state._ssSeqMode) {
        // 非连续学习模式下，每次进入自学页都重置目录视图，防止学段下拉被隐藏
        this._ssInitTree();
        this._applySSResumeIfAny();
      } else {
        this._ssRenderProgressMini();
      }
    },
    _applySSResumeIfAny() {
      const r = state._pendingResume;
      if (!r || !r.ss || r.prec) return;      // 精准学的断点由精准学页面处理
      state._pendingResume = null;
      this.applyPendingResumeSS(r);
    },
    applyPendingResumeSS(r) {
      const ss = r && r.ss;
      if (!ss || !ss.cid) return;
      if (ss.seq && ss.seq.name) {
        this.ssStartSeq(ss.seq.name);
        const idx = ss.seq.idx || 0;
        if (idx > 0) this.loadSSSeqLesson(idx);
        toast("已回到上次学到的地方 📚");
        return;
      }
      const setSel = (id, val, cb) => {
        const e2 = el(id);
        if (e2 && val && [...e2.options].some(o => o.value === val)) { e2.value = val; if (cb) cb.call(this); }
      };
      setSel("ss-stage", ss.stage, this.onSSStage);
      setSel("ss-grade", ss.grade, this.onSSGrade);
      setSel("ss-subject", ss.subject, this.onSSSubject);
      const c = el("ss-chapter");
      if (c && [...c.options].some(o => o.value === ss.cid)) {
        c.value = ss.cid; this.onSSChapter();
        toast("已回到上次学到的地方 📚");
      } else {
        this.loadSSLesson(ss.cid);
        toast("已回到上次学到的地方 📚");
      }
    },
    _ssInitTree() {
      // 防御：连续学习模式可能给 .ss-field 打了 display:none；重新进入目录时务必恢复
      document.querySelectorAll(".ss-field").forEach(e => e.style.display = "");
      for (const st of state.curriculum)
        for (const subj of st.subjects)
          for (const g of subj.grades)
            for (const t of g.topics)
              if (!t.lang) t.lang = subj.lang || "zh";
      state._ssTree = state.curriculum;
      const stageSel = el("ss-stage");
      // 「拓展与素养」只通过顶部卡片进入连续学习，不出现在学段下拉里
      const stageList = (state._ssTree || []).filter(st => st && st.stage !== "拓展与素养");
      state._ssStageList = stageList;
      if (!stageList.length) {
        console.error("[ssInitTree] 未找到除拓展与素养外的学段数据", state._ssTree);
        if (stageSel) stageSel.innerHTML = `<option value="">未找到学段数据</option>`;
        state._ssStage = "";
        this._ssRenderExtra();
        this._ssRenderProgressMini();
        return;
      }
      stageSel.innerHTML = stageList.map(st => `<option value="${esc(st.stage)}">${esc(st.stage)}</option>`).join("");
      state._ssStage = stageList[0].stage;
      stageSel.value = state._ssStage;
      this._ssRenderExtra();
      this.onSSStage();
      this._ssRenderProgressMini();
    },
    _ssRenderExtra() {
      const box = el("ss-extra-cards");
      if (!box) return;
      const st = this._ssStageObj("拓展与素养");
      if (!st) { box.innerHTML = ""; return; }
      const icons = { "中医": "🌿", "Python编程": "🐍", "记忆方法": "🧠", "英语学习方法": "🔤", "珠心算": "🧮", "象棋": "♟️", "围棋": "⚫", "军棋": "🎖️", "网络安全": "🛡️" };
      box.innerHTML = st.subjects.map(s => {
        const nCh = s.grades.reduce((a, g) => a + ((g.topics && g.topics.length) || 0), 0);
        const nG = s.grades.length;
        return `<button class="ss-extra-card" onclick="UI.ssJumpExtra('${esc(s.name)}')">
          <span class="ss-extra-ico">${icons[s.name] || "📌"}</span>
          <span class="ss-extra-name">${esc(s.name)}</span>
          <span class="ss-extra-meta">${nG} 篇 · ${nCh} 章</span>
        </button>`;
      }).join("");
    },
    ssJumpExtra(name) {
      this.ssStartSeq(name);
    },
    // 连续学习模式：点拓展与素养卡片后，按序拼接该学科全部章节，从头学到尾，无需选年级/章节
    ssStartSeq(name) {
      const st = this._ssStageObj("拓展与素养");
      if (!st) return toast("找不到拓展与素养模块");
      const subj = st.subjects.find(s => s.name === name);
      if (!subj) return toast("找不到该模块：" + name);
      const seq = [];
      for (const g of subj.grades) {
        for (const t of (g.topics || [])) {
          seq.push({ id: t.id, title: t.title, grade: g.grade });
        }
      }
      if (!seq.length) return toast("「" + name + "」暂无可学章节");
      state._ssSeq = seq;
      state._ssSeqName = name;
      state._ssSeqMode = true;
      document.querySelectorAll(".ss-field").forEach(e => e.style.display = "none");
      const back = el("ss-seq-back"); if (back) back.style.display = "";
      const bar = el("ss-seq-bar"); if (bar) bar.style.display = "flex";
      this.loadSSSeqLesson(0);
    },
    async loadSSSeqLesson(idx) {
      const seq = state._ssSeq;
      if (!seq || idx < 0 || idx >= seq.length) return;
      state._ssSeqIdx = idx;
      const item = seq[idx];
      state._ssChapterId = item.id;
      el("ss-content").innerHTML = `<div class="ss-empty">⏳ 正在加载本章节学习内容…</div>`;
      this._ssRenderStatusBtn();
      el("ss-notes").style.display = "none";
      el("ss-ai").style.display = "none";
      el("ss-quiz").style.display = "none";
      el("ss-quiz-btn").textContent = "📝 测验";
      const label = el("ss-seq-label");
      if (label) label.textContent = `📚 ${state._ssSeqName} · 第 ${idx + 1}/${seq.length} 章`;
      const prog = el("ss-seq-progress");
      if (prog) prog.style.width = Math.round((idx + 1) / seq.length * 100) + "%";
      try {
        const L = await api("GET", "/api/lesson?course_id=" + encodeURIComponent(item.id));
        state._ssLesson = L;
        el("ss-crumb").textContent = `${L.stage} · ${item.grade} · ${esc(L.subject)} · ${esc(L.title)}`;
        this._ssRenderStatusBtn();
        this.renderSSLesson(L);
        this._ssLoadNote();
        state._lastView = "selfstudy";
        this.saveResumeSoon();
        el("ss-prev").disabled = idx <= 0;
        el("ss-next").disabled = idx >= seq.length - 1;
        if (idx === seq.length - 1) {
          const done = document.createElement("div");
          done.className = "ss-seq-done";
          done.innerHTML = `<div class="ss-seq-done-card">🎉 <b>「${esc(state._ssSeqName)}」全部学完啦！</b>` +
            `<div class="ss-seq-done-tip">你已学完所有 ${seq.length} 章。可以复习薄弱环节、做测验，或点「📚 返回目录」换一个模块继续。</div>` +
            `<button class="btn small" onclick="UI.ssExitSeq()">📚 返回目录</button></div>`;
          el("ss-content").appendChild(done);
        }
      } catch (e) {
        el("ss-content").innerHTML = `<div class="ss-empty">加载失败：${esc(e.message)}</div>`;
      }
    },
    ssExitSeq() {
      state._ssSeqMode = false;
      state._ssSeq = [];
      document.querySelectorAll(".ss-field").forEach(e => e.style.display = "");
      const back = el("ss-seq-back"); if (back) back.style.display = "none";
      const bar = el("ss-seq-bar"); if (bar) bar.style.display = "none";
      const label = el("ss-seq-label"); if (label) label.textContent = "";
      const prog = el("ss-seq-progress"); if (prog) prog.style.width = "0%";
      el("ss-prev").disabled = true;
      el("ss-next").disabled = true;
      // 重新初始化学段下拉，防止连续学习后学段选择器未恢复
      this._ssInitTree();
      el("ss-crumb").textContent = "未选择章节";
      el("ss-content").innerHTML = `<div class="ss-empty">👈 在左侧点一张「拓展与素养」卡片，即可从头到尾连续学习；也可在上方用「学段 → 年级 → 科目 → 章节」精确定位。</div>`;
    },
    _ssStageObj(stage) { return state._ssTree.find(s => s.stage === stage); },
    _ssGradesOf(stage) {
      const set = [];
      const st = this._ssStageObj(stage);
      if (!st) return set;
      for (const subj of st.subjects)
        for (const g of subj.grades)
          if (!set.includes(g.grade)) set.push(g.grade);
      return set;
    },
    _ssSubjectsOf(stage, grade) {
      const st = this._ssStageObj(stage);
      if (!st) return [];
      return st.subjects.filter(subj => (subj.grades || []).some(g => g.grade === grade));
    },
    _ssChaptersOf(stage, grade, subject) {
      const st = this._ssStageObj(stage);
      if (!st) return [];
      const subj = st.subjects.find(s => s.name === subject);
      if (!subj) return [];
      const g = (subj.grades || []).find(x => x.grade === grade);
      return (g && g.topics) || [];
    },
    onSSStage() {
      state._ssStage = el("ss-stage").value;
      const grades = this._ssGradesOf(state._ssStage);
      const gSel = el("ss-grade");
      gSel.innerHTML = grades.map(g => `<option value="${esc(g)}">${esc(g)}</option>`).join("");
      state._ssGrade = grades[0];
      if (grades[0]) gSel.value = grades[0];
      this.onSSGrade();
    },
    onSSGrade() {
      state._ssGrade = el("ss-grade").value;
      const subs = this._ssSubjectsOf(state._ssStage, state._ssGrade);
      const sSel = el("ss-subject");
      sSel.innerHTML = subs.map(s => `<option value="${esc(s.name)}">${esc(s.name)}</option>`).join("");
      state._ssSubject = subs[0] && subs[0].name;
      if (subs[0]) sSel.value = subs[0].name;
      this.onSSSubject();
    },
    onSSSubject() {
      state._ssSubject = el("ss-subject").value;
      const chs = this._ssChaptersOf(state._ssStage, state._ssGrade, state._ssSubject);
      const cSel = el("ss-chapter");
      cSel.innerHTML = chs.map(c => `<option value="${esc(c.id)}">${esc(c.title)}</option>`).join("");
      if (chs[0]) { cSel.value = chs[0].id; this.onSSChapter(); }
      else { el("ss-content").innerHTML = `<div class="ss-empty">该科目此年级暂无章节</div>`; }
    },
    onSSChapter() {
      const id = el("ss-chapter").value;
      if (id) this.loadSSLesson(id);
    },
    ssResetSelectors() {
      if (state._ssSeqMode) { this.ssExitSeq(); return; }
      const list = state._ssStageList || state._ssTree || [];
      if (list.length) { state._ssStage = list[0].stage; el("ss-stage").value = state._ssStage; this.onSSStage(); }
    },
    // ---- 进度（服务端主库 + localStorage 离线缓存，按账号隔离） ----
    // 原来只写 localStorage：换设备 / 清缓存 / 切孩子 / 换浏览器都会「进度归零」。
    // 现在每次写都双写：本地立即可用（离线也行），随后同步到 /api/study/records。
    _ssLoadProgress() {
      try { return JSON.parse(localStorage.getItem(this.SS_PROGRESS_KEY) || "{}"); }
      catch (e) { return {}; }
    },
    _ssSaveProgress(map) {
      try { localStorage.setItem(this.SS_PROGRESS_KEY, JSON.stringify(map)); } catch (e) {}
      this._ssSyncProgress(map);
    },
    // 推送到服务端（失败静默：离线时本地照常可用，联网后再补传）
    _ssSyncProgress(map) {
      if (!state.token) { state._ssPendingSync = true; return; }
      clearTimeout(this._ssSyncTimer);
      this._ssSyncTimer = setTimeout(() => {
        api("POST", "/api/study/records", { records: map })
          .then(() => { state._ssPendingSync = false; })
          .catch(() => { state._ssPendingSync = true; });
      }, 400);
    },
    // 登录后 / 进自学页前：把服务端记录合并回本地（取 status 大者）
    async _ssLoadRemoteProgress() {
      if (!state.token) return false;
      try {
        const r = await api("GET", "/api/study/records");
        const remote = (r && r.records) || {};
        const local = this._ssLoadProgress();
        let changed = false;
        for (const cid of Object.keys(remote)) {
          const rs = (remote[cid] && remote[cid].status) || 0;
          const ls = (local[cid] && local[cid].status) || 0;
          if (rs > ls) {
            local[cid] = Object.assign({}, local[cid], { status: rs, ts: remote[cid].ts });
            changed = true;
          }
        }
        if (changed) {
          try { localStorage.setItem(this.SS_PROGRESS_KEY, JSON.stringify(local)); } catch (e) {}
        }
        // 本地有、服务端没有的（离线期间学的）→ 补传
        if (state._ssPendingSync) this._ssSyncProgress(local);
        // 阅读进度（story: 前缀）也一并还原
        try {
          let sm = {};
          try { sm = JSON.parse(localStorage.getItem("al_stories_v1") || "{}"); } catch (e) {}
          let sChanged = false;
          for (const key of Object.keys(remote)) {
            if (key.indexOf("story:") !== 0) continue;
            const sid = key.slice(6);
            const rs = (remote[key] && remote[key].status) || 0;
            const cur = (sm[sid] && sm[sid].done) ? 2 : ((sm[sid] && sm[sid].read) ? 1 : 0);
            if (rs > cur) { sm[sid] = Object.assign({}, sm[sid], { read: true, done: rs >= 2 }); sChanged = true; }
          }
          if (sChanged) localStorage.setItem("al_stories_v1", JSON.stringify(sm));
        } catch (e) {}
        if (changed) { this._ssRenderProgressMini(); this._ssRenderStatusBtn(); }
        return changed;
      } catch (e) { return false; }
    },
    _ssStatus(id) { const m = this._ssLoadProgress(); return (m[id] && m[id].status) || 0; },
    _ssStatusLabel(s) { return [["○ 未学", ""], ["✓ 已学", "ss-st-done"], ["⭐ 已掌握", "ss-st-master"]][s] || ["○ 未学", ""]; },
    _ssRenderStatusBtn() {
      const btn = el("ss-status-btn");
      if (!btn) return;
      const id = state._ssChapterId;
      const s = id ? this._ssStatus(id) : 0;
      const [txt, cls] = this._ssStatusLabel(s);
      btn.textContent = txt;
      btn.className = "btn small ghost " + cls;
    },
    ssCycleStatus() {
      const id = state._ssChapterId; if (!id) return;
      const map = this._ssLoadProgress();
      const cur = (map[id] && map[id].status) || 0;
      const next = (cur + 1) % 3;
      map[id] = Object.assign({}, map[id], { status: next, ts: Date.now() });
      this._ssSaveProgress(map);
      this._ssRenderStatusBtn();
      this._ssRenderProgressMini();
      toast(["已标记为：未学", "已标记为：已学 ✓", "已标记为：已掌握 ⭐"][next]);
      // 成就点：每学一个知识点即时发星
      if (next === 1 && cur === 0) {
        this.awardStars("selfstudy_learned", 2);
        this._ssXpToast("📖 学习完成", "+2 ⭐ 成就点");
        try { if (window.AL_GAMIFY) window.AL_GAMIFY.track("learned"); } catch (e) {}
      } else if (next === 2) {
        const pts = cur === 0 ? 7 : 5;   // 0→2 直接掌握：学习+掌握；1→2 掌握
        this.awardStars("selfstudy_mastered", pts);
        this._ssXpToast("🌟 知识掌握", "+" + pts + " ⭐ 成就点");
        try { if (window.AL_GAMIFY) { window.AL_GAMIFY.track("learned"); if (cur === 0) window.AL_GAMIFY.track("lessons"); } } catch (e) {}
      }
      this.checkAchievements();
    },
    _ssXpToast(title, sub) {
      // 居中弹出成就点动画，2.2 秒后自动消失
      const old = document.getElementById("ss-xp-toast");
      if (old) old.remove();
      const d = document.createElement("div");
      d.id = "ss-xp-toast";
      d.innerHTML = `<div class="ssxp-title">${esc(title)}</div><div class="ssxp-sub">${esc(sub)}</div>`;
      document.body.appendChild(d);
      setTimeout(() => { d.classList.add("out"); setTimeout(() => d.remove(), 350); }, 2200);
    },
    _ssRenderProgressMini() {
      const box = el("ss-progress-mini");
      if (!box || !state._ssTree) return;
      const map = this._ssLoadProgress();
      let total = 0, done = 0, master = 0;
      for (const st of state._ssTree)
        for (const subj of st.subjects)
          for (const g of subj.grades)
            for (const t of g.topics) {
              total++;
              const s = (map[t.id] && map[t.id].status) || 0;
              if (s >= 1) done++;
              if (s >= 2) master++;
            }
      const pct = total ? Math.round(done / total * 100) : 0;
      const learnedToday = this._ssTodayLearnedCount();
      box.innerHTML = `<div class="ss-pm-row">📊 自学进度 ${learnedToday ? `<span class="ss-pm-xp">今日已学 ${learnedToday} 节 ⭐</span>` : ""}</div>` +
        `<div class="ss-pm-bar"><span style="width:${pct}%"></span></div>` +
        `<div class="ss-pm-stat">已学 ${done} · 已掌握 ${master} / 共 ${total} 节</div>`;
    },
    _ssTodayLearnedCount() {
      const map = this._ssLoadProgress();
      const today = new Date().toISOString().slice(0, 10);
      return Object.values(map).filter(v => (v.status || 0) >= 1 && (v.ts || 0) && new Date(v.ts).toISOString().slice(0, 10) === today).length;
    },
    // ---- 加载与渲染章节内容 ----
    async loadSSLesson(id) {
      state._ssChapterId = id;
      el("ss-content").innerHTML = `<div class="ss-empty">⏳ 正在加载本章节学习内容…</div>`;
      this._ssRenderStatusBtn();
      el("ss-notes").style.display = "none";
      el("ss-ai").style.display = "none";
      el("ss-quiz").style.display = "none";
      el("ss-quiz-btn").textContent = "📝 测验";
      try {
        const L = await api("GET", "/api/lesson?course_id=" + encodeURIComponent(id));
        state._ssLesson = L;
        el("ss-crumb").textContent = `${L.stage} · ${L.grade} · ${L.subject} · ${L.title}`;
        this._ssUpdateNav();
        this._ssRenderStatusBtn();
        this.renderSSLesson(L);
        this._ssLoadNote();
      } catch (e) {
        el("ss-content").innerHTML = `<div class="ss-empty">加载失败：${esc(e.message)}</div>`;
      }
    },
    _ssChapterList() { return this._ssChaptersOf(state._ssStage, state._ssGrade, state._ssSubject); },
    _ssUpdateNav() {
      const list = this._ssChapterList();
      const idx = list.findIndex(c => c.id === state._ssChapterId);
      state._ssChapterIdx = idx;
      el("ss-prev").disabled = idx <= 0;
      el("ss-next").disabled = idx < 0 || idx >= list.length - 1;
    },
    ssPrev() {
      if (state._ssSeqMode) {
        const i = state._ssSeqIdx || 0;
        if (i > 0) this.loadSSSeqLesson(i - 1);
      } else {
        const list = this._ssChapterList(); const i = state._ssChapterIdx;
        if (i > 0) { el("ss-chapter").value = list[i - 1].id; this.onSSChapter(); }
      }
    },
    ssNext() {
      if (state._ssSeqMode) {
        const seq = state._ssSeq; const i = state._ssSeqIdx || 0;
        if (seq && i < seq.length - 1) this.loadSSSeqLesson(i + 1);
      } else {
        const list = this._ssChapterList(); const i = state._ssChapterIdx;
        if (i >= 0 && i < list.length - 1) { el("ss-chapter").value = list[i + 1].id; this.onSSChapter(); }
      }
    },
    renderSSLesson(L) {
      let html = "";
      html += `<div class="ss-lesson-head"><h2>${esc(L.title)}</h2><div class="ss-lesson-meta">${esc(L.stage)} · ${esc(L.grade)} · ${esc(L.subject)}${L.lang === 'en' ? ' · 英语' : ''}</div></div>`;
      if (L.goals) html += `<div class="lesson-goals"><b>🎯 学习目标</b><div>${esc(L.goals)}</div></div>`;
      html += `<div class="lesson-sections">`;
      (L.sections || []).forEach(s => {
        html += `<div class="lesson-sec">
          <div class="ls-h"><span class="ls-no">${s.no}</span>${esc(s.heading)}</div>
          <div class="ls-body">${renderBody(s.body)}</div>
          ${s.tip ? `<div class="ls-tip">💡 ${esc(s.tip)}</div>` : ""}
        </div>`;
      });
      html += `</div>`;
      if (L.mistakes && L.mistakes.length) {
        html += `<div class="lesson-mistakes"><b>📌 易错提醒</b><ul>` + L.mistakes.map(m => `<li>${esc(m)}</li>`).join("") + `</ul></div>`;
      }
      if (L.selfcheck && L.selfcheck.length) {
        html += `<div class="lesson-selfcheck"><b>🧠 想一想（自测）</b><ul>` + L.selfcheck.map(q => `<li>${esc(q)}</li>`).join("") + `</ul></div>`;
      }
      if (L.summary) html += `<div class="lesson-summary">📝 ${esc(L.summary)}</div>`;
      el("ss-content").innerHTML = html;
      renderMath(el("ss-content"));
    },
    ssSpeakAll() {
      const L = state._ssLesson; if (!L) return toast("还没有可朗读的内容");
      let txt = L.title + "。" + (L.goals || "") + "。";
      (L.sections || []).forEach(s => { txt += s.heading + "。" + (s.body || "") + "。"; });
      (L.selfcheck || []).forEach(q => { txt += "想一想：" + q + "。"; });
      txt += (L.summary || "");
      txt = txt.replace(/<[^>]+>/g, "").trim();
      if (!txt) return toast("没有可朗读的内容");
      speak(txt);
    },
    // ---- 笔记 ----
    ssToggleNotes() {
      const box = el("ss-notes");
      if (box.style.display === "none") {
        box.style.display = "block";
        this._ssLoadNote();
        const ta = el("ss-notes-area");
        if (ta) ta.focus();
      } else { box.style.display = "none"; }
    },
    _ssLoadNote() {
      const id = state._ssChapterId; if (!id) return;
      const map = this._ssLoadProgress();
      const ta = el("ss-notes-area");
      if (ta) ta.value = (map[id] && map[id].note) || "";
    },
    ssSaveNotes() {
      const id = state._ssChapterId; if (!id) return;
      const ta = el("ss-notes-area"); if (!ta) return;
      const map = this._ssLoadProgress();
      map[id] = Object.assign({}, map[id], { note: ta.value, status: (map[id] && map[id].status) || 0, ts: Date.now() });
      this._ssSaveProgress(map);
    },
    // ---- AI 分步讲解（自学页独立状态） ----
    async ssAIExplain() {
      const L = state._ssLesson; if (!L) return toast("请先选择章节");
      const box = el("ss-ai");
      box.style.display = "block";
      box.innerHTML = `<div class="ss-ai-head">✨ AI 分步讲解 <button class="btn ghost small" onclick="UI.ssSpeakAiAll()">🔊 朗读</button></div><div class="empty">🤖 正在生成分步讲解…</div>`;
      const btn = el("ss-ai-btn");
      if (btn) { btn.disabled = true; btn.textContent = "生成中…"; }
      try {
        const r = await api("POST", "/api/lesson/explain", { course_id: L.id });
        state._ssAiLesson = {
          title: r.title || L.title,
          points: (r.points || []).map(p => ({ key: p.key || "", explain: p.explain || "", example: p.example || "" })),
          summary: r.summary || "",
          mock: !!r.mock, revealed: 1, alts: {}, confirmed: {}, loading: {}
        };
        this.ssRenderAiLesson();
        if (!r.mock) { try { this.ssSpeakAiPoint(0); } catch (e) {} }
      } catch (e) {
        const msg = (e && e.message) || String(e);
        box.innerHTML = /401|未登录/.test(msg)
          ? `<div class="empty">⚠️ 请先登录后再用 AI 讲解（右上角「登录」）。</div>`
          : `<div class="empty">生成失败：${esc(msg)}</div>`;
        if (!state.token) toast("请先登录后再使用 AI 深度讲解");
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "✨ 重讲"; }
      }
    },
    ssRenderAiLesson() {
      const a = state._ssAiLesson; const box = el("ss-ai");
      if (!a || !a.points || !a.points.length) { box.style.display = "none"; return; }
      box.style.display = "block";
      const note = a.mock
        ? `<div class="lesson-ai-note">ℹ️ 演示模式：讲解由讲义生成。填入 Key 并关闭演示模式可获 AI 原创分步讲解与换讲法。</div>`
        : `<div class="lesson-ai-note ok">✅ 由 AI 老师（真实模型）现场撰写，每讲完一个要点会让你确认是否学会。</div>`;
      let html = `<div class="ss-ai-head">✨ AI 分步讲解（${a.mock ? "演示模式" : "真实 AI"}） <button class="btn ghost small" onclick="UI.ssSpeakAiAll()">🔊 朗读</button></div>` + note;
      html += `<div class="ai-progress">进度：已学 ${Object.keys(a.confirmed).filter(k => a.confirmed[k]).length} / ${a.points.length} 个要点</div>`;
      a.points.forEach((p, i) => {
        if (i >= a.revealed) return;
        html += `<div class="ai-point">`;
        html += `<div class="ap-key">📍 要点 ${i + 1}：${esc(p.key)} <button class="btn ghost tiny" onclick="UI.ssSpeakAiPoint(${i})" title="朗读这个要点">🔊</button></div>`;
        html += `<div class="ap-explain"><b>讲解：</b>${nl2br(esc(p.explain))}</div>`;
        if (p.example) html += `<div class="ap-example"><b>例题：</b>${nl2br(esc(p.example))}</div>`;
        (a.alts[i] || []).forEach((alt, k) => {
          html += `<div class="ap-alt"><b>💡 换种讲法 ${k + 1}：</b>${nl2br(esc(alt.explain))}`;
          if (alt.example) html += `<div class="ap-example">例题：${nl2br(esc(alt.example))}</div>`;
          html += `</div>`;
        });
        if (a.confirmed[i]) html += `<div class="ap-done">✅ 这个要点你已学会</div>`;
        else if (a.loading[i]) html += `<div class="ap-loading">🔄 老师正在换一种讲法…</div>`;
        else html += `<div class="ap-confirm"><button class="btn small ok" onclick="UI.ssConfirmPoint(${i},true)">✅ 我学会了</button><button class="btn small warn" onclick="UI.ssConfirmPoint(${i},false)">❌ 没听懂，换种讲法</button></div>`;
        html += `</div>`;
      });
      if (a.revealed < a.points.length) html += `<div class="ap-more"><button class="btn small" onclick="UI.ssRevealNext()">下一个要点 →</button></div>`;
      if (a.revealed >= a.points.length && a.summary) html += `<div class="ai-summary">📝 ${nl2br(esc(a.summary))}</div>`;
      box.innerHTML = html;
    },
    ssRevealNext() {
      const a = state._ssAiLesson; if (!a) return;
      if (a.revealed < a.points.length) {
        a.revealed++; this.ssRenderAiLesson();
        if (!a.mock) { try { this.ssSpeakAiPoint(a.revealed - 1); } catch (e) {} }
      }
    },
    ssConfirmPoint(i, ok) {
      const a = state._ssAiLesson; if (!a) return;
      if (ok) { a.confirmed[i] = true; this.ssRenderAiLesson(); }
      else {
        a.loading[i] = true; this.ssRenderAiLesson();
        const L = state._ssLesson;
        api("POST", "/api/lesson/reexplain", { course_id: L.id, key: a.points[i].key, explain: a.points[i].explain, example: a.points[i].example, lang: L.lang })
          .then(r => {
            a.alts[i] = (a.alts[i] || []).concat([{ explain: r.explain || "", example: r.example || "" }]);
            a.loading[i] = false; this.ssRenderAiLesson();
            if (!r.mock) { try { this.ssSpeakAiPoint(i); } catch (e) {} }
          })
          .catch(e => { a.loading[i] = false; this.ssRenderAiLesson(); toast("换讲法失败：" + e.message); });
      }
    },
    ssSpeakAiPoint(i) {
      const a = state._ssAiLesson; if (!a || !a.points || !a.points[i]) return;
      const p = a.points[i];
      let t = (p.key ? ("要点" + (i + 1) + "，" + p.key + "。 ") : "") + (p.explain || "");
      (a.alts[i] || []).forEach((alt, k) => { t += " 换种讲法" + (k + 1) + "：" + (alt.explain || ""); if (alt.example) t += " 例题：" + alt.example; });
      if (p.example) t += " 例题：" + p.example;
      speak(t);
    },
    ssSpeakAiAll() {
      const a = state._ssAiLesson; if (!a || !a.points || !a.points.length) return toast("还没有 AI 讲解");
      let t = (a.title ? a.title + "。 " : "");
      a.points.forEach((p, i) => {
        if (i >= a.revealed) return;
        t += "要点" + (i + 1) + "，" + (p.key || "") + "。" + (p.explain || "");
        (a.alts[i] || []).forEach((alt, k) => { t += " 换种讲法" + (k + 1) + "：" + (alt.explain || ""); if (alt.example) t += " 例题：" + alt.example; });
        if (p.example) t += " 例题：" + p.example;
      });
      if (a.summary && a.revealed >= a.points.length) t += " 总结：" + a.summary;
      speak(t);
    },
    // ---- 自主测验与纠错 ----
    ssToggleQuiz() {
      const box = el("ss-quiz");
      if (box.style.display === "none") {
        this.ssRenderQuiz();
        box.style.display = "block";
        el("ss-quiz-btn").textContent = "📝 收起测验";
      } else {
        box.style.display = "none";
        el("ss-quiz-btn").textContent = "📝 测验";
      }
    },
    ssRenderQuiz() {
      const L = state._ssLesson; const box = el("ss-quiz");
      if (!L) { box.innerHTML = `<div class="ss-empty">请先选择章节</div>`; return; }
      const quiz = L.quiz || [];
      if (!quiz.length) { box.innerHTML = `<div class="ss-empty">本章暂无测验题，可用上方「想一想」自测。</div>`; return; }
      state._ssQuiz = quiz.map(q => Object.assign({}, q, { chosen: null, correct: null }));
      box.innerHTML = `<div class="ss-quiz-head">📝 自主测验（${quiz.length} 题）· 答完看对错与解析 <button class="btn small ghost" onclick="UI.ssQuizRedo()">🔄 重做</button></div><div id="ss-quiz-list"></div><div id="ss-quiz-result" class="ss-quiz-result"></div>`;
      this._ssRenderQuizList();
    },
    _ssRenderQuizList() {
      const list = el("ss-quiz-list"); if (!list) return;
      list.innerHTML = state._ssQuiz.map((q, qi) => {
        let body = "";
        if (q.type === "choice" && q.options && q.options.length) {
          body = `<div class="q-opts">` + q.options.map((o, oi) => {
            const cls = q.chosen === null ? "" : (oi === q.answer ? " right" : (oi === q.chosen ? " wrong" : ""));
            const letters = ["A", "B", "C", "D", "E", "F", "G", "H"];
            const prefix = letters[oi] ? `<b class="q-opt-lbl">${letters[oi]}.</b> ` : "";
            const txt = esc(o).replace(/^[A-H][\.．、:]\s*/, "");
            return `<label class="q-opt ${cls}"><input type="radio" name="ssq-${qi}" value="${oi}" ${q.chosen === oi ? "checked" : ""} onclick="UI.ssQuizAnswer(${qi},${oi})"><span class="q-opt-txt">${prefix}${txt}</span></label>`;
          }).join("") + `</div>`;
        } else if (q.type === "open") {
          body = `<div class="q-open">（开放式思考题：写下你的理解即可，不计分）<br><textarea class="q-open-area" placeholder="我的理解……" oninput="UI.ssQuizAnswerText(${qi}, this.value)">${esc(q.chosen || "")}</textarea></div>`;
        } else {
          body = `<div class="q-input"><input type="text" id="ssq-in-${qi}" placeholder="输入你的答案" value="${esc(q.chosen || "")}" onchange="UI.ssQuizAnswerText(${qi}, this.value)"><button class="btn tiny" onclick="UI.ssQuizCheckText(${qi})">检查</button></div>`;
        }
        const fb = q.correct === null ? "" : (q.correct
          ? `<div class="q-fb ok">✅ 答对了！</div>`
          : `<div class="q-fb bad">❌ 正确答案：${esc(this._ssAnswerText(q))}<br>解析：${esc(q.explanation || "")}</div>`);
        return `<div class="q-item"><div class="q-stem">${qi + 1}. ${esc(q.stem)}</div>${body}${fb}</div>`;
      }).join("");
    },
    _ssAnswerText(q) { if (q.type === "choice") return (q.options && q.options[q.answer]) || ""; return q.answer || ""; },
    // 答题统一反馈：音效 + 连击 + 每日任务埋点
    _ssOnAnswer(correct) {
      try {
        if (correct) {
          state._ssComboN = (state._ssComboN || 0) + 1;
          if (window.AL_GAMIFY) window.AL_GAMIFY.track("quizCorrect");
          if (state._ssComboN >= 3) {
            _SFX.play("combo");
            this._ssComboFx(state._ssComboN);
          } else {
            _SFX.play("correct");
          }
        } else {
          state._ssComboN = 0;
          _SFX.play("wrong");
        }
      } catch (e) {}
    },
    // 连击动画：显示 xN 连击浮标
    _ssComboFx(n) {
      const old = document.getElementById("ss-combo-fx");
      if (old) old.remove();
      const d = document.createElement("div");
      d.id = "ss-combo-fx";
      d.className = "ss-combo-fx";
      d.textContent = "🔥 " + n + " 连对！";
      document.body.appendChild(d);
      setTimeout(() => d.remove(), 1200);
    },
    ssQuizAnswer(qi, oi) {
      const q = state._ssQuiz[qi]; if (!q || q.correct !== null) return;
      q.chosen = oi; q.correct = (oi === q.answer);
      this._ssOnAnswer(q.correct);
      this._ssRenderQuizList(); this._ssQuizScore();
    },
    ssQuizAnswerText(qi, val) { const q = state._ssQuiz[qi]; if (q) q.chosen = val; },
    ssQuizCheckText(qi) {
      const q = state._ssQuiz[qi]; if (!q || q.correct !== null) return;
      const ans = ("" + (q.answer || "")).trim().toLowerCase();
      const given = ("" + (q.chosen || "")).trim().toLowerCase();
      q.correct = !!(ans && given && (given === ans || given.indexOf(ans) >= 0 || ans.indexOf(given) >= 0));
      this._ssOnAnswer(q.correct);
      this._ssRenderQuizList(); this._ssQuizScore();
    },
    _ssQuizScore() {
      const graded = state._ssQuiz.filter(q => q.type !== "open");
      const done = graded.filter(q => q.correct !== null);
      const right = done.filter(q => q.correct).length;
      const res = el("ss-quiz-result");
      if (!res) return;
      if (graded.length === 0) { res.innerHTML = `本章为开放式思考题，写下理解即可，无需评分。`; return; }
      if (done.length < graded.length) { res.innerHTML = `已答 ${done.length} / ${graded.length} 题，对 ${right} 题`; return; }
      const pct = Math.round(right / graded.length * 100);
      res.innerHTML = `🎯 测验完成：正确 ${right} / ${graded.length}（${pct}%）` +
        (pct >= 80 ? ` <b class="ok">很棒，掌握得不错！</b>` : ` <b class="bad">再复习一下薄弱点吧。</b>`);
      if (pct === 100) { state._ssQuizPerfect = true; this.checkAchievements(); }
      if (pct >= 60) {
        try { if (window.AL_GAMIFY) window.AL_GAMIFY.track("lessons"); } catch (e) {}
        if (pct >= 80) _SFX.play("claim");
      }
      if (pct >= 80 && state._ssChapterId) {
        const map = this._ssLoadProgress();
        const cur = (map[state._ssChapterId] && map[state._ssChapterId].status) || 0;
        if (cur < 2) {
          map[state._ssChapterId] = Object.assign({}, map[state._ssChapterId], { status: 2, ts: Date.now() });
          this._ssSaveProgress(map); this._ssRenderStatusBtn(); this._ssRenderProgressMini();
          const pts = cur === 0 ? 7 : 5;
          this.awardStars("selfstudy_mastered", pts);
          this._ssXpToast("🎉 测验全对·掌握本章", "+" + pts + " ⭐ 成就点");
          this.checkAchievements();
        }
      }
    },
    ssQuizRedo() {
      if (state._ssQuiz) state._ssQuiz = state._ssQuiz.map(q => Object.assign({}, q, { chosen: null, correct: null }));
      this._ssRenderQuizList();
      const r = el("ss-quiz-result"); if (r) r.innerHTML = "";
    },

    // ---------- 🔇 沉默检测 ----------
    _silenceTimer: null,
    _silenceHintShown: false,
    _lastUserMsgTime: 0,
    startSilenceMonitor() {
      this.stopSilenceMonitor();
      this._lastUserMsgTime = Date.now();
      this._silenceHintShown = false;
      this._silenceTimer = setInterval(() => {
        if (state.busy || state.testMode || !state.sessionId) return;
        if (el("speech-panel") && el("speech-panel").style.display !== "none") return;
        const elapsed = (Date.now() - this._lastUserMsgTime) / 1000;
        if (elapsed > 12 && !this._silenceHintShown) {
          this._silenceHintShown = true;
          const hints = [
            "💡 是不是有点卡住啦？试着说说你的想法",
            "💡 不用着急，想到什么就说什么",
            "💡 需要我提示一下吗？你可以问「给个提示」",
            "💡 试试用自己的话把问题说一遍",
          ];
          const hint = hints[Math.floor(Math.random() * hints.length)];
          appendBubble("bot", hint, false);
          scrollChat();
        }
      }, 3000);
    },
    stopSilenceMonitor() {
      if (this._silenceTimer) {
        clearInterval(this._silenceTimer);
        this._silenceTimer = null;
      }
      this._silenceHintShown = false;
    },
    // ---------- 🗣️ 英语口语练习 ----------
    async startSpeech() {
      if (!state.selectedCourse) return toast("请先在「📚 浏览课程目录」中选择一个英语知识点");
      const rid = state.currentRole && state.currentRole.id;
      if (!rid) return toast("请先选择一个学习角色（推荐 Emma 老师）");
      if (state.currentRole && state.currentRole.lang !== "en") {
        toast("💡 英语口语练习建议选择 Emma 老师（英语外教）");
      }
      state.speechSentences = [];
      state.speechIdx = 0;
      state.speechResults = [];
      // 隐藏聊天
      el("chat-log").style.display = "none";
      el("composer").style.display = "none";
      el("test-panel").style.display = "none";
      el("assess-banner").style.display = "none";
      const panel = el("speech-panel");
      panel.style.display = "flex";
      el("speech-progress").textContent = "准备中…";
      el("speech-body").innerHTML = `<div class="speech-sentence">🔄 正在生成跟读句子…</div>`;
      try {
        const r = await api("POST", "/api/speech/practice", {
          course_id: state.selectedCourse.id,
          count: 5, lang: "en"
        });
        state.speechSentences = r.sentences || [];
        if (state.speechSentences.length === 0) {
          el("speech-body").innerHTML = `<div class="speech-sentence">暂无跟读句子</div>`;
          return;
        }
        this.showSpeechSentence(0);
      } catch (e) {
        el("speech-body").innerHTML = `<div class="speech-sentence">⚠️ ${esc(e.message)}</div>`;
      }
    },
    stopSpeech() {
      state.speechSentences = [];
      state.speechIdx = 0;
      state.speechResults = [];
      this.stopSpeechRecord();
      el("speech-panel").style.display = "none";
      el("chat-log").style.display = "block";
      el("composer").style.display = "";
    },
    showSpeechSentence(idx) {
      const sentences = state.speechSentences;
      if (idx >= sentences.length) {
        this.showSpeechSummary();
        return;
      }
      state.speechIdx = idx;
      el("speech-progress").textContent = `${idx + 1}/${sentences.length}`;
      el("speech-sentence").textContent = sentences[idx];
      el("speech-result").style.display = "none";
      el("speech-navi").style.display = "none";
      el("speech-footer").style.display = "block";
      const btn = el("speech-record-btn");
      btn.style.display = ""; // 重置显示（可能在总结页被隐藏）
      btn.className = "speech-record-btn";
      btn.disabled = false;
      el("sr-label").textContent = "点击跟读";
      el("speech-hint").textContent = "🎤 点击麦克风按钮，朗读屏幕上显示的英文句子";
    },
    startSpeechRecord() {
      if (state.speechBusy) return;
      state.speechBusy = true;
      state._speechScored = false;
      const btn = el("speech-record-btn");
      btn.className = "speech-record-btn recording";
      el("sr-label").textContent = "🎤 正在听…";
      el("speech-hint").textContent = "🗣️ 大声朗读句子…";

      // 重置语音识别
      if (recognition) {
        try { recognition.abort(); } catch(e) {}
      }
      if (!initSpeech()) {
        el("sr-label").textContent = "不支持语音识别";
        state.speechBusy = false;
        return;
      }
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = false;

      const timeout = setTimeout(() => {
        try { recognition.stop(); } catch(e) {}
      }, 5000);

      recognition.onresult = (e) => {
        clearTimeout(timeout);
        if (state._speechScored) return;
        state._speechScored = true;
        const result = e.results[e.results.length - 1];
        let transcript = (result[0].transcript || "").trim();
        const confidence = result[0].confidence || 0;
        try { recognition.stop(); } catch(e) {}
        this.scoreSpeech(transcript, confidence);
      };
      recognition.onerror = () => {
        clearTimeout(timeout);
        if (state._speechScored) return;
        state._speechScored = true;
        el("sr-label").textContent = "未识别到语音，再试一次";
        btn.className = "speech-record-btn";
        state.speechBusy = false;
      };
      recognition.onend = () => {
        clearTimeout(timeout);
        if (state._speechScored) return;
        state._speechScored = true;
        if (state.speechBusy) {
          this.scoreSpeech("", 0);
        }
      };
      try { recognition.start(); } catch (e) {
        clearTimeout(timeout);
        el("sr-label").textContent = "麦克风启动失败";
        btn.className = "speech-record-btn";
        state.speechBusy = false;
      }
    },
    stopSpeechRecord() {
      if (recognition) { try { recognition.abort(); } catch(e) {} }
      state.speechBusy = false;
    },
    scoreSpeech(transcript, confidence) {
      state.speechBusy = false;
      const btn = el("speech-record-btn");
      btn.className = "speech-record-btn done";
      el("sr-label").textContent = "✅ 完成";

      const expected = state.speechSentences[state.speechIdx] || "";
      const expWords = expected.toLowerCase().replace(/[^\w\s]/g, "").split(/\s+/).filter(Boolean);
      const recWords = transcript.toLowerCase().replace(/[^\w\s]/g, "").split(/\s+/).filter(Boolean);

      // 逐词对比
      const wordsDetail = expWords.map((w, i) => {
        const recW = recWords[i] || "";
        const correct = recW === w;
        return { word: w, recognized: recW, correct, confidence: correct ? (confidence + 0.3) / 2 : confidence / 2 };
      });

      // 后端评分
      api("POST", "/api/speech/evaluate", {
        expected, recognized: transcript, words_detail: wordsDetail
      }).then(res => {
        this.showSpeechResult(res, transcript);
      }).catch(() => {
        // 离线兜底：前端打分
        const matched = wordsDetail.filter(w => w.correct).length;
        const total = expWords.length || 1;
        const wordAcc = matched / total * 100;
        const finalScore = Math.round(wordAcc * 0.7 + confidence * 30);
        const grade = finalScore >= 90 ? "A" : finalScore >= 75 ? "B" : finalScore >= 60 ? "C" : "D";
        this.showSpeechResult({
          score: finalScore, grade, words_detail: wordsDetail,
          feedback: matched < total ? "有些单词发音可以再练练，试试再读一遍" : "读得很好！"
        }, transcript);
      });

      state.speechResults.push({
        sentence: expected,
        transcript,
        score: 0, // filled by callback
      });
    },
    showSpeechResult(res, transcript) {
      const resultBox = el("speech-result");
      resultBox.style.display = "block";
      const words = res.words_detail || [];
      
      // 逐词显示
      const wordsHtml = words.map(w =>
        `<span class="sr-word ${w.correct ? 'ok' : 'bad'}">${esc(w.word)}</span>`
      ).join("");
      
      resultBox.innerHTML = `
        <div class="sr-score">
          <div class="sr-grade ${res.grade}">${res.grade}</div>
          <div class="sr-score-label">评分 · ${res.score} 分</div>
        </div>
        <div class="sr-words">${wordsHtml}</div>
        <div class="sr-feedback">${esc(res.feedback || "")}</div>
      `;

      el("speech-navi").style.display = "flex";
      el("speech-footer").style.display = "none";
      el("speech-hint").textContent = "🔊 绿色=发音准确，红色=需改进";

      // 更新结果
      if (state.speechResults.length > 0) {
        const last = state.speechResults[state.speechResults.length - 1];
        last.score = res.score;
        last.grade = res.grade;
        last.words = words;
      }
    },
    nextSpeechSentence() {
      this.showSpeechSentence(state.speechIdx + 1);
    },
    showSpeechSummary() {
      const results = state.speechResults;
      const total = results.length;
      const avgScore = total > 0 ? Math.round(results.reduce((s, r) => s + (r.score || 0), 0) / total) : 0;
      const gradeCounts = {A:0, B:0, C:0, D:0};
      results.forEach(r => { const g = r.grade || "D"; gradeCounts[g] = (gradeCounts[g] || 0) + 1; });
      const topGrade = Object.entries(gradeCounts).sort((a,b) => b[1] - a[1])[0]?.[0] || "D";
      const avgGrade = avgScore >= 90 ? "A" : avgScore >= 75 ? "B" : avgScore >= 60 ? "C" : "D";

      let rows = results.map((r, i) =>
        `<tr><td>${i + 1}</td><td class="grade-${r.grade || 'D'}">${r.grade || '-'}</td><td>${r.score || 0}</td><td>${esc(r.sentence || '')}</td></tr>`
      ).join("");

      el("speech-sentence").textContent = "🎉 练习完成！";
      el("speech-result").style.display = "block";
      el("speech-result").innerHTML = `
        <div class="speech-summary">
          <div class="ss-head">口语练习总结</div>
          <div class="ss-grade grade-${avgGrade}">${avgGrade}</div>
          <div class="ss-stats">
            <span>平均分 <b>${avgScore}</b></span>
            <span>练习 <b>${total}</b> 句</span>
          </div>
          <table class="ss-table">
            <tr><th>#</th><th>评分</th><th>分数</th><th>句子</th></tr>
            ${rows}
          </table>
          <div style="text-align:center;margin-top:12px">
            <button class="btn" onclick="UI.stopSpeech()">✅ 完成</button>
            <button class="btn ghost" onclick="UI.startSpeech()">🔄 再来一轮</button>
          </div>
        </div>
      `;
      el("speech-navi").style.display = "none";
      el("speech-footer").style.display = "none";
      el("speech-record-btn").style.display = "none";
      // 口语练习完成奖励
      this.awardStars("speech", 3);
      this.checkAchievements();
    },

    // ---------- 语音 ----------
    setVoiceMode(on) {
      state.voiceMode = on;
      const btn = el("voice-mode-btn");
      if (btn) btn.classList.toggle("active", on);
    },
    toggleVoiceMode() {
      this.setVoiceMode(!state.voiceMode);
      toast(state.voiceMode ? "语音对话模式已开启：导师回复将自动朗读 🔊" : "语音对话模式已关闭");
    },
    speakLast() {
      if (state.lastBotText) speak(state.lastBotText);
      else toast("还没有导师的回复可朗读");
    },
    toggleMic() {
      if (!recognition) {
        if (!initSpeech()) return toast("当前浏览器不支持语音识别，请用 Chrome / Edge，并允许麦克风权限");
      }
      if (state.recognizing) { try { recognition.stop(); } catch (e) {} return; }
      recognition.lang = state.curLang;
      state._finalTranscript = "";
      try { recognition.start(); state.recognizing = true; el("mic-btn").classList.add("recording"); }
      catch (e) { /* 可能已在识别中，忽略 */ }
    },

    showEmotion(r) {
      const bar = el("emotion-bar");
      const col = EMOTION_COLOR[r.emotion] || "#14b8a6";
      let html = `<span>检测到情绪：</span>
        <span class="emotion-chip" style="background:${col}">${esc(r.emotion_label || r.emotion)}</span>
        <span>· 教学策略：${esc(r.strategy || "")}</span>`;
      if (r.concepts && r.concepts.length) {
        html += `<span style="margin-left:8px">本次概念：</span>` +
          r.concepts.map(c => `<span class="concept-chip">${esc(c)}</span>`).join("");
      }
      bar.innerHTML = html; bar.style.display = "flex";
    },
    async markCheckpoint() {
      if (!state.sessionId) return toast("先发一条消息建立会话，再标记检查点");
      const note = prompt("为这个检查点写一句备注（可选）：", "");
      if (note === null) return;
      try {
        await api("POST", "/api/sessions/" + state.sessionId + "/checkpoint", { note });
        toast("已标记学习检查点 📌");
        this.refreshSessionSelect();
      } catch (e) { toast(e.message); }
    },
    async refreshSessionSelect() {
      const rid = state.currentRole && state.currentRole.id;
      if (!rid) return;
      const list = await api("GET", "/api/sessions?role_id=" + rid);
      const sel = el("learn-session");
      let html = `<option value="new">＋ 新建会话</option>`;
      list.forEach(s => {
        const cp = s.checkpoint ? " 📌" : "";
        html += `<option value="${s.id}">${esc((s.title || "会话") + cp)}（${s.message_count}条）</option>`;
      });
      sel.innerHTML = html;
      sel.value = String(state.sessionId);
    },

    // ---------- 角色管理 ----------
    resetRoleForm() {
      el("role-id").value = "";
      ["role-name", "role-persona", "role-style", "role-course", "role-world"].forEach(id => el(id).value = "");
      el("role-form-title").textContent = "创建学习角色";
    },
    editRole(id) {
      const r = state.roles.find(x => x.id === id);
      if (!r) return;
      el("role-id").value = r.id;
      el("role-name").value = r.name;
      el("role-persona").value = r.persona || "";
      el("role-style").value = r.teaching_style || "";
      el("role-course").value = r.course || "";
      el("role-world").value = r.world_setting || "";
      el("role-form-title").textContent = "编辑角色：" + r.name;
      this.go("roles");
      window.scrollTo(0, 0);
    },
    async saveRole() {
      const id = el("role-id").value;
      const payload = {
        name: el("role-name").value.trim(),
        persona: el("role-persona").value,
        teaching_style: el("role-style").value,
        course: el("role-course").value,
        world_setting: el("role-world").value,
      };
      if (!payload.name) return toast("角色名称不能为空");
      try {
        if (id) await api("PUT", "/api/roles/" + id, payload);
        else await api("POST", "/api/roles", payload);
        this.resetRoleForm();
        await this.loadRoles();
        toast("角色已保存");
      } catch (e) { toast(e.message); }
    },
    async deleteRole(id) {
      if (!confirm("删除该角色会同时删除其会话与知识图谱，确定？")) return;
      try { await api("DELETE", "/api/roles/" + id); await this.loadRoles(); toast("已删除"); }
      catch (e) { toast(e.message); }
    },
    async renderRoleList() {
      await this.loadRoles();
      const wrap = el("role-list");
      if (state.roles.length === 0) {
        wrap.innerHTML = `<div class="empty">还没有角色。在上方表单创建你的第一位 AI 导师吧。</div>`;
        return;
      }
      wrap.innerHTML = state.roles.map(r => {
        const isSys = r.user_id === 0;
        const actions = isSys
          ? `<span class="sys-tag">系统内置</span><button class="btn small" onclick="UI.useRole(${r.id})">去学习</button>`
          : `<button class="btn ghost small" onclick="UI.editRole(${r.id})">编辑</button>
             <button class="btn danger small" onclick="UI.deleteRole(${r.id})">删除</button>
             <button class="btn small" onclick="UI.useRole(${r.id})">去学习</button>`;
        return `<div class="role-card">
          <h3>${esc(r.name)} ${isSys ? '<span class="sys-badge">内置</span>' : ''}</h3>
          <div class="meta">课程：${esc(r.course || "—")}</div>
          <div class="meta">阶段：${STAGE_NAME(r.relationship_stage)}</div>
          <div class="meta">${esc((r.persona || "").slice(0, 40) || "（未设定人格）")}</div>
          <div class="row">${actions}</div>
        </div>`;
      }).join("");
    },
    useRole(id) {
      el("learn-role").value = String(id);
      this.onRoleChange();
      this.go("learn");
    },

    // ---------- 知识图谱 ----------
    async renderKG() {
      const sel = el("kg-role");
      sel.innerHTML = state.roles.map(r => `<option value="${r.id}">${esc(r.name)}</option>`).join("");
      if (!state.roles.length) { el("kg-svg").innerHTML = `<text x="450" y="260" text-anchor="middle" fill="#94a3b8">请先创建角色</text>`; return; }
      const rid = parseInt(sel.value, 10);
      const kg = await api("GET", "/api/knowledge_graph?role_id=" + rid);
      drawGraph(kg.nodes, kg.edges);
      // 更新统计
      const s = kg.stats || {};
      const statsEl = el("kg-stats");
      if (statsEl && s.total_nodes) {
        statsEl.innerHTML = `
          <span class="kg-stat"><span class="kg-dot" style="background:#22c55e"></span>掌握 ${s.mastered || 0}</span>
          <span class="kg-stat"><span class="kg-dot" style="background:#eab308"></span>熟悉 ${s.familiar || 0}</span>
          <span class="kg-stat"><span class="kg-dot" style="background:#f97316"></span>了解 ${s.understood || 0}</span>
          <span class="kg-stat"><span class="kg-dot" style="background:#ef4444"></span>未掌握 ${s.not_mastered || 0}</span>
          <span class="kg-stat"><span class="kg-dot" style="background:#94a3b8"></span>未测 ${s.untested || 0}</span>
          <span class="kg-stat-total">共 ${s.total_nodes} 个知识点</span>
        `;
      }
    },

    kgNodeClick(el) {
      const label = el.getAttribute("data-label");
      const mastery = el.getAttribute("data-mastery");
      const cid = el.getAttribute("data-cid");
      let html = `<b>${esc(label)}</b><br>掌握度：${esc(mastery || '未测')}<br><br>`;
      if (cid) {
        html += `<button class="btn primary small" onclick="UI.kgJumpCourse('${esc(cid)}')">📖 去学这个知识点</button>`;
      }
      toast(html, 3000);
    },

    kgJumpCourse(cid) {
      const topic = this.findTopic(cid);
      if (topic) {
        this.selectCourse(topic);
        this.go("learn");
      }
    },

    // ---------- 今日学习计划 ----------
    goDailyPlan() {
      this.go("plan");
      this.loadDailyPlan();
    },

    async loadDailyPlan() {
      const box = el("daily-plan-box");
      if (!box) return;
      try {
        const r = await api("GET", "/api/plan/daily");
        const items = r.items || [];
        const completed = r.completed || [];
        // 更新日期
        const dateEl = el("plan-date");
        if (dateEl) dateEl.textContent = r.date || "";
        // 更新首页进度
        this._updatePlanHome(items, completed);
        if (!items.length) {
          box.innerHTML = `<div class="empty">今日暂无学习计划，去课程广场选一些吧 📚</div>`;
          return;
        }
        box.innerHTML = items.map((it, i) => {
          const done = completed.includes(i);
          return `<div class="plan-item ${done ? 'done' : ''}" data-idx="${i}">
            <div class="pi-check" onclick="UI.completePlanItem(${i})">${done ? '✓' : ''}</div>
            <div class="pi-content">
              <div class="pi-title">${it.icon || '📖'} ${esc(it.title)}</div>
              <div class="pi-meta">${it.type === 'review_mistake' ? '错题复习 · 艾宾浩斯到期' :
                it.type === 'consolidate' ? '薄弱巩固 · 掌握度' + (it.mastery_level || '') + '级' :
                it.type === 'new_learn' ? '新知识点学习' : ''}
                ${it.subject ? ' · ' + esc(it.subject) : ''}
              </div>
            </div>
            ${it.course_id ? `<button class="btn small" onclick="UI.planJump('${esc(it.course_id)}', ${i})">开始</button>` : ''}
          </div>`;
        }).join("");
      } catch (e) {
        box.innerHTML = `<div class="empty">加载失败：${esc(e.message)}</div>`;
      }
    },

    _updatePlanHome(items, completed) {
      // 更新首页计划卡片
      const planEl = el("launcher-plan");
      if (!planEl) return;
      planEl.style.display = items.length ? "flex" : "none";
      const progEl = el("plan-progress");
      if (progEl) progEl.textContent = `已完成 ${completed.length} / ${items.length}`;
      const listEl = el("plan-list");
      if (listEl && items.length) {
        // 首页只显示前2项
        listEl.innerHTML = items.slice(0, 2).map((it, i) => {
          const done = completed.includes(i);
          return `<div class="pi-mini ${done ? 'done' : ''}">
            <span class="pi-dot">${done ? '✓' : '○'}</span>
            <span>${it.icon || ''} ${esc(it.title)}</span>
          </div>`;
        }).join("") + (items.length > 2 ? `<div class="pi-more">还有 ${items.length - 2} 项…</div>` : "");
      }
    },

    async completePlanItem(idx) {
      try {
        const r = await api("POST", "/api/plan/daily/complete", { index: idx });
        toast("完成任务！+1 ⭐ 星星 🎉");
        this.loadDailyPlan();
      } catch (e) { toast(e.message); }
    },

    planJump(cid, idx) {
      const topic = this.findTopic(cid);
      if (topic) {
        this.selectCourse(topic);
        this.go("learn");
      }
    },

    // ---------- 课程目录 ----------
    async openCourse() {
      try {
        if (!state.curriculum || !state.curMeta) {
          const res = await api("GET", "/api/curriculum");
          state.curriculum = res.curriculum || res;
          state.curMeta = { region: res.region, textbook: res.textbook, standard: res.standard };
        }
      } catch (e) { return toast(e.message); }
      // 把学科的语言(lang)继承到每个知识点，便于选课时切换语音语言
      for (const st of state.curriculum)
        for (const subj of st.subjects)
          for (const g of subj.grades)
            for (const t of g.topics)
              if (!t.lang) t.lang = subj.lang || "zh";
      if (!state._courseStage) state._courseStage = state.curriculum[0].stage;
      if (state.curMeta) {
        const meta = el("course-meta");
        meta.textContent = `适配${state.curMeta.region} · 教材版本：${state.curMeta.textbook}`;
        meta.title = state.curMeta.standard || "";
      }
      this.renderCourseTabs();
      this.renderCourseBody();
      el("course-modal").hidden = false;
    },
    closeCourse() { el("course-modal").hidden = true; },
    pickStage(stage) { state._courseStage = stage; this.renderCourseTabs(); this.renderCourseBody(); },
    renderCourseTabs() {
      const tabs = el("course-stage-tabs");
      // 「拓展与素养」只通过卡片进入连续学习，不出现在课程广场的学段标签里
      const list = state.curriculum.filter(st => st.stage !== "拓展与素养");
      if (!state._courseStage || state._courseStage === "拓展与素养") state._courseStage = list[0] ? list[0].stage : (state.curriculum[0] && state.curriculum[0].stage);
      tabs.innerHTML = list.map(st =>
        `<button class="cstage ${st.stage === state._courseStage ? "active" : ""}" onclick="UI.pickStage('${esc(st.stage)}')">${esc(st.stage)}</button>`
      ).join("");
    },
    findTopic(id) {
      // 课程目录可能尚未加载（如从聊天历史「看AI讲解」/掌握度「学」直接进入），
      // 此时 state.curriculum 为 undefined，直接遍历会抛 "not iterable"。先判空。
      if (!Array.isArray(state.curriculum)) return null;
      for (const st of state.curriculum)
        for (const subj of st.subjects)
          for (const g of subj.grades)
            for (const t of g.topics)
              if (t.id === id) return t;
      return null;
    },
    renderCourseBody() {
      const st = state.curriculum.find(s => s.stage === state._courseStage) || state.curriculum[0];
      let html = "";
      st.subjects.forEach(subj => {
        html += `<div class="course-subject"><h4>${esc(subj.name)}</h4>`;
        subj.grades.forEach(g => {
          html += `<div class="course-grade"><span class="grade-label">${esc(g.grade)}</span><div class="topic-list">`;
          g.topics.forEach(t => {
            const sel = state.selectedCourse && state.selectedCourse.id === t.id ? "selected" : "";
            html += `<button class="topic-btn ${sel}" data-cid="${esc(t.id)}" onclick="UI.openLessonById(this.getAttribute('data-cid'))" title="查看「${esc(t.title)}」的详细课程内容">${esc(t.title)}</button>`;
          });
          html += `</div></div>`;
        });
        html += `</div>`;
      });
      el("course-body").innerHTML = html;
    },
    selectCourseById(id) {
      const t = this.findTopic(id);
      if (t) this.selectCourse(t);
    },
    selectCourse(topic) {
      this.stopAssess();
      state.selectedCourse = topic;
      const c = el("current-course");
      c.textContent = `${topic.stage} · ${topic.subject} · ${topic.grade} · ${topic.title}`;
      c.classList.add("chosen");
      this.closeCourse();
      toast("已选择课程：" + topic.title);
      // 英语课：自动切到英语外教并开启语音模式，形成英语语音对话闭环
      if (topic.lang === "en") {
        const eng = state.roles.find(r => r.lang === "en");
        if (eng && (!state.currentRole || state.currentRole.lang !== "en")) {
          this.useRole(eng.id);  // 内部会 applyLangByRole -> en-US
          toast("英语课已自动切换到英语外教「" + eng.name + "」，并开启语音对话模式 🎙️");
        } else if (state.currentRole && state.currentRole.lang === "en") {
          state.curLang = "en-US";
        }
        this.setVoiceMode(true);
      } else {
        if (state.currentRole) this.applyLangByRole(state.currentRole);
        this.setVoiceMode(false);
      }
      this.loadMastery(topic.id);
    },

    // ---------- 课程内容（详细讲义预览） ----------
    openCurrentLesson() {
      if (!state.selectedCourse) return toast("请先在「📚 浏览课程目录」中选择一个知识点");
      this.openLessonById(state.selectedCourse.id);
    },
    openLessonById(id) {
      if (!id) return;
      this.openLesson({ id });
    },
    async     openLesson(topicLike) {
      const id = topicLike && topicLike.id;
      if (!id) return toast("课程 ID 缺失");
      // 同步当前正在学习的知识点，确保「课后测试」针对的就是本知识点
      const full = this.findTopic(id);
      if (full) state.selectedCourse = full;
      el("course-modal").hidden = true;
      el("lesson-title").textContent = "加载中…";
      el("lesson-meta").textContent = "";
      el("lesson-content").innerHTML = `<div class="empty">正在准备这节课的内容…</div>`;
      el("lesson-ai").style.display = "none";
      el("lesson-ai").innerHTML = "";
      state._aiLesson = null;
      const btn = el("ai-explain-btn");
      if (btn) { btn.disabled = false; btn.textContent = "✨ AI 深度讲解"; }
      el("lesson-modal").hidden = false;
      try {
        const L = await api("GET", "/api/lesson?course_id=" + encodeURIComponent(id));
        state._lesson = L;
        state._lessonTopic = { id: L.id, title: L.title, stage: L.stage,
          subject: L.subject, grade: L.grade, lang: L.lang };
        // 若目录未加载导致 findTopic 没补上 selectedCourse，这里用 API 返回补全，
        // 保证「课后测试」等下游功能能定位到正确课程
        if (!state.selectedCourse) state.selectedCourse = state._lessonTopic;
        this.renderLesson(L);
        // 用户希望打开课程就能看到「带具体例题的详细讲解」：已登录则自动请 AI 老师现场讲解
        if (state.token) {
          this.aiExplain();
        }
      } catch (e) {
        el("lesson-content").innerHTML = `<div class="empty">加载课程内容失败：${esc(e.message)}</div>`;
      }
    },
    renderLesson(L) {
      el("lesson-title").textContent = L.title;
      el("lesson-meta").textContent = `${L.stage} · ${L.subject} · ${L.grade}` + (L.lang === "en" ? " · 英语" : "");
      let html = "";
      html += state.token
        ? `<div class="lesson-banner">📖 下面是本课<b>大纲</b>；<b>AI 老师正在下方现场撰写「带具体例题」的详细讲解</b>，本地模型生成较慢，请耐心稍候约半分钟到一分钟（不要关闭）。</div>`
        : `<div class="lesson-banner warn">📖 下面是本课大纲。<b>登录后</b>打开课程会自动出现 AI 老师带<b>具体例题</b>的一步步详细讲解。</div>`;
      if (L.goals) html += `<div class="lesson-goals"><b>🎯 学习目标</b><div>${esc(L.goals)}</div></div>`;
      html += `<div class="lesson-sections">`;
      (L.sections || []).forEach(s => {
        html += `<div class="lesson-sec">
          <div class="ls-h"><span class="ls-no">${s.no}</span>${esc(s.heading)}</div>
          <div class="ls-body">${renderBody(s.body)}</div>
          ${s.tip ? `<div class="ls-tip">💡 ${esc(s.tip)}</div>` : ""}
        </div>`;
      });
      html += `</div>`;
      if (L.mistakes && L.mistakes.length) {
        html += `<div class="lesson-mistakes"><b>📌 易错提醒</b><ul>` +
          L.mistakes.map(m => `<li>${esc(m)}</li>`).join("") + `</ul></div>`;
      }
      if (L.selfcheck && L.selfcheck.length) {
        html += `<div class="lesson-selfcheck"><b>🧠 想一想（自测）</b><ul>` +
          L.selfcheck.map(q => `<li>${esc(q)}</li>`).join("") + `</ul></div>`;
      }
      if (L.summary) html += `<div class="lesson-summary">📝 ${esc(L.summary)}</div>`;
      el("lesson-content").innerHTML = html;
      renderMath(el("lesson-content"));
    },
    chooseLesson() {
      if (!state._lessonTopic) return toast("请先选择一门课程");
      this.selectCourse(state._lessonTopic);
      this.closeLesson();
      toast("已选择课程：" + state._lessonTopic.title);
    },
    closeLesson() { el("lesson-modal").hidden = true; },
    listenLesson() {
      const L = state._lesson;
      if (!L) return toast("还没有可朗读的内容");
      // 若已生成分步 AI 讲解，优先朗读已展示的讲解内容
      if (state._aiLesson && state._aiLesson.points && state._aiLesson.points.length) {
        this.speakAiAll();
        return;
      }
      let txt = L.title + "。" + (L.goals || "") + "。";
      (L.sections || []).forEach(s => { txt += s.heading + "。" + (s.body || "") + "。"; });
      (L.selfcheck || []).forEach(q => { txt += "想一想：" + q + "。"; });
      txt += (L.summary || "");
      if (!txt.trim()) return toast("这节课没有可朗读的内容");
      // 清理 HTML 标签（sections.body 可能含 <b>/<i> 等）
      txt = txt.replace(/<[^>]+>/g, "").trim();
      if (!txt) return toast("清理后无可朗读内容");
      console.log("[TTS] listenLesson text length:", txt.length);
      speak(txt);
    },
    speakAiLesson() { this.speakAiAll(); },  // 兼容旧调用
    // 朗读某个要点（含其换讲法）
    speakPoint(i) {
      const a = state._aiLesson;
      if (!a || !a.points || !a.points[i]) return toast("该要点暂无内容");
      const p = a.points[i];
      let t = (p.key ? ("要点" + (i + 1) + "，" + p.key + "。 ") : "") + (p.explain || "");
      (a.alts[i] || []).forEach((alt, k) => {
        t += " 换种讲法" + (k + 1) + "：" + (alt.explain || "");
        if (alt.example) t += " 例题：" + alt.example;
      });
      if (p.example) t += " 例题：" + p.example;
      speak(t);
    },
    // 朗读全部已展示要点
    speakAiAll() {
      const a = state._aiLesson;
      if (!a || !a.points || !a.points.length) return toast("还没有 AI 讲解内容，请先点「✨ AI 深度讲解」");
      let t = (a.title ? (a.title + "。 ") : "");
      a.points.forEach((p, i) => {
        if (i >= a.revealed) return;
        t += "要点" + (i + 1) + "，" + (p.key || "") + "。" + (p.explain || "");
        (a.alts[i] || []).forEach((alt, k) => {
          t += " 换种讲法" + (k + 1) + "：" + (alt.explain || "");
          if (alt.example) t += " 例题：" + alt.example;
        });
        if (p.example) t += " 例题：" + p.example;
      });
      if (a.summary && a.revealed >= a.points.length) t += " 总结：" + a.summary;
      speak(t);
    },
    diagnoseVoice() {
      const box = el("voice-diag");
      if (!box) return;
      box.style.display = "block";
      // APK 离线包用的是手机系统引擎，和浏览器 speechSynthesis 是两套东西，必须走原生自检
      if (_nativePresent()) { this.ttsSelfTest(); return; }
      if (!("speechSynthesis" in window)) {
        box.innerHTML = `<div class="vd-bad">当前浏览器不支持语音合成（Web Speech API）。请改用 <b>Chrome</b> 或 <b>Edge</b>，并通过地址栏直接打开 <b>${location.origin}</b>（不要双击 index.html 或在预览面板操作）。</div>`;
        return;
      }
      const vs = window.speechSynthesis.getVoices() || [];
      const zh = vs.filter(v => v.lang && v.lang.toLowerCase().startsWith("zh"));
      const en = vs.filter(v => v.lang && v.lang.toLowerCase().startsWith("en"));
      let html = `<div class="vd-ok">✅ 浏览器支持语音合成</div>`;
      html += `<div class="vd-row">共检测到 <b>${vs.length}</b> 个语音：` +
              (vs.length ? vs.map(v => `${esc(v.name)}<span class="vd-lang">[${esc(v.lang)}]</span>`).join("、") : "<b>无</b>") + `</div>`;
      if (zh.length) {
        html += `<div class="vd-ok">✅ 已安装中文语音：<b>${zh.map(v => esc(v.name)).join("、")}</b></div>`;
      } else {
        html += `<div class="vd-bad">❌ 未检测到任何<b>中文语音</b>。两种解法：① 在系统设置里安装中文语音包后重开浏览器；② 直接到「语音朗读设置」把<b>朗读引擎</b>切到「云端朗读」（由服务端生成音频，手机/平板稳出声）。</div>`;
      }
      // 实测朗读一句中文
      const testLang = zh[0] ? zh[0].lang : (en[0] ? en[0].lang : "zh-CN");
      const testVoice = zh[0] || en[0] || null;
      const u = new SpeechSynthesisUtterance("你好，这是语音朗读测试。");
      u.lang = testLang;
      if (testVoice) u.voice = testVoice;
      let ended = false;
      u.onstart = () => { html += `<div class="vd-ok">▶️ 已开始朗读测试句…</div>`; box.innerHTML = html; };
      u.onend = () => { ended = true; html += `<div class="vd-ok">✅ 朗读测试成功，扬声器应已出声。若仍听不到，请检查系统音量 / 浏览器标签页是否被静音。</div>`; box.innerHTML = html; };
      u.onerror = (e) => { html += `<div class="vd-bad">❌ 朗读测试失败：${esc(e && e.error || "未知错误")}。多数情况是系统未安装对应语言语音包。</div>`; box.innerHTML = html; };
      box.innerHTML = html + `<div class="vd-row">正在播放测试句…</div>`;
      try { window.speechSynthesis.cancel(); window.speechSynthesis.speak(u); }
      catch (e) { html += `<div class="vd-bad">❌ 触发朗读异常：${esc(e.message)}</div>`; box.innerHTML = html; }
      // 兜底：4 秒无响应
      setTimeout(() => {
        if (!ended) {
          const extra = `<div class="vd-bad">⚠️ 4 秒内无任何播放回调：请确认①系统扬声器/音量正常 ②浏览器标签页未静音 ③已用 Chrome/Edge 直连 ${location.origin}。若语音列表为空，需先安装中文语音包。</div>`;
          if (!box.innerHTML.includes("⚠️")) box.innerHTML += extra;
        }
      }, 4000);
    },
    videoLesson() {
      const L = state._lesson;
      if (!L) return toast("请先打开课程内容");
      const kw = encodeURIComponent(`${L.subject} ${L.grade} ${L.title}`);
      window.open("https://search.bilibili.com/all?keyword=" + kw, "_blank", "noopener");
    },
    async aiExplain() {
      const L = state._lesson;
      if (!L) return toast("请先打开课程内容");
      const box = el("lesson-ai");
      box.style.display = "block";
      box.innerHTML = `<div class="empty">🤖 正在请 AI 老师写分步讲解…</div>`;
      const btn = el("ai-explain-btn");
      if (btn) { btn.disabled = true; btn.textContent = "讲解生成中…"; }
      try {
        const r = await api("POST", "/api/lesson/explain", { course_id: L.id });
        // 结构化状态：逐点展示，每点确认是否学会
        state._aiLesson = {
          title: r.title || L.title,
          points: (r.points || []).map(p => ({
            key: p.key || "", explain: p.explain || "", example: p.example || ""
          })),
          summary: r.summary || "",
          mock: !!r.mock,
          revealed: 1,            // 先只展示第 1 个要点
          alts: {},               // { 索引: [{explain, example}, ...] }
          confirmed: {},          // { 索引: true }
          loading: {},            // { 索引: true } 正在换讲法
        };
        this.renderAiLesson();
        // 真实 AI：自动朗读第一个要点，帮学生进入状态
        if (!r.mock) { try { this.speakPoint(0); } catch (e) {} }
      } catch (e) {
        const msg = (e && e.message) || String(e);
        if (/401|未登录/.test(msg)) {
          box.innerHTML = `<div class="empty">⚠️ 请先<b>登录</b>后再使用 AI 深度讲解（右上角「登录」）。</div>`;
        } else {
          box.innerHTML = `<div class="empty">生成失败：${esc(msg)}</div>`;
        }
        if (!state.token) toast("请先登录后再使用 AI 深度讲解");
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "✨ 重新生成讲解"; }
      }
    },
    // 渲染分步讲解：已展示的要点 + 每点确认按钮 + 换讲法
    renderAiLesson() {
      const a = state._aiLesson;
      const box = el("lesson-ai");
      if (!a || !a.points || !a.points.length) { box.style.display = "none"; return; }
      box.style.display = "block";
      const allDone = a.revealed >= a.points.length && a.points.every((_, i) => a.confirmed[i]);
      const note = a.mock
        ? `<div class="lesson-ai-note">ℹ️ 演示模式：讲解由讲义生成。填入 Key 并关闭演示模式可获 AI 原创分步讲解与换讲法。</div>`
        : `<div class="lesson-ai-note ok">✅ 由 AI 老师（真实模型）现场撰写，每讲完一个要点会让你确认是否学会。</div>`;
      let html = `<div class="ai-head">✨ AI 分步讲解（${a.mock ? "演示模式" : "真实 AI"}）` +
        `<button class="btn ghost small pulse" onclick="UI.speakAiAll()" title="朗读已学要点">🔊 朗读</button></div>`;
      html += `<div class="ai-progress">进度：已学 ${Object.keys(a.confirmed).filter(k => a.confirmed[k]).length} / ${a.points.length} 个要点</div>`;
      a.points.forEach((p, i) => {
        if (i >= a.revealed) return;
        html += `<div class="ai-point">`;
        html += `<div class="ap-key">📍 要点 ${i + 1}：${esc(p.key)}` +
                `<button class="btn ghost tiny" onclick="UI.speakPoint(${i})" title="朗读这个要点">🔊</button></div>`;
        html += `<div class="ap-explain"><b>讲解：</b>${nl2br(esc(p.explain))}</div>`;
        if (p.example) html += `<div class="ap-example"><b>例题：</b>${nl2br(esc(p.example))}</div>`;
        (a.alts[i] || []).forEach((alt, k) => {
          html += `<div class="ap-alt"><b>💡 换种讲法 ${k + 1}：</b>${nl2br(esc(alt.explain))}`;
          if (alt.example) html += `<div class="ap-example">例题：${nl2br(esc(alt.example))}</div>`;
          html += `</div>`;
        });
        if (a.confirmed[i]) {
          html += `<div class="ap-done">✅ 这个要点你已学会</div>`;
        } else if (a.loading[i]) {
          html += `<div class="ap-loading">🔄 老师正在换一种讲法…</div>`;
        } else {
          html += `<div class="ap-confirm">` +
            `<button class="btn small ok" onclick="UI.confirmPoint(${i},true)">✅ 我学会了</button>` +
            `<button class="btn small warn" onclick="UI.confirmPoint(${i},false)">❌ 没听懂，换种讲法</button>` +
            `</div>`;
        }
        html += `</div>`;
      });
      if (allDone) {
        if (a.summary) html += `<div class="ai-summary"><b>📝 本章总结</b><div>${nl2br(esc(a.summary))}</div></div>`;
        html += `<div class="ap-done big">🎉 太棒了！这一章的要点你都学明白了。可以点上方「想一想」自测，或点「✅ 选择这门课并开始学习」。</div>`;
      }
      html += note;
      box.innerHTML = html;
      renderMath(box);
      box.scrollIntoView({ behavior: "smooth", block: "nearest" });
    },
    // 确认某个要点是否学会
    confirmPoint(i, learned) {
      const a = state._aiLesson;
      if (!a || !a.points[i]) return;
      if (learned) {
        a.confirmed[i] = true;
        // 当前要点是最后一个已展示的，则揭示下一个
        if (i === a.revealed - 1 && a.revealed < a.points.length) a.revealed++;
        this.renderAiLesson();
        if (!a.mock) { try { this.speakPoint(i); } catch (e) {} }
      } else {
        this.reexplainPoint(i);
      }
    },
    // 没听懂：调后端换一种讲法，追加到该要点下
    async reexplainPoint(i) {
      const a = state._aiLesson;
      const p = a.points[i];
      if (!p) return;
      a.loading[i] = true;
      this.renderAiLesson();
      try {
        const r = await api("POST", "/api/lesson/reexplain", {
          course_id: state._lesson.id, key: p.key, explain: p.explain, example: p.example
        });
        a.alts[i] = a.alts[i] || [];
        // 避免无限追加（最多 3 种讲法）
        if (a.alts[i].length < 3) {
          a.alts[i].push({ explain: r.explain || "", example: r.example || "" });
        }
        if (!a.mock) {
          const t = (r.explain || "") + (r.example ? (" 例题：" + r.example) : "");
          try { speak(t); } catch (e) {}
        }
      } catch (e) {
        toast("换讲法失败：" + ((e && e.message) || e));
      } finally {
        a.loading[i] = false;
        this.renderAiLesson();
      }
    },

    // ---------- 设置 ----------
    // which: "teach"(教学模型) | "reason"(推理模型)
    applyModelPreset(which) {
      which = which || "teach";
      const selId = which === "reason" ? "set-r-preset" : "set-preset";
      const v = el(selId).value;
      if (!v) return;
      const presets = {
        "qwen":      { base: "http://127.0.0.1:11434/v1", model: "qwen2.5:7b",     key: "ollama",   mock: false },
        "qwen3b":    { base: "http://127.0.0.1:11434/v1", model: "qwen2.5:3b",     key: "ollama",   mock: false },
        "ollama-r1": { base: "http://127.0.0.1:11434/v1", model: "deepseek-r1:7b", key: "ollama",   mock: false },
        "ollama":    { base: "http://127.0.0.1:11434/v1", model: "",              key: "ollama",   mock: false },
        "lmstudio":  { base: "http://127.0.0.1:1234/v1",  model: "",              key: "lmstudio", mock: false },
        "deepseek":  { base: "https://api.deepseek.com/v1", model: "deepseek-chat", key: "",       mock: true },
      };
      const p = presets[v];
      if (which === "reason") {
        el("set-r-base").value = p.base;
        el("set-r-model").value = p.model;
        el("set-r-key").value = p.key;
        // 推理模型选了本机预设也应退出演示模式
        if (!p.mock) el("set-mock").checked = false;
      } else {
        el("set-base").value = p.base;
        el("set-model").value = p.model;
        el("set-key").value = p.key;
        el("set-mock").checked = p.mock;
      }
      const name = (el(selId).selectedOptions[0] || {}).textContent || "预设";
      toast("已填入「" + name + "」的地址，点「保存设置」生效");
    },
    async loadSettings() {
      try {
        const s = await api("GET", "/api/settings");
        el("set-key").value = s.api_key || "";
        el("set-base").value = s.base_url || "https://api.deepseek.com/v1";
        el("set-model").value = s.model || "deepseek-chat";
        el("set-mock").checked = !!s.mock_mode;
        el("set-r-key").value = s.r_api_key || "";
        el("set-r-base").value = s.r_base_url || "";
        el("set-r-model").value = s.r_model || "";
      } catch (e) { toast(e.message); }
    },
    async saveSettings() {
      const payload = {
        api_key: el("set-key").value.trim(),
        base_url: el("set-base").value.trim() || "https://api.deepseek.com/v1",
        model: el("set-model").value.trim() || "deepseek-chat",
        mock_mode: el("set-mock").checked ? 1 : 0,
        r_api_key: el("set-r-key").value.trim(),
        r_base_url: el("set-r-base").value.trim(),
        r_model: el("set-r-model").value.trim(),
      };
      try {
        await api("POST", "/api/settings", payload);
        const hasReason = payload.r_model || payload.r_base_url;
        toast("设置已保存" + (payload.api_key ? "，已启用真实模型" : "，仍处演示模式") +
              (hasReason ? "；测评将使用独立推理模型" : "；测评复用教学模型"));
      }
      catch (e) { toast(e.message); }
    },
    // 一键填好本地推荐配置并直接保存：教学=Qwen2.5:7B，推理=DeepSeek-R1:7B
    async applyRecommended() {
      el("set-base").value = "http://127.0.0.1:11434/v1";
      el("set-model").value = "qwen2.5:7b";
      el("set-key").value = "ollama";
      el("set-r-base").value = "http://127.0.0.1:11434/v1";
      el("set-r-model").value = "deepseek-r1:7b";
      el("set-r-key").value = "ollama";
      el("set-mock").checked = false;
      toast("已填入本地推荐（教学 Qwen2.5:7B / 推理 DeepSeek-R1:7B），正在保存…");
      await this.saveSettings();
      this.testConnection();
    },
    // 一键测试「教学 / 推理」两个模型是否可达
    async testConnection() {
      const box = el("conn-status");
      box.innerHTML = "🔄 正在测试两个模型连接…";
      try {
        const r = await api("POST", "/api/settings/test");
        const mk = (o) => o.ok ? "✅ " + esc(o.model || "模型") + " 可达" : "❌ " + esc(o.msg || "不可达");
        box.innerHTML = "🎓 教学模型：" + mk(r.teaching) + "<br>🧠 推理模型：" + mk(r.reasoning);
      } catch (e) {
        box.innerHTML = "❌ 测试失败：" + esc(e.message);
      }
    },

    // ---------- 🗣️ 语音朗读设置（可调音色，告别机械嗓音） ----------
    // 情感风格预设：自动设定语速/音调组合（音量单独保留用户设定）
    _ttsStylePresets: {
      natural: { rate: 0.95, pitch: 1.02 },  // 自然
      warm:    { rate: 0.90, pitch: 0.92 },  // 温柔：稍慢、偏低沉
      teacher: { rate: 0.92, pitch: 1.06 },  // 老师：清晰、稳重
      lively:  { rate: 1.06, pitch: 1.18 },  // 活泼：稍快、偏明亮（适合小朋友）
    },
    _ttsStyleName(s) { return ({ natural: "自然", warm: "温柔", teacher: "老师", lively: "活泼", custom: "自定义" })[s] || s; },
    // 判断某个嗓音是否为高质量（用于下拉里打 ★ 推荐）
    _isGoodVoice(name) {
      const n = (name || "").toLowerCase();
      return ["xiaoxiao", "xiaoyi", "yunxi", "yunyang", "yunjian", "晓晓", "云希", "云扬",
        "yue", "ting-ting", "tingting", "mei-jia", "meijia", "sin-ji", "sinji", "yaoyao", "yu",
        "google 普通话", "google 國語", "google 粤語", "google us english", "google uk english",
        "natural", "online", "neural", "premium", "enhanced", "siri", "aria", "jenny", "guy"
      ].some(k => n.includes(k));
    },
    // edge-tts 神经网络音色（由电脑端合成，音质远好于手机系统引擎）
    _edgeVoices: [
      ["zh-CN-XiaoxiaoNeural", "晓晓 · 女声 · 温柔自然（推荐）"],
      ["zh-CN-XiaoyiNeural", "晓伊 · 女声 · 活泼"],
      ["zh-CN-YunxiNeural", "云希 · 男声 · 清朗"],
      ["zh-CN-YunjianNeural", "云健 · 男声 · 浑厚"],
      ["zh-CN-YunyangNeural", "云扬 · 男声 · 专业播报"],
      ["zh-CN-YunxiaNeural", "云夏 · 男声 · 少年"],
      ["zh-CN-liaoning-XiaobeiNeural", "晓北 · 女声 · 东北话"],
      ["zh-CN-shaanxi-XiaoniNeural", "晓妮 · 女声 · 陕西话"],
      ["en-US-AriaNeural", "Aria · 英语女声"],
      ["en-US-GuyNeural", "Guy · 英语男声"],
    ],
    populateVoices() {
      const sel = el("set-voice");
      if (!sel) return;
      // 走电脑语音服务器：列出 edge-tts 音色（与手机/浏览器嗓音是两套东西）
      if (_useNativeHttpTts()) {
        const cur = state.ttsVoice || "";
        const isEn = (state.curLang || "zh").toLowerCase().startsWith("en");
        const opts = ['<option value="">— 默认：晓晓（推荐）—</option>'];
        for (const it of this._edgeVoices) {
          if (isEn && it[0].indexOf("zh-") === 0) continue;
          if (!isEn && it[0].indexOf("en-") === 0) continue;
          opts.push('<option value="' + esc(it[0]) + '"' + (cur === it[0] ? " selected" : "") + ">" + esc(it[1]) + "</option>");
        }
        sel.innerHTML = opts.join("");
        return;
      }
      let vs = [];
      try { vs = (window.speechSynthesis && window.speechSynthesis.getVoices()) || []; } catch (e) {}
      if (!vs.length) { sel.innerHTML = '<option value="">— 本机暂未加载嗓音，点「刷新可用嗓音」—</option>'; return; }
      const lang = (state.curLang || "zh-CN").toLowerCase();
      const base = lang.slice(0, 2);
      const sorted = vs.slice().sort((a, b) => {
        const la = (a.lang || "").replace("_", "-").toLowerCase(), lb = (b.lang || "").replace("_", "-").toLowerCase();
        const sa = (la === lang || la.startsWith(base)) ? 0 : 1;
        const sb = (lb === lang || lb.startsWith(base)) ? 0 : 1;
        return sa - sb;
      });
      if (_nativeAvail()) {
        // APK 离线包：走手机系统自带 TTS，嗓音由系统设置决定，网页侧不干预
        sel.innerHTML = '<option value="">— 由手机系统决定（推荐）—</option>';
        return;
      }
      const opts = ['<option value="">— 自动优选（推荐）—</option>'];
      for (const v of sorted) {
        const star = this._isGoodVoice(v.name) ? " ★" : "";
        const cur = (state.ttsVoice && v.name === state.ttsVoice) ? " selected" : "";
        opts.push('<option value="' + esc(v.name) + '"' + cur + '>' + esc(v.name) + '（' + esc(v.lang || "?") + '）' + star + '</option>');
      }
      sel.innerHTML = opts.join("");
    },
    refreshVoices() {
      const self = this;
      // 走「电脑语音服务器」时，嗓音由电脑 edge-tts 提供，直接列出可选音色
      if (_useNativeHttpTts()) {
        this.populateVoices();
        toast("嗓音由电脑 edge-tts 提供，已列出可选音色（晓晓/云希等神经网络嗓音，比手机引擎自然得多）");
        return;
      }
      // APK 离线包（用手机自带引擎）：嗓音由系统决定，不是浏览器的嗓音列表
      if (_nativePresent()) {
        toast(_ttsServerBase()
          ? "当前用手机自带引擎，嗓音请在「⚙️ 打开手机语音设置」里选择/下载"
          : "手机自带引擎的嗓音由系统决定；填「电脑语音服务器地址」可改用更好听的电脑嗓音");
        this.ttsSelfTest();
        return;
      }
      if (!("speechSynthesis" in window)) { _ttsNoEngineHint(); return; }
      let tries = 0;
      const poll = () => {
        const vs = window.speechSynthesis.getVoices() || [];
        if (vs.length) { self.populateVoices(); toast("已刷新可用嗓音（共 " + vs.length + " 个，带 ★ 为高质量）"); return; }
        if (tries++ >= 15) { self.populateVoices(); toast("本机暂未提供额外嗓音；可在系统设置里下载高质量嗓音后重试"); return; }
        setTimeout(poll, 120);
      };
      poll();
    },
    onTtsVoiceChange() {
      const sel = el("set-voice");
      if (!sel) return;
      state.ttsVoice = sel.value || "";
      localStorage.setItem("al_tts_voice", state.ttsVoice);
      this.syncTtsStyleSeg();
    },
    onTtsEngineChange() {
      const sel = el("set-tts-engine");
      if (!sel) return;
      state.ttsEngine = sel.value || "auto";
      localStorage.setItem("al_tts_engine", state.ttsEngine);
      const srv = _ttsServerBase();
      const why = state.ttsEngine === "native" ? (_nativeAvail()
                    ? "已切换到本地离线朗读（用手机/平板自带引擎，不联网）"
                    : (srv
                        ? "本机没有可用的语音引擎，会自动改用电脑语音服务器（" + srv + "）朗读"
                        : "本地离线朗读需要手机/平板自带语音引擎；华为等无引擎机型请在下方填「电脑语音服务器地址」")) :
                  state.ttsEngine === "cloud" ? (srv
                    ? "已切换到电脑语音服务器朗读（" + srv + "，音质最好）"
                    : "已切换到云端朗读（网页端由服务端生成音频；APK 内需先在下方填电脑语音服务器地址）") :
                  state.ttsEngine === "browser" ? "已切换到浏览器朗读（用本机嗓音，部分设备可能无声）" :
                  "已切换到自动模式（有语音服务器就用服务器，没有就用本机引擎）";
      toast(why);
    },
    // 电脑语音服务器地址（APK 无引擎机型专用）
    saveTtsServer() {
      const inp = el("set-tts-server");
      if (!inp) return;
      const norm = _normalizeServerBase(inp.value);
      state.ttsServer = norm;
      localStorage.setItem("al_tts_server", norm);
      inp.value = norm;
      // 保存后立刻把界面同步过来：否则「当前：未配置」和嗓音下拉还是旧状态，
      // 看起来像没生效（用户会反复点保存）。
      const srvHint = el("tts-server-state");
      if (srvHint) {
        srvHint.textContent = norm
          ? "当前：电脑语音服务器 " + norm
          : "当前：未配置（华为等无引擎机型会无声）";
      }
      this.populateVoices();   // 走服务器时换成 edge-tts 音色列表
      toast(norm ? "已保存语音服务器：" + norm + "，点「🔌 测试语音服务器」验证一下" : "已清空语音服务器地址");
    },
    // 一键填本机地址（网页端打开时，电脑自己的地址就是当前访问地址，直接拿来用）
    fillTtsServerFromLocation() {
      const inp = el("set-tts-server");
      if (!inp) return;
      let host = "";
      try { host = location.host || ""; } catch (e) {}
      if (!host || /^localhost(:\d+)?$/i.test(host) || /^127\./.test(host)) {
        toast("当前就是在这台电脑上打开的，手机端请填电脑的局域网 IP（启动脚本的黑窗口里有显示）");
        return;
      }
      inp.value = _normalizeServerBase(host);
      this.saveTtsServer();
    },
    async testTtsServer() {
      const inp = el("set-tts-server");
      const raw = inp ? inp.value : state.ttsServer;
      const base = _normalizeServerBase(raw);
      if (!base) { toast("请先填写电脑语音服务器地址，例如 192.168.1.5:8000"); return; }
      if (inp) { inp.value = base; }
      state.ttsServer = base;
      localStorage.setItem("al_tts_server", base);
      const srvHint0 = el("tts-server-state");
      if (srvHint0) srvHint0.textContent = "当前：电脑语音服务器 " + base;
      const box = el("voice-diag");
      const hasBridge = _nativePresent() && typeof window.ALNative.httpGet === "function";
      if (box) {
        box.style.display = "block";
        box.innerHTML = '<div class="vd-row">正在连接 ' + esc(base) + ' …</div>';
      }
      toast("正在测试语音服务器…");
      const lines = [];
      const push = (ok, txt) => { lines.push('<div class="' + (ok ? "vd-ok" : "vd-bad") + '">' + (ok ? "✅ " : "❌ ") + txt + '</div>'); if (box) box.innerHTML = lines.join(""); };
      try {
        // 1) 连通性（不合成音频，毫秒级）
        let txt = "";
        try {
          const t0 = Date.now();
          txt = hasBridge ? await _nativeHttpGet(base + "/api/tts_ping", 8000) : await _fetchTextRaw(base + "/api/tts_ping", 8000);
          const info = JSON.parse(txt);
          const ms = Date.now() - t0;
          push(true, "已连上语音服务器（" + ms + "ms）：" + esc(info.service || "AL 自学系统"));
          push(!!info.edge_tts, "电脑端 edge-tts：" + (info.edge_tts ? "已就绪（" + esc(info.voice || "") + "）" : "未安装！请用「启动_AL系统_语音版.bat」启动服务"));
          if (info.lan_primary) push(true, "电脑局域网地址（手机要填的就是这个）：" + esc(info.lan_primary));
        } catch (e) {
          const m = String((e && e.message) || e);
          let tip = "";
          if (/timeout/i.test(m)) tip = "连接超时：多半是电脑防火墙拦了 8000 端口，或手机与电脑不在同一 WiFi";
          else if (/cleartext|permit/i.test(m)) tip = "系统拦截了明文 HTTP：需在清单里开启 usesCleartextTraffic（新版本已修）";
          else if (/refused|ECONN|net:/i.test(m)) tip = "连不上：确认服务已启动、地址端口没写错（黑窗口里显示的那个）";
          else tip = m;
          push(false, "连接失败：" + esc(tip));
          push(false, hasBridge ? "（已通过原生通道尝试，绕过浏览器混合内容限制）" : "（网页端直连；APK 内会走原生通道）");
          return;
        }
        // 2) 真合成一小段并取回音频（证明端到端可用）
        try {
          const t1 = Date.now();
          const u = base + "/api/tts?" + new URLSearchParams({ text: "语音测试", lang: "zh-CN", rate: "+0%", pitch: "+0Hz" }).toString();
          const b64 = hasBridge ? await _nativeHttpGet(u, 30000) : await _fetchB64Raw(u, 30000);
          const n = b64 ? _b64ByteLen(b64) : 0;
          push(n > 1000, "音频回传正常（" + (n / 1024).toFixed(1) + " KB，" + (Date.now() - t1) + "ms）" + (n > 1000 ? "" : "，返回内容过小，可能服务端报错"));
        } catch (e) {
          push(false, "取音频失败：" + esc(String((e && e.message) || e)));
        }
        toast("测试完成，请看下方结果");
      } catch (e) { /* 已在上面处理 */ }
    },
    onTtsSlider() {
      const r = parseFloat(el("set-rate").value), p = parseFloat(el("set-pitch").value), v = parseFloat(el("set-vol").value);
      state.ttsRate = r; state.ttsPitch = p; state.ttsVolume = v;
      localStorage.setItem("al_tts_rate", String(r));
      localStorage.setItem("al_tts_pitch", String(p));
      localStorage.setItem("al_tts_volume", String(v));
      el("rate-val").textContent = r.toFixed(2);
      el("pitch-val").textContent = p.toFixed(2);
      el("vol-val").textContent = v.toFixed(2);
      state.ttsStyle = "custom";   // 手动调滑块视为自定义，取消风格高亮
      localStorage.setItem("al_tts_style", "custom");
      this.syncTtsStyleSeg();
    },
    applyTtsStyle(style) {
      const preset = this._ttsStylePresets[style] || this._ttsStylePresets.natural;
      state.ttsStyle = style;
      state.ttsRate = preset.rate;
      state.ttsPitch = preset.pitch;
      localStorage.setItem("al_tts_style", style);
      localStorage.setItem("al_tts_rate", String(preset.rate));
      localStorage.setItem("al_tts_pitch", String(preset.pitch));
      const rEl = el("set-rate"), pEl = el("set-pitch");
      if (rEl) { rEl.value = preset.rate; el("rate-val").textContent = preset.rate.toFixed(2); }
      if (pEl) { pEl.value = preset.pitch; el("pitch-val").textContent = preset.pitch.toFixed(2); }
      this.syncTtsStyleSeg();
      toast("已应用「" + this._ttsStyleName(style) + "」风格");
    },
    syncTtsStyleSeg() {
      const seg = el("tts-style-seg");
      if (!seg) return;
      const cur = state.ttsStyle || "natural";
      seg.querySelectorAll(".seg-btn").forEach(b => b.classList.toggle("active", b.dataset.style === cur));
    },
    loadTtsUI() {
      const engEl = el("set-tts-engine");
      if (engEl) engEl.value = state.ttsEngine || "auto";
      const srvEl = el("set-tts-server");
      if (srvEl) srvEl.value = state.ttsServer || "";
      const srvHint = el("tts-server-state");
      if (srvHint) {
        srvHint.textContent = _ttsServerBase()
          ? "当前：电脑语音服务器 " + _ttsServerBase()
          : "当前：未配置（华为等无引擎机型会无声）";
      }
      const rEl = el("set-rate"), pEl = el("set-pitch"), vEl = el("set-vol");
      if (rEl) { rEl.value = state.ttsRate || 0.95; el("rate-val").textContent = (state.ttsRate || 0.95).toFixed(2); }
      if (pEl) { pEl.value = state.ttsPitch || 1.02; el("pitch-val").textContent = (state.ttsPitch || 1.02).toFixed(2); }
      if (vEl) { vEl.value = state.ttsVolume || 1.0; el("vol-val").textContent = (state.ttsVolume || 1.0).toFixed(2); }
      this.syncTtsStyleSeg();
      this.populateVoices();
    },
    testTts() {
      const sample = (state.curLang === "en-US")
        ? "Hello! Today we are going to learn something fun together. Are you ready? Let's begin!"
        : "同学们好，今天我们一起来学习一个有趣的知识点。准备好了吗？我们开始吧！";
      // APK 离线包：用手机/平板系统自带引擎试音
      // 引擎还没就绪时原生侧会排队、就绪后自动朗读，这里不当作失败
      if (_nativePresent()) {
        unlockTTS();
        speak(sample);
        if (!_nativeAvail()) this.ttsSelfTest();
        return;
      }
      if (!("speechSynthesis" in window)) { _ttsNoEngineHint(); return; }
      unlockTTS();
      speak(sample);
    },

    // ---------- 🩺 语音自检（装到手机/平板上「没声音」时的定位工具）----------
    _nativeDiagObj() {
      try {
        const s = window.ALNative && window.ALNative.diagnose ? window.ALNative.diagnose() : "";
        return s ? JSON.parse(s) : null;
      } catch (e) { return null; }
    },
    ttsSelfTest() {
      const box = el("voice-diag");
      let html = "";
      if (_nativePresent()) {
        const d = this._nativeDiagObj() || {};
        const ok = !!d.ready;
        const srv = _ttsServerBase();
        // 第一行直接回答「这台机器现在到底靠什么出声」——用户最需要看的就是这个
        if (srv) {
          html += `<div class="vd-ok">▶️ 当前朗读方式：电脑语音服务器（${esc(srv)}）</div>`;
          html += `<div class="vd-line">电脑关机 / 手机不在同一 WiFi / 电脑防火墙拦了端口 → 都会没声音。点下方 <b>🔌 测试语音服务器</b> 一键验证。</div>`;
        } else if (ok) {
          html += `<div class="vd-ok">▶️ 当前朗读方式：手机系统语音引擎（${esc(d.engine || "系统默认")}）</div>`;
        } else {
          html += `<div class="vd-bad">▶️ 当前朗读方式：❌ 无可用引擎 —— 这就是「没声音」的原因</div>`;
        }
        html += `<div class="vd-line">系统引擎：${ok ? "✅ 可用" : "❌ 不可用"}　Android ${esc(String(d.sdk || "?"))}（${esc(d.brand || "?")}）</div>`;
        html += `<div class="vd-line">当前引擎：${esc(d.engine || "（无）")}　默认引擎：${esc(d.defaultEngine || "（无）")}</div>`;
        html += `<div class="vd-line">中文语言包：${esc(d.lang === "ok" ? "正常" : (d.lang === "missing-data" ? "缺少语音数据（需下载）" : (d.lang === "not-supported" ? "不支持中文" : esc(String(d.lang || "未知")))))}</div>`;
        const engs = d.engines || [];
        html += `<div class="vd-line">检测到的引擎（${engs.length} 个）：${esc(engs.join("、") || "一个都没有")}</div>`;
        if (d.lastError) html += `<div class="vd-line">最近错误：${esc(d.lastError)}（已重试 ${esc(String(d.retry || 0))} 次）</div>`;
        if (_cloudLastErr) html += `<div class="vd-line">最近取音频失败：${esc(_cloudLastErr)}</div>`;
        if (!srv && !ok) {
          // 华为等机型出厂既没有引擎、也没法安装语音包 —— 唯一可行的是「电脑当语音服务器」
          html += `<div class="vd-tip"><b>这台手机没有系统语音引擎（华为等机型常见，且设置里也没有「文字转语音」选项）。</b><br>解决办法：在下方「电脑语音服务器地址」里填电脑的局域网 IP（形如 <b>192.168.1.5:8000</b>）→ 点 <b>💾 保存</b> → 点 <b>🔌 测试语音服务器</b>。电脑上用「启动_AL系统_语音版.bat」启动着，手机连同一个 WiFi，就能出声（音质比手机引擎好得多）。</div>`;
        } else if (!ok && srv) {
          html += `<div class="vd-tip">手机本地没有引擎，但已配好电脑语音服务器，朗读会走服务器出声。点 <b>🔌 测试语音服务器</b> 确认能连上。</div>`;
        } else if (!srv && ok && d.lang !== "ok") {
          html += `<div class="vd-tip">引擎在，但中文语音包不完整：可去系统语音设置下载中文语音数据；或直接改用「电脑语音服务器」更省事。</div>`;
        } else if (!srv) {
          html += `<div class="vd-tip">引擎正常。若还是没声音，请检查手机<b>媒体音量</b>是否被调成 0，或是否插着耳机/连着蓝牙音箱。想要更好的音质，可填「电脑语音服务器地址」改用电脑朗读。</div>`;
        }
      } else if (!("speechSynthesis" in window)) {
        html = `<div class="vd-bad">当前环境是普通浏览器且不支持语音合成（Web Speech API）。请改用 <b>Chrome</b> 或 <b>Edge</b>，并通过地址栏直接打开 <b>${esc(location.origin)}</b>（不要双击 index.html 或在预览面板操作）。</div>`;
      } else {
        const vs = window.speechSynthesis.getVoices() || [];
        const zh = vs.filter(v => v.lang && v.lang.toLowerCase().startsWith("zh"));
        html = `<div class="vd-ok">✅ 浏览器支持语音合成</div>` +
               `<div class="vd-line">可用嗓音共 ${vs.length} 个，其中中文 ${zh.length} 个</div>`;
      }
      if (box) { box.style.display = "block"; box.innerHTML = html; }
      try {
        toast(_nativePresent()
          ? (_ttsServerBase() ? "自检完成：朗读走电脑语音服务器" : ((this._nativeDiagObj() || {}).ready ? "语音引擎正常" : "未检测到可用的语音引擎，请看下方自检结果"))
          : "自检完成");
      } catch (e) {}
    },
    openTtsSettings() {
      if (!_nativePresent() || !window.ALNative.openTtsSettings) {
        toast("该功能只在装成 App 手机/平板上可用");
        return;
      }
      const ok = window.ALNative.openTtsSettings();
      toast(ok ? "已打开系统语音设置：请选择语言为「中文」的引擎" : "没打开系统的语音设置页，请手动到「设置 → 无障碍/语言和输入法 → 文字转语音输出」");
    },
    reinitTts() {
      if (!_nativePresent() || !window.ALNative.reinit) { toast("该功能只在装成 App 手机/平板上可用"); return; }
      try { window.ALNative.reinit(); } catch (e) {}
      toast("正在重新初始化语音引擎…");
      const self = this;
      setTimeout(function () { self.ttsSelfTest(); }, 1800);
    },


    // ---------- 精准学（讯飞式 测-学-练-测 闭环） ----------
    async loadPrecUnits() {
      try {
        const r = await api("GET", "/api/precision/units");
        state.precUnits = r.units || [];
        const subjects = [...new Set(state.precUnits.map(u => u.subject))];
        const sel = el("prec-subject");
        sel.innerHTML = subjects.map(s => `<option value="${esc(s)}">${esc(s)}</option>`).join("");
        if (subjects.length) { state.precSubject = subjects[0]; sel.value = subjects[0]; }
        this.onPrecSubject();
        this.loadPrecProgress();
        this.applyPendingResume();
        this.saveResumeSoon();
      } catch (e) { toast(e.message); }
    },

    // ---------- 📊 学习进度总览 ----------
    async loadPrecProgress() {
      try {
        const r = await api("GET", "/api/precision/progress");
        state.precProgress = r;
        this.renderPrecProgress();
      } catch (e) { /* 进度拉取失败不影响主流程 */ }
    },
    renderPrecProgress() {
      const box = el("prec-progress");
      if (!box) return;
      const d = state.precProgress;
      if (!d) { box.innerHTML = ""; return; }
      const dist = d.dist || {};
      const total = d.total || 0;
      const seg = (n) => total ? (n * 100 / total) : 0;
      const bar = total ? `<div class="pp-bar">
          <span class="pp-seg pp-mastered" style="width:${seg(dist.mastered || 0)}%"></span>
          <span class="pp-seg pp-familiar" style="width:${seg(dist.familiar || 0)}%"></span>
          <span class="pp-seg pp-know" style="width:${seg(dist.know || 0)}%"></span>
          <span class="pp-seg pp-weak" style="width:${seg(dist.weak || 0)}%"></span>
          <span class="pp-seg pp-untested" style="width:${seg(dist.untested || 0)}%"></span>
        </div>` : `<div class="pp-bar pp-empty"></div>`;
      const last = d.last_retest;
      let lastHtml = "";
      if (last) {
        const gain = (last.weak_before || 0) - (last.weak_after || 0);
        lastHtml = `<div class="pp-last">
          🔁 上次${last.scope === "weak" ? "再测" : "诊断"}：${(last.created_at || "").slice(0, 10)} ·
          答对 ${last.correct || 0}/${last.total || 0} ·
          <b class="${gain > 0 ? "ok" : ""}">薄弱项 ${last.weak_before || 0} → ${last.weak_after || 0}${gain > 0 ? "（攻克 " + gain + " 个）" : ""}</b>
        </div>`;
      }
      // 分学科进度（只显示已测过的，最多 6 个）
      const subjRows = (d.by_subject || []).filter(s => s.tested > 0).slice(0, 6).map(s =>
        `<div class="pp-subj"><span class="pp-subj-name">${esc(s.subject)}</span>
          <span class="pp-subj-bar"><span style="width:${s.mastery_pct || 0}%"></span></span>
          <span class="pp-subj-num">${s.mastered}/${s.total}</span></div>`).join("");
      box.innerHTML = `
        <div class="pp-head">
          <span class="pp-title">📊 我的学习进度</span>
          <span class="pp-rate">掌握率 <b>${d.mastery_pct || 0}%</b> · 已测 ${d.coverage_pct || 0}%</span>
        </div>
        ${bar}
        <div class="pp-legend">
          <span><i class="dot green"></i>掌握 ${dist.mastered || 0}</span>
          <span><i class="dot yellow"></i>熟悉 ${dist.familiar || 0}</span>
          <span><i class="dot yellow"></i>了解 ${dist.know || 0}</span>
          <span><i class="dot red"></i>薄弱 ${dist.weak || 0}</span>
          <span><i class="dot gray"></i>未测 ${dist.untested || 0}</span>
          <span class="pp-total">共 ${total} 个知识点</span>
        </div>
        ${lastHtml}
        ${subjRows ? `<div class="pp-subjects">${subjRows}</div>` : ""}`;
    },
    onPrecSubject() {
      state.precSubject = el("prec-subject").value;
      const grades = [...new Set(state.precUnits.filter(u => u.subject === state.precSubject).map(u => u.grade))];
      const sel = el("prec-grade");
      sel.innerHTML = grades.map(g => `<option value="${esc(g)}">${esc(g)}</option>`).join("");
      if (grades.length) { state.precGrade = grades[0]; sel.value = grades[0]; }
      this.onPrecGrade();
    },
    onPrecGrade() {
      state.precGrade = el("prec-grade").value;
      this.renderPrecGraph();
    },
    async renderPrecGraph() {
      const g = el("prec-graph");
      if (!state.precSubject || !state.precGrade) { g.innerHTML = ""; return; }
      g.innerHTML = `<div class="empty">正在加载「${esc(state.precSubject)} · ${esc(state.precGrade)}」的知识图谱…</div>`;
      try {
        const r = await api("GET", "/api/precision/graph?subject=" + encodeURIComponent(state.precSubject) +
          "&grade=" + encodeURIComponent(state.precGrade));
        state.precGraph = r;
        this.paintGraph(r.nodes || []);
      } catch (e) {
        g.innerHTML = `<div class="empty">加载图谱失败：${esc(e.message)}</div>`;
      }
    },
    paintGraph(nodes) {
      const g = el("prec-graph");
      if (!nodes.length) { g.innerHTML = `<div class="empty">该学科/年级暂无知识点</div>`; return; }
      g.innerHTML = `<div class="graph-grid">` + nodes.map(n => `
        <div class="gcard ${n.color}" data-cid="${esc(n.course_id)}">
          <div class="gcard-title">${esc(n.title)}</div>
          <div class="gcard-meta">${MASTERY_LABEL[n.level] || "未测"}</div>
          <div class="gcard-actions">
            <button class="btn ghost tiny" onclick="UI.openLessonById('${esc(n.course_id)}')">📖 学</button>
            <button class="btn ghost tiny" onclick="UI.startPractice('${esc(n.course_id)}')">✏️ 练</button>
          </div>
        </div>`).join("") + `</div>`;
    },
    async startDiagnose() {
      if (!state.precSubject || !state.precGrade) return toast("请先选择学科和年级");
      el("prec-practice").style.display = "none";
      el("prec-mistakes").style.display = "none";
      const box = el("prec-diag");
      box.style.display = "block";
      box.innerHTML = `<div class="empty">📋 正在生成摸底诊断题（本地模型较慢，请稍候）…</div>`;
      try {
        const r = await api("POST", "/api/precision/diagnose",
          { subject: state.precSubject, grade: state.precGrade });
        state.precDiag = r;
        state.precDiagAnswers = {};
        this.renderDiag(r);
      } catch (e) {
        box.innerHTML = `<div class="empty">诊断生成失败：${esc(e.message)}</div>`;
      }
    },
    renderDiag(r) {
      const box = el("prec-diag");
      const qs = r.questions || [];
      let html = `<div class="panel-title">📋 摸底诊断 · ${esc(r.subject)} ${esc(r.grade)}（共 ${qs.length} 题，全部答完点提交）</div>`;
      const labels = ["A","B","C","D"];
      html += qs.map((q, i) => `
        <div class="diag-q">
          <div class="dq-stem"><b>${i + 1}.</b> ${plainMath(esc(q.stem))}<span class="answer-blank">(　　)</span></div>
          <div class="choice-opts">
            ${q.options.map((o, oi) => `
              <label class="choice-row"><span class="choice-lbl">${labels[oi]||oi}.</span> <span class="choice-txt">${plainMath(esc(o))}</span><input type="radio" name="dq_${esc(q.qid)}" value="${oi}" onchange="UI.pickDiag('${esc(q.qid)}',${oi})"></label>
            `).join("")}
          </div>
        </div>`).join("");
      html += `<div class="btn-row"><button class="btn btn-primary" onclick="UI.submitDiagnose()">提交诊断</button>
        <button class="btn ghost small" onclick="UI.diagSaveExit()">保存并稍后继续（下次打开自动恢复）</button></div>`;
      box.innerHTML = html;
      renderMath(box);
      this._diagProgress();
    },
    pickDiag(qid, oi) {
      state.precDiagAnswers[qid] = oi;
      this._diagProgress();
      this.saveResumeSoon();
    },
    _diagProgress() {
      const box = el("diag-progress");
      if (!box || !state.precDiag) return;
      const total = (state.precDiag.questions || []).length;
      const done = Object.keys(state.precDiagAnswers || {}).length;
      const pct = total ? Math.round(done / total * 100) : 0;
      box.innerHTML = `<div class="dp-bar"><span style="width:${pct}%"></span></div>
        <span class="dp-text">已答 ${done}/${total}${done >= total ? " · 可以提交啦 ✅" : ""}</span>`;
    },
    _restoreDiagPicks() {
      const ans = state.precDiagAnswers || {};
      Object.keys(ans).forEach(qid => {
        document.querySelectorAll('input[name="dq_' + qid + '"]').forEach(inp => {
          if (String(inp.value) === String(ans[qid])) inp.checked = true;
        });
      });
      this._diagProgress();
    },
    async diagSaveExit() {
      await this.saveResume(true);
      toast("已保存进度，下次打开首页点「继续学习」即可接着答 📌");
    },
    async submitDiagnose() {
      if (!state.precDiag) return;
      const answered = Object.keys(state.precDiagAnswers).length;
      const total = (state.precDiag.questions || []).length;
      if (answered < total) return toast(`还有 ${total - answered} 题未作答`);
      try {
        const r = await api("POST", "/api/precision/diagnose/grade",
          { diag_id: state.precDiag.diag_id, answers: state.precDiagAnswers });
        state.precDiag = null;
        state._precLastPanel = "diag";
        const box = el("prec-diag");
        const weak = r.weak || [];
        const results = r.results || [];
        const scope = r.scope || "full";
        const before = r.weak_before || 0, after = r.weak_after || 0, gain = r.fixed_count || 0;
        const stillRes = results.filter(x => !x.correct);
        let html = `<div class="panel-title">📊 ${scope === "weak" ? "薄弱项再测" : "诊断"}结果 · 答对 ${r.correct_count || 0}/${r.total || results.length}</div>`;
        // 前后对比（有基线才显示，避免首次诊断时出现 0→0 的无意义对比）
        if (before > 0) {
          html += `<div class="rt-compare">
            <div class="rt-col"><span class="rt-num">${before}</span><span class="rt-lbl">${scope === "weak" ? "再测前薄弱项" : "开始前薄弱项"}</span></div>
            <div class="rt-arrow">→</div>
            <div class="rt-col ${after < before ? "good" : ""}"><span class="rt-num">${after}</span><span class="rt-lbl">现在的薄弱项</span></div>
            <div class="rt-gain ${gain > 0 ? "up" : ""}">${gain > 0
              ? `🎉 攻克了 <b>${gain}</b> 个薄弱知识点`
              : (after < before ? "薄弱项减少了一点，继续加油" : "这次没有减少薄弱项 —— 先点下面每条的「📖 学」补讲解，再「✏️ 练」做几道，然后回来再测")}</div>
          </div>`;
        }
        html += `<div class="diag-summary">` + results.map(res => `
          <span class="diag-pill ${res.correct ? 'ok' : 'bad'}" ${res.correct ? '' : `onclick="UI.openLessonById('${esc(res.topic_id)}')" title="点我学这个知识点"`}>${esc(res.topic_title)} ${res.correct ? '✓' : '✗'}</span>
        `).join("") + `</div>`;
        if ((r.fixed || []).length) {
          html += `<div class="rt-list ok"><div class="rt-list-title">✅ 本次拿下（${r.fixed.length}）</div>
            <div class="rt-pills">${r.fixed.map(t => `<span class="rt-pill ok">${esc(t)}</span>`).join("")}</div></div>`;
        }
        if (stillRes.length) {
          html += `<div class="rt-list bad"><div class="rt-list-title">🔴 仍是薄弱（${stillRes.length}）—— 按顺序补一遍，再回来测</div>`
            + stillRes.map(x => `<div class="rt-still">
                <span class="rt-still-name">${esc(x.topic_title)}</span>
                <button class="btn ghost tiny" onclick="UI.openLessonById('${esc(x.topic_id)}')">📖 学</button>
                <button class="btn ghost tiny" onclick="UI.startPractice('${esc(x.topic_id)}')">✏️ 练</button>
              </div>`).join("")
            + `</div>`;
        } else if (before > 0) {
          html += `<div class="diag-weak ok">🎉 薄弱项已清零，图谱全绿！可以换个知识点「✏️ 练」巩固，或点「📕 错题本」把错题清一清。</div>`;
        }
        html += `<div class="btn-row">
            <button class="btn small" onclick="UI.retestWeak()">🔁 再测薄弱项</button>
            <button class="btn ghost small" onclick="UI.showMistakes()">📕 错题本</button>
            <button class="btn ghost small" onclick="UI.renderPrecGraph();UI.loadPrecProgress()">刷新图谱与进度</button>
          </div>`;
        box.innerHTML = html;
        renderMath(box);
        if (r.graph) this.paintGraph(r.graph.nodes || []);
        this.loadPrecProgress();
        this.saveResumeSoon();
      } catch (e) { toast(e.message); }
    },
    async retestWeak() {
      if (!state.precSubject || !state.precGrade) return toast("请先选择学科和年级");
      if (!state.precGraph) { await this.renderPrecGraph(); }
      const nodes = (state.precGraph && state.precGraph.nodes) || [];
      const weak = nodes.filter(n => (n.level || 0) <= 1).map(n => n.course_id);
      if (!weak.length) return toast("当前没有薄弱项可再测 🎉 先做一次诊断找找薄弱项吧");
      el("prec-practice").style.display = "none";
      el("prec-mistakes").style.display = "none";
      state._precLastPanel = "diag";
      const box = el("prec-diag");
      box.style.display = "block";
      box.innerHTML = `<div class="empty">🔁 正在为 ${weak.length} 个薄弱知识点生成再测题…</div>`;
      try {
        const r = await api("POST", "/api/precision/diagnose",
          { subject: state.precSubject, grade: state.precGrade, course_ids: weak });
        state.precDiag = r;
        state.precDiagAnswers = {};
        state._diagMeta = { scope: r.scope || "weak", weak_before: r.weak_before,
                            weak_total: r.weak_total, covered: r.covered };
        this.renderDiag(r);
        if ((r.weak_total || 0) > (r.covered || 0)) {
          const g = el("diag-progress");
          if (g) g.insertAdjacentHTML("afterend",
            `<div class="diag-note">本次覆盖 ${r.covered} 个知识点（薄弱项共 ${r.weak_total} 个，其余的下一轮再测）。</div>`);
        }
        this.saveResumeSoon();
      } catch (e) { box.innerHTML = `<div class="empty">再测生成失败：${esc(e.message)}</div>`; }
    },
    async startPractice(course_id) {
      if (!course_id) return;
      el("prec-diag").style.display = "none";
      el("prec-mistakes").style.display = "none";
      const box = el("prec-practice");
      box.style.display = "block";
      box.innerHTML = `<div class="panel-title">✏️ 分层练习</div>
        <div class="tier-row">
          <button class="btn ghost small" onclick="UI.genPractice('${esc(course_id)}','基础')">基础</button>
          <button class="btn ghost small" onclick="UI.genPractice('${esc(course_id)}','提升')">提升</button>
          <button class="btn ghost small" onclick="UI.genPractice('${esc(course_id)}','拓展')">拓展</button>
        </div>
        <div id="practice-body" class="empty">选一个层级开始练习（基础=直接应用，提升=变式综合，拓展=迁移开放）</div>`;
      state._practiceCourse = course_id;
    },
    async genPractice(course_id, tier) {
      const body = el("practice-body");
      body.className = "empty"; body.textContent = `📝 正在生成「${tier}」层级的 5 道练习题…`;
      try {
        const r = await api("POST", "/api/precision/practice", { course_id, tier });
        state.precPractice = r;          // { questions:[{qid,stem,options,idx}], total }
        state._practiceAnswers = {};     // { qid: user_answer }
        state._practiceCourse = course_id;
        state._practiceTier = tier;
        state._precLastPanel = "practice";
        this._renderPractice(r, tier);
        this.saveResumeSoon();
      } catch (e) {
        body.textContent = "练习生成失败：" + e.message;
      }
    },
    _renderPractice(r, tier, title) {
      const labels = ["A","B","C","D","E","F"];
      const qs = r.questions || [];
      const host = el("practice-body");
      let html = `<div class="prac-header"><span class="prac-count">${title ? esc(title) + " · " : ""}${tier ? esc(tier) + " · " : ""}共 ${qs.length} 题</span><span class="prac-hint">全部作答后提交</span></div>`;
      html += `<div class="diag-progress" id="practice-progress"></div>`;
      qs.forEach((q, qi) => {
        html += `<div class="diag-q" data-pq="${esc(q.qid)}">
          <div class="dq-stem"><b>${q.idx || (qi+1)}.</b> ${plainMath(esc(q.stem))}<span class="answer-blank">(　　)</span></div>
          <div class="choice-opts">
            ${(q.options || []).map((o, oi) =>
              `<label class="choice-row"><span class="choice-lbl">${labels[oi]||oi}.</span> <span class="choice-txt">${plainMath(esc(o))}</span><input type="radio" name="pq_${esc(q.qid)}" value="${oi}" onchange="UI.pickPractice('${esc(q.qid)}',${oi})"></label>`
            ).join("")}
          </div></div>`;
      });
      html += `<div class="btn-row" style="margin-top:12px"><button class="btn btn-primary" onclick="UI.submitPractice()">📤 提交全部答案并看解析</button>
        <button class="btn ghost small" onclick="UI.practiceSaveExit()">保存进度，稍后继续</button></div>`;
      html += `<div id="practice-feedback"></div>`;
      host.className = "";
      host.innerHTML = html;
      renderMath(host);
      // 断点续学：回填上次已选的答案
      Object.keys(state._practiceAnswers || {}).forEach(qid => {
        document.querySelectorAll('input[name="pq_' + qid + '"]').forEach(inp => {
          if (String(inp.value) === String(state._practiceAnswers[qid])) inp.checked = true;
        });
      });
      this._practiceProgress();
    },
    _practiceProgress() {
      const box = el("practice-progress");
      if (!box || !state.precPractice) return;
      const total = (state.precPractice.questions || []).length;
      const done = Object.keys(state._practiceAnswers || {}).length;
      box.innerHTML = `<div class="dp-bar"><span style="width:${total ? Math.round(done / total * 100) : 0}%"></span></div>
        <span class="dp-text">已答 ${done}/${total}${done >= total ? " · 可以提交啦 ✅" : ""}</span>`;
    },
    async practiceSaveExit() {
      await this.saveResume(true);
      toast("已保存练习进度，下次打开首页点「继续学习」接着做 ✏️");
    },
    pickPractice(qid, oi) {
      state._practiceAnswers[qid] = oi;
      this._practiceProgress();
      this.saveResumeSoon();
    },
    async submitPractice() {
      if (!state.precPractice) return;
      const answers = (state.precPractice.questions || []).map(q => ({
        qid: q.qid,
        user_answer: state._practiceAnswers[q.qid] !== undefined ? state._practiceAnswers[q.qid] : null
      }));
      const unanswered = answers.filter(a => a.user_answer === null);
      if (unanswered.length) return toast(`还有 ${unanswered.length} 题未作答，请先完成所有题目`);
      try {
        const r = await api("POST", "/api/precision/practice/grade", { answers });
        const fb = el("practice-feedback");
        const results = r.results || [];
        // 每道题的结果
        let html = `<div class="pf-score">✅ 得分：<b>${r.correct_count}/${r.total}</b></div>`;
        results.forEach((res, i) => {
          if (res.error) return;
          const q = (state.precPractice.questions || [])[i];
          const cls = res.correct ? "ok" : "bad";
          const icon = res.correct ? "✅" : "❌";
          html += `<div class="pf ${cls}">
            <div><b>${icon} 第${(q&&q.idx)||(i+1)}题</b>${res.saved_mistake ? ' <small>(已入错题本)</small>' : ''}</div>
            ${!res.correct ? `<div style="font-size:12px;color:var(--muted);margin:2px 0">正确答案：${esc(res.answer)}</div>` : ""}
            <div class="pf-ex">${nl2br(esc(res.explanation))}</div>
          </div>`;
        });
        fb.innerHTML = html;
        renderMath(fb);
        state.precPractice = null;
      } catch (e) { toast(e.message); }
    },
    async showMistakes(filter) {
      el("prec-diag").style.display = "none";
      el("prec-practice").style.display = "none";
      const box = el("prec-mistakes");
      box.style.display = "block";
      box.innerHTML = `<div class="empty">📕 正在加载错题本…</div>`;
      state._precLastPanel = "mistakes";
      state._mistakeFilter = filter || state._mistakeFilter || "all";
      try {
        const url = state._mistakeFilter === "review"
          ? "/api/precision/mistakes?only_review=1"
          : (state._mistakeFilter && state._mistakeFilter !== "all"
            ? "/api/precision/mistakes?category=" + encodeURIComponent(state._mistakeFilter)
            : "/api/precision/mistakes");
        const [r, prog] = await Promise.all([
          api("GET", url),
          api("GET", "/api/mistakes/progress").catch(() => null),
        ]);
        const ms = r.mistakes || [];
        state._mistakeCache = {};
        ms.forEach(m => { state._mistakeCache[m.id] = m; });
        // ---- 顶部：错题掌握进度 + 薄弱知识点排行 ----
        let head = "";
        if (prog) {
          const pct = prog.mastery_pct || 0;
          head += `<div class="mk-progress">
            <div class="mkp-head"><span>📕 错题掌握进度</span><span class="mkp-num">${prog.mastered || 0}/${prog.total || 0} 已掌握 · ${pct}%</span></div>
            <div class="mkp-bar"><span style="width:${pct}%"></span></div>
            <div class="mkp-stats">
              <span class="mkp-chip due">🔔 待复习 ${prog.due_today || 0}</span>
              <span class="mkp-chip">📌 未掌握 ${prog.unmastered || 0}</span>
              <span class="mkp-chip ok">✅ 已掌握 ${prog.mastered || 0}</span>
              <span class="mkp-chip">🔄 重做 ${prog.redo_total || 0} 次 · 答对 ${prog.redo_correct || 0}</span>
            </div>
            ${this._mkTrendBar(prog.trend || [])}
          </div>`;
          const wt = prog.weak_topics || [];
          if (wt.length) {
            head += `<div class="mk-topics"><div class="mkt-title">🔴 错得最多的知识点 —— 补讲解再练同类题，比反复看答案有用</div>`
              + wt.slice(0, 5).map(t => `<div class="mkt-row">
                  <span class="mkt-name">${esc(t.title)}</span>
                  <span class="mkt-meta">错 ${t.total} · 未掌握 ${t.unmastered}${t.due ? " · 待复习 " + t.due : ""}</span>
                  <button class="btn ghost tiny" onclick="UI.openLessonById('${esc(t.course_id)}')">📖 学</button>
                  <button class="btn ghost tiny" onclick="UI.startPractice('${esc(t.course_id)}')">✏️ 练</button>
                </div>`).join("") + `</div>`;
          }
        }
        const stats = prog || await api("GET", "/api/mistakes/stats").catch(() => null);
        let filterHtml = `<div class="mk-filter">
          <button class="mk-fbtn ${state._mistakeFilter==='all'?'active':''}" onclick="UI.showMistakes('all')">全部</button>
          <button class="mk-fbtn ${state._mistakeFilter==='review'?'active':''}" onclick="UI.showMistakes('review')">
            🔔 待复习 ${stats && stats.due_today ? '('+stats.due_today+')' : ''}
          </button>
          <button class="mk-fbtn ${state._mistakeFilter==='概念混淆'?'active':''}" onclick="UI.showMistakes('概念混淆')">概念混淆</button>
          <button class="mk-fbtn ${state._mistakeFilter==='计算错误'?'active':''}" onclick="UI.showMistakes('计算错误')">计算错误</button>
          <button class="mk-fbtn ${state._mistakeFilter==='审题不清'?'active':''}" onclick="UI.showMistakes('审题不清')">审题不清</button>
          <button class="mk-fbtn ${state._mistakeFilter==='思路错误'?'active':''}" onclick="UI.showMistakes('思路错误')">思路错误</button>
        </div>`;
        if (!ms.length) {
          box.innerHTML = head + filterHtml + `<div class="empty">${state._mistakeFilter==='review' ? '今天没有待复习的错题，继续保持！🎉' : '错题本还是空的，多做练习就会自动收录错题 📕'}</div>`;
          this.saveResumeSoon();
          return;
        }
        const labels = ["A","B","C","D","E","F"];
        const listHtml = ms.map((m) => {
          const opts = Array.isArray(m.options) ? m.options : null;
          let myIdx = null;
          if (m.user_answer !== null && m.user_answer !== undefined && m.user_answer !== "") {
            const v = parseInt(m.user_answer, 10);
            if (!isNaN(v)) myIdx = v;
          }
          const optHtml = opts ? `<div class="mk-opts">${opts.map((o, oi) => {
            const isRight = String(oi) === String(m.answer);
            const isMine = myIdx !== null && oi === myIdx;
            const cls = isRight ? "mk-right" : (isMine ? "mk-wrong" : "");
            const mark = isRight ? "✔ " : (isMine ? "✘ " : "　");
            return `<span class="${cls}">${mark}${labels[oi]||oi}. ${esc(o)}${isMine ? ' <small>（我选的）</small>' : ''}</span>`;
          }).join("")}</div>` : "";
          const rightTxt = (opts && opts[m.answer] !== undefined) ? opts[m.answer] : String(m.answer);
          const mineTxt = (opts && myIdx !== null && opts[myIdx] !== undefined) ? opts[myIdx] : null;
          const catBadge = m.category ? `<span class="mk-cat mk-cat-${m.category}">${esc(m.category)}</span>` : "";
          const reviewBadge = m.mastered ? `<span class="mk-ok">✅ 已掌握</span>`
            : (m.due_review ? `<span class="mk-due">🔔 待复习</span>`
              : `<span class="mk-review-count">复习 ${m.review_count || 0} 次 · 重做 ${m.redo_count || 0} 次</span>`);
          return `<div class="mistake" id="mk-${m.id}">
            <div class="mk-head">
              <div class="mk-tier">${esc(m.tier)}</div>
              ${catBadge}
              ${reviewBadge}
            </div>
            <div class="mk-stem">${esc(m.stem)}</div>
            ${optHtml}
            ${mineTxt ? `<div class="mk-mine">✘ 我选的：<b>${esc(mineTxt)}</b>　✔ 正确：<b>${esc(String(rightTxt))}</b></div>` : ""}
            <div class="mk-ex">💡 解析：${esc(m.explanation || '')}</div>
            <div class="mk-actions">
              ${!m.mastered ? `<button class="btn small btn-primary" onclick="UI.toggleRedo(${m.id})">🔄 重做这道</button>` : ''}
              ${!m.mastered ? `<button class="btn small ghost" onclick="UI.markMistakeReviewed(${m.id})">✓ 复习过了</button>` : ''}
              <button class="btn small ghost" onclick="UI.showSimilar(${m.id})">🔁 同类题练习</button>
              ${!m.mastered ? `<button class="btn small ghost" onclick="UI.markMistakeMastered(${m.id})">✓ 已掌握</button>` : ''}
            </div>
            <div class="mk-redo" id="redo-${m.id}"></div>
          </div>`;
        }).join("");
        box.innerHTML = head + filterHtml + `<div class="panel-title">📕 错题本（${state._mistakeFilter==='review'?'待复习':'共'} ${ms.length} 条）</div>` + listHtml;
        renderMath(box);
        this.saveResumeSoon();
      } catch (e) { box.innerHTML = `<div class="empty">加载错题本失败：${esc(e.message)}</div>`; }
    },

    // 近 7 日新增错题小柱图
    _mkTrendBar(trend) {
      if (!trend.length) return "";
      const max = Math.max(1, ...trend.map(t => t.added || 0));
      return `<div class="mkp-trend">` + trend.map(t =>
        `<div class="mkp-day" title="${esc(t.date)}：新增 ${t.added || 0} 题">
           <span class="mkp-day-bar" style="height:${Math.max(6, Math.round((t.added || 0) / max * 100))}%"></span>
           <span class="mkp-day-lbl">${esc((t.date || "").slice(5))}</span>
         </div>`).join("") + `</div>`;
    },

    // ---------- 错题重做闭环 ----------
    toggleRedo(id) {
      const host = document.getElementById("redo-" + id);
      if (!host) return;
      if (host.dataset.open === "1") { host.innerHTML = ""; host.dataset.open = "0"; return; }
      const m = (state._mistakeCache || {})[id];
      if (!m) return;
      const opts = Array.isArray(m.options) ? m.options : [];
      if (!opts.length) { toast("这道题没有选项，请点「同类题练习」巩固"); return; }
      const labels = ["A","B","C","D","E","F"];
      host.dataset.open = "1";
      host.innerHTML = `<div class="redo-box">
        <div class="redo-tip">🔁 先别看上面的解析 —— 自己重新做一遍，这才算真把错题变成会做的题。</div>
        <div class="redo-opts">
          ${opts.map((o, oi) => `<label class="redo-opt" id="ro-${id}-${oi}" onclick="UI.pickRedo(${id},${oi})">
            <span class="redo-lbl">${labels[oi] || oi}</span><span class="redo-txt">${esc(o)}</span>
          </label>`).join("")}
        </div>
        <div class="redo-actions">
          <button class="btn small btn-primary" onclick="UI.submitRedo(${id})">提交重做</button>
          <button class="btn small ghost" onclick="UI.toggleRedo(${id})">收起</button>
        </div>
        <div class="redo-result" id="ro-res-${id}"></div>
      </div>`;
      state._redoPick = state._redoPick || {};
      delete state._redoPick[id];
    },
    pickRedo(id, oi) {
      state._redoPick = state._redoPick || {};
      state._redoPick[id] = oi;
      const m = (state._mistakeCache || {})[id] || {};
      (Array.isArray(m.options) ? m.options : []).forEach((_, i) => {
        const e2 = document.getElementById("ro-" + id + "-" + i);
        if (e2) e2.classList.toggle("sel", i === oi);
      });
    },
    async submitRedo(id) {
      const pick = (state._redoPick || {})[id];
      if (pick === undefined || pick === null) return toast("先选一个答案再提交");
      const res = document.getElementById("ro-res-" + id);
      if (res) res.innerHTML = `<span class="redo-loading">判卷中…</span>`;
      try {
        const r = await api("POST", `/api/mistakes/${id}/redo`, { answer: pick });
        const m = (state._mistakeCache || {})[id] || {};
        const opts = Array.isArray(m.options) ? m.options : [];
        const rightTxt = (opts[r.answer] !== undefined) ? opts[r.answer] : r.answer;
        let html = `<div class="redo-verdict ${r.correct ? 'ok' : 'bad'}">${r.correct ? "✅ 答对了！" : "❌ 还是不对，看看解析再重做一次"}</div>`;
        html += `<div class="redo-ans">正确答案：<b>${esc(String(rightTxt))}</b></div>`;
        html += `<div class="redo-ex">💡 ${nl2br(esc(r.explanation || ""))}</div>`;
        html += `<div class="redo-chain">${r.mastered ? "🎉 已自动标记为「已掌握」，不用再复习这道了"
          : `已排入复习计划：下次复习 ${(r.next_review || "").slice(0, 10) || "—"}`}</div>`;
        if (res) { res.innerHTML = html; renderMath(res); }
        // 局部更新卡片状态，不整体重渲染（保留滚动位置）
        if (m) { m.redo_count = r.redo_count; m.redo_correct = r.redo_correct; m.review_count = r.review_count; if (r.mastered) m.mastered = 1; }
        const card = document.getElementById("mk-" + id);
        if (card) {
          const btn = card.querySelector(".mk-actions .btn-primary");
          if (r.correct && btn) btn.remove();
          if (r.mastered) {
            const head = card.querySelector(".mk-head");
            if (head) head.insertAdjacentHTML("beforeend", `<span class="mk-ok">✅ 已掌握</span>`);
            card.querySelectorAll(".mk-actions .btn").forEach(b => {
              if (b.textContent.includes("已掌握") && !b.textContent.includes("重做")) b.remove();
            });
          }
        }
        if (r.correct) { this.awardStars("mistake_redo", 2); this._ssXpToast("🔄 错题过关", "+2 ⭐ 成就点"); }
        this.saveResumeSoon();
      } catch (e) { if (res) res.innerHTML = `<span class="redo-bad">${esc(e.message)}</span>`; }
    },

    async markMistakeReviewed(mid) {
      try {
        await api("POST", `/api/mistakes/${mid}/review`);
        toast("已记录复习，下次复习时间已更新 📅");
        this.showMistakes(state._mistakeFilter);
      } catch (e) { toast(e.message); }
    },

    async markMistakeMastered(mid) {
      if (!confirm("确定标记这道题为已掌握吗？之后不会再提醒复习。")) return;
      try {
        await api("POST", `/api/mistakes/${mid}/mastered`);
        toast("太棒了！又掌握了一道错题 🎉");
        this.showMistakes(state._mistakeFilter);
      } catch (e) { toast(e.message); }
    },

    async showSimilar(mid) {
      try {
        const r = await api("GET", `/api/mistakes/${mid}/similar`);
        const sim = r.similar || [];
        if (!sim.length) { toast("暂无同类题"); return; }
        let html = `<div class="similar-box">
          <div class="panel-title">🔁 同类题练习（${sim.length} 道）</div>
          <p style="font-size:12px;color:var(--muted);margin:6px 0 12px">做完后可以对照答案，检验是否真正掌握了这一类题。</p>`;
        sim.forEach((q, i) => {
          const optHtml = q.options && q.options.length
            ? `<div class="mk-opts">${q.options.map((o, oi) => `<span>${String.fromCharCode(65+oi)}. ${esc(o)}</span>`).join('　')}</div>`
            : "";
          html += `<div class="mistake sim-q">
            <div class="mk-head"><div class="mk-tier">第 ${i+1} 题 · ${q.type==='choice'?'选择':q.type==='calc'?'计算':'填空'}</div>
              ${q.sub_point ? `<span class="mk-cat">${esc(q.sub_point)}</span>` : ''}
            </div>
            <div class="mk-stem">${esc(q.stem)}</div>
            ${optHtml}
            <details class="sim-ans"><summary>查看答案与解析</summary>
              <div><b>答案：</b>${esc(String(q.answer))}</div>
              <div style="margin-top:4px"><b>解析：</b>${esc(q.explanation || '')}</div>
            </details>
          </div>`;
        });
        html += `</div>`;
        // 插入到对应错题下面
        const mkEl = document.getElementById("mk-" + mid);
        if (mkEl) {
          let simBox = mkEl.nextElementSibling;
          if (simBox && simBox.classList.contains("similar-box")) {
            simBox.remove();
          } else {
            const div = document.createElement("div");
            div.innerHTML = html;
            mkEl.parentNode.insertBefore(div.firstElementChild, mkEl.nextSibling);
          }
        }
      } catch (e) { toast(e.message); }
    },
  };

  // ---------- 渲染辅助 ----------
  // ---------- 语音：识别与朗读 ----------
  function initSpeech() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return false;
    recognition = new SR();
    recognition.lang = state.curLang;
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onresult = (e) => {
      let interim = "", final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) final += t; else interim += t;
      }
      const input = el("chat-input");
      if (interim) input.value = final + interim;
      else if (final) input.value = final;
      state._finalTranscript = final || state._finalTranscript;
    };
    recognition.onend = () => {
      state.recognizing = false;
      const btn = el("mic-btn"); if (btn) btn.classList.remove("recording");
      const ft = state._finalTranscript; state._finalTranscript = "";
      const input = el("chat-input");
      if (ft && ft.trim()) {
        input.value = ft.trim();
        if (state.voiceMode) UI.send();
        else toast("已识别语音：" + ft.trim() + "（点发送或继续说）");
      }
    };
    recognition.onerror = (e) => {
      state.recognizing = false;
      const btn = el("mic-btn"); if (btn) btn.classList.remove("recording");
      if (e.error === "not-allowed") toast("麦克风权限被拒绝，请在浏览器地址栏允许麦克风");
      else if (e.error !== "aborted") toast("语音识别出错：" + e.error);
    };
    return true;
  }
  // 语音列表在部分浏览器异步加载，需缓存并监听 voiceschanged
  let _voices = [];
  function loadVoices() {
    try { _voices = window.speechSynthesis ? (window.speechSynthesis.getVoices() || []) : []; }
    catch (e) { _voices = []; }
  }
  function pickVoice(lang) {
    if (!_voices || !_voices.length) return null;
    const want = (lang || state.curLang || "zh-CN").toLowerCase();
    const base = want.slice(0, 2); // zh / en
    // 目标语言的候选
    const cand = _voices.filter(x => {
      const l = (x.lang || "").replace("_", "-").toLowerCase();
      return l === want || l.startsWith(base);
    });
    if (!cand.length) return null;
    // 神经网络 / 自然语音优先（更有感情）。覆盖桌面、iPad、Android 平板各平台高质量嗓音：
    //   Windows/Edge  : Xiaoxiao / Yunxi / Yunyang / 晓晓 / 云希 …（Neural 神经嗓音）
    //   iPad/iOS Siri : Yue / Ting-Ting / Mei-Jia / Sin-Ji / Yaoyao（需在系统设置里下载）
    //   Android/Chrome: Google 普通话（Enhanced）/ Google 國語 / Google US English …
    const preferByName = [
      "xiaoxiao", "xiaoyi", "yunxi", "yunyang", "yunjian", "晓晓", "云希", "云扬",
      "yue", "ting-ting", "tingting", "mei-jia", "meijia", "sin-ji", "sinji", "yaoyao", "yu",
      "google 普通话", "google 普通话（中国大陆）", "google 國語", "google 粤語",
      "google us english", "google uk english",
      "natural", "online", "neural", "premium", "enhanced", "siri",
      "aria", "jenny", "guy"
    ];
    for (const kw of preferByName) {
      const v = cand.find(x => (x.name || "").toLowerCase().includes(kw));
      if (v) return v;
    }
    // 其次：精确匹配 zh-CN / en-US
    const exact = cand.find(x => (x.lang || "").replace("_", "-").toLowerCase() === want);
    return exact || cand[0];
  }
  if ("speechSynthesis" in window) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = function () { loadVoices(); if (typeof UI !== "undefined" && UI.populateVoices) try { UI.populateVoices(); } catch (e) {} };
  }
  // ---------- 语音：朗读与停止 ----------
  let _speaking = false;  // 当前是否正在朗读
  function stopSpeak() {
    _cloudStop();   // 同时停止云端朗读（无云端时为空操作）
    _nativeStop();  // 同时停止本地离线朗读（非 APK 时为空操作）
    if (_ttsPump) { clearInterval(_ttsPump); _ttsPump = null; }
    stopResumeGuard();
    _ttsActiveU = null;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    _ttsChunks = [];
    _ttsIdx = 0;
    _ttsSegmentDone = true;
    _speaking = false;
    hideStopBtn();
  }
  function showStopBtn() {
    let btn = document.getElementById("tts-stop-btn");
    if (!btn) {
      btn = document.createElement("button");
      btn.id = "tts-stop-btn";
      btn.innerHTML = "⏹ 停止朗读";
      btn.title = "点击停止当前语音";
      btn.onclick = stopSpeak;
      document.body.appendChild(btn);
    }
    _speaking = true;
    btn.style.display = "flex";
  }
  function hideStopBtn() {
    const btn = document.getElementById("tts-stop-btn");
    if (btn) { btn.style.display = "none"; _speaking = false; }
    _karaokeHide();
  }

  // ---------- 📢 跟读面板：朗读时逐句高亮（分段引擎精确高亮；APK 原生整段显示） ----------
  function _karaokeShow(chunks) {
    const p = document.getElementById("karaoke-panel");
    if (!p || !chunks || !chunks.length) return;
    p.style.display = "block";
    p._krChunks = chunks;
    _karaokeUpdate(0);
  }
  function _karaokeShowNative(text) {
    const p = document.getElementById("karaoke-panel");
    if (!p) return;
    p.style.display = "block";
    p._krChunks = null;
    el("karaoke-meta").textContent = "🔊 正在朗读（跟读模式）";
    el("karaoke-current").textContent = text.slice(0, 120);
  }
  function _karaokeUpdate(idx) {
    const p = document.getElementById("karaoke-panel");
    if (!p || !p._krChunks) return;
    const chunks = p._krChunks;
    el("karaoke-meta").textContent = `🔊 正在朗读 ${Math.min(idx + 1, chunks.length)}/${chunks.length}`;
    const cur = el("karaoke-current");
    cur.textContent = chunks[idx] || "";
    cur.style.animation = "none"; void cur.offsetWidth; cur.style.animation = "";
  }
  function _karaokeHide() {
    const p = document.getElementById("karaoke-panel");
    if (p) { p.style.display = "none"; p._krChunks = null; }
  }

  // ---------- 语音：朗读与停止（健壮版，兼容 iPad / Android 平板） ----------
  let _ttsUnlocked = false;
  let _resumeTimer = null;

  // iOS/iPadOS 限制：Web Speech 必须在用户手势内首次触发，否则静默失败。
  // 首次点击/触摸时做一次「静默解锁」，之后程序化朗读（如 AI 讲解返回后的自动朗读）才有效。
  function unlockTTS() {
    if (_ttsUnlocked || !("speechSynthesis" in window)) return;
    try {
      const u = new SpeechSynthesisUtterance(" ");
      u.volume = 0;
      window.speechSynthesis.speak(u);
      _ttsUnlocked = true;
    } catch (e) {}
  }
  if ("speechSynthesis" in window) {
    const _unlockOnce = () => { unlockTTS(); };
    document.addEventListener("pointerdown", _unlockOnce);
    document.addEventListener("keydown", _unlockOnce);
  }

  function startResumeGuard() {
    stopResumeGuard();
    // iOS 长文本约 15s 会被自动暂停，每 9s resume 一次保活
    _resumeTimer = setInterval(() => {
      try { if (window.speechSynthesis.speaking) window.speechSynthesis.resume(); } catch (e) {}
    }, 9000);
  }
  function stopResumeGuard() {
    if (_resumeTimer) { clearInterval(_resumeTimer); _resumeTimer = null; }
  }

  // 等待语音列表就绪再朗读（兼容 Android Chrome 异步加载；避免空语音导致无声）
  function whenVoicesReady(cb) {
    if (!("speechSynthesis" in window)) { cb(); return; }
    let done = false;
    const run = () => { if (done) return; done = true; window.speechSynthesis.onvoiceschanged = function () { loadVoices(); if (typeof UI !== "undefined" && UI.populateVoices) try { UI.populateVoices(); } catch (e) {} }; cb(); };
    let tries = 0;
    const poll = () => {
      const vs = window.speechSynthesis.getVoices() || [];
      if (vs.length) { run(); return; }
      if (tries++ >= 20) { run(); return; }   // ~2s 超时也尝试（部分浏览器用默认语音）
      setTimeout(poll, 100);
    };
    window.speechSynthesis.onvoiceschanged = run;
    poll();
  }

  // ============ 朗读引擎（iPad / iOS Safari 兼容版）============
  // 关键：iPad 的 onend / onerror 经常不触发，因此「续播下一段」改用轮询 speechSynthesis.speaking
  // 从 true 变 false 作为可靠信号；onend 仅作快速路径。双保险，且单次只前进一段（防跳段/重复）。
  let _ttsChunks = [];          // 当前待播段落
  let _ttsIdx = 0;              // 当前段下标（单一真相）
  let _ttsLang = "zh-CN";
  let _ttsExpectSince = 0;      // 最近一次 speak 时间戳（grace 期内不算"已结束"）
  let _ttsPump = null;          // 轮询定时器
  let _ttsSegmentDone = false;  // 当前段是否已被 onend/pump 处理过（防重复前进）
  let _ttsActiveU = null;       // 当前活跃的 utterance（过滤上一轮残留回调）

  // 文本预处理：清理 LaTeX/公式、分数转口语，让朗读更像老师讲课
  // ====== 数学公式 → 中文口语（TTS 专用）======
  // 把 LaTeX 片段转成学生能听懂的口语：x^2 → x的平方，\frac{1}{2} → 二分之一，\sqrt{x} → 根号x
  function _findBrace(s, open) {
    let depth = 0;
    for (let i = open; i < s.length; i++) {
      if (s[i] === "{") depth++;
      else if (s[i] === "}") { depth--; if (depth === 0) return i; }
    }
    return -1;
  }
  const _MATH_CMD = {
    "\\pi":"派","\\alpha":"阿尔法","\\beta":"贝塔","\\gamma":"伽马","\\theta":"西塔",
    "\\lambda":"兰姆达","\\mu":"缪","\\Delta":"德尔塔","\\delta":"德尔塔","\\Sigma":"西格玛","\\sigma":"西格玛",
    "\\omega":"欧米伽","\\Omega":"欧米伽","\\phi":"斐","\\varphi":"斐","\\psi":"普西","\\rho":"柔",
    "\\tau":"陶","\\eta":"伊塔","\\xi":"可西","\\zeta":"截塔","\\varepsilon":"艾普西隆","\\epsilon":"艾普西隆",
    "\\times":"乘以","\\div":"除以","\\cdot":"点","\\ast":"星乘","\\star":"星","\\pm":"正负","\\mp":"负正",
    "\\leq":"小于等于","\\le":"小于等于","\\geq":"大于等于","\\ge":"大于等于",
    "\\neq":"不等于","\\ne":"不等于","\\approx":"约等于","\\equiv":"恒等于","\\sim":"相似于","\\cong":"全等于",
    "\\in":"属于","\\notin":"不属于","\\subset":"包含于","\\subseteq":"包含于","\\supset":"包含","\\supseteq":"包含",
    "\\cup":"并集","\\cap":"交集","\\emptyset":"空集","\\forall":"对任意","\\exists":"存在",
    "\\infty":"无穷","\\angle":"角","\\circ":"圈","\\prime":"一撇","\\mathrm":"","\\text":"","\\mbox":"","\\rm":"",
    "\\sin":"正弦","\\cos":"余弦","\\tan":"正切","\\cot":"余切","\\sec":"正割","\\csc":"余割",
    "\\log":"对数","\\ln":"自然对数","\\lg":"常用对数","\\exp":"指数",
    "\\lim":"极限","\\max":"最大值","\\min":"最小值",
    "\\sum":"求和","\\prod":"连乘","\\int":"积分","\\oint":"闭曲线积分",
    "\\partial":"偏","\\nabla":"梯度","\\to":"趋于","\\rightarrow":"趋于","\\Rightarrow":"推出","\\mapsto":"映射为",
    "\\and":"且","\\or":"或","\\not":"非","\\neg":"非","\\bmod":"模","\\mod":"模",
    "\\langle":"左尖括号","\\rangle":"右尖括号","\\lfloor":"左取整","\\rfloor":"右取整","\\lceil":"左取整","\\rceil":"右取整",
    "\\colon":"比","\\mid":"满足","\\vert":"","\\Vert":"","\\quad":" ","\\qquad":"  ","\\,":" ","\\;":" ","\\:":" "
  };
  const _MATH_SYM = {
    "×":"乘以","÷":"除以","−":"减","√":"根号","π":"派","∞":"无穷","°":"度","≈":"约等于","≠":"不等于",
    "≤":"小于等于","≥":"大于等于","∑":"求和","∏":"连乘","∫":"积分","∮":"闭曲线积分",
    "α":"阿尔法","β":"贝塔","γ":"伽马","θ":"西塔","λ":"兰姆达","μ":"缪","Δ":"德尔塔","Σ":"西格玛","Ω":"欧米伽","φ":"斐","ψ":"普西",
    "→":"推出","∴":"所以","∵":"因为","⊥":"垂直","∥":"平行","∠":"角","∘":"圈",
    "≡":"恒等于","≅":"全等于","∼":"相似","∈":"属于","∉":"不属于","∩":"交集","∪":"并集","∅":"空集",
    "∂":"偏","∇":"梯度","±":"正负","∓":"负正",
    "²":"平方","³":"立方","¹":"一次方","⁴":"四次方","ⁿ":"的n次方",
    "₀":"下标0","₁":"下标1","₂":"下标2","₃":"下标3","ₙ":"下标n","ₐ":"下标a"
  };
  function _latexAccent(s) {
    s = s.replace(/\\vec\{([^}]*)\}/g, "$1向量");
    s = s.replace(/\\bar\{([^}]*)\}/g, "$1平均");
    s = s.replace(/\\hat\{([^}]*)\}/g, "$1帽");
    s = s.replace(/\\dot\{([^}]*)\}/g, "$1一撇");
    s = s.replace(/\\ddot\{([^}]*)\}/g, "$1两撇");
    s = s.replace(/\\tilde\{([^}]*)\}/g, "$1波浪");
    return s;
  }
  function _latexFrac(s) {
    let g = 0;
    while (g++ < 60) {
      const i = s.indexOf("\\frac");
      if (i < 0) break;
      const b1 = s.indexOf("{", i + 5); if (b1 < 0) break;
      const e1 = _findBrace(s, b1); if (e1 < 0) break;
      const b2 = s.indexOf("{", e1 + 1); if (b2 < 0) break;
      const e2 = _findBrace(s, b2); if (e2 < 0) break;
      const num = _latexToSpeech(s.slice(b1 + 1, e1));
      const den = _latexToSpeech(s.slice(b2 + 1, e2));
      s = s.slice(0, i) + den + "分之" + num + s.slice(e2 + 1);
    }
    return s;
  }
  function _latexSqrt(s) {
    let g = 0;
    while (g++ < 60) {
      const i = s.indexOf("\\sqrt");
      if (i < 0) break;
      let p = i + 5, root = "";
      if (s[p] === "[") { const e = s.indexOf("]", p); if (e < 0) break; root = _latexToSpeech(s.slice(p + 1, e)); p = e + 1; }
      let body, end;
      if (s[p] === "{") { const e = _findBrace(s, p); if (e < 0) break; body = _latexToSpeech(s.slice(p + 1, e)); end = e + 1; }
      else { body = _latexToSpeech(s[p]); end = p + 1; }
      s = s.slice(0, i) + (root ? (body + "的" + root + "次方根") : ("根号" + body)) + s.slice(end);
    }
    return s;
  }
  function _latexSup(s) {
    let g = 0;
    while (g++ < 60) {
      const i = s.indexOf("^");
      if (i < 0) break;
      let exp, after;
      if (s[i + 1] === "{") { const e = _findBrace(s, i + 1); if (e < 0) break; exp = s.slice(i + 2, e); after = e + 1; }
      else { exp = s[i + 1]; after = i + 2; }
      const _expClean = exp.replace(/\s/g, "");
      if (/^(?:\\prime|prime)+$/i.test(_expClean)) {
        // 导数撇号：f^{\prime} → f一撇，f^{\prime\prime} → f两撇（不再念「的一撇次方」）
        const _n = (exp.match(/prime|\\prime/gi) || []).length;
        const _mark = _n === 1 ? "一撇" : (_n === 2 ? "两撇" : _n + "撇");
        s = s.slice(0, i) + _mark + s.slice(after);
      } else {
        s = s.slice(0, i) + "的" + _latexToSpeech(exp) + "次方" + s.slice(after);
      }
    }
    return s;
  }
  function _latexSub(s) {
    let g = 0;
    while (g++ < 60) {
      const i = s.indexOf("_");
      if (i < 0) break;
      let sub, after;
      if (s[i + 1] === "{") { const e = _findBrace(s, i + 1); if (e < 0) break; sub = s.slice(i + 2, e); after = e + 1; }
      else { sub = s[i + 1]; after = i + 2; }
      s = s.slice(0, i) + "下标" + _latexToSpeech(sub) + s.slice(after);
    }
    return s;
  }
  function _latexToSpeech(tex) {
    tex = tex == null ? "" : String(tex);
    tex = tex.replace(/\^\\circ/g, "度");   // 30度（角度上标圈）
    tex = _latexFrac(tex);
    tex = _latexSqrt(tex);
    tex = _latexSup(tex);
    tex = _latexSub(tex);
    tex = _latexAccent(tex);
    tex = tex.replace(/\\%/g, "%");   // LaTeX 转义百分号归一化，交给后续 % 规则
    for (const k in _MATH_CMD) { if (_MATH_CMD.hasOwnProperty(k)) tex = tex.split(k).join(_MATH_CMD[k]); }
    tex = tex.replace(/\\[a-zA-Z]+/g, "");
    tex = tex.replace(/\\[,;:!]/g, " ");
    tex = tex.replace(/\\ /g, " ");
    tex = tex.replace(/[{}]/g, "");
    for (const k in _MATH_SYM) { if (_MATH_SYM.hasOwnProperty(k)) tex = tex.split(k).join(_MATH_SYM[k]); }
    // 裸撇号（导数 f'(x)）→ 一撇
    tex = tex.replace(/'/g, "一撇");
    // 函数参数括号消除：f(x)→f x，sin(x) 已转「正弦 x」→ 正弦x，f一撇(x)→f一撇 x；
    // 分组括号 (a+b) 前面非字母/汉字，保留「括号」以表达整体运算优先级
    tex = tex.replace(/([A-Za-z一-龥])\(([^()]*)\)/g, "$1 $2");
    return tex;
  }
  function _latexWrap(tex) { return " " + _latexToSpeech(tex) + " "; }

  function _ttsPreprocess(raw) {
    let s = String(raw)
      .replace(/\s*[\r\n]+\s*/g, "。")
      // 公式块：提取内部 LaTeX 转口语（不再整段吞掉成「公式」）
      // 注意：replace 的回调第一个参数是“整个匹配(含定界符$)”，必须用捕获组 m 取内部
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => " " + _latexToSpeech(m) + " ")
      .replace(/\\\[([\s\S]+?)\\\]/g, (_, m) => " " + _latexToSpeech(m) + " ")
      .replace(/\\\(([\s\S]+?)\\\)/g, (_, m) => " " + _latexToSpeech(m) + " ")
      .replace(/\$([^$]+?)\$/g, (_, m) => " " + _latexToSpeech(m) + " ");
    // 公式外残留的 LaTeX / 符号也整体转一次
    s = _latexToSpeech(s);
    // 普通分数 a/b（纯文本，限短数字避免误伤年份如 2024/2025）
    s = s.replace(/(?<![\d.])(\d{1,3})\/(\d{1,3})(?![\d.])/g, function (_m, a, b) {
      const zh = ["零","一","二","三","四","五","六","七","八","九"];
      const z = n => n.length === 1 ? (zh[+n] || n) : n;
      return z(b) + "分之" + z(a);
    });
    // 运算符与排版（仅在数学语境安全转换）
    s = s.replace(/(^|[\s(（=+*/-])-(?=\d)/g, "$1负")   // 数字前的负号
          .replace(/(?<=\d)-(?=\d)/g, "减")             // 数字间的减号
          .replace(/\+/g, "加")
          .replace(/=/g, "等于")
          .replace(/</g, "小于")
          .replace(/>/g, "大于")
          .replace(/(?<=\d)·(?=\d)/g, "乘以")           // 数字间的乘点
          .replace(/(\d+)%/g, "百分之$1")
          .replace(/([。！？；])/g, "$1 pause ")
          .replace(/([，、])/g, "$1 ")
          .replace(/pause\s+/g, ", ")
          .replace(/\s{2,}/g, " ")
          .trim();
    return s;
  }

  function _ttsSpeakChunk(text) {
    loadVoices();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = _ttsLang;
    // 使用用户在「语音朗读设置」里调节的语速/音调/音量；未调则用按语言给的默认值
    const defRate = _ttsLang === "en-US" ? 0.88 : 0.95;
    u.rate = state.ttsRate || defRate;
    u.pitch = state.ttsPitch || 1.02;
    u.volume = (state.ttsVolume === 0) ? 1.0 : (state.ttsVolume || 1.0);
    // 优先用用户手动指定的嗓音；否则自动优选本机最自然嗓音
    let v = null;
    if (state.ttsVoice) v = _voices.find(x => x.name === state.ttsVoice) || null;
    if (!v) v = pickVoice(_ttsLang);
    if (v) u.voice = v;
    _ttsActiveU = u;
    u.onend = () => { if (_ttsActiveU !== u) return; _ttsAdvance("onend"); };
    u.onerror = (e) => {
      const err = (e && e.error) || "";
      if (err === "interrupted") return;   // 主动停止，忽略
      if (_ttsActiveU !== u) return;
      console.warn("[TTS] 段落错误:", err);
      _ttsAdvance("error");
    };
    _ttsSegmentDone = false;
    _ttsExpectSince = Date.now();
    try { window.speechSynthesis.speak(u); } catch (e) { console.warn("[TTS] speak 抛错:", e && e.message); _ttsAdvance("throw"); }
  }

  // 续播下一段（被 onend / onerror / 轮询 调用）。用 _ttsIdx 单一真相 + _ttsSegmentDone 防跳段/重复
  function _ttsAdvance(from) {
    if (_ttsSegmentDone) return;          // 同一段只前进一次（onend 与 pump 二选一）
    _ttsSegmentDone = true;
    try { if (window.AL_GAMIFY) window.AL_GAMIFY.track("speaks"); } catch (e) {}   // 朗读埋点（每段一次）
    if (_ttsIdx >= _ttsChunks.length) { _ttsFinish(); return; }
    _ttsIdx++;
    if (_ttsIdx >= _ttsChunks.length) { _ttsFinish(); return; }
    _karaokeUpdate(_ttsIdx);
    const snippet = _ttsChunks[_ttsIdx].slice(0, 18).replace(/\s+/g, " ");
    console.log("[TTS] 播第 " + (_ttsIdx + 1) + "/" + _ttsChunks.length + " 段(" + from + "): " + snippet);
    _ttsSpeakChunk(_ttsChunks[_ttsIdx]);
  }

  // 轮询：iPad onend 不可靠，但段末 speaking 会变 false——以此续播
  function _ttsPumpTick() {
    if (!_ttsChunks.length) return;
    if (Date.now() - _ttsExpectSince < 500) return;   // 刚 speak，等引擎真正开始
    const cur = _ttsChunks[_ttsIdx] || "";
    const est = cur.length * 260 + 2000;              // 预计朗读时长（中文约0.26s/字 + 2s余量）
    if (!window.speechSynthesis.speaking) {
      if (Date.now() - _ttsExpectSince < est) {
        // 未到预计时长就停了 = iOS 自动暂停，尝试 resume 而非续播（避免跳过半段）
        try { if (window.speechSynthesis.paused) window.speechSynthesis.resume(); } catch (e) {}
        return;
      }
      console.log("[TTS] 段 " + (_ttsIdx + 1) + " 结束(speaking=false)，续播");
      _ttsAdvance("pump");
    }
  }

  function _ttsFinish() {
    if (_ttsPump) { clearInterval(_ttsPump); _ttsPump = null; }
    stopResumeGuard();
    _ttsActiveU = null;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    _ttsChunks = [];
    _ttsIdx = 0;
    hideStopBtn();
    console.log("[TTS] 全部段落朗读完毕");
  }

  function _ttsStartPump() {
    if (_ttsPump) clearInterval(_ttsPump);
    startResumeGuard();
    _ttsPump = setInterval(_ttsPumpTick, 250);
  }

  function speak(text) {
    if (!text || !text.trim()) return;
    // 朗读引擎分流：云端模式用服务端音频，彻底绕开移动端 speechSynthesis 限制（无语音包/微信内嵌）
    const _eng = _chooseTtsEngine();
    if (_eng === "native") {
      // APK 离线包：交给平板系统自带的 TTS 引擎（先做一遍公式/符号口语化）
      const spoken0 = _ttsPreprocess(text);
      if (!spoken0) return;
      _karaokeShowNative(spoken0);
      _nativeSpeak(spoken0);
      return;
    }
    if (_eng === "cloud") {
      // 同一篇：正在播→暂停；暂停中→继续；已播完→重开；否则新播
      if (text === _cloudText) {
        if (_cloudPaused) { _cloudResume(); return; }
        if (_cloudFinished) { _cloudRestart(); return; }
        if (_cloudActive) { _cloudPause(); return; }
      }
      _cloudSpeak(text);
      return;
    }
    if (!("speechSynthesis" in window)) { _ttsNoEngineHint(); return; }
    unlockTTS();   // 确保 iOS 引擎已解锁
    // 新的朗读：先停掉上一轮（此处 cancel 在用户手势内，不会触发 iOS 静默吞首句）
    try { window.speechSynthesis.cancel(); } catch (e) {}

    const spoken = _ttsPreprocess(text);
    if (!spoken) return;

    _ttsLang = state.curLang || "zh-CN";
    _ttsIdx = 0;
    _ttsSegmentDone = false;

    // 按句号/分号拆，单段 ≤130 字（缩短以提高 iOS 续播稳定性）
    const MAX_CHUNK = 130;
    const sents = spoken.split(/(?<=[。！？；])/).filter(s => s.trim());
    const chunks = [];
    let buf = "";
    for (const s of sents) {
      if ((buf + s).length > MAX_CHUNK && buf) { chunks.push(buf.trim()); buf = ""; }
      buf += s;
    }
    if (buf.trim()) chunks.push(buf.trim());
    if (!chunks.length) return;

    _ttsChunks = chunks;
    _ttsIdx = 0;
    showStopBtn();
    console.log("[TTS] 分段朗读: 共 " + chunks.length + " 段, 全文 " + spoken.length + " 字");
    const snippet = chunks[0].slice(0, 18).replace(/\s+/g, " ");
    console.log("[TTS] 播第 1/" + chunks.length + " 段: " + snippet);
    _karaokeShow(chunks);
    _ttsSpeakChunk(chunks[0]);
    _ttsStartPump();
  }

  // ---------- 本地离线朗读（Android 原生 TextToSpeech，APK 内无需联网、无需服务器）----------
  // 说明：APK 是纯离线包，没有后端，所以 /api/tts 用不了。
  //       Android 侧在 WebView 上注入了 window.ALNative，直接调用平板/手机**系统自带**的
  //       文字转语音引擎朗读，一装即用、完全离线。
  let _nativeActive = false;
  let _nativeText = "";
  let _nativeWaitingHinted = false;

  // 桥是否注入成功（APK 内为 true；普通浏览器为 false）
  function _nativePresent() {
    try {
      return !!(window.ALNative && typeof window.ALNative.speak === "function");
    } catch (e) { return false; }
  }

  function _nativeAvail() {
    try {
      return !!(window.ALNative && window.ALNative.ttsAvailable && window.ALNative.ttsAvailable());
    } catch (e) { return false; }
  }

  // 「没声音」的统一引导：
  //   在 APK 里 → 华为等机型出厂就没有 TTS 引擎（设置页里根本没有「文字转语音」这一项），
  //              所以引导必须落在「填电脑语音服务器地址」上，而不是让用户去找一个不存在的开关。
  //   在浏览器里 → 给浏览器侧建议
  function _ttsNoEngineHint() {
    if (_nativePresent()) {
      const hasSrv = !!_ttsServerBase();
      try {
        toast(hasSrv
          ? "朗读失败：连不上电脑语音服务器（" + _ttsServerBase() + "）。请确认电脑上已用「启动_AL系统_语音版.bat」启动、手机与电脑在同一 WiFi"
          : "这台手机没有系统语音引擎（华为等机型常见）。请在下方「电脑语音服务器地址」里填上电脑的局域网 IP（形如 192.168.1.5:8000），电脑开着就能出声");
      } catch (e) {}
      // 自动弹出一次自检+引导，让用户/我们都能看到真实原因
      // （自检面板在「设置」页里，所以必须跳过去才看得见；每次启动只自动跳一次，避免打扰）
      try { if (typeof UI !== "undefined" && UI.ttsSelfTest) UI.ttsSelfTest(); } catch (e) {}
      if (!_ttsHintJumped) {
        _ttsHintJumped = true;
        try { if (typeof UI !== "undefined" && UI.go) UI.go("settings"); } catch (e) {}
      }
      return;
    }
    try { toast("当前浏览器不支持语音朗读，请改用 Chrome / Edge，或到设置里把朗读引擎切到「云端朗读」"); } catch (e) {}
  }

  // 原生 -> JS 的回调：朗读结束/出错时复位 UI
  window.__AL_TTS_EVENT = function (type, extra) {
    try { console.log("[TTS][native] " + type + (extra ? " " + extra : "")); } catch (e) {}
    if (type === "done" || type === "error") {
      _nativeActive = false;
      _nativeText = "";
      hideStopBtn();
    }
    // 引擎尚未就绪：已排队，等就绪后会自动朗读。只提示一次，避免刷屏。
    if (type === "waiting" && !_nativeWaitingHinted) {
      _nativeWaitingHinted = true;
      try { toast("正在初始化手机语音引擎，就绪后会自动开始朗读…"); } catch (e) {}
      setTimeout(function () { _nativeWaitingHinted = false; }, 8000);
    }
    if (type === "ready") {
      // 引擎就绪后若仍无在播内容，复位按钮状态
      if (!_nativeActive) hideStopBtn();
    }
    if (type === "error") {
      const msg = (extra === "not-ready" || extra === "no-engine")
        ? "手机没有可用的文字转语音引擎：请到「设置 → 文字转语音(TTS)输出」选一个中文引擎（没有就安装语音数据），再回来自检"
        : "本地朗读出错（" + extra + "）";
      try { toast(msg); } catch (e) {}
      // 只提示一次，避免开机时反复弹
      if ((extra === "no-engine" || extra === "not-ready") && !_nativeWaitingHinted) {
        _nativeWaitingHinted = true;
        setTimeout(function () { _nativeWaitingHinted = false; }, 15000);
      }
    }
  };

  function _nativeStop() {
    _nativeActive = false;
    _nativeText = "";
    try { if (window.ALNative && window.ALNative.stop) window.ALNative.stop(); } catch (e) {}
  }

  function _nativeSpeak(text) {
    // 同一篇再点一次 = 停止
    if (_nativeActive && text === _nativeText) { _nativeStop(); hideStopBtn(); return; }
    _nativeText = text;
    _nativeActive = true;
    showStopBtn();
    try {
      window.ALNative.speak(text, state.ttsRate || 0.95, state.ttsPitch || 1.02);
    } catch (e) {
      _nativeActive = false;
      hideStopBtn();
      try { toast("本地朗读调用失败：" + (e && e.message)); } catch (e2) {}
    }
  }

  // ---------- 云端朗读播放器（服务端 edge-tts 生成音频，支持暂停/继续/重开/进度条拖动）----------
  let _cloudText = "";        // 当前朗读全文（判断“同一篇”用）
  let _cloudSegs = [];        // 分段文本
  let _cloudUrls = [];        // 每段已生成的 blob URL（缓存，避免重复请求）
  let _cloudDurs = [];        // 每段时长（秒）
  let _cloudIdx = 0;          // 当前段索引
  let _cloudAudio = null;     // 当前段 Audio 元素
  let _cloudActive = false;   // 是否处于播放会话（含暂停）
  let _cloudPaused = false;   // 是否暂停
  let _cloudFinished = false; // 是否播放完毕
  let _cloudTotalDur = 0;     // 总时长（秒，段加载后累加）
  let _cloudProgTimer = null; // 进度条定时器
  let _cloudUnlocked = false;
  let _cloudGen = 0;          // 播放代次令牌：每次“开始新播放”自增，旧链据此放弃，保证同一时刻只有一个声音

  // iOS / 部分 Android 要求在“用户手势内”先解锁音频，否则首次 new Audio().play() 会被静音拦截
  function _ensureCloudAudioUnlock() {
    if (_cloudUnlocked) return;
    _cloudUnlocked = true;
    try {
      const s = new Audio("data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=");
      s.muted = true;
      const pp = s.play();
      if (pp && pp.catch) pp.catch(function () {});
    } catch (e) {}
  }

  // 引擎选择：
  //   1) 只要原生桥在（APK 离线包）：
  //      · 配了「电脑语音服务器地址」→ 走 cloud（音频由电脑 edge-tts 生成，经原生通道取回）；
  //      · 没配 → 走 native（手机/平板自带引擎，离线可用）。
  //      无论哪种，都**绝不回落浏览器**（Android WebView 没有 speechSynthesis，一回落就是彻底无声）。
  //   2) 网页端默认走云端（服务端生成音频，全设备稳定出声）；
  //   3) 显式选「浏览器」才用本机 speechSynthesis。
  function _chooseTtsEngine() {
    if (_nativePresent()) {
      const e = (state.ttsEngine || "cloud").toLowerCase();
      if (e === "browser") return "browser";
      // 用 _useNativeHttpTts() 而不是只看地址：老版本 APK 的桥没有 httpGet，
      // 光有地址也取不到音频，那种情况必须老老实实退回本机引擎。
      if (e === "native") {
        // 显式选本机引擎，但本机确实没有引擎、又能连服务器 → 自动改用服务器，避免白点
        if (!_nativeAvail() && _useNativeHttpTts()) return "cloud";
        return "native";
      }
      // cloud / auto：能用服务器就用服务器；否则退回本机引擎
      return _useNativeHttpTts() ? "cloud" : "native";
    }
    const e = (state.ttsEngine || "cloud").toLowerCase();
    if (e === "browser" || e === "native") return "browser";
    return "cloud";
  }

  // 把文本切成 ≤maxLen 字的段（在句末切，减少段数让进度条更连续）
  function _cloudSplit(text, maxLen) {
    const sents = text.split(/(?<=[。！？；])/).filter(s => s.trim());
    const segs = [];
    let buf = "";
    for (const s of sents) {
      if ((buf + s).length > maxLen && buf) { segs.push(buf.trim()); buf = ""; }
      buf += s;
    }
    if (buf.trim()) segs.push(buf.trim());
    return segs.length ? segs : [text];
  }

  function _estDur(t) { return Math.max(1, Math.round((t || "").length * 0.26)); }

  function _fmtTime(s) {
    s = Math.max(0, Math.floor(s || 0));
    const m = Math.floor(s / 60), ss = s % 60;
    return m + ":" + (ss < 10 ? "0" : "") + ss;
  }

  // ---------- 电脑语音服务器通道（华为等「出厂无 TTS 引擎、也装不了语音包」机型的解法）----------
  // 背景：这类手机系统朗读彻底走不通，只能让电脑出声（edge-tts 音质还更好）。
  // 但 App 页面来源是 https://localhost，直接 fetch("http://192.168.x.x:8000/...") 会被
  // WebView 的「混合内容(Mixed Content)」策略拦死。所以取音频这一步交给原生
  // HttpURLConnection（不受该策略约束），原生按 base64 分片回传，这里拼回二进制，
  // 再交给**现有的云端播放器**播放 —— 暂停/继续/进度条/预加载全部沿用，一行都没重写。
  let _httpSeq = 0;
  const _httpPending = Object.create(null);

  // 原生 -> JS：分片回传
  window.__AL_HTTP = function (cbId, kind, payload) {
    const p = _httpPending[cbId];
    if (!p) return;                    // 已作废/已超时的请求，直接丢弃
    if (kind === "chunk") { p.pieces.push(payload || ""); return; }
    delete _httpPending[cbId];
    if (kind === "done") { p.resolve(p.pieces.join("")); return; }
    p.reject(new Error(payload || "http-error"));
  };

  function _nativeHttpGet(url, timeoutMs) {
    return new Promise(function (resolve, reject) {
      let id = null;
      try {
        if (!(window.ALNative && typeof window.ALNative.httpGet === "function")) {
          reject(new Error("no-bridge"));
          return;
        }
        id = "h" + (++_httpSeq);
        _httpPending[id] = { pieces: [], resolve: resolve, reject: reject };
        // 原生侧也有超时，这里只是兜底，防止 Promise 永久挂起
        setTimeout(function () {
          if (_httpPending[id]) {
            delete _httpPending[id];
            try { if (window.ALNative.httpAbort) window.ALNative.httpAbort(id); } catch (e) {}
            reject(new Error("timeout"));
          }
        }, (timeoutMs || 30000) + 3000);
        window.ALNative.httpGet(url, id, timeoutMs || 30000);
      } catch (e) {
        if (id && _httpPending[id]) delete _httpPending[id];
        reject(e);
      }
    });
  }

  function _httpAbortAll() {
    for (const id in _httpPending) {
      const p = _httpPending[id];
      delete _httpPending[id];
      try { if (window.ALNative && window.ALNative.httpAbort) window.ALNative.httpAbort(id); } catch (e) {}
      try { p.reject(new Error("aborted")); } catch (e) {}
    }
  }

  // base64 → 二进制字节数（不解码，省一次大字符串拷贝）
  function _b64ByteLen(b64) {
    if (!b64) return 0;
    const n = b64.length;
    let pad = 0;
    if (n > 0 && b64.charAt(n - 1) === "=") pad++;
    if (n > 1 && b64.charAt(n - 2) === "=") pad++;
    return Math.floor(n * 3 / 4) - pad;
  }

  function _b64ToBlob(b64, mime) {
    const bin = atob(b64);
    const len = bin.length;
    const u8 = new Uint8Array(len);
    for (let i = 0; i < len; i++) u8[i] = bin.charCodeAt(i) & 0xff;
    return new Blob([u8], { type: mime || "audio/mpeg" });
  }

  // 网页端直连（APK 内不用这两条，走原生通道）
  async function _fetchTextRaw(url, timeoutMs) {
    const ctl = ("AbortController" in window) ? new AbortController() : null;
    const t = setTimeout(function () { if (ctl) ctl.abort(); }, timeoutMs || 8000);
    try {
      const r = await fetch(url, { cache: "no-store", signal: ctl ? ctl.signal : undefined });
      if (!r.ok) throw new Error("http-" + r.status);
      return await r.text();
    } finally { clearTimeout(t); }
  }
  async function _fetchB64Raw(url, timeoutMs) {
    const ctl = ("AbortController" in window) ? new AbortController() : null;
    const t = setTimeout(function () { if (ctl) ctl.abort(); }, timeoutMs || 30000);
    try {
      const r = await fetch(url, { cache: "no-store", signal: ctl ? ctl.signal : undefined });
      if (!r.ok) throw new Error("http-" + r.status);
      const u8 = new Uint8Array(await r.arrayBuffer());
      let s = "";
      const CH = 8192;
      for (let i = 0; i < u8.length; i += CH) {
        s += String.fromCharCode.apply(null, u8.subarray(i, Math.min(u8.length, i + CH)));
      }
      return btoa(s);
    } finally { clearTimeout(t); }
  }

  // 用户填的地址 → 规范化："192.168.1.5" / "192.168.1.5:8000" / "http://a:8000/" 都接受
  function _normalizeServerBase(raw) {
    let s = String(raw == null ? "" : raw).trim();
    if (!s) return "";
    let scheme = "http://";
    if (/^https:\/\//i.test(s)) { scheme = "https://"; s = s.replace(/^https:\/\//i, ""); }
    else { s = s.replace(/^http:\/\//i, ""); }
    s = s.replace(/\s+/g, "").replace(/\/+$/, "");
    if (!s) return "";
    if (!/:\d+$/.test(s)) s = s + ":8000";   // 只填 IP/域名 → 补默认端口
    return scheme + s;
  }
  function _ttsServerBase() { return _normalizeServerBase(state.ttsServer); }

  // 是否该走「原生 HTTP 取音频」：必须是 APK（有桥）且填了服务器地址
  function _useNativeHttpTts() {
    try {
      return !!(_nativePresent() && window.ALNative && typeof window.ALNative.httpGet === "function" && _ttsServerBase());
    } catch (e) { return false; }
  }

  // 请求某段音频 blob（串行友好：edge-tts 对并发敏感，避免同时合成多段）
  let _cloudFetchBusy = false;
  let _cloudLastErr = "";     // 最近一次取音频失败原因（供「语音自检」显示）
  async function _fetchTtsBlob(seg, retries) {
    retries = retries == null ? 2 : retries;
    const params = new URLSearchParams({ text: seg, lang: _ttsLang });
    const rate = state.ttsRate || 0.95;
    const pitch = state.ttsPitch || 1.02;
    const rPct = Math.round((rate - 1) * 100);
    const pHz = Math.round((pitch - 1) * 50);
    params.set("rate", (rPct >= 0 ? "+" : "") + rPct + "%");
    params.set("pitch", (pHz >= 0 ? "+" : "") + pHz + "Hz");
    // 走电脑语音服务器时，可指定 edge-tts 音色（手机引擎嗓音名不会命中这个格式，安全）
    if (/^(zh|en)-[A-Za-z]{2}-[A-Za-z]+Neural$/i.test(state.ttsVoice || "")) {
      params.set("voice", state.ttsVoice);
    }
    const useNative = _useNativeHttpTts();
    const url = (useNative ? _ttsServerBase() : "") + "/api/tts?" + params.toString();

    // APK + 已配电脑语音服务器：走原生 HttpURLConnection（绕过 https 页面的混合内容拦截）
    if (useNative) {
      for (let attempt = 0; attempt <= retries; attempt++) {
        if (attempt > 0) await new Promise(r => setTimeout(r, 500 + attempt * 300));
        try {
          const b64 = await _nativeHttpGet(url, 30000);
          if (b64 && _b64ByteLen(b64) > 0) { _cloudLastErr = ""; return _b64ToBlob(b64, "audio/mpeg"); }
          _cloudLastErr = "empty";
        } catch (e) {
          _cloudLastErr = String((e && e.message) || e);
          console.warn("[TTS][lan] 取音频失败(第" + (attempt + 1) + "次): " + _cloudLastErr);
        }
      }
      return null;
    }

    for (let attempt = 0; attempt <= retries; attempt++) {
      if (attempt > 0) await new Promise(r => setTimeout(r, 500 + attempt * 300));
      try {
        const r = await fetch(url, { method: "GET", cache: "no-store" });
        if (!r.ok) {
          _cloudLastErr = "http-" + r.status;
          console.warn("[TTS][cloud] fetch seg HTTP " + r.status);
          continue;
        }
        const blob = await r.blob();
        if (blob && blob.size > 0) { _cloudLastErr = ""; return blob; }
        _cloudLastErr = "empty-blob";
      } catch (e) {
        _cloudLastErr = "fetch:" + ((e && e.message) || e);
        console.warn("[TTS][cloud] fetch seg error:", e && e.message);
      }
    }
    return null;
  }

  // 串行加载一段并转成 blob URL（全局锁，防止并发压垮 edge-tts）
  async function _cloudLoadSeg(i) {
    if (i < 0 || i >= _cloudSegs.length) return false;
    if (_cloudUrls[i]) return true;
    while (_cloudFetchBusy) await new Promise(r => setTimeout(r, 100));
    if (_cloudUrls[i]) return true;
    _cloudFetchBusy = true;
    let ok = false;
    try {
      const b = await _fetchTtsBlob(_cloudSegs[i], 2);
      if (b && b.size > 0) {
        _cloudUrls[i] = URL.createObjectURL(b);
        _cloudDurs[i] = _estDur(_cloudSegs[i]);
        ok = true;
      } else {
        console.warn("[TTS][cloud] 第 " + (i + 1) + " 段加载失败，将被跳过");
      }
    } finally {
      _cloudFetchBusy = false;
    }
    return ok;
  }

  // 只准备结构；第 0 段需要时才加载，其余边播边缓存
  function _cloudPrepare(text) {
    if (_cloudUrls && _cloudUrls.length) {
      for (const u of _cloudUrls) { try { URL.revokeObjectURL(u); } catch (e) {} }
    }
    _cloudSegs = _cloudSplit(text, 800);
    _cloudUrls = new Array(_cloudSegs.length).fill(null);
    _cloudDurs = new Array(_cloudSegs.length).fill(0);
    _cloudUpdateTotalDur();
  }

  function _cloudUpdateTotalDur() {
    _cloudTotalDur = _cloudSegs.reduce((sum, s) => sum + _estDur(s), 0);
  }

  // 后台预加载下一段（播放当前段时悄悄准备）
  function _cloudPrefetchNext(i) {
    const next = i + 1;
    if (next < _cloudSegs.length && !_cloudUrls[next]) {
      _cloudLoadSeg(next).catch(() => {});
    }
  }

  async function _cloudPlayFrom(i, startAt) {
    const gen = _cloudGen;        // 捕获本次播放链代次
    if (!_cloudActive) return;
    // 跳过加载失败的段，直到找到可用的或播完
    while (i < _cloudSegs.length && !_cloudUrls[i]) {
      const ok = await _cloudLoadSeg(i);
      if (gen !== _cloudGen) return;   // 已有新的播放指令（如再次拖动/重开），放弃旧链
      if (!ok) {
        i++;
        continue;
      }
    }
    if (i < 0 || i >= _cloudSegs.length) { if (gen === _cloudGen) _cloudFinish(); return; }
    if (gen !== _cloudGen) return;      // 安全再检查
    _cloudIdx = i;
    // 双保险：开新段前先彻底停掉任何仍在发声 / 即将发声的旧 Audio，保证同一时刻只有一个声音
    if (_cloudAudio) { try { _cloudAudio.pause(); _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
    const a = new Audio(_cloudUrls[i]);
    try { a.playsInline = true; } catch (e) {}
    a.volume = (state.ttsVolume === 0) ? 1.0 : (state.ttsVolume || 1.0);
    a.onended = () => {
      if (gen !== _cloudGen) return;    // 本段已被新的播放取代，不再续播下一段
      if (!_cloudActive) return;
      _cloudPlayFrom(i + 1);
    };
    a.onerror = () => {
      if (gen !== _cloudGen) return;
      console.warn("[TTS][cloud] 段落播放错误 seg#" + i + "，跳过");
      _cloudPlayFrom(i + 1);
    };
    _cloudAudio = a;
    _cloudPaused = false;
    _cloudFinished = false;
    _updateCloudCtrl();
    // 预加载下一段
    _cloudPrefetchNext(i);
    if (startAt && startAt > 0.1) {
      a.currentTime = Math.min(startAt, _cloudDurs[i] || startAt);
    }
    const p = a.play();
    if (p && p.catch) p.catch(err => {
      if (gen !== _cloudGen) return;
      console.warn("[TTS][cloud] play 被拒:", err && err.message);
      // 自动播放策略拒绝：降级到浏览器兜底
      _cloudFallbackFrom(i);
    });
  }

  function _cloudFinish() {
    _cloudActive = false; _cloudPaused = false; _cloudFinished = true;
    if (_cloudAudio) { try { _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
    if (_cloudProgTimer) { clearInterval(_cloudProgTimer); _cloudProgTimer = null; }
    _updateCloudCtrl();
    setTimeout(hideCloudCtrl, 1000);
  }

  function _cloudPause() {
    if (_cloudAudio) { try { _cloudAudio.pause(); } catch (e) {} }
    _cloudPaused = true; _cloudActive = true;
    _updateCloudCtrl();
  }
  function _cloudResume() {
    if (_cloudAudio && _cloudUrls[_cloudIdx]) {
      const p = _cloudAudio.play();
      if (p && p.catch) p.catch(() => {});
      _cloudPaused = false; _cloudActive = true;
      _updateCloudCtrl();
      return;
    }
    // 若当前段没加载（例如 seek 后），从当前段重播
    _cloudGen++;                       // 作废旧链
    _cloudPaused = false; _cloudActive = true;
    if (!_cloudProgTimer) _cloudProgTimer = setInterval(_cloudTick, 250);
    _cloudPlayFrom(_cloudIdx || 0);
  }
  function _cloudRestart() {
    _cloudGen++;                       // 作废旧链，保证重开后只有一个声音
    if (_cloudAudio) { try { _cloudAudio.pause(); _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
    _cloudFinished = false; _cloudActive = true; _cloudPaused = false;
    if (!_cloudProgTimer) _cloudProgTimer = setInterval(_cloudTick, 250);
    _cloudPlayFrom(0);
  }

  // 拖动进度条：定位到指定秒数（可跨段）
  async function _cloudSeek(tSec) {
    if (!_cloudTotalDur) return;
    tSec = Math.max(0, Math.min(tSec, _cloudTotalDur));
    let acc = 0, target = 0, inT = 0;
    for (let i = 0; i < _cloudSegs.length; i++) {
      const d = _cloudDurs[i] || _estDur(_cloudSegs[i]);
      if (acc + d >= tSec) { target = i; inT = tSec - acc; break; }
      acc += d;
    }
    _cloudGen++;                       // 关键：作废任何在途的旧播放链，避免拖动时多个声音叠播
    _cloudActive = true; _cloudPaused = false;
    if (_cloudAudio) { try { _cloudAudio.pause(); _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
    if (!_cloudProgTimer) _cloudProgTimer = setInterval(_cloudTick, 250);
    _cloudPlayFrom(target, inT);
  }

  function _cloudStop() {
    _cloudGen++;                       // 作废旧链
    _cloudActive = false; _cloudPaused = false; _cloudFinished = false;
    if (_cloudAudio) { try { _cloudAudio.pause(); _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
    if (_cloudProgTimer) { clearInterval(_cloudProgTimer); _cloudProgTimer = null; }
    hideCloudCtrl();
  }

  async function _cloudSpeak(text) {
    _ensureCloudAudioUnlock();
    if (_cloudActive) _cloudStop();
    const spoken = _ttsPreprocess(text);
    if (!spoken) { toast("没有可朗读的内容"); return; }
    _ttsLang = state.curLang || "zh-CN";
    _cloudText = spoken;
    _cloudPrepare(spoken);
    _cloudActive = true; _cloudPaused = false; _cloudFinished = false;
    if (!_cloudProgTimer) _cloudProgTimer = setInterval(_cloudTick, 250);
    showCloudCtrl(true);
    // 先加载第 0 段，让用户尽快听到声音
    const ok0 = await _cloudLoadSeg(0);
    if (!_cloudActive) return;
    if (!ok0) {
      // 首段实在不行才降级浏览器
      _cloudFallbackFrom(0);
      return;
    }
    _cloudPlayFrom(0);
  }

  // 云端播放失败 → 降级到浏览器 speechSynthesis（极少数情况）
  function _cloudFallbackFrom(idx) {
    if (!_cloudActive) return;
    _cloudGen++;                       // 作废云端旧链，避免与兜底叠声
    console.warn("[TTS][cloud] 云端失败，降级；段 " + (idx + 1) + "，原因: " + (_cloudLastErr || "unknown"));
    _cloudActive = false; _cloudPaused = false;
    if (_cloudAudio) { try { _cloudAudio.pause(); _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
    if (_cloudProgTimer) { clearInterval(_cloudProgTimer); _cloudProgTimer = null; }
    hideCloudCtrl();
    const remaining = _cloudSegs.slice(idx).join("。");
    // 降级必须降到「真能出声」的地方：APK 内 Android WebView 没有 speechSynthesis，
    // 若还按老逻辑回落到浏览器，结果就是彻底静音（这正是用户报的「没声音」）。
    if (_nativePresent()) {
      if (_nativeAvail()) {
        toast("电脑语音服务器取不到音频，已改用手机自带引擎朗读");
        if (remaining && remaining.trim()) _nativeSpeak(remaining);
      } else {
        _ttsNoEngineHint();            // 两边都没法出声：把原因和下一步说清楚
      }
      return;
    }
    toast("云端朗读暂时不可用，已自动改用本机朗读");
    if (remaining && remaining.trim()) _speakBrowserRaw(remaining);
  }

  // 进度条定时刷新
  function _cloudTick() {
    if (!_cloudActive) return;
    let cur = 0;
    for (let i = 0; i < _cloudIdx; i++) cur += (_cloudDurs[i] || 0);
    if (_cloudAudio && !isNaN(_cloudAudio.currentTime)) cur += _cloudAudio.currentTime;
    const prog = document.getElementById("tts-progress");
    if (prog && _cloudTotalDur > 0 && !prog._dragging) prog.value = Math.min(cur, _cloudTotalDur);
    const time = document.getElementById("tts-time");
    if (time) time.textContent = _fmtTime(cur) + " / " + _fmtTime(_cloudTotalDur);
  }

  // ---------- 云端朗读控制条（放在 ss-toolbar 内，不遮挡正文）----------
  function showCloudCtrl(preparing) {
    let bar = document.getElementById("tts-ctrl");
    if (!bar) {
      bar = document.createElement("div");
      bar.id = "tts-ctrl";
      bar.innerHTML =
        '<div class="tts-ctrl-inner">' +
        '  <button id="tts-play-toggle" class="tts-ctrl-btn" title="暂停/继续">⏸</button>' +
        '  <button id="tts-restart" class="tts-ctrl-btn" title="重新开始">↺</button>' +
        '  <input id="tts-progress" class="tts-progress" type="range" min="0" max="100" step="0.1" value="0" />' +
        '  <span id="tts-time" class="tts-time">0:00 / 0:00</span>' +
        '  <button id="tts-close" class="tts-ctrl-btn" title="关闭">✕</button>' +
        '</div>';
      // 插入到 ss-toolbar 的 ss-tools 之前（顶部面包屑/进度条下方，按钮上方）
      const tools = document.querySelector(".ss-tools");
      const toolbar = document.querySelector(".ss-toolbar");
      if (tools && toolbar) toolbar.insertBefore(bar, tools);
      else document.body.appendChild(bar);
      const toggle = document.getElementById("tts-play-toggle");
      toggle.onclick = function () { if (_cloudPaused) _cloudResume(); else if (_cloudActive) _cloudPause(); };
      document.getElementById("tts-restart").onclick = function () { _cloudRestart(); };
      document.getElementById("tts-close").onclick = function () { _cloudStop(); };
      const prog = document.getElementById("tts-progress");
      prog.max = 100;
      prog.addEventListener("input", function () {
        prog._dragging = true;
        // 拖动过程中：立即作废在途播放链并暂停当前声音，避免拖动时持续出声 / 串声
        _cloudGen++;
        if (_cloudAudio) { try { _cloudAudio.pause(); _cloudAudio.src = ""; } catch (e) {} _cloudAudio = null; }
        const v = parseFloat(prog.value);
        const time = document.getElementById("tts-time");
        if (time && _cloudTotalDur) time.textContent = _fmtTime(v) + " / " + _fmtTime(_cloudTotalDur);
      });
      prog.addEventListener("change", function () {
        prog._dragging = false;
        _cloudSeek(parseFloat(prog.value));
      });
    }
    bar.style.display = "flex";
    _updateCloudCtrl();
    const time = document.getElementById("tts-time");
    if (preparing && time) time.textContent = "准备中…";
  }
  function hideCloudCtrl() {
    const bar = document.getElementById("tts-ctrl");
    if (bar) bar.style.display = "none";
  }
  function _updateCloudCtrl() {
    const t = document.getElementById("tts-play-toggle");
    if (t) t.textContent = _cloudPaused ? "▶" : "⏸";
  }

  // 直接用浏览器 speechSynthesis 朗读一段原文（云端兜底用，不进入分段 pump，避免 cancel/speak 竞态）
  function _speakBrowserRaw(text) {
    if (!("speechSynthesis" in window)) { _ttsNoEngineHint(); return; }
    try { window.speechSynthesis.cancel(); } catch (e) {}
    const u = new SpeechSynthesisUtterance(text);
    u.lang = state.curLang || "zh-CN";
    u.rate = state.ttsRate || 0.95;
    u.pitch = state.ttsPitch || 1.02;
    u.volume = (state.ttsVolume === 0) ? 1.0 : (state.ttsVolume || 1.0);
    let v = null;
    if (state.ttsVoice) v = _voices.find(x => x.name === state.ttsVoice) || null;
    if (!v) v = pickVoice(u.lang);
    if (v) u.voice = v;
    u.onend = () => { hideStopBtn(); };
    u.onerror = (e) => { if ((e && e.error) !== "interrupted") console.warn("[TTS][browser] 兜底朗读失败:", e && e.error); hideStopBtn(); };
    showStopBtn();
    // 加一点延迟，规避 Chrome “cancel 后紧接 speak 吞首句”的竞态
    setTimeout(() => { try { window.speechSynthesis.speak(u); } catch (e) { hideStopBtn(); } }, 120);
  }

  // 旧 _fractionReplacer / _speakOnce / doSpeak 已移除——分数转口语现内联在 _ttsPreprocess，
  // 公式转口语由 _latexToSpeech 完成（iPad onend 不可靠，故朗读由轮询驱动 _ttsPumpTick）

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  // 把模型偶尔残留的 LaTeX / 数学代码改成学生看得懂的普通写法
  function plainMath(s) {
    if (s == null) return "";
    return String(s)
      .replace(/\\\(\s*\\frac\{([^{}]*)\}\{([^{}]*)\}\s*\\\)/g, "$1/$2")  // \(\frac{a}{b}\) -> a/b
      .replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, "$1/$2")                // \frac{a}{b} -> a/b
      .replace(/\\times/g, "×")
      .replace(/\\div/g, "÷")
      .replace(/\\cdot/g, "·")
      .replace(/\\\((?!frac)/g, "(")   // \( 开头的非 frac（兜底）
      .replace(/\\\)/g, ")")
      .replace(/\\\[|\\\]/g, "")
      .replace(/\$(?![0-9])/g, "")      // 去掉孤立的 $ 符号
      .replace(/\\([a-zA-Z]+)/g, "$1")  // 丢掉其它 LaTeX 命令的反斜杠（如 \text -> text）
      .replace(/\\/g, "")               // 清掉剩余反斜杠
      .trim();
  }
  // 把换行转成 <br>，让例题的每一步分行显示（需在 esc 之后调用）
  function nl2br(s) { return String(s == null ? "" : s).replace(/\r\n|\r|\n/g, "<br>"); }

  // 将课程内容（含 **bold**、##标题、|表格|、-列表、$$公式块、【】强调）转为安全HTML
  function renderBody(text) {
    if (text == null || text === "") return "";
    let s = String(text);
    // 先做 HTML 转义（防 XSS）
    s = esc(s);
    // —— 围栏代码块 ```lang ... ```：先整体抽离，避免内部被加粗/表格/列表等规则破坏 ——
    const _codeBlocks = [];
    s = s.replace(/```[a-zA-Z0-9_+\-]*\n([\s\S]*?)```/g, (m, code) => {
      const token = "\u0000CB" + _codeBlocks.length + "\u0000";
      _codeBlocks.push(String(code).replace(/\n$/, ""));
      return "\n\n" + token + "\n\n";
    });
    // 【标题】→ <h4>
    s = s.replace(/^【(.+?)】$/gm, '<h4 class="lb-h">$1</h4>');
    // **加粗** → <strong>
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // 表格行：| ... | → <tr><td>...</td></tr>
    const lines = s.split("\n");
    let inTable = false, tableHtml = "";
    let outLines = [];
    for (let li = 0; li < lines.length; li++) {
      const line = lines[li].trim();
      if (line.startsWith("|") && line.endsWith("|") && !line.replace(/\|/g, "").match(/^[-: ]+$/)) {
        if (!inTable) { inTable = true; tableHtml = ""; }
        // 跳过分隔行 |---|---|
        if (/^[\s\|:-]+$/.test(line)) continue;
        const cells = line.split("|").filter((c, i, arr) => i > 0 && i < arr.length - 1).map(c => c.trim());
        tableHtml += "<tr>" + cells.map(c => `<td>${c}</td>`).join("") + "</tr>";
        // 检查下一行是否还是表格
        const nextLine = (li + 1 < lines.length) ? lines[li + 1].trim() : "";
        if (!nextLine.startsWith("|") || !nextLine.endsWith("|")) {
          inTable = false;
          outLines.push(`<table class="lb-table"><tbody>${tableHtml}</tbody></table>`);
        }
        continue;
      } else if (inTable) {
        inTable = false;
        outLines.push(`<table class="lb-table"><tbody>${tableHtml}</tbody></table>`);
      }
      // 无序列表 • 或 - 开头
      if (/^[•\-]\s/.test(line)) {
        outLines.push('<li class="lb-li">' + line.replace(/^[•\-]\s/, "") + '</li>');
        continue;
      }
      // 公式块 $$...$$ 保留（KaTeX 会渲染）
      outLines.push(line);
    }
    s = outLines.join("\n");
    // 连续的 <li> 包裹为 <ul>
    s = s.replace(/(<li class="lb-li">.*?<\/li>(\n|$))+/g, (m) => '<ul class="lb-ul">' + m + '</ul>');
    // 空行变段落分隔
    s = s.replace(/\n\n+/g, '</p><p>');
    s = s.replace(/\n/g, '<br>');
    s = '<p>' + s + '</p>';
    // 清理空标签
    s = s.replace(/<p><\/p>/g, "");
    s = s.replace(/<p>(<h4)/g, '$1');
    s = s.replace(/(<\/h4>)<\/p>/g, '$1');
    s = s.replace(/<p>(<(?:table|ul))/g, '$1');
    s = s.replace(/(<\/(?:table|ul)>)<\/p>/g, '$1');
    // —— 还原代码块：把裸 TOKEN 替换回 <pre class="lb-code">（不包裹在 <p> 内）——
    s = s.replace(/<p>(\u0000CB\d+\u0000)<\/p>/g, '$1');
    s = s.replace(/\u0000CB(\d+)\u0000/g, (m, i) => '<pre class="lb-code">' + _codeBlocks[Number(i)] + '</pre>');
    return s;
  }

  // ====== KaTeX 数学公式渲染 ======
  // 对容器内所有 $...$ 和 $$...$$ 内容渲染为可视化数学公式
  function renderMath(container) {
    if (!container || typeof window.renderMathInElement !== "function") return;
    try {
      renderMathInElement(container, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
        ],
        // 中文学习系统里常有中文误入 $...$ 公式定界符，strict:false 让 KaTeX 静默接受
        // 数学模式中的 Unicode 文本（等价于 "ignore"），不再刷 unicodeTextInMathMode 告警
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
        katexOptions: { strict: false, throwOnError: false },
      });
    } catch (e) { /* 静默失败，不影响主流程 */ }
  }
  // ====== KaTeX 结束 ======
  function STAGE_NAME(i) { return ["初识", "熟悉", "信赖", "默契", "亦师亦友"][i] || "初识"; }
  function scrollChat() { const l = el("chat-log"); l.scrollTop = l.scrollHeight; }

  function appendBubble(role, text, animate, emotion, done) {
    const log = el("chat-log");
    const empty = log.querySelector(".empty"); if (empty) empty.remove();
    const wrap = document.createElement("div");
    wrap.className = "msg " + (role === "user" ? "user" : "bot");
    const av = document.createElement("div");
    av.className = "av";
    av.textContent = role === "user" ? "🧑" : "🤖";
    const box = document.createElement("div");
    const who = document.createElement("div");
    who.className = "who";
    who.textContent = role === "user" ? "我" : (state.currentRole ? state.currentRole.name : "导师");
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    box.appendChild(who); box.appendChild(bubble);
    wrap.appendChild(av); wrap.appendChild(box);
    log.appendChild(wrap);
    if (animate) typeText(bubble, text, () => { renderMath(wrap); if (done) done(); });
    else { bubble.innerHTML = renderBody(text); renderMath(wrap); if (done) done(); }
    return wrap;
  }
  function appendTyping() {
    const log = el("chat-log");
    const wrap = document.createElement("div");
    wrap.className = "msg bot typing";
    wrap.innerHTML = `<div class="av">🤖</div><div class="bubble"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;
    log.appendChild(wrap);
    return wrap;
  }
  function typeText(node, text, done) {
    let i = 0;
    const speed = 18;
    const timer = setInterval(() => {
      node.textContent = text.slice(0, i);
      scrollChat();
      i += 1;
      if (i > text.length) { clearInterval(timer); if (done) done(); }
    }, speed);
  }

  // ---------- 知识图谱力学布局（增强版：掌握度颜色 + 权重 + 点击交互） ----------
  function masteryColor(level) {
    // 0未测灰 / 1未掌握红 / 2了解橙 / 3熟悉黄 / 4掌握绿
    const colors = ["#94a3b8", "#ef4444", "#f97316", "#eab308", "#22c55e"];
    return colors[Math.min(Math.max(level || 0, 0), 4)];
  }

  function drawGraph(nodes, edges) {
    const svg = el("kg-svg");
    const W = 900, H = 520;
    if (!nodes.length) {
      svg.innerHTML = `<text x="450" y="260" text-anchor="middle" fill="#94a3b8">该角色暂无知识节点，去「学习」页对话后会自动生成 🕸️</text>`;
      return;
    }
    const pos = {};
    nodes.forEach((n, i) => {
      const a = (i / nodes.length) * Math.PI * 2;
      pos[n.id] = { x: W / 2 + Math.cos(a) * 180 + (Math.random() - .5) * 40,
                    y: H / 2 + Math.sin(a) * 160 + (Math.random() - .5) * 40, vx: 0, vy: 0 };
    });
    const deg = {}; nodes.forEach(n => deg[n.id] = 0);
    edges.forEach(e => { deg[e.source] = (deg[e.source] || 0) + 1; deg[e.target] = (deg[e.target] || 0) + 1; });

    for (let it = 0; it < 320; it++) {
      nodes.forEach(a => {
        let fx = 0, fy = 0;
        nodes.forEach(b => {
          if (a.id === b.id) return;
          let dx = pos[a.id].x - pos[b.id].x, dy = pos[a.id].y - pos[b.id].y;
          let d2 = dx * dx + dy * dy + 0.01;
          const f = 5200 / d2;
          const d = Math.sqrt(d2);
          fx += (dx / d) * f; fy += (dy / d) * f;
        });
        fx += (W / 2 - pos[a.id].x) * 0.012;
        fy += (H / 2 - pos[a.id].y) * 0.012;
        pos[a.id].vx = (pos[a.id].vx + fx) * 0.85;
        pos[a.id].vy = (pos[a.id].vy + fy) * 0.85;
      });
      edges.forEach(e => {
        if (!pos[e.source] || !pos[e.target]) return;
        let dx = pos[e.target].x - pos[e.source].x, dy = pos[e.target].y - pos[e.source].y;
        const d = Math.sqrt(dx * dx + dy * dy) + 0.01;
        const w = e.weight || 1;
        const f = (d - 130) * 0.02 * w;
        const ux = dx / d, uy = dy / d;
        pos[e.source].vx += ux * f; pos[e.source].vy += uy * f;
        pos[e.target].vx -= ux * f; pos[e.target].vy -= uy * f;
      });
      nodes.forEach(n => {
        const p = pos[n.id];
        p.x += Math.max(-12, Math.min(12, p.vx));
        p.y += Math.max(-12, Math.min(12, p.vy));
        p.x = Math.max(40, Math.min(W - 40, p.x));
        p.y = Math.max(30, Math.min(H - 30, p.y));
      });
    }

    let svgText = "";
    // 边
    edges.forEach(e => {
      if (!pos[e.source] || !pos[e.target]) return;
      const a = pos[e.source], b = pos[e.target];
      const opacity = Math.min(1, 0.4 + (e.weight || 1) * 0.2);
      svgText += `<line class="kg-edge" x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" opacity="${opacity}" />`;
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      if (e.rel) svgText += `<text class="kg-edge-label" x="${mx.toFixed(1)}" y="${my.toFixed(1)}" text-anchor="middle">${esc(e.rel)}</text>`;
    });
    // 节点（带点击事件）
    nodes.forEach(n => {
      const p = pos[n.id];
      const baseR = 12 + Math.min(10, (deg[n.id] || 0) * 2);
      const r = baseR * (0.8 + (n.weight || 1) * 0.3); // 权重影响大小
      const col = masteryColor(n.mastery);
      const label = n.mastery_label || "";
      const cid = n.course_id ? `data-cid="${esc(n.course_id)}"` : "";
      svgText += `<g class="kg-node" style="cursor:pointer" onclick="UI.kgNodeClick(this)" data-label="${esc(n.label)}" data-mastery="${label}" ${cid}>` +
        `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${r.toFixed(1)}" fill="${col}" opacity="0.9" stroke="#fff" stroke-width="2"/>` +
        `<text x="${p.x.toFixed(1)}" y="${(p.y + r + 14).toFixed(1)}" text-anchor="middle" font-size="12">${esc(n.label)}</text>` +
        `</g>`;
    });
    svg.innerHTML = svgText;
  }

  // ================================================================
  // 🏠 学习机模式（对标科大讯飞 AI 学习机）
  //  - 宫格主页 / 顶部状态条 / AI 学伴卡 / 常驻学伴球 / 全屏学伴对话
  // ================================================================

  const MACH_TILES = [
    { icon: "📖", title: "同步学", sub: "教材同步", cls: "mt-c1", go: "selfstudy" },
    { icon: "🎯", title: "精准学", sub: "查漏补缺", cls: "mt-c2", go: "precision" },
    { icon: "✏️", title: "AI 解题", sub: "拍照讲解", cls: "mt-c3", act: "ocr" },
    { icon: "📕", title: "错题本", sub: "温故知新", cls: "mt-c4", act: "mistakes" },
    { icon: "📊", title: "学情报告", sub: "学习总结", cls: "mt-c5", go: "report" },
    { icon: "🌈", title: "课外阅读", sub: "分级读物", cls: "mt-c6", act: "stories" },
    { icon: "🏆", title: "我的成就", sub: "星星徽章", cls: "mt-c7", act: "achievement" },
    { icon: "👨‍👩‍👦", title: "家长中心", sub: "时长设置", cls: "mt-c8", act: "parent" },
  ];

  const COMPANION_STATE = { opening: null, messages: [], busy: false, voice: false, context: null, recog: null,
    courseId: null, sectionIdx: 0, quizIndex: 0, quizState: null };

  function cpEsc(t) { return String(t == null ? "" : t).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  // 学习机宫格：一屏直达所有功能
  function renderMachGrid() {
    const box = el("mach-grid");
    if (!box) return;
    box.innerHTML = MACH_TILES.map((t, i) => {
      const badge = t.act === "mistakes" ? '<span class="mt-badge" id="mt-badge-mistakes" style="display:none"></span>' : "";
      return '<button class="mach-tile ' + t.cls + '" data-tile="' + i + '">' + badge +
        '<span class="mt-ico">' + t.icon + '</span>' +
        '<span class="mt-title">' + cpEsc(t.title) + '</span>' +
        '<span class="mt-sub">' + cpEsc(t.sub || "") + '</span>' +
        '</button>';
    }).join("");
    box.querySelectorAll(".mach-tile").forEach(btn => {
      btn.addEventListener("click", () => {
        try { window._AL_SFX && window._AL_SFX.play("tap"); } catch (e) {}
        const t = MACH_TILES[parseInt(btn.dataset.tile, 10)];
        if (!t) return;
        if (t.go) return UI.go(t.go);
        if (t.act === "ocr") return UI.openOCR();
        if (t.act === "stories") return UI.openStories();
        if (t.act === "achievement") return UI.openAchievement();
        if (t.act === "parent") return UI.openParentGate();
        if (t.act === "mistakes") return UI.goMistakes();
      });
    });
  }

  // 顶部状态条：连续天数 / 星星 / 今日时长
  function renderMachStatus(ctx) {
    ctx = ctx || {};
    const st = el("ms-streak"); if (st) st.textContent = "🔥 " + (ctx.streak || 0) + " 天";
    const sa = el("ms-stars"); if (sa) sa.textContent = "⭐ " + (ctx.stars || 0);
    const todayMin = Math.floor((state.todaySec || 0) / 60);
    const tmax = ctx.daily_max || state.dailyMaxMin || 30;
    const tm = el("ms-time"); if (tm) tm.textContent = "⏱ " + todayMin + "/" + tmax + " 分";
    const av = el("launcher-avatar"); if (av) av.textContent = state.childAvatar || "🐱";
    const nm = el("launcher-name"); if (nm) nm.textContent = state.childName || "小朋友";
  }

  // AI 学伴卡：开场白 + 动作按钮
  async function renderCompanionCard(force) {
    if (COMPANION_STATE.opening && !force) return;
    let data = null;
    try {
      data = await api("GET", "/api/ai/companion/opening?view=home");
    } catch (e) {
      // 离线/未登录：本地兜底，保证界面不空
      data = {
        greeting: "你好呀",
        opening: (state.childName || "小朋友") + "，今天想学点什么？点下面的按钮就能开始。",
        mood: "guide",
        actions: [{ id: "learn_new", label: "同步学", icon: "📖", type: "route", target: "selfstudy" },
                  { id: "practice2", label: "练几道题", icon: "✏️", type: "route", target: "practice" }],
        context: {},
      };
    }
    COMPANION_STATE.opening = data;
    const bubble = el("companion-opening");
    if (bubble) bubble.textContent = (data.greeting ? data.greeting + " " : "") + (data.opening || "");
    const hint = el("companion-mood-hint");
    const MOOD = { encourage: "继续加油中 · 我陪着你", congratulate: "今天表现很棒", remind: "有任务在等你", guide: "随时为你解答" };
    if (hint) hint.textContent = MOOD[data.mood] || "随时为你解答";
    const act = el("companion-actions");
    if (act) {
      act.innerHTML = (data.actions || []).map((a, i) =>
        '<button class="cc-act" data-act="' + i + '"><span class="ca-ico">' + cpEsc(a.icon || "▶") + '</span>' + cpEsc(a.label) + '</button>'
      ).join("");
      act.querySelectorAll(".cc-act").forEach(btn => {
        btn.addEventListener("click", () => UI.companionAction((data.actions || [])[parseInt(btn.dataset.act, 10)]));
      });
    }
    renderMachStatus(data.context);
  }

  // 学伴动作路由：continue/practice/review/learn_new/rest/explain/none
  function runCompanionAction(a) {
    if (!a) return;
    const action = a.action || a.id;
    // 学伴内部动作：直接在对话里继续，不跳页
    if (action === "explain" || action === "explain_next") {
      if (a.topic_id) COMPANION_STATE.courseId = a.topic_id;
      if (action === "explain_next") COMPANION_STATE.sectionIdx = parseInt(a.section_idx, 10) || 0;
      cpPush("user", action === "explain_next" ? "继续下一部分" : "讲讲这个");
      cpRenderSuggest([]);
      return companionPost(action === "explain_next" ? "继续讲下一部分" : "给我讲讲这个知识点",
                            { topic_id: a.topic_id });
    }
    if (action === "quiz") {
      if (a.topic_id) COMPANION_STATE.courseId = a.topic_id;
      cpPush("user", "考考我");
      cpRenderSuggest([]);
      return companionPost("考考我", { topic_id: a.topic_id, want_quiz: true });
    }
    if (action === "continue" || action === "resume") {
      if (state.resume) return UI.resumeGo();
      return UI.go("selfstudy");
    }
    if (action === "practice") {
      if (a.course_id) { UI.selectCourseById(a.course_id); UI.enterApp("precision"); }
      else UI.go("precision");
      return;
    }
    if (action === "review") return UI.goMistakes();
    if (action === "learn_new") {
      if (a.course_id) { UI.openLessonById(a.course_id); return; }
      return UI.go("selfstudy");
    }
    if (action === "rest") { UI.toast("好，休息 2 分钟，我在这儿等你回来 🌿"); return; }
  }

  // ---------- AI 学伴全屏对话 ----------
  function cpPush(role, text, extra) {
    COMPANION_STATE.messages.push({ role, text, extra: extra || null });
    cpRenderLog();
  }

  // 卡片：把「出题 / 判分 / 讲义」渲染成可点击的结构，而不是一坨文字
  function cpRenderCard(card) {
    if (!card || !card.type) return "";
    if (card.type === "quiz") {
      const opts = (card.options || []).map((o, i) =>
        '<button class="cpq-opt" data-qopt="' + i + '">' + cpEsc(o) + '</button>').join("");
      return '<div class="cp-card cpq-card" data-topic="' + cpEsc(card.topic_id || "") + '" data-qidx="' + (card.quiz_index || 0) + '">' +
        '<div class="cpq-head">📝 第 ' + ((card.quiz_index || 0) + 1) + '/' + (card.quiz_total || 0) + ' 题</div>' +
        (opts ? '<div class="cpq-opts">' + opts + '</div>' :
          '<div class="cpq-open"><input class="cpq-input" placeholder="写下你的答案…" /><button class="cpq-send">提交</button></div>') +
        '</div>';
    }
    if (card.type === "quiz_result") {
      return '<div class="cp-card cpq-result ' + (card.correct ? "ok" : "bad") + '">' +
        '<div class="cpq-res-head">' + (card.correct ? "✅ 答对了" : "❌ 再想想") + '</div>' +
        (card.explanation ? '<div class="cpq-res-body">' + cpEsc(card.explanation) + '</div>' : "") +
        '</div>';
    }
    if (card.type === "lesson") {
      return '<div class="cp-card cpl-card">' +
        '<div class="cpl-head">📖 ' + cpEsc(card.title || "") +
        (card.section_total ? ' · 第 ' + ((card.section_idx || 0) + 1) + '/' + card.section_total + ' 部分' : "") +
        '</div></div>';
    }
    return "";
  }

  function cpRenderLog() {
    const log = el("cp-log");
    if (!log) return;
    const rows = COMPANION_STATE.messages.map(m => {
      if (m.role === "assistant") {
        const cardHtml = m.extra && m.extra.card ? cpRenderCard(m.extra.card) : "";
        return '<div class="cp-msg"><div class="cp-msg-avatar">🦊</div><div class="cp-col">' +
          '<div class="cp-bubble">' + cpEsc(m.text) + '</div>' + cardHtml + '</div></div>';
      }
      return '<div class="cp-msg me"><div class="cp-msg-avatar">' + cpEsc(state.childAvatar || "🧒") + '</div><div class="cp-bubble">' + cpEsc(m.text) + '</div></div>';
    });
    if (COMPANION_STATE.busy) {
      rows.push('<div class="cp-msg cp-typing"><div class="cp-msg-avatar">🦊</div>' +
        '<div class="cp-bubble"><span class="cp-dot"></span><span class="cp-dot"></span><span class="cp-dot"></span></div></div>');
    }
    log.innerHTML = rows.join("");
    log.scrollTop = log.scrollHeight;
    // 选项点击 → 把选项字母作为答案发给服务端判分
    log.querySelectorAll(".cpq-opt").forEach(btn => {
      btn.addEventListener("click", () => {
        const cardEl = btn.closest(".cpq-card");
        if (!cardEl || cardEl.dataset.done === "1") return;
        cardEl.dataset.done = "1";
        const idx = parseInt(btn.dataset.qopt, 10);
        const letter = String.fromCharCode(65 + idx);
        UI.companionAnswer(letter, cardEl.dataset.topic, parseInt(cardEl.dataset.qidx, 10));
      });
    });
    log.querySelectorAll(".cpq-send").forEach(btn => {
      btn.addEventListener("click", () => {
        const cardEl = btn.closest(".cpq-card");
        const inp = cardEl && cardEl.querySelector(".cpq-input");
        const v = inp ? inp.value.trim() : "";
        if (!v) return;
        UI.companionAnswer(v, cardEl.dataset.topic, parseInt(cardEl.dataset.qidx, 10));
      });
    });
  }

  function cpRenderSuggest(list) {
    const box = el("cp-suggest");
    if (!box) return;
    box.innerHTML = (list || []).map((s, i) =>
      '<button class="cp-sg" data-sg="' + i + '">' + cpEsc(s.label) + '</button>').join("");
    box.querySelectorAll(".cp-sg").forEach(btn => {
      btn.addEventListener("click", () => {
        const s = (list || [])[parseInt(btn.dataset.sg, 10)];
        if (!s) return;
        if (s.action && s.action !== "none") runCompanionAction(s);
        else UI.companionQuick(s.label);
      });
    });
  }

  function speakCompanion(text) {
    if (!COMPANION_STATE.voice || !text) return;
    try {
      if (typeof window._alSpeak === "function") { window._alSpeak(text); return; }
      if (typeof speak === "function") { speak(text); return; }
      if (window.UI && typeof window.UI.speakLastText === "function") { window.UI.speakLastText(text); return; }
      if (window.speechSynthesis) {
        const u = new SpeechSynthesisUtterance(text);
        u.lang = "zh-CN"; u.rate = state.ttsRate || 0.95;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      }
    } catch (e) {}
  }

  // 打开学伴：若还没有开场，学伴主动先开口
  async function openCompanion(prefill) {
    UI.go("companion");
    const log = el("cp-log");
    if (!log) return;
    if (!COMPANION_STATE.messages.length) {
      const op = COMPANION_STATE.opening || {};
      const hi = ((op.greeting || "你好呀") + (op.opening ? " " + op.opening : "")).trim();
      cpPush("assistant", hi);
      cpRenderSuggest(op.actions ? op.actions.map(a => ({ label: a.label, action: a.id === "resume" ? "continue" : (a.id === "review" ? "review" : (a.id === "practice" ? "practice" : (a.id === "learn_new" ? "learn_new" : "none"))) })) : []);
    }
    const st = el("cp-status");
    if (st) st.textContent = "随时为你解答";
    if (prefill) {
      const inp = el("cp-input");
      if (inp) { inp.value = prefill; inp.focus(); }
    }
    cpRenderLog();
  }

  // 真正打接口：所有入口（打字/点按钮/点选项）最后都到这里
  async function companionPost(text, opts) {
    opts = opts || {};
    COMPANION_STATE.busy = true;
    cpRenderLog();
    const st = el("cp-status"); if (st) st.textContent = "小艾正在想…";
    const history = COMPANION_STATE.messages.slice(-10, -1).map(m => ({ role: m.role, content: m.text }));
    // 当前课程：优先用对话里最近一次讲到的课，其次当前自学章节
    const cid = COMPANION_STATE.courseId || state._ssChapterId ||
      (state.selectedCourse && state.selectedCourse.id) || null;
    const payload = {
      message: text, history,
      view: state._lastView || "companion",
      course_id: opts.topic_id || cid,
      section_idx: COMPANION_STATE.sectionIdx || 0,
      quiz_index: COMPANION_STATE.quizIndex || 0,
      quiz_state: COMPANION_STATE.quizState || null,
      want_quiz: !!opts.want_quiz,
    };
    try {
      const r = await api("POST", "/api/ai/companion/chat", payload);
      COMPANION_STATE.busy = false;
      // 记住学伴讲到哪一课，下一个「考考我 / 下一部分」才不会跑偏
      const card = r.card || null;
      if (card && card.topic_id) {
        COMPANION_STATE.courseId = card.topic_id;
        if (card.type === "lesson") COMPANION_STATE.sectionIdx = (card.section_idx || 0) + 1;
        if (card.type === "quiz") {
          COMPANION_STATE.quizIndex = (card.quiz_index || 0);
          COMPANION_STATE.quizState = { topic_id: card.topic_id, quiz_index: card.quiz_index || 0, awaiting: true };
        }
        if (card.type === "quiz_result") {
          COMPANION_STATE.quizIndex = ((COMPANION_STATE.quizIndex || 0) + 1);
          COMPANION_STATE.quizState = { topic_id: card.topic_id || COMPANION_STATE.courseId,
                                        quiz_index: COMPANION_STATE.quizIndex, awaiting: false };
        }
      }
      cpPush("assistant", r.reply || "…", { card: card });
      cpRenderSuggest(r.suggest || []);
      speakCompanion(r.reply);
      if (st) st.textContent = "随时为你解答";
    } catch (e) {
      COMPANION_STATE.busy = false;
      cpPush("assistant", "哎呀，我这边网络有点卡。你先试试下面的按钮，或者过一会儿再问我～");
      if (st) st.textContent = "随时为你解答";
    }
  }

  async function companionSend() {
    if (COMPANION_STATE.busy) return;
    const inp = el("cp-input");
    const text = (inp && inp.value || "").trim();
    if (!text) return;
    if (inp) inp.value = "";
    cpPush("user", text);
    cpRenderSuggest([]);
    await companionPost(text, {});
  }

  // 点选项交答案：先把孩子选的显示成一条气泡，再判分
  async function companionAnswer(answer, topicId, quizIdx) {
    if (COMPANION_STATE.busy) return;
    cpPush("user", String(answer));
    cpRenderSuggest([]);
    COMPANION_STATE.quizState = { topic_id: topicId || COMPANION_STATE.courseId,
                                  quiz_index: quizIdx || 0, awaiting: true };
    await companionPost(String(answer), { topic_id: topicId });
  }

  // 快捷指令：点胶囊直接发一句话
  function companionQuick(text) {
    const inp = el("cp-input");
    if (inp) inp.value = text;
    companionSend();
  }

  function onCompanionKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); companionSend(); }
  }

  function companionMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast("当前浏览器不支持语音识别，改用打字吧"); return; }
    const btn = el("cp-mic");
    if (COMPANION_STATE.recog) {
      try { COMPANION_STATE.recog.stop(); } catch (e) {}
      COMPANION_STATE.recog = null;
      if (btn) btn.classList.remove("rec");
      return;
    }
    const rec = new SR();
    rec.lang = "zh-CN"; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult = ev => {
      const t = ev.results[0][0].transcript;
      const inp = el("cp-input"); if (inp) inp.value = t;
      COMPANION_STATE.recog = null;
      if (btn) btn.classList.remove("rec");
      companionSend();
    };
    rec.onerror = () => { COMPANION_STATE.recog = null; if (btn) btn.classList.remove("rec"); };
    rec.onend = () => { COMPANION_STATE.recog = null; if (btn) btn.classList.remove("rec"); };
    try { rec.start(); COMPANION_STATE.recog = rec; if (btn) btn.classList.add("rec"); }
    catch (e) { toast("麦克风启动失败"); }
  }

  function toggleCompanionVoice() {
    COMPANION_STATE.voice = !COMPANION_STATE.voice;
    const b = el("cp-voice-btn");
    if (b) b.classList.toggle("on", COMPANION_STATE.voice);
    toast(COMPANION_STATE.voice ? "语音模式已开启，小艾会读给你听 🔊" : "语音模式已关闭");
  }

  function clearCompanion() {
    COMPANION_STATE.messages = [];
    cpRenderLog(); cpRenderSuggest([]);
    UI.openCompanion();
  }

  // 学伴球显隐：学习机内部页面显示，全屏对话页隐藏
  function updateCompanionFab(view) {
    const fab = el("companion-fab");
    if (!fab) return;
    const hideViews = ["companion"];
    fab.classList.toggle("show", hideViews.indexOf(view) < 0);
  }

  // 学习机模式入口：把新方法挂到 UI 上（不改动原对象定义，避免影响既有代码）
  Object.assign(UI, {
    renderMachineHome(force) {
      renderMachGrid();
      renderCompanionCard(force !== false);
    },
    renderMachStatus,
    openCompanion,
    companionSend,
    companionAnswer,
    companionQuick,
    onCompanionKey,
    companionMic,
    toggleCompanionVoice,
    clearCompanion,
    companionAction: runCompanionAction,
  });

  // ---------- 🚀 启动（学习机模式） ----------
  window.UI = UI;

  // 初始化交互：头像选择器 + 时长选择器
  UI.initAvatarPicker();
  UI.initTimeOptions();

  // 静默登录/注册子账号
  // 记住每个孩子「这个账号是否已注册」，下次直接用 /api/login，
  // 不再每次都先打 /api/register（那条路在服务端要占 1 次鉴权限流名额，
  // 反复刷新会把 60 秒 10 次的额度耗光 → 401/429 → 桌面静默空白）。
  function accountKnown(user) {
    try { return localStorage.getItem("al_reg_" + user) === "1"; } catch (e) { return false; }
  }
  function markAccountKnown(user) {
    try { localStorage.setItem("al_reg_" + user, "1"); } catch (e) {}
  }

  async function bootLogin() {
    if (state.token) {
      try { await api("GET", "/api/me"); return; } catch (e) {
        state.token = ""; localStorage.removeItem("al_token");
      }
    }
    const uname = accountOfChild(state.childName || "user");
    const useLogin = accountKnown(uname);

    // 顺序按「该账号是否已注册」决定，避免无谓的 409 占用限流额度
    const attempt = async (path) => {
      const r = await api("POST", path, { username: uname, password: "al_child_default" });
      bindAccount(r.username);
      state.token = r.token; state.username = r.username;
      localStorage.setItem("al_token", r.token);
      localStorage.setItem("al_user", r.username);
      markAccountKnown(r.username);
      const b = document.getElementById("export-data-btn"); if (b) b.style.display = "block";
      return r;
    };
    try {
      await attempt(useLogin ? "/api/login" : "/api/register");
    } catch (e) {
      const msg = (e && e.message) || "";
      const isRate = /频繁|429/.test(msg);
      if (isRate) { state._authLimitedAt = Date.now(); return; }   // 限流：别继续硬试
      // 注册说「已存在」→ 说明早就有账号，转 login；login 说「不存在」→ 转 register
      try {
        await attempt(useLogin ? "/api/register" : "/api/login");
      } catch (e2) { /* 离线可忽略：本地进度仍可用，联网后自动补 */ }
    }
  }

  // 孩子档案同步到服务端（跨域名/设备/清缓存都能自动恢复，不必再填名字头像）
  // ================================================================
  // 👥 账号绑定：每个孩子 = 一个服务端账号（child_<名字>），本地数据按账号隔离
  // ================================================================
  // 旧实现的问题：al_ss_progress / al_resume_v1 / al_stories_v1 都是全局 key，
  // 多个孩子共用一份 → 切孩子会串数据。这里在切换前把当前孩子的本地数据打包
  // 存到 al_scope_<账号名> 下，切过去再还原，做到「一人一份」。
  const SCOPE_KEYS = ["al_ss_progress", "al_resume_v1", "al_stories_v1"];

  // 孩子名 → 服务端账号名（同一台学习机上，每个孩子独立一份学习数据）
  function accountOfChild(name) {
    return "child_" + String(name || "").trim();
  }

  function saveScopeFor(user) {
    if (!user) return;
    try {
      const blob = {};
      SCOPE_KEYS.forEach(k => {
        const v = localStorage.getItem(k);
        if (v != null) blob[k] = v;
      });
      localStorage.setItem("al_scope_" + user, JSON.stringify(blob));
    } catch (e) {}
  }

  function restoreScopeFor(user) {
    if (!user) return;
    let blob = null;
    try { blob = JSON.parse(localStorage.getItem("al_scope_" + user) || "null"); } catch (e) {}
    SCOPE_KEYS.forEach(k => {
      try {
        if (blob && blob[k] != null) localStorage.setItem(k, blob[k]);
        else localStorage.removeItem(k);
      } catch (e) {}
    });
  }

  // 切换账号实体（含首次登录）：先存旧账号的数据，再清空，再还原新账号的数据
  function bindAccount(newUser) {
    const oldUser = localStorage.getItem("al_user") || "";
    if (oldUser && oldUser !== newUser) {
      saveScopeFor(oldUser);
      SCOPE_KEYS.forEach(k => { try { localStorage.removeItem(k); } catch (e) {} });
    }
    if (newUser) restoreScopeFor(newUser);
  }

  // ---------------------------------------------------------------
  async function syncProfile() {
    try {
      const children = JSON.parse(localStorage.getItem("al_children") || "[]");
      await api("POST", "/api/profile", {
        children,
        active: state.childName,
        parentPin: state.parentPin,
        dailyMax: state.dailyMaxMin
      });
    } catch (e) { /* 离线可忽略 */ }
  }

  // 学习机启动入口
  async function boot() {
    // 首次使用？检查孩子档案
    if (!localStorage.getItem("al_child_name")) {
      // 跨域名/换设备/清缓存恢复：先尝试从服务端拉取已保存档案
      try {
        const prof = await api("GET", "/api/profile");
        const kids = (prof && prof.children) || [];
        const activeName = (prof && prof.active) || (kids[0] && kids[0].name) || "";
        if (activeName) {
          const k = kids.find(c => c.name === activeName) || kids[0];
          localStorage.setItem("al_child_name", k.name);
          localStorage.setItem("al_child_avatar", k.avatar || "🐱");
          if (prof && prof.parentPin) localStorage.setItem("al_parent_pin", prof.parentPin);
          if (prof && prof.dailyMax) localStorage.setItem("al_daily_max", String(prof.dailyMax));
          localStorage.setItem("al_children", JSON.stringify(kids));
          state.childName = k.name;
          state.childAvatar = k.avatar || "🐱";
          state.parentPin = (prof && prof.parentPin) || "";
          state.dailyMaxMin = parseInt((prof && prof.dailyMax) || "30", 10);
          showLauncher();
          await bootLogin();
          return;
        }
      } catch (e) { /* 离线/无档案，走本地向导 */ }
      // 真的没有档案 → 显示设置向导
      el("app-view").hidden = true;
      el("setup-wizard").hidden = false;
      el("setup-step-1").hidden = false;
      el("setup-step-2").hidden = true;
      // 默认选中第一个头像
      const firstAv = document.querySelector(".av-opt");
      if (firstAv) { firstAv.classList.add("selected"); state.childAvatar = firstAv.dataset.av; }
      return;
    }
    // 有档案 → 显示学习桌面
    state.childName = localStorage.getItem("al_child_name") || "小朋友";
    state.childAvatar = localStorage.getItem("al_child_avatar") || "🐱";
    state.parentPin = localStorage.getItem("al_parent_pin") || "";
    state.dailyMaxMin = parseInt(localStorage.getItem("al_daily_max") || "30", 10);
    showLauncher();
    syncProfile();   // 本地已有档案也立即备份到服务端，防域名/缓存变化后丢失

    // 💎 激励引擎初始化：首页任务卡/连胜条/宝石数 + 数据变化自动重渲染
    try {
      window.AL_GAMIFY_REFRESH = () => { try { UI.renderGamify(); } catch (e) {} };
      UI.renderGamify();
    } catch (e) {}

    // ⏯ 「下次打开可以继续」：开机即读回上次学习位置，首页显示「继续学习」卡片。
    // 注意必须放在这里 —— 常态启动走的是 boot() → showLauncher()，不经过 enter()。
    UI.loadResume();

    // 后台静默登录（不阻塞桌面显示）
    await bootLogin();
    // 📊 登录就绪后，把服务端的学习进度合并回本地（换设备/清缓存后不丢）
    try { await UI._ssLoadRemoteProgress(); } catch (e) {}
    try { UI.renderMachineHome && UI.renderMachineHome(true); } catch (e) {}
  }

  boot();

  // ---------- 学习桌面函数 ----------
  function showLauncher() {
    // 进入孩子学习主页（app-view 内的 #view-home）
    el("app-view") && (el("app-view").hidden = false);
    el("setup-wizard") && (el("setup-wizard").hidden = true);
    state._fromLauncher = true;
    // 顶栏孩子信息
    const topAv = el("top-avatar");
    if (topAv) topAv.textContent = state.childAvatar || "🐱";
    const topNm = el("top-name");
    if (topNm) topNm.textContent = (state.childName || "小朋友") + " 同学";
    // 主页内容
    const av = el("launcher-avatar");
    if (av) av.textContent = state.childAvatar;
    const nm = el("launcher-name");
    if (nm) nm.textContent = state.childName + " 同学";
    const dt = el("launcher-date");
    if (dt) {
      const d = new Date();
      const opts = { year: "numeric", month: "long", day: "numeric", weekday: "long" };
      dt.textContent = d.toLocaleDateString("zh-CN", opts);
    }
    // 激活主页
    UI.go("home");
    // 加载统计 + 学习计划
    loadLauncherStats();
    loadPlan();
    // 🏠 学习机模式：宫格 + AI 学伴主动开口
    try { UI.renderMachineHome && UI.renderMachineHome(false); } catch (e) {}
    // ⏯ 断点快照读回后，再刷新一次学伴开场（让"继续上次"更有依据）
    setTimeout(() => { try { UI.renderMachineHome && UI.renderMachineHome(true); } catch (e) {} }, 1600);
    // 恢复学习计时
    resumeTimer();
  }

  async function loadLauncherStats() {
    if (!state.token) return;
    try {
      const [daily, stars] = await Promise.all([
        api("GET", "/api/report/daily"),
        api("GET", "/api/stars"),
      ]);
      const m = daily.mastery || {};
      const mEl = el("stat-mastered");
      if (mEl) mEl.textContent = m.mastered || 0;
      const starEl = el("stat-stars");
      if (starEl) starEl.textContent = stars.total || 0;
    } catch(e) {}
  }

  async function loadPlan() {
    const planDiv = el("launcher-plan");
    if (!planDiv || !state.token) return;
    try {
      const r = await api("GET", "/api/plan/daily");
      if (r.items && r.items.length) {
        UI._updatePlanHome(r.items, r.completed || []);
      }
    } catch (e) { /* 静默，降级用旧接口 */
      try {
        const r2 = await api("GET", "/api/plan/next");
        if (r2.recommended) {
          planDiv.style.display = "flex";
          const progEl = el("plan-progress");
          if (progEl) progEl.textContent = r2.recommended.title;
        }
      } catch (e2) { /* 静默 */ }
    }
  }

  function resumeTimer() {
    if (state._timerHandle) clearInterval(state._timerHandle);
    // 取今天开始的时间戳
    const today = new Date();
    today.setHours(0,0,0,0);
    const savedSec = parseInt(localStorage.getItem("al_today_sec_" + today.getTime()) || "0", 10);
    state.todaySec = savedSec;
    state._lastTick = Date.now();
    state._timerHandle = setInterval(tickTimer, 1000);
    updateTodayStat();
    // 确保锁屏不自动显示
    state._lockSeconds = 0;
    const lock = el("lock-screen");
    if (lock) lock.setAttribute("hidden", "");
    if (state._lockTimerHandle) {
      clearInterval(state._lockTimerHandle);
      state._lockTimerHandle = null;
    }
  }

  let _lastSyncSec = 0; // 上次同步到后端的秒数

  function tickTimer() {
    const now = Date.now();
    if (state._fromLauncher) {
      if (el("app-view").hidden) return;
    }
    const elapsed = Math.floor((now - state._lastTick) / 1000);
    if (elapsed > 0) {
      state.todaySec += elapsed;
      state._lastTick = now;
      // 每10秒存一次到 localStorage
      if (elapsed >= 10 || state.todaySec % 30 < 5) {
        const today = new Date();
        today.setHours(0,0,0,0);
        localStorage.setItem("al_today_sec_" + today.getTime(), String(state.todaySec));
      }
      updateTodayStat();
      // ⏱️ 学习时长 → 每日任务（time15）埋点，每 60 秒一次
      try {
        if (window.AL_GAMIFY && state.todaySec - (state._lastTrackMin || 0) >= 60) {
          state._lastTrackMin = state.todaySec;
          window.AL_GAMIFY.track("minutes", 1);
        }
      } catch (e) {}
      // 每60秒同步到后端
      const syncDelta = state.todaySec - _lastSyncSec;
      if (syncDelta >= 60 && state.token) {
        _lastSyncSec = state.todaySec;
        api("POST", "/api/report/log-time", { seconds: syncDelta }).catch(() => {});
      }
      // 🚫 锁屏暂时禁用（调试阶段）
      // const maxSec = state.dailyMaxMin * 60;
      // if (state.todaySec >= maxSec && !state._lockSeconds) {
      //   showLockScreen();
      // }
    }
    state._lastTick = now;
  }

  function updateTodayStat() {
    const elMin = el("stat-today");
    if (elMin) elMin.textContent = Math.floor(state.todaySec / 60);
    const starEl = el("stat-stars");
    if (starEl) starEl.textContent = Math.floor(state.todaySec / 120);
  }

  // ---------- 锁屏（调试期间屏蔽）----------
  function showLockScreen() {
    // 🔇 锁屏已禁用
    return;
  }

  function hideLockScreen() {
    const lock = el("lock-screen");
    if (lock) lock.setAttribute("hidden", "");
    state._lockSeconds = 0;
    if (state._lockTimerHandle) {
      clearInterval(state._lockTimerHandle);
      state._lockTimerHandle = null;
    }
    // 恢复计时
    resumeTimer();
  }

  // 语音环境自检：在 iframe / 预览面板中浏览器会禁用 speechSynthesis，提示用浏览器打开
  (function checkVoiceEnv() {
    try {
      if (window.self !== window.top) {
        const b = document.getElementById("voice-env-banner");
        if (b) b.hidden = false;
      }
    } catch (e) {}
  })();
})();
