/*
 * gamify.js —— AL 自学系统激励引擎（每日任务 / 连胜周历 / 纯星星奖励）
 *
 * 设计（2026-10-12 按用户要求调整）：
 *  - 自家孩子使用，**不做商店/宝石等交易类功能**，只有单一货币 ⭐ 星星。
 *  - 任务完成、连胜里程碑 → 直接发星星（走 /api/stars/award：
 *    联网进服务端账本，离线进 offline-shim 记账层），攒星星解锁成就。
 *  - 纯本地 localStorage（al_gamify_v1），联网离线行为一致，不依赖服务端。
 *  - 每日任务按日期种子确定性生成（同一天刷新不变）。
 *  - 对外接口 window.AL_GAMIFY，app.js 在关键节点防御式调用 track()。
 */
(function () {
  "use strict";

  var KEY = "al_gamify_v1";
  var DAY_MS = 24 * 3600 * 1000;

  function todayStr(d) {
    d = d || new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function dateSeed(s) {
    return parseInt(s.replace(/-/g, ""), 10) || 1;
  }
  // mulberry32 确定性伪随机
  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  var TASK_POOL = [
    { id: "learn3",  icon: "📖", title: "学习 3 个新知识点", goal: 3, stars: 5, metric: "learned" },
    { id: "quiz5",   icon: "✏️", title: "答对 5 道题", goal: 5, stars: 5, metric: "quizCorrect" },
    { id: "lesson1", icon: "🎯", title: "完成 1 次本章测验", goal: 1, stars: 4, metric: "lessons" },
    { id: "speak3",  icon: "🔊", title: "朗读 3 段讲义", goal: 3, stars: 4, metric: "speaks" },
    { id: "time15",  icon: "⏱️", title: "累计学习 15 分钟", goal: 15, stars: 6, metric: "minutes" }
  ];
  var MILESTONES = { 3: 10, 7: 20, 14: 40, 30: 100, 60: 200, 100: 400 };
  var MILESTONE_BADGE = { 3: "streak_3", 7: "streak_7" };

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; }
  }
  function save(s) {
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {}
    notify();
  }
  // 待庆祝事件队列（连胜里程碑），由 UI 层 takeMilestone() 取走弹层
  var _pendingMs = [];

  function notify() {
    try { if (typeof window.AL_GAMIFY_REFRESH === "function") window.AL_GAMIFY_REFRESH(); } catch (e) {}
  }

  function base() {
    var s = load();
    if (!s.v) {
      s = { v: 2,
        streak: { cur: 0, best: 0, last: "", days: {}, milestones: {} },
        tasks: { date: "", items: [] },
        counters: { date: "", learned: 0, quizCorrect: 0, lessons: 0, speaks: 0, minutes: 0 } };
    }
    return s;
  }

  // 发星星：统一走 /api/stars/award（联网→服务端；离线→shim 记账层）
  function grantStars(points) {
    try {
      window.fetch("/api/stars/award", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "daily_task", points: points })
      }).catch(function () {});
    } catch (e) {}
  }
  function grantBadge(bid) {
    try {
      window.fetch("/api/achievements/unlock", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ badge_id: bid })
      }).catch(function () {});
    } catch (e) {}
  }

  // ---------- 每日任务 ----------
  function ensureTasks(s, t) {
    if (s.tasks.date === t && s.tasks.items.length) return;
    var rand = rng(dateSeed(t) ^ 0x5F5F);
    var pool = TASK_POOL.slice();
    var items = [];
    while (items.length < 3 && pool.length) {
      var i = Math.floor(rand() * pool.length);
      var def = pool.splice(i, 1)[0];
      items.push({ id: def.id, icon: def.icon, title: def.title, goal: def.goal,
        stars: def.stars, metric: def.metric, progress: 0, claimed: false });
    }
    s.tasks = { date: t, items: items };
  }
  function ensureCounters(s, t) {
    if (s.counters.date !== t) {
      s.counters = { date: t, learned: 0, quizCorrect: 0, lessons: 0, speaks: 0, minutes: 0 };
    }
  }

  // ---------- 连胜 ----------
  function markActive(s, t) {
    var st = s.streak;
    if (st.last === t) return false;
    var y = todayStr(new Date(Date.now() - DAY_MS));
    st.cur = (st.last === y) ? st.cur + 1 : 1;
    st.last = t;
    st.best = Math.max(st.best, st.cur);
    st.days[t] = 1;
    // 清理 120 天前的格子，防膨胀
    try {
      var ks = Object.keys(st.days).sort();
      while (ks.length > 120) delete st.days[ks.shift()];
    } catch (e) {}
    return true;
  }
  function milestoneOf(cur) { return MILESTONES[cur] || 0; }

  // ---------- 对外接口 ----------
  var API = {
    state: function () {
      var s = base(), t = todayStr();
      ensureCounters(s, t); ensureTasks(s, t);
      return s;
    },

    // 埋点：learned / quizCorrect / lessons / speaks / minutes
    track: function (metric, n) {
      var s = base(), t = todayStr();
      ensureCounters(s, t); ensureTasks(s, t);
      n = n || 1;
      if (metric === "minutes") s.counters.minutes += n;
      else if (s.counters[metric] != null) s.counters[metric] += n;
      var becameActive = markActive(s, t);
      // 任务进度
      s.tasks.items.forEach(function (it) {
        if (it.claimed) return;
        var v = metric === "minutes" ? s.counters.minutes : s.counters[it.metric];
        it.progress = Math.min(it.goal, v || 0);
      });
      // 连胜里程碑
      var reward = 0, newBadge = "";
      if (becameActive) {
        var ms = milestoneOf(s.streak.cur);
        if (ms && !s.streak.milestones[s.streak.cur]) {
          s.streak.milestones[s.streak.cur] = 1;
          reward = ms;
          newBadge = MILESTONE_BADGE[s.streak.cur] || "";
        }
      }
      if (reward) {
        grantStars(reward);
        _pendingMs.push({ day: s.streak.cur, stars: reward });
      }
      if (newBadge) grantBadge(newBadge);
      save(s);
      return { active: becameActive, milestoneStars: reward, milestoneDay: reward ? s.streak.cur : 0 };
    },

    claim: function (idx) {
      var s = base(), t = todayStr();
      ensureTasks(s, t);
      var it = s.tasks.items[idx];
      if (!it || it.claimed || it.progress < it.goal) return null;
      it.claimed = true;
      grantStars(it.stars);
      save(s);
      return { stars: it.stars, title: it.title };
    },

    week: function () {
      var s = base();
      var out = [];
      for (var i = 6; i >= 0; i--) {
        var d = todayStr(new Date(Date.now() - i * DAY_MS));
        out.push({ date: d, active: !!(s.streak.days && s.streak.days[d]) });
      }
      return out;
    },

    // offline-shim 记账回调：星星入账 / 徽章解锁 → 通知 UI
    onStars: function () { notify(); },
    onBadge: function () { notify(); },

    // 取走待庆祝的连胜里程碑（UI 渲染时调用并弹层）
    takeMilestone: function () { return _pendingMs.shift() || null; }
  };

  window.AL_GAMIFY = API;
})();
