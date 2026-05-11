/* ================================================================
   AQ11 Dashboard  ·  script.js  ·  complete clean rewrite
================================================================ */
"use strict";

let redrawTimeout;

function safeRedraw() {
  clearTimeout(redrawTimeout);
  redrawTimeout = setTimeout(() => redrawCanvases(), 50);
}

/* ── Global state ─────────────────────────────────────────────── */
let DATA             = null;
let tableData        = [];
let activeClassFilter= "all";
let sortState        = { col: null, dir: 1 };

/* ══════════════════════════════════════════════════════════════
   BOOT — runs once DOM is ready
══════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  /* 1. Hard-reset theme & color every page load */
  const savedTheme = localStorage.getItem("theme") || "dark";
  const savedColor = localStorage.getItem("color") || "blue";

  document.documentElement.setAttribute("data-theme", savedTheme);
  document.documentElement.setAttribute("data-color", savedColor);
  window.scrollTo(0, 0);

  /* 2. Wire up controls FIRST (no async dependency) */
  initTheme();
  initPalette();
  initSideNav();
  initFooter();
  initParallax();
  initScrollReveal();

  /* 3. Load data then render */
  loadData();
});

/* ══════════════════════════════════════════════════════════════
   DATA
══════════════════════════════════════════════════════════════ */
async function loadData() {
  try {
    const res = await fetch("./data.json");
    DATA = await res.json();
  } catch (_) {
    DATA = getFallbackData();
  }
  renderAll();
}

function renderAll() {
  renderTable();
  renderExperiments(0);
  renderRules();
  renderComparisonTable();
  renderScatter();
  renderConfusion();
  renderRuleSpace();
  renderExpChart();
  animateCounters();
}

/* ══════════════════════════════════════════════════════════════
   THEME  (dark / light)
══════════════════════════════════════════════════════════════ */
function initTheme() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const html = document.documentElement;
    const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";

    html.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);

    // FORCE repaint
  safeRedraw();
  });
}
/* ══════════════════════════════════════════════════════════════
   COLOR PALETTE
══════════════════════════════════════════════════════════════ */
function initPalette() {
  const paletteBtn   = document.getElementById("paletteBtn");
  const palettePanel = document.getElementById("palettePanel");
  if (!paletteBtn || !palettePanel) return;

  /* open / close */
  paletteBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = palettePanel.classList.contains("open");
    palettePanel.classList.toggle("open", !isOpen);
  });

  /* close when clicking outside */
  document.addEventListener("click", () => {
    palettePanel.classList.remove("open");
  });

  /* keep open when clicking inside panel */
  palettePanel.addEventListener("click", (e) => e.stopPropagation());

  /* swatch selection */
  document.querySelectorAll(".swatch").forEach((sw) => {
    sw.addEventListener("click", (e) => {
      e.stopPropagation();
      applyColor(sw.dataset.color);
      palettePanel.classList.remove("open");
    });
  });

  /* apply initial blue */
  const savedColor = localStorage.getItem("color") || "blue";
  applyColor(savedColor);
}

function applyColor(color) {
  const html = document.documentElement;

  html.setAttribute("data-color", color);
  localStorage.setItem("color", color);

  document.querySelectorAll(".swatch").forEach((sw) => {
    sw.classList.toggle("active", sw.dataset.color === color);
  });

  // FIX: okamžitá aktualizácia orbov
  if (typeof window.__orbApplyTheme === "function") {
    window.__orbApplyTheme();
  }

  // FIX: redraw canvas v správnom frame
  safeRedraw();
}

/* ══════════════════════════════════════════════════════════════
   PARALLAX BACKGROUND  (scroll-only, no mouse)
══════════════════════════════════════════════════════════════ */
function initParallax() {
  const SIZES = [680, 460, 560, 340, 300, 220];
  const THEME_X = {
    blue:      [-12, 82, 28, 56, 78, 20],
    green:     [ -8, 86, 43, 63, 80, 32],
    turquoise: [-16, 80, 10, 48, 73,  6],
    orange:    [ -6, 88, 38, 58, 76, 24],
    red:       [-12, 82, 22, 52, 82, 14],
    lava:      [ -4, 90, 33, 60, 74,  8],
    purple:    [-18, 78, 16, 50, 86, 36],
  };

  const orbEls = document.querySelectorAll(".orb");
  const state  = [];
  let   tick   = 0;

  function xList() {
    const c = document.documentElement.getAttribute("data-color") || "blue";
    return THEME_X[c] || THEME_X.blue;
  }

  orbEls.forEach((el, i) => {
    const size = SIZES[i] || 300;
    el.style.cssText += `;left:0;top:0;right:unset;bottom:unset;width:${size}px;height:${size}px;pointer-events:none`;
    state[i] = {
      size,
      y     : window.innerHeight * 0.1 + Math.random() * window.innerHeight * 0.8,
      vy    : 0,
      xBase : xList()[i] ?? (i * 18 - 10),
      phase : Math.random() * Math.PI * 2,
      freqX : 0.18 + Math.random() * 0.14,
      freqY : 0.14 + Math.random() * 0.12,
      ampX  : 35   + Math.random() * 40,
      ampY  : 28   + Math.random() * 34,
    };
  });

  /* called by applyColor() */
  window.__orbApplyTheme = () => {
    const xs = xList();
    state.forEach((s, i) => { if (s) s.xBase = xs[i] ?? s.xBase; });
  };

  /* scroll accumulator */
  let lastSY      = window.scrollY;
  let scrollAccum = 0;
  window.addEventListener("scroll", () => {
    const y = window.scrollY;
    scrollAccum += (y - lastSY) * 0.5;
    lastSY = y;
    if (y > 60) document.getElementById("scrollInd")?.classList.add("hidden");
  }, { passive: true });

  /* RAF loop */
  (function loop() {
    tick++;
    const vp   = window.innerHeight;
    const vw   = window.innerWidth;
    const push = scrollAccum;
    scrollAccum = 0;

    state.forEach((s, i) => {
      s.vy += push * (1.0 + i * 0.08);
      s.vy *= 0.90;
      if (Math.abs(s.vy) < 0.04) s.vy = 0;
      s.y  += s.vy;

      const pad = s.size * 0.35;
      if (s.vy > 0 && s.y > vp + pad)          s.y = -s.size - pad * 0.3;
      else if (s.vy < 0 && s.y + s.size < -pad) s.y =  vp    + pad * 0.3;

      const t  = tick / 60;
      const fs = Math.max(0, 1 - Math.abs(s.vy) / 50);
      const fx = Math.sin(t * s.freqX * Math.PI * 2 + s.phase)       * s.ampX * fs;
      const fy = Math.cos(t * s.freqY * Math.PI * 2 + s.phase + 1.4) * s.ampY * fs;
      const x  = (s.xBase / 100) * vw - s.size / 2;
      orbEls[i].style.transform = `translate(${(x + fx).toFixed(1)}px,${(s.y + fy).toFixed(1)}px)`;
    });

    requestAnimationFrame(loop);
  })();
}

/* ══════════════════════════════════════════════════════════════
   SCROLL REVEAL
══════════════════════════════════════════════════════════════ */
function initScrollReveal() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      el.classList.add("visible");
      el.querySelectorAll(".reveal-card").forEach((c, i) =>
        setTimeout(() => c.classList.add("visible"), 80 + i * 90)
      );
      io.unobserve(el);
    });
  }, { threshold: 0.06, rootMargin: "0px 0px -60px 0px" });

  document.querySelectorAll(".reveal, .reveal-left, .reveal-right, .reveal-scale")
    .forEach((el) => io.observe(el));
}

/* ══════════════════════════════════════════════════════════════
   SIDE NAV  (scroll spy)
══════════════════════════════════════════════════════════════ */
function initSideNav() {
  const secs  = document.querySelectorAll("section[id]");
  const items = document.querySelectorAll(".nav-item");
  window.addEventListener("scroll", () => {
    let cur = "";
    secs.forEach((s) => { if (window.scrollY >= s.offsetTop - 130) cur = s.id; });
    items.forEach((ni) => ni.classList.toggle("active", ni.getAttribute("href") === "#" + cur));
  }, { passive: true });
}

function initFooter() {
  const el = document.getElementById("footerYear");
  if (el) el.textContent = new Date().getFullYear();
}

/* ══════════════════════════════════════════════════════════════
   DATASET TABLE
══════════════════════════════════════════════════════════════ */
function renderTable() {
  tableData = DATA.dataset_sample;
  const countEl = document.getElementById("ds-rows");
  if (countEl) countEl.textContent = tableData.length;
  buildTable();

  document.getElementById("tableSearch")?.addEventListener("input", buildTable);

  document.querySelectorAll(".cf-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".cf-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeClassFilter = btn.dataset.cls;
      buildTable();
    });
  });

  document.querySelectorAll("th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      sortState.dir = sortState.col === col ? sortState.dir * -1 : 1;
      sortState.col = col;
      buildTable();
    });
  });
}

function buildTable() {
  const tbody = document.getElementById("tableBody");
  const query = (document.getElementById("tableSearch")?.value || "").toLowerCase();

  let rows = tableData.filter((r) => {
    const okClass  = activeClassFilter === "all" || String(r.class) === activeClassFilter;
    const okSearch = !query || [r.hair, r.eyes, String(r.class), String(r.x), String(r.y)]
                       .some((v) => v.toLowerCase().includes(query));
    return okClass && okSearch;
  });

  if (sortState.col) {
    rows = [...rows].sort((a, b) => (a[sortState.col] - b[sortState.col]) * sortState.dir);
  }

  tbody.innerHTML = rows.length
    ? rows.map((r) => `
        <tr>
          <td>${r.id}</td>
          <td>${r.x.toFixed(2)}</td>
          <td>${r.y.toFixed(2)}</td>
          <td>${r.hair}</td>
          <td>${r.eyes}</td>
          <td><span class="class-badge class-${r.class}">Trieda ${r.class}</span></td>
        </tr>`).join("")
    : `<tr><td colspan="6" class="loading-row">Žiadne výsledky</td></tr>`;
}

/* ══════════════════════════════════════════════════════════════
   EXPERIMENTS
══════════════════════════════════════════════════════════════ */
function renderExperiments(idx) {
  const exp       = DATA.experiments[idx];
  const container = document.getElementById("expContent");
  if (!exp || !container) return;

  container.innerHTML = `
    <div class="exp-card">
      <h3>${exp.label}</h3>
      <div class="exp-stat"><span class="exp-stat-k">Veľkosť datasetu</span><span class="exp-stat-v">${exp.size} vzoriek</span></div>
      <div class="exp-stat"><span class="exp-stat-k">Trénovacie dáta</span><span class="exp-stat-v">${exp.train} vzoriek</span></div>
      <div class="exp-stat"><span class="exp-stat-k">Testovacie dáta</span><span class="exp-stat-v">${exp.test} vzoriek</span></div>
      <div class="exp-stat"><span class="exp-stat-k">Vygenerované pravidlá</span><span class="exp-stat-v">${exp.rules_generated}</span></div>
      <div class="exp-stat"><span class="exp-stat-k">Čas trénovania</span><span class="exp-stat-v">${exp.training_time_ms} ms</span></div>
      <p class="exp-desc">${exp.description}</p>
    </div>
    <div class="exp-bar">
      <h3>Metriky výkonu</h3>
      ${mkBar("Accuracy",  exp.accuracy)}
      ${mkBar("Precision", exp.precision)}
      ${mkBar("Recall",    exp.recall)}
      ${mkBar("F1 Score",  exp.f1)}
    </div>`;

  requestAnimationFrame(() => {
    container.querySelectorAll(".exp-bar-fill").forEach((b) => {
      b.style.width = (parseFloat(b.dataset.target) * 100).toFixed(1) + "%";
    });
  });
}

function mkBar(label, val) {
  return `<div class="exp-metric">
    <span class="exp-metric-k">${label}</span>
    <div class="exp-bar-wrap"><div class="exp-bar-fill" data-target="${val}" style="width:0%"></div></div>
    <span class="exp-metric-v">${(val * 100).toFixed(1)}%</span>
  </div>`;
}

document.addEventListener("click", (e) => {
  const tab = e.target.closest(".exp-tab");
  if (!tab) return;
  document.querySelectorAll(".exp-tab").forEach((t) => t.classList.remove("active"));
  tab.classList.add("active");
  renderExperiments(parseInt(tab.dataset.exp));
});

/* ══════════════════════════════════════════════════════════════
   RULES
══════════════════════════════════════════════════════════════ */
function renderRules() {
  const container = document.getElementById("rulesContainer");
  if (!container) return;
  container.innerHTML = DATA.rules.map((r, i) => `
    <div class="rule-card">
      <span class="rule-num">#${String(i + 1).padStart(2, "0")}</span>
      <div class="rule-body">
        <div class="rule-text">
          <span class="rule-kw">IF</span>
          <span class="rule-cond"> ${r.condition} </span>
          <span class="rule-kw">THEN</span>
          <span class="rule-then"> ${r.conclusion}</span>
        </div>
        <div class="rule-meta">
          <span class="rule-badge">Support: ${(r.support * 100).toFixed(1)}%</span>
          <span class="rule-badge">Confidence: ${(r.confidence * 100).toFixed(1)}%</span>
          <span class="rule-badge">Coverage: ${r.coverage} vzoriek</span>
        </div>
      </div>
    </div>`).join("");
}

/* ══════════════════════════════════════════════════════════════
   COMPARISON TABLE
══════════════════════════════════════════════════════════════ */
function renderComparisonTable() {
  const tbody = document.getElementById("compTableBody");
  if (!tbody) return;
  const c = DATA.comparison;
  const rows = [
    ["Presnosť (Accuracy)",  fmtPct(c[0].accuracy),        fmtPct(c[1].accuracy),        fmtPct(c[2].accuracy)],
    ["Interpretovateľnosť",  lvl(c[0].interpretability),   lvl(c[1].interpretability),   lvl(c[2].interpretability)],
    ["Rýchlosť trénovania",  lvl(c[0].training_speed),     lvl(c[1].training_speed),     lvl(c[2].training_speed)],
    ["Škálovateľnosť",       lvl(c[0].scalability),        lvl(c[1].scalability),        lvl(c[2].scalability)],
    ["IF–THEN pravidlá",     boolBadge(c[0].rule_based),   boolBadge(c[1].rule_based),   boolBadge(c[2].rule_based)],
    ["Robustnosť na šum",    lvl(c[0].noise_robustness),   lvl(c[1].noise_robustness),   lvl(c[2].noise_robustness)],
  ];
  tbody.innerHTML = rows.map((r) =>
    `<tr>${r.map((cell) => `<td>${cell}</td>`).join("")}</tr>`
  ).join("");
}

function fmtPct(v)    { return `<span class="badge-high">${(v * 100).toFixed(1)} %</span>`; }
function boolBadge(v) { return v ? '<span class="badge-yes">Áno</span>' : '<span class="badge-no">Nie</span>'; }
function lvl(v) {
  if (v === "Vysoká" || v === "Rýchly")  return `<span class="badge-high">${v}</span>`;
  if (v === "Stredná" || v === "Pomalý") return `<span class="badge-med">${v}</span>`;
  return `<span class="badge-low">${v}</span>`;
}

/* ══════════════════════════════════════════════════════════════
   SCATTER PLOT  +  TOOLTIP
══════════════════════════════════════════════════════════════ */
function renderScatter() {
  const canvas = document.getElementById("scatterCanvas");
  if (!canvas || !DATA?.scatter_points) return;

  const ctx    = canvas.getContext("2d");
  const pts    = DATA.scatter_points;
  const accent = getAccentColor();
  const dark   = isDarkTheme();
  const textC  = dark ? "#c8d6f0" : "#283b5a";
  const gridC  = dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";
  const rgb    = hexToRgb(accent);

  const W = canvas.width, H = canvas.height;
  const PAD = { left:44, right:20, top:20, bottom:44 };
  const pW  = W - PAD.left - PAD.right;
  const pH  = H - PAD.top  - PAD.bottom;
  const toX = (v) => PAD.left + (v / 10) * pW;
  const toY = (v) => PAD.top  + (1 - v / 10) * pH;

  ctx.clearRect(0, 0, W, H);

  // GRID
  ctx.strokeStyle = gridC;
  ctx.lineWidth = 1;

  for (let i = 0; i <= 10; i++) {
    ctx.beginPath();
    ctx.moveTo(toX(i), PAD.top);
    ctx.lineTo(toX(i), PAD.top + pH);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(PAD.left, toY(i));
    ctx.lineTo(PAD.left + pW, toY(i));
    ctx.stroke();
  }

  // DECISION BOUNDARY
  ctx.strokeStyle = dark ? "rgba(255,255,255,.18)" : "rgba(0,0,0,.14)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([6, 4]);

  ctx.beginPath();
  ctx.moveTo(toX(4.5), PAD.top);
  ctx.lineTo(toX(4.5), PAD.top + pH);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(PAD.left, toY(4.5));
  ctx.lineTo(PAD.left + pW, toY(4.5));
  ctx.stroke();

  ctx.setLineDash([]);

  // CLASS AREA
  ctx.fillStyle = `rgba(${rgb},.05)`;
  ctx.fillRect(toX(4.5), PAD.top, pW - (toX(4.5) - PAD.left), toY(4.5) - PAD.top);

  // POINTS
  pts.forEach((p) => {
    ctx.beginPath();
    ctx.arc(toX(p.x), toY(p.y), 7, 0, Math.PI * 2);

    if (p.class === 1) {
      ctx.fillStyle   = `rgba(${rgb},.78)`;
      ctx.strokeStyle = accent;
      ctx.shadowColor = accent;
      ctx.shadowBlur  = 6;
    } else {
      ctx.fillStyle   = "rgba(239,68,68,.72)";
      ctx.strokeStyle = "#ef4444";
      ctx.shadowColor = "#ef4444";
      ctx.shadowBlur  = 5;
    }

    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0;
  });

  // AXIS LABELS
  ctx.fillStyle = textC;
  ctx.font = "11px Space Mono, monospace";

  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (let i = 0; i <= 10; i += 2) {
    ctx.fillText(i, toX(i), H - 14);
  }

  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let i = 0; i <= 10; i += 2) {
    ctx.fillText(i, PAD.left - 8, toY(i));
  }

  ctx.fillStyle = accent;
  ctx.font = "bold 11px Space Mono, monospace";

  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText("x →", W / 2, H - 3);

  ctx.save();
  ctx.translate(10, H / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textBaseline = "middle";
  ctx.fillText("y →", 0, 0);
  ctx.restore();

  // TOOLTIP
  const tooltip = document.getElementById("scatterTooltip");

  canvas.onmousemove = (e) => {
    const rect = canvas.getBoundingClientRect();

    const scaleX = W / rect.width;
    const scaleY = H / rect.height;

    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top)  * scaleY;

    let found = null;
    let minDist = Infinity;

    pts.forEach((p) => {
      const px = toX(p.x);
      const py = toY(p.y);
      const dist = Math.hypot(mx - px, my - py);

      if (dist < 12 && dist < minDist) {
        minDist = dist;
        found = p;
      }
    });

    if (found) {
      tooltip.innerHTML = `
        <div class="tt-row"><span class="tt-key">x</span><span class="tt-val">${found.x.toFixed(2)}</span></div>
        <div class="tt-row"><span class="tt-key">y</span><span class="tt-val">${found.y.toFixed(2)}</span></div>
        <div class="tt-row"><span class="tt-key">vlasy</span><span class="tt-val">${found.hair}</span></div>
        <div class="tt-row"><span class="tt-key">oči</span><span class="tt-val">${found.eyes}</span></div>
        <div class="tt-row"><span class="tt-key">trieda</span>
          <span class="${found.class === 1 ? "tt-c1" : "tt-c0"}">${found.class}</span>
        </div>
      `;

      tooltip.classList.add("show");

      const tx = Math.min(window.innerWidth - 180, e.clientX + 24);
      const ty = Math.max(10, e.clientY - 18);

      tooltip.style.transform = `translate(${tx}px, ${ty}px)`;

      canvas.style.cursor = "crosshair";
    } else {
      tooltip.classList.remove("show");
      canvas.style.cursor = "default";
    }
  };

  canvas.onmouseleave = () => {
    tooltip.classList.remove("show");
    canvas.style.cursor = "default";
  };
}

/* ══════════════════════════════════════════════════════════════
   CONFUSION MATRIX
══════════════════════════════════════════════════════════════ */
function renderConfusion() {
  const canvas = document.getElementById("confusionCanvas");
  if (!canvas || !DATA?.confusion_matrix) return;
  const ctx    = canvas.getContext("2d");
  const cm     = DATA.confusion_matrix.size_1000;
  const accent = getAccentColor();
  const dark   = isDarkTheme();
  const textC  = dark ? "#f2f6ff" : "#06101e";
  const dimC   = dark ? "#c8d6f0" : "#283b5a";
  const rgb    = hexToRgb(accent);

  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const PAD = 80, cW = (W - PAD * 2) / 2, cH = (H - PAD * 2) / 2;
  const maxV = Math.max(...cm.flat());

  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 2; c++) {
      const v = cm[r][c], x = PAD + c * cW, y = PAD + r * cH;
      const ins = v / maxV;
      ctx.fillStyle = r === c
        ? `rgba(${rgb},${ins * .65 + .08})`
        : `rgba(239,68,68,${ins * .45 + .04})`;
      roundRect(ctx, x + 4, y + 4, cW - 8, cH - 8, 12); ctx.fill();

      ctx.fillStyle = textC;
      ctx.font = `bold ${Math.min(cW, cH) * .28}px Space Mono,monospace`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(v, x + cW / 2, y + cH / 2 - 10);
      ctx.font = "11px Space Mono,monospace"; ctx.fillStyle = dimC;
      ctx.fillText(r === c ? (r === 0 ? "TN" : "TP") : (r === 0 ? "FP" : "FN"),
                   x + cW / 2, y + cH / 2 + 16);
    }
  }
  ["Trieda 0", "Trieda 1"].forEach((lb, i) => {
    ctx.fillStyle = dimC; ctx.font = "12px Syne,sans-serif";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(lb, PAD + i * cW + cW / 2, PAD - 22);
    ctx.fillText(lb, PAD - 38, PAD + i * cH + cH / 2);
  });
  ctx.fillStyle = accent; ctx.font = "bold 11px Space Mono,monospace";
  ctx.textAlign = "center"; ctx.fillText("PREDIKOVANÉ", W / 2, 14);
  ctx.save(); ctx.translate(12, H / 2); ctx.rotate(-Math.PI / 2);
  ctx.fillText("SKUTOČNÉ", 0, 0); ctx.restore();
}

/* ══════════════════════════════════════════════════════════════
   RULE SPACE
══════════════════════════════════════════════════════════════ */
function renderRuleSpace() {
  const canvas = document.getElementById("ruleSpaceCanvas");
  if (!canvas) return;
  const ctx    = canvas.getContext("2d");
  const accent = getAccentColor();
  const dark   = isDarkTheme();
  const dimC   = dark ? "#c8d6f0" : "#283b5a";
  const rgb    = hexToRgb(accent);

  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const PAD = { left:52, right:20, top:22, bottom:50 };
  const pW  = W - PAD.left - PAD.right;
  const pH  = H - PAD.top  - PAD.bottom;
  const toX = (v) => PAD.left + (v / 10) * pW;
  const toY = (v) => PAD.top  + (1 - v / 10) * pH;

  ctx.fillStyle = "rgba(239,68,68,.04)"; ctx.fillRect(PAD.left, PAD.top, pW, pH);
  ctx.fillStyle = `rgba(${rgb},.07)`;
  ctx.fillRect(toX(4.5), PAD.top, pW - (toX(4.5) - PAD.left), toY(4.5) - PAD.top);

  const rules = [
    {x0:5.2,x1:10,y0:0,  y1:10, l:"R1",cls:1},
    {x0:0,  x1:10,y0:0,  y1:3.1,l:"R2",cls:0},
    {x0:6,  x1:10,y0:4.5,y1:10, l:"R3",cls:1},
    {x0:3.5,x1:5.2,y0:5, y1:10, l:"R5",cls:1},
    {x0:0,  x1:4, y0:0,  y1:10, l:"R4",cls:0},
    {x0:0,  x1:3, y0:0,  y1:2,  l:"R7",cls:0},
  ];
  rules.forEach((rule) => {
    const rx = toX(rule.x0), ry = toY(rule.y1);
    const rw = toX(rule.x1) - rx, rh = toY(rule.y0) - ry;
    const sc = rule.cls === 1 ? accent : "#ef4444";
    ctx.fillStyle = rule.cls === 1 ? `rgba(${rgb},.12)` : "rgba(239,68,68,.10)";
    ctx.strokeStyle = sc; ctx.lineWidth = 1.5; ctx.setLineDash([5, 3]);
    roundRect(ctx, rx, ry, rw, rh, 4); ctx.fill(); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = sc; ctx.font = "bold 11px Space Mono,monospace";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(rule.l, rx + rw / 2, ry + 12);
  });

  ctx.strokeStyle = dark ? "rgba(255,255,255,.22)" : "rgba(0,0,0,.18)";
  ctx.lineWidth = 2; ctx.setLineDash([8, 4]);
  ctx.beginPath(); ctx.moveTo(toX(4.5), PAD.top); ctx.lineTo(toX(4.5), PAD.top + pH); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(PAD.left, toY(4.5)); ctx.lineTo(PAD.left + pW, toY(4.5)); ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = dark ? "rgba(255,255,255,.04)" : "rgba(0,0,0,.04)"; ctx.lineWidth = 1;
  for (let i = 0; i <= 10; i++) {
    ctx.beginPath(); ctx.moveTo(toX(i), PAD.top); ctx.lineTo(toX(i), PAD.top + pH); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(PAD.left, toY(i)); ctx.lineTo(PAD.left + pW, toY(i)); ctx.stroke();
  }

  ctx.fillStyle = dimC; ctx.font = "11px Space Mono,monospace";
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  for (let i = 0; i <= 10; i += 2) ctx.fillText(i, toX(i), H - 16);
  ctx.textAlign = "right"; ctx.textBaseline = "middle";
  for (let i = 0; i <= 10; i += 2) ctx.fillText(i, PAD.left - 8, toY(i));
  ctx.fillStyle = accent; ctx.font = "bold 11px Space Mono,monospace";
  ctx.textAlign = "center"; ctx.textBaseline = "top"; ctx.fillText("x →", W / 2, H - 4);
  ctx.save(); ctx.translate(10, H / 2); ctx.rotate(-Math.PI / 2);
  ctx.textBaseline = "middle"; ctx.fillText("y →", 0, 0); ctx.restore();
}

/* ══════════════════════════════════════════════════════════════
   EXPERIMENTS BAR CHART
══════════════════════════════════════════════════════════════ */
function renderExpChart() {
  const canvas = document.getElementById("expChart");
  if (!canvas || !DATA?.experiments) return;
  const ctx    = canvas.getContext("2d");
  const accent = getAccentColor();
  const dark   = isDarkTheme();
  const textC  = dark ? "#c8d6f0" : "#283b5a";
  const gridC  = dark ? "rgba(255,255,255,.05)" : "rgba(0,0,0,.05)";
  const rgb    = hexToRgb(accent);

  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const exps    = DATA.experiments;
  const metrics = ["accuracy","precision","recall","f1"];
  const mLabels = ["Accuracy","Precision","Recall","F1"];
  const PAD     = { left:58, bottom:50, top:24 };
  const pH      = H - PAD.bottom - PAD.top;
  const groupW  = (W - PAD.left) / exps.length;
  const barW    = (groupW - 24) / metrics.length;
  const minV    = 0.6;

  [0.6,0.7,0.8,0.9,1.0].forEach((v) => {
    const y = PAD.top + pH * (1 - (v - minV) / (1 - minV));
    ctx.strokeStyle = gridC; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(W, y); ctx.stroke();
    ctx.fillStyle = textC; ctx.font = "10px Space Mono,monospace";
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    ctx.fillText((v * 100).toFixed(0) + "%", PAD.left - 8, y);
  });

  exps.forEach((exp, gi) => {
    const gx = PAD.left + gi * groupW + 12;
    metrics.forEach((m, mi) => {
      const val   = exp[m];
      const bH    = ((val - minV) / (1 - minV)) * pH;
      const x     = gx + mi * barW;
      const y     = PAD.top + pH - bH;
      const alpha = 0.38 + (mi / (metrics.length - 1)) * 0.55;
      ctx.fillStyle   = `rgba(${rgb},${alpha})`;
      ctx.strokeStyle = `rgba(${rgb},.7)`;
      ctx.lineWidth = 1;
      roundRect(ctx, x, y, barW - 2, bH, 3); ctx.fill(); ctx.stroke();
      ctx.fillStyle = dark ? "#f2f6ff" : "#06101e";
      ctx.font = "bold 9px Space Mono,monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "bottom";
      ctx.fillText((val * 100).toFixed(1), x + (barW - 2) / 2, y - 2);
    });
    ctx.fillStyle = textC; ctx.font = "11px Syne,sans-serif";
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    ctx.fillText(exp.label, PAD.left + gi * groupW + groupW / 2, H - PAD.bottom + 8);
  });

  mLabels.forEach((lb, i) => {
    const lx    = PAD.left + i * 100;
    const alpha = 0.38 + (i / (metrics.length - 1)) * 0.55;
    ctx.fillStyle = `rgba(${rgb},${alpha})`;
    ctx.fillRect(lx, PAD.top - 14, 12, 12);
    ctx.fillStyle = textC; ctx.font = "10px Space Mono,monospace";
    ctx.textAlign = "left"; ctx.textBaseline = "top";
    ctx.fillText(lb, lx + 16, PAD.top - 14);
  });
}

/* ══════════════════════════════════════════════════════════════
   COUNTER ANIMATIONS
══════════════════════════════════════════════════════════════ */
function animateCounters() {
  document.querySelectorAll(".hs-val, .rv").forEach((el) => {
    const target  = parseFloat(el.dataset.target);
    const isFloat = target % 1 !== 0;
    const dur     = 1600;
    const t0      = performance.now();
    const step = (now) => {
      const p = Math.min((now - t0) / dur, 1);
      const e = 1 - Math.pow(1 - p, 3);
      el.textContent = isFloat ? (target * e).toFixed(1) : Math.round(target * e);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
}

/* ══════════════════════════════════════════════════════════════
   REDRAW  (called after theme / color change)
══════════════════════════════════════════════════════════════ */
function redrawCanvases() {
  if (!DATA) return;
  renderScatter();
  renderConfusion();
  renderRuleSpace();
  renderExpChart();
}

/* ══════════════════════════════════════════════════════════════
   UTILITIES
══════════════════════════════════════════════════════════════ */
function getAccentColor() {
  return getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
}
function isDarkTheme() {
  return document.documentElement.getAttribute("data-theme") === "dark";
}
function hexToRgb(hex) {
  hex = hex.replace("#", "");
  if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
  return [parseInt(hex.slice(0,2),16), parseInt(hex.slice(2,4),16), parseInt(hex.slice(4,6),16)].join(",");
}
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}

/* ══════════════════════════════════════════════════════════════
   FALLBACK DATA  (if data.json fails to load)
══════════════════════════════════════════════════════════════ */
function getFallbackData() {
  return {
    experiments: [
      {id:1,label:"Malý dataset",   size:100, train:70, test:30, accuracy:.867,precision:.854,recall:.881,f1:.867,rules_generated:6, training_time_ms:12, description:"Malý dataset so 100 vzorkami."},
      {id:2,label:"Stredný dataset",size:500, train:350,test:150,accuracy:.913,precision:.907,recall:.921,f1:.914,rules_generated:11,training_time_ms:48, description:"Stredný dataset s 500 vzorkami."},
      {id:3,label:"Veľký dataset",  size:1000,train:700,test:300,accuracy:.943,precision:.939,recall:.948,f1:.943,rules_generated:17,training_time_ms:187,description:"Veľký dataset s 1 000 vzorkami."},
      {id:4,label:"So šumom",       size:1000,train:700,test:300,accuracy:.882,precision:.871,recall:.895,f1:.883,rules_generated:23,training_time_ms:210,description:"Dataset s pridaným šumom (10 %)."},
    ],
    confusion_matrix:{size_1000:[[278,18],[14,290]]},
    rules:[
      {id:1,condition:"x > 5.2 AND hair = tmavé",                   conclusion:"trieda = 1",support:.312,confidence:.941,coverage:156},
      {id:2,condition:"y < 3.1 AND eyes = modré",                    conclusion:"trieda = 0",support:.287,confidence:.923,coverage:143},
      {id:3,condition:"x > 6.0 AND y > 4.5",                        conclusion:"trieda = 1",support:.198,confidence:.967,coverage:99 },
      {id:4,condition:"hair = svetlé AND eyes = zelené AND x < 4.0", conclusion:"trieda = 0",support:.156,confidence:.912,coverage:78 },
      {id:5,condition:"x BETWEEN 3.5 AND 5.2 AND y > 5.0",          conclusion:"trieda = 1",support:.134,confidence:.886,coverage:67 },
      {id:6,condition:"eyes = hnedé AND hair = ryšavé",              conclusion:"trieda = 0",support:.089,confidence:.902,coverage:44 },
      {id:7,condition:"y < 2.0 AND x < 3.0",                        conclusion:"trieda = 0",support:.072,confidence:.971,coverage:36 },
      {id:8,condition:"hair = tmavé AND eyes = hnedé AND x > 4.5",   conclusion:"trieda = 1",support:.064,confidence:.923,coverage:32 },
    ],
    comparison:[
      {algorithm:"AQ11",               accuracy:.943,interpretability:"Vysoká",training_speed:"Rýchly",scalability:"Stredná",rule_based:true, noise_robustness:"Stredná"},
      {algorithm:"Decision Tree (C4.5)",accuracy:.931,interpretability:"Vysoká",training_speed:"Rýchly",scalability:"Vysoká", rule_based:true, noise_robustness:"Stredná"},
      {algorithm:"Neurónová sieť (MLP)",accuracy:.971,interpretability:"Nízka", training_speed:"Pomalý",scalability:"Vysoká", rule_based:false,noise_robustness:"Vysoká"},
    ],
    scatter_points:[
      {x:1.2,y:1.5,hair:"svetlé",eyes:"modré", class:0},{x:1.5,y:2.1,hair:"tmavé", eyes:"hnedé", class:0},
      {x:2.0,y:1.8,hair:"svetlé",eyes:"zelené",class:0},{x:2.3,y:2.5,hair:"ryšavé",eyes:"hnedé", class:0},
      {x:1.8,y:3.0,hair:"svetlé",eyes:"modré", class:0},{x:2.5,y:1.2,hair:"tmavé", eyes:"zelené",class:0},
      {x:3.0,y:2.0,hair:"ryšavé",eyes:"modré", class:0},{x:1.0,y:1.0,hair:"svetlé",eyes:"hnedé", class:0},
      {x:3.5,y:3.5,hair:"tmavé", eyes:"modré", class:0},{x:2.8,y:2.8,hair:"svetlé",eyes:"zelené",class:0},
      {x:4.0,y:4.2,hair:"tmavé", eyes:"hnedé", class:0},{x:3.2,y:3.8,hair:"ryšavé",eyes:"zelené",class:0},
      {x:4.5,y:3.0,hair:"svetlé",eyes:"modré", class:1},{x:5.0,y:4.5,hair:"tmavé", eyes:"hnedé", class:1},
      {x:5.5,y:5.0,hair:"tmavé", eyes:"zelené",class:1},{x:6.0,y:5.5,hair:"tmavé", eyes:"modré", class:1},
      {x:6.5,y:6.0,hair:"ryšavé",eyes:"hnedé", class:1},{x:7.0,y:6.5,hair:"tmavé", eyes:"zelené",class:1},
      {x:7.5,y:7.0,hair:"tmavé", eyes:"modré", class:1},{x:5.2,y:5.8,hair:"svetlé",eyes:"zelené",class:1},
      {x:6.2,y:4.8,hair:"tmavé", eyes:"hnedé", class:1},{x:5.8,y:6.2,hair:"ryšavé",eyes:"modré", class:1},
      {x:7.2,y:5.5,hair:"tmavé", eyes:"zelené",class:1},{x:4.8,y:5.2,hair:"tmavé", eyes:"hnedé", class:1},
      {x:3.8,y:4.0,hair:"svetlé",eyes:"modré", class:0},{x:4.2,y:3.5,hair:"ryšavé",eyes:"zelené",class:0},
      {x:8.0,y:7.5,hair:"tmavé", eyes:"hnedé", class:1},{x:8.5,y:8.0,hair:"tmavé", eyes:"modré", class:1},
      {x:0.8,y:0.5,hair:"svetlé",eyes:"zelené",class:0},{x:1.3,y:0.9,hair:"ryšavé",eyes:"hnedé", class:0},
    ],
    dataset_sample:[
      {id:1,x:1.23,y:2.45,hair:"svetlé",eyes:"modré", class:0},{id:2,x:5.67,y:6.12,hair:"tmavé", eyes:"hnedé", class:1},
      {id:3,x:3.45,y:1.23,hair:"ryšavé",eyes:"zelené",class:0},{id:4,x:7.89,y:7.34,hair:"tmavé", eyes:"modré", class:1},
      {id:5,x:2.11,y:3.56,hair:"svetlé",eyes:"zelené",class:0},{id:6,x:6.78,y:5.90,hair:"tmavé", eyes:"hnedé", class:1},
    ],
  };
}

window.redrawCanvases = redrawCanvases;