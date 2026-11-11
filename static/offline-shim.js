/*
 * offline-shim.js —— AL 自学系统离线内核（纯离线版）
 *
 * 职责：
 *  1) 课程树(/api/curriculum)与课程详情(/api/lesson)从本地 static/offline/ 读取，
 *     保证"断网可用、内置知识"。
 *  2) 激励/统计接口（星星、成就、今日报告、学习计划）在离线时由本地记账层
 *     (al_ledger_v1) 提供真实数据，响应格式与 server.py 完全对齐 —— 前端零改动。
 *  3) 其余交互接口返回 503 占位（必须是 5xx，api() 才会抛错给出明确提示）。
 *
 * 设计约束（2026-09-10 按用户要求）：
 *  - 不依赖任何云端地址。
 *  - 本文件仅做本地内容拦截与本地记账，不做任何外网转发。
 *
 * 配置（由打包脚本注入，可选）：
 *  window.AL_OFFLINE = true   // 强制离线（APK 离线包用）
 */
(function () {
  "use strict";

  // ⚠ 只有「离线包环境」才启用拦截：
  //   · APK 离线包 —— 由 android-app/prep_apk.py 注入 window.AL_OFFLINE = true
  //   · 用 file:// 直接打开 index.html
  // 网页版（http/https）必须走真实服务器。
  var FORCE_OFFLINE = (window.AL_OFFLINE === true) || (location.protocol === "file:");
  if (!FORCE_OFFLINE) return;
  var docBase = location.pathname.replace(/[^/]*$/, "");
  if (docBase === "" || docBase.charAt(docBase.length - 1) !== "/") docBase = "/";

  var LEDGER_KEY = "al_ledger_v1";

  // ---------- 本地记账层 ----------
  function todayStr() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function loadLedger() {
    try { return JSON.parse(localStorage.getItem(LEDGER_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function saveLedger(lg) {
    try { localStorage.setItem(LEDGER_KEY, JSON.stringify(lg)); } catch (e) {}
  }
  // 每日来源上限（与 server.py _stars_award 对齐）
  var STAR_LIMITS = { chat: 10, selfstudy_learned: 30, selfstudy_mastered: 30 };

  function starsAdd(source, points) {
    points = Math.max(1, Math.min(20, Math.floor(points) || 1));
    var lg = loadLedger();
    if (!lg.stars) lg.stars = { byDate: {}, unlockedBadges: [] };
    var t = todayStr();
    var day = lg.stars.byDate[t] || (lg.stars.byDate[t] = { total: 0, bySource: {} });
    var limit = STAR_LIMITS[source];
    if (limit && (day.bySource[source] || 0) >= limit) {
      saveLedger(lg);
      return { awarded: false, reason: "今日该来源星星已达上限" };
    }
    day.total += points;
    day.bySource[source] = (day.bySource[source] || 0) + points;
    saveLedger(lg);
    try { if (window.AL_GAMIFY && window.AL_GAMIFY.onStars) window.AL_GAMIFY.onStars(points); } catch (e) {}
    return { awarded: true, points: points };
  }
  function starsTotal() {
    var lg = loadLedger();
    var total = 0, today = 0, t = todayStr(), breakdown = {};
    var byDate = (lg.stars && lg.stars.byDate) || {};
    Object.keys(byDate).forEach(function (d) {
      total += byDate[d].total || 0;
      if (d === t) today = byDate[d].total || 0;
      var bs = byDate[d].bySource || {};
      Object.keys(bs).forEach(function (s) { breakdown[s] = (breakdown[s] || 0) + bs[s]; });
    });
    return { total: total, today: today, breakdown: breakdown };
  }

  var BADGES = [
    { id: "first_learn", title: "🎯 初次学习", desc: "发出第一条学习消息", icon: "🎯" },
    { id: "streak_3", title: "🔥 连续3天", desc: "连续学习 3 天", icon: "🔥" },
    { id: "first_mastery", title: "✅ 第一个掌握", desc: "首次掌握一个知识点", icon: "✅" },
    { id: "speech_done", title: "🗣️ 口语达人", desc: "完成一次口语练习", icon: "🗣️" },
    { id: "stars_50", title: "⭐ 积少成多", desc: "累计获得 50 颗星星", icon: "⭐" },
    { id: "master_5", title: "📚 学霸", desc: "掌握 5 个知识点", icon: "📚" },
    { id: "test_10", title: "🎯 测试达人", desc: "完成 10 次课后测试", icon: "🎯" },
    { id: "streak_7", title: "💪 坚持一周", desc: "连续学习 7 天", icon: "💪" },
    { id: "first_selfstudy", title: "📖 自主学习", desc: "首次进入自学页", icon: "📖" },
    { id: "selfstudy_10", title: "🌱 初学乍练", desc: "累计自学 10 个知识点", icon: "🌱" },
    { id: "selfstudy_50", title: "🚀 涉猎广泛", desc: "累计自学 50 个知识点", icon: "🚀" },
    { id: "selfstudy_master_10", title: "🏅 知识达人", desc: "累计掌握 10 个知识点", icon: "🏅" },
    { id: "quiz_perfect", title: "💯 满分小能手", desc: "首次自主测验全对", icon: "💯" }
  ];
  function badgesGet() {
    var lg = loadLedger();
    var unlocked = (lg.stars && lg.stars.unlockedBadges) || [];
    return {
      badges: BADGES.map(function (b) {
        return { id: b.id, title: b.title, desc: b.desc, icon: b.icon, unlocked: unlocked.indexOf(b.id) >= 0 };
      })
    };
  }
  function badgeUnlock(bid) {
    var lg = loadLedger();
    if (!lg.stars) lg.stars = { byDate: {}, unlockedBadges: [] };
    if (!lg.stars.unlockedBadges) lg.stars.unlockedBadges = [];
    if (lg.stars.unlockedBadges.indexOf(bid) >= 0) return { unlocked: false, reason: "已解锁过" };
    lg.stars.unlockedBadges.push(bid);
    saveLedger(lg);
    try { if (window.AL_GAMIFY && window.AL_GAMIFY.onBadge) window.AL_GAMIFY.onBadge(bid); } catch (e) {}
    return { unlocked: true, badge_id: bid };
  }

  // 本地学情：时长来自 al_today_sec_*，掌握来自 al_ss_progress
  function ssProgressMap() {
    try { return JSON.parse(localStorage.getItem("al_ss_progress") || "{}"); }
    catch (e) { return {}; }
  }
  function reportDaily() {
    var d = new Date(); d.setHours(0, 0, 0, 0);
    var secs = parseInt(localStorage.getItem("al_today_sec_" + d.getTime()) || "0", 10);
    var map = ssProgressMap(), mastered = 0, know = 0, total = 0;
    Object.keys(map).forEach(function (k) {
      var st = (map[k] && map[k].status) || 0;
      total += 1;
      if (st >= 2) mastered += 1; else if (st >= 1) know += 1;
    });
    return {
      date: todayStr(),
      seconds: secs, minutes: Math.round(secs / 60 * 10) / 10,
      msg_count: 0, session_count: 0, mistake_count: 0,
      mastery: { mastered: mastered, familiar: 0, know: know, weak: 0, total_tested: total }
    };
  }

  // 本地学习计划：基于 al_ss_progress 生成 3 条（新学/巩固/完成一课）
  function planDaily() {
    var t = todayStr();
    var lg = loadLedger();
    lg.plans = lg.plans || {};
    if (lg.plans[t]) return { date: t, items: lg.plans[t].items, completed: lg.plans[t].completed };
    var map = ssProgressMap();
    var fresh = [], mid = [];
    Object.keys(map).forEach(function (cid) {
      var st = (map[cid] && map[cid].status) || 0;
      if (st === 0) fresh.push(cid); else if (st === 1) mid.push(cid);
    });
    var items = [];
    mid.slice(0, 1).forEach(function (cid) {
      var m = map[cid] || {};
      items.push({ type: "consolidate", title: "巩固：" + (m.title || cid), course_id: cid, mastery_level: 1, priority: 2, icon: "💪" });
    });
    var need = 3 - items.length;
    fresh.slice(0, need).forEach(function (cid) {
      var m = map[cid] || {};
      items.push({ type: "new_learn", title: "学习：" + (m.title || cid), course_id: cid, priority: 3, icon: "📖" });
    });
    if (!items.length) {
      items.push({ type: "new_learn", title: "去自学页挑一课开始吧", priority: 3, icon: "📖" });
    }
    lg.plans[t] = { items: items, completed: [] };
    // 清理 14 天前的旧计划，防膨胀
    try {
      var keys = Object.keys(lg.plans).sort();
      while (keys.length > 14) { delete lg.plans[keys.shift()]; }
    } catch (e) {}
    saveLedger(lg);
    return { date: t, items: items, completed: [], is_new: true };
  }
  function planComplete(idx) {
    var t = todayStr();
    var lg = loadLedger();
    if (!lg.plans || !lg.plans[t]) return { error: "今日计划不存在" };
    var c = lg.plans[t].completed || [];
    if (c.indexOf(idx) < 0) c.push(idx);
    lg.plans[t].completed = c;
    saveLedger(lg);
    return { ok: true, completed: c };
  }

  // ---------- 响应工具 ----------
  function localPathFor(url) {
    var u, p, id;
    try { u = new URL(url, location.href); } catch (e) { return null; }
    p = u.pathname;
    if (p === "/api/curriculum") return docBase + "offline/curriculum.json";
    if (p === "/api/lesson") {
      id = u.searchParams.get("course_id");
      if (id) return docBase + "offline/lessons/" + encodeURIComponent(id) + ".json";
    }
    return null;
  }

  function respFromText(text, status) {
    return new Response(text, {
      status: status || 200,
      headers: { "Content-Type": "application/json; charset=utf-8" }
    });
  }
  function respJson(obj, status) { return respFromText(JSON.stringify(obj), status); }

  function stubOffline() {
    // 必须返回 5xx：api() 只在 res.ok 为 false 时抛错。
    // 曾经返回 200 + {ok:false}，前端把占位当成功拿到"空数据"，
    // 导致 AI 讲解点了没反应、成就页显示 0 星 0 徽章等"静默失效"。
    return Promise.resolve(respFromText(
      JSON.stringify({ offline: true, ok: false, error: "当前为离线版，该功能需要联网的云端服务；课程学习不受影响" }),
      503
    ));
  }


  // ---------- 学习机模式 · AI 学伴（离线规则版） ----------
  // 离线包里没有大模型，但学伴必须还在：开场白 + 规则回复全部本地生成，
  // 保证 APK 断网时首页学伴卡不是空壳、首页不出现 503 报错。
  function companionContext() {
    var plan = null;
    try { plan = planDaily(); } catch (e) {}
    var next = null;
    if (plan && plan.items && plan.items.length) {
      next = { course_id: plan.items[0].course_id, title: plan.items[0].title,
               subject: plan.items[0].subject, grade: plan.items[0].grade };
    }
    var name = '';
    try { name = localStorage.getItem('al_child_name') || ''; } catch (e) {}
    var maxMin = 30;
    try { maxMin = parseInt(localStorage.getItem('al_daily_max') || '30', 10) || 30; } catch (e) {}
    var todaySec = 0;
    try {
      var d = new Date(); d.setHours(0,0,0,0);
      todaySec = parseInt(localStorage.getItem('al_today_sec_' + d.getTime()) || '0', 10) || 0;
    } catch (e) {}
    var mastered = 0;
    try {
      var mp = JSON.parse(localStorage.getItem('al_ss_progress') || '{}');
      mastered = Object.keys(mp).filter(function (k) { return mp[k] && mp[k].status === 2; }).length;
    } catch (e) {}
    var stars = 0;
    try { stars = starsTotal().total || 0; } catch (e) {}
    return {
      child: name || '小朋友',
      today_sec: todaySec,
      daily_max: maxMin,
      streak: 0,
      stars: stars,
      mastered: mastered,
      mistake_todo: 0,
      resume: null,
      pending_course: next,
      offline: true
    };
  }

  function companionOpeningOffline() {
    var ctx = companionContext();
    var child = ctx.child;
    var name = child.length > 2 ? child.slice(-2) : child;
    var actions = [];
    var opening = '';
    if (ctx.pending_course && ctx.pending_course.course_id) {
      opening = name + ' 离线也能学！要不要从《' + (ctx.pending_course.title || '下一课') + '》开始？';
      actions.push({ id: 'learn_new', label: '学这一课', icon: '📖', type: 'route',
                     target: 'learn', course_id: ctx.pending_course.course_id,
                     title: ctx.pending_course.title || '' });
    } else {
      opening = name + ' 离线也能学！去课程目录挑一节课开始吧。';
    }
    actions.push({ id: 'practice2', label: '逐课小测', icon: '✏️', type: 'route', target: 'selfstudy' });
    actions.push({ id: 'chat', label: '看看成就', icon: '🏆', type: 'route', target: 'achievement' });
    return {
      greeting: name + '，你好呀！',
      opening: opening,
      mood: 'guide',
      offline: true,
      actions: actions,
      context: { child: child, today_min: Math.floor(ctx.today_sec / 60),
                 daily_max: ctx.daily_max, streak: 0, stars: ctx.stars,
                 mastered: ctx.mastered, mistake_todo: 0, resume_desc: '' }
    };
  }

  // 离线版「本地知识引擎」：直接从本地包里的讲义/题库取内容，
  // 断网也能讲知识点、出题、判分（和联网时的演示模式同一套逻辑）。
  var _kbCache = {};

  function loadLessonFile(cid) {
    if (!cid) return Promise.resolve(null);
    if (_kbCache[cid]) return Promise.resolve(_kbCache[cid]);
    var url = docBase + 'offline/lessons/' + encodeURIComponent(cid) + '.json';
    return fetch(url, { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (d) { if (d) _kbCache[cid] = d; return d; });
  }

  function _grab(body, tag) {
    var m = new RegExp('【' + tag + '[^】]*】([\\s\\S]*?)(?=【|$)').exec(body || '');
    return m ? m[1].trim() : '';
  }

  function _clip(s, n) {
    s = (s || '').replace(/\s+/g, ' ').trim();
    return s.length > n ? s.slice(0, n).replace(/[，。；、 ]+$/, '') + '…' : s;
  }

  function explainOffline(L, secIdx) {
    if (!L) return null;
    var secs = L.sections || [];
    if (!secs.length) return { title: L.title, text: L.goals || '' };
    var si = Math.max(0, Math.min(secIdx || 0, secs.length - 1));
    var sec = secs[si] || {};
    var body = sec.body || '';
    var parts = ['【' + (sec.heading || L.title) + '】'];
    var one = _grab(body, '一句话懂'), why = _grab(body, '为什么重要'), how = _grab(body, '具体怎么做');
    if (one) parts.push('一句话懂：' + _clip(one, 140));
    if (why) parts.push('为什么重要：' + _clip(why, 160));
    if (how) parts.push('具体怎么做：' + _clip(how, 200));
    if (!(one || why || how)) parts.push(_clip(body, 320));
    if (sec.tip) parts.push('小提示：' + _clip(sec.tip, 100));
    return { title: L.title, heading: sec.heading, section_idx: si, section_total: secs.length,
             has_next: si + 1 < secs.length, text: parts.join('\n') };
  }

  function quizOf(L) {
    return ((L && L.quiz) || []).filter(function (q) { return q && q.stem; });
  }

  function quizPresentOffline(L, idx) {
    var qs = quizOf(L);
    if (!qs.length) return null;
    var i = ((idx || 0) % qs.length + qs.length) % qs.length;
    var q = qs[i];
    var lines = ['第 ' + (i + 1) + ' 题（共 ' + qs.length + ' 题）'];
    if (q.sub) lines.push('考点：' + q.sub);
    lines.push(q.stem);
    (q.options || []).forEach(function (o) { lines.push('  ' + o); });
    if (!(q.options || []).length) lines.push('（直接说出你的答案）');
    return { quiz_index: i, quiz_total: qs.length, stem: q.stem,
             options: q.options || [], kind: (q.options || []).length ? 'choice' : 'open',
             text: lines.join('\n'), title: L.title };
  }

  function quizGradeOffline(L, idx, ua) {
    var qs = quizOf(L);
    if (!qs.length) return null;
    var q = qs[((idx || 0) % qs.length + qs.length) % qs.length];
    var ans = q.answer;
    var correct = false;
    ua = (ua || '').trim();
    if ((q.options || []).length && typeof ans === 'number') {
      var m = /\b([A-Da-d])\b/.exec(ua);
      var num = m ? (m[1].toUpperCase().charCodeAt(0) - 65) : null;
      if (num === null) { var m2 = /(\d+)/.exec(ua); if (m2) num = parseInt(m2[1], 10) - 1; }
      correct = (num === ans);
    } else {
      var a = String(ans == null ? '' : ans).replace(/\s+/g, '');
      var u = ua.replace(/\s+/g, '');
      correct = !!(a && u && (a === u || u.indexOf(a) >= 0 || a.indexOf(u) >= 0));
    }
    var ansText = (typeof ans === 'number' && q.options && q.options[ans]) ? q.options[ans] : String(ans);
    return { correct: correct, answer: ans, explanation: q.explanation || '',
             text: (correct ? '答对啦！\n' : ('再想想～ 正确答案是：' + ansText + '\n')) + '解析：' + (q.explanation || '') };
  }

  function companionChatOfflineAsync(body) {
    var ctx = companionContext();
    var name = ctx.child.length > 2 ? ctx.child.slice(-2) : ctx.child;
    var msg = ((body && body.message) || '').trim();
    var cid = (body && body.course_id) || (ctx.pending_course && ctx.pending_course.course_id) || '';
    var quizState = (body && body.quiz_state) || null;

    function out(reply, emotion, suggest, card) {
      var o = { reply: reply, emotion: emotion || 'neutral', suggest: suggest || [],
                speak: true, offline: true, offline_engine: true, emotion_label: '平和',
                lang: 'zh-CN', context: { child: ctx.child,
                  today_min: Math.floor(ctx.today_sec / 60), daily_max: ctx.daily_max,
                  streak: 0, stars: ctx.stars } };
      if (card) o.card = card;
      return o;
    }

    return loadLessonFile(cid).then(function (L) {
      // ① 判分
      if (quizState && quizState.topic_id && quizState.awaiting && msg.length <= 40) {
        return loadLessonFile(quizState.topic_id).then(function (L2) {
          var g = quizGradeOffline(L2, quizState.quiz_index, msg);
          if (!g) return out('我这儿暂时没有这道题的答案～', 'neutral');
          return out(g.text, g.correct ? 'satisfaction' : 'confusion',
            g.correct ? [{ label: '再练一题', action: 'quiz' }, { label: '学下一节', action: 'learn_new' }]
                      : [{ label: '再想一题', action: 'quiz' }, { label: '讲讲这节', action: 'explain' }],
            { type: 'quiz_result', correct: g.correct, answer: g.answer, explanation: g.explanation });
        });
      }
      // ② 情绪
      if (/累|烦|不想|休息|困|讨厌|太难/.test(msg)) {
        return out(name + ' 先喘口气，累的时候学不进去很正常。休息 2 分钟，回来只做一点点就行。' +
                   (L ? '\n等你回来，我们只学一小段：《' + L.title + '》。' : ''),
          'frustration', [{ label: '休息一下', action: 'rest' },
                          L ? { label: '学一小段', action: 'explain', topic_id: cid } : { label: '去选课', action: 'learn_new' }]);
      }
      // ③ 讲解
      if (/讲|解释|是什么|是啥|说说|介绍|教我|怎么回事|学一下/.test(msg)) {
        var ex = explainOffline(L, (body && body.section_idx) || 0);
        if (ex) {
          var acts = [];
          if (ex.has_next) acts.push({ label: '下一部分', action: 'explain_next', topic_id: cid, section_idx: ex.section_idx + 1 });
          if (quizOf(L).length) acts.push({ label: '考考我', action: 'quiz', topic_id: cid });
          if (acts.length < 2) acts.push({ label: '看整课', action: 'learn_new', course_id: cid });
          return out(ex.text, 'curiosity', acts.slice(0, 3),
            { type: 'lesson', topic_id: cid, title: ex.title, heading: ex.heading,
              section_idx: ex.section_idx, section_total: ex.section_total });
        }
        return out(name + ' 离线版里我暂时没找到这节课。你可以回到「同步学」挑一节，我陪你学。',
          'confusion', [{ label: '去同步学', action: 'learn_new' }]);
      }
      // ④ 出题
      if (/题|练习|做题|练|考我|测验/.test(msg) || (body && body.want_quiz)) {
        var q = quizPresentOffline(L, (body && body.quiz_index) || 0);
        if (q) {
          return out('来，我给你出一道关于《' + q.title + '》的题，先说你的答案，我再讲。\n\n' + q.text,
            'curiosity', [{ label: '换一题', action: 'quiz' },
                          { label: '不会，讲讲', action: 'explain', topic_id: cid }],
            { type: 'quiz', topic_id: cid, quiz_index: q.quiz_index, quiz_total: q.quiz_total,
              stem: q.stem, options: q.options, kind: q.kind });
        }
        return out('这节课还没配题库，我们先读一遍讲义再来考，好不好？', 'curiosity',
          [{ label: '讲讲这节', action: 'explain' }]);
      }
      // ⑤ 学什么
      if (/学什么|学点啥|今天|开始|计划/.test(msg)) {
        if (L) {
          var heads = (L.sections || []).map(function (x) { return x.heading; }).filter(Boolean);
          var b = name + ' 我们今天从《' + L.title + '》开始吧。';
          if (L.goals) b += '\n要掌握：' + L.goals;
          if (heads.length) b += '\n一共 ' + heads.length + ' 个部分：' + heads.slice(0, 8).join('、');
          return out(b, 'curiosity',
            [{ label: '开始学', action: 'explain', topic_id: cid },
             { label: '考考我', action: 'quiz', topic_id: cid }]);
        }
        return out(name + ' 先去「同步学」挑一节课吧。', 'curiosity', [{ label: '去同步学', action: 'learn_new' }]);
      }
      // ⑥ 错题
      if (/错题|复习|温习/.test(msg)) {
        return out('离线版看不到云端错题本。不过你把这一课再测一遍，答对了照样算掌握。',
          'remind', [{ label: '考考我', action: 'quiz', topic_id: cid }]);
      }
      // ⑦ 答对了
      if (/谢谢|明白|懂了|会了/.test(msg)) {
        return out('太棒了！能自己想明白，比听我讲十遍都值。要不要我考考你？',
          'satisfaction', [{ label: '考考我', action: 'quiz', topic_id: cid }]);
      }
      // ⑧ 兜底
      var acts2 = [{ label: '讲一课', action: 'explain', topic_id: cid }];
      if (quizOf(L).length) acts2.push({ label: '考考我', action: 'quiz', topic_id: cid });
      if (acts2.length < 2) acts2.push({ label: '去同步学', action: 'learn_new' });
      return out('我在听呢。你可以说「讲讲这节」「考考我」，或者点下面的按钮。', 'neutral', acts2);
    });
  }

  // ---------- 离线可用的 API 路由（格式对齐 server.py） ----------
  function routeLocalApi(path, method, body) {
    try {
      if (path === "/api/stars" && method === "GET") return respJson(starsTotal());
      if (path === "/api/stars/award" && method === "POST")
        return respJson(starsAdd((body && body.source) || "selfstudy_learned", (body && body.points) || 1));
      if (path === "/api/achievements" && method === "GET") return respJson(badgesGet());
      if (path === "/api/achievements/unlock" && method === "POST")
        return respJson(badgeUnlock((body && body.badge_id) || ""));
      if (path === "/api/report/daily" && method === "GET") return respJson(reportDaily());
      if (path === "/api/plan/daily" && method === "GET") return respJson(planDaily());
      if (path === "/api/plan/daily/complete" && method === "POST")
        return respJson(planComplete(body ? body.index : -1));
      if (path === "/api/ai/companion/opening" && method === "GET") return respJson(companionOpeningOffline());
      if (path === "/api/ai/companion/chat" && method === "POST")
        return companionChatOfflineAsync(body).then(function (o) { return respJson(o); });
      return null; // 未覆盖的接口 → 走离线占位
    } catch (e) {
      return respJson({ error: "离线记账异常: " + (e && e.message) }, 500);
    }
  }

  var realFetch = window.fetch ? window.fetch.bind(window) : null;
  if (!realFetch) return; // 环境无 fetch，放弃拦截

  function readBody(opt) {
    if (!opt || !opt.body) return null;
    try { return JSON.parse(opt.body); } catch (e) { return null; }
  }

  function shimFetch(url, opt) {
    var u, path;
    try { u = new URL(url, location.href); path = u.pathname; }
    catch (e) { return realFetch(url, opt); }

    var isApi = path.indexOf("/api/") === 0;

    // 1) 本地内容优先：课程树 / 课程详情（始终走本地包）
    var lp = localPathFor(url);
    if (lp) {
      return realFetch(lp, { method: "GET", cache: "no-store" })
        .then(function (r) {
          if (r.ok) return r.text().then(respFromText);
          throw new Error("local-miss");
        })
        .catch(function () {
          // 本地缺失：离线版直接报错，不回退任何外网
          return Response.error();
        });
    }

    // 2) 非接口的静态资源：直接放行，交给本地资源服务器读取。
    if (!isApi) return realFetch(url, opt);

    // 3) 激励/统计/计划：本地记账层提供真实数据
    var local = routeLocalApi(path, (opt && opt.method) || "GET", readBody(opt));
    if (local) return Promise.resolve(local);

    // 4) 其余接口：503 离线占位（明确报错，不静默）
    return stubOffline();
  }

  window.fetch = shimFetch;
  window.__AL_OFFLINE_SHIM__ = true;
})();
