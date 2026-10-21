// Injecté dans chaque page : curseur Windows, repère du scénario (haut gauche),
// annotations façon « ajoutées par-dessus » et cartons simples. Exposé via window.__demo.
(() => {
  if (window.__demo) return;
  const CSS = (window.__demoFontCSS || '') + `
  *{scroll-margin-top:110px}
  #demo-cursor{position:fixed;left:0;top:0;width:13px;height:20px;z-index:2147483647;pointer-events:none}
  #demo-box{position:fixed;z-index:2147483640;pointer-events:none;border:3px solid #f97316;border-radius:14px;
    transition:opacity .45s ease;opacity:0}
  #demo-note{position:fixed;z-index:2147483645;max-width:470px;padding:20px 24px 18px 26px;border-radius:16px;
    background:#1e3a8a;color:#fff;font-family:'Poppins','Segoe UI',sans-serif;border:none;
    border-left:6px solid #f97316;box-shadow:0 14px 36px rgba(15,23,42,.35);
    opacity:0;transform:translateY(8px);transition:opacity .3s,transform .3s;pointer-events:none}
  #demo-note.show{opacity:1;transform:none}
  #demo-note h3{margin:0;font-size:25px;line-height:1.3;font-weight:700}
  #demo-note ul{margin:12px 0 0;padding:0;list-style:none}
  #demo-note li{position:relative;padding-left:20px;margin:7px 0;font-size:19px;line-height:1.4;font-weight:500;color:#dbeafe}
  #demo-note li:before{content:'';position:absolute;left:2px;top:11px;width:8px;height:8px;border-radius:50%;background:#f97316}
  #demo-tag{position:fixed;left:18px;top:96px;z-index:2147483644;width:auto;padding:12px 16px;border-radius:12px;
    background:#1e3a8a;border:none;box-shadow:0 8px 24px rgba(15,23,42,.3);font-family:'Poppins','Segoe UI',sans-serif;
    pointer-events:none;display:none}
  #demo-tag.show{display:block}
  #demo-tag .row{display:flex;white-space:nowrap;gap:9px;align-items:center;font-size:14px;font-weight:600;color:#93a8d6;margin:5px 0}
  #demo-tag .row i{font-style:normal;display:grid;place-items:center;width:22px;height:22px;border-radius:50%;
    border:2px solid #5b74b8;font-size:12px;font-weight:800}
  #demo-tag .row.on{color:#fff}
  #demo-tag .row.on i{background:#f97316;border-color:#f97316;color:#fff}
  #demo-tag .row.done i{background:#fff;border-color:#fff;color:#1e3a8a}
  #demo-card{position:fixed;inset:0;z-index:2147483646;display:flex;flex-direction:column;align-items:center;justify-content:center;
    gap:34px;text-align:center;color:#111827;font-family:'Poppins','Segoe UI',sans-serif;background:#f8fafc;
    opacity:0;transition:opacity .5s}
  #demo-card.show{opacity:1}
  #demo-card img{height:130px}
  #demo-card .parts{display:flex;flex-direction:column;gap:18px;align-items:flex-start}
  #demo-card .parts div{display:flex;gap:18px;align-items:center;font-size:40px;font-weight:700}
  #demo-card .parts b,#demo-card .num{display:grid;place-items:center;width:58px;height:58px;border-radius:50%;
    background:#f97316;color:#fff;font-size:30px;font-weight:800}
  #demo-card .num{width:76px;height:76px;font-size:40px}
  #demo-card h1{font-family:'Poppins','Segoe UI',sans-serif !important;margin:0;font-size:58px;font-weight:800}
  `;
  // Flèche Windows standard (blanche, contour noir)
  const CURSOR = `<svg viewBox="0 0 12 19" width="13" height="20"><path d="M.5.5v15.6l3.7-3.6 2.4 5.6 2.2-.9-2.3-5.5h5.1z" fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round"/></svg>`;
  const el = (id) => { let n = document.getElementById(id); if (!n) { n = document.createElement("div"); n.id = id; document.documentElement.appendChild(n); } return n; };
  const PARTS = ["Import planning IA", "Passager", "Conducteur"];
  // État conservé d'une page à l'autre (window.name survit aux rechargements).
  const state = () => { try { return JSON.parse(window.name.startsWith("{") ? window.name : "{}"); } catch { return {}; } };
  const save = (patch) => { window.name = JSON.stringify({ ...state(), ...patch }); };
  // Idempotent : recrée style, curseur et repère s'ils manquent (le chargement
  // de la page peut les retirer). Appelé tout de suite, au DOMContentLoaded et en boucle.
  function boot() {
    if (!document.getElementById("demo-style")) {
      const s = document.createElement("style"); s.id = "demo-style"; s.textContent = CSS; (document.head || document.documentElement).appendChild(s);
      if (document.fonts) ["500", "600", "700", "800"].forEach((w) => document.fonts.load(`${w} 16px Poppins`));
    }
    if (!document.getElementById("demo-cursor")) {
      const c = el("demo-cursor"); c.innerHTML = CURSOR;
      const p = window.__demoPos || { x: -50, y: -50 }; c.style.left = p.x + "px"; c.style.top = p.y + "px";
    }
    const cover = state().cover;
    if (cover && !document.getElementById("demo-card")) {
      const c = el("demo-card"); c.style.transition = "none"; c.innerHTML = cover; c.classList.add("show");
      const k = document.getElementById("demo-cursor"); if (k) k.style.visibility = "hidden";
    }
    if (!document.getElementById("demo-tag")) {
      const part = state().part || 0;
      if (part) window.__demo.tag(part);
    }
  }
  document.addEventListener("mousemove", (e) => {
    window.__demoPos = { x: e.clientX, y: e.clientY };
    const c = document.getElementById("demo-cursor"); if (c) { c.style.left = e.clientX + "px"; c.style.top = e.clientY + "px"; }
  }, true);

  const esc = (t) => String(t).replace(/[&<>]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]));
  window.__demo = {
    tag(part) {
      save({ part });
      const t = el("demo-tag");
      t.innerHTML = PARTS.map((p, i) => `<div class="row ${i + 1 === part ? "on" : i + 1 < part ? "done" : ""}"><i>${i + 1}</i>${esc(p)}</div>`).join("");
      t.classList.toggle("show", part > 0);
    },
    box(rect) {
      const b = el("demo-box");
      if (!rect) { b.style.opacity = 0; return; }
      const pad = 8;
      b.style.opacity = 0;
      Object.assign(b.style, { left: rect.x - pad + "px", top: rect.y - pad + "px", width: rect.width + pad * 2 + "px", height: rect.height + pad * 2 + "px" });
      requestAnimationFrame(() => requestAnimationFrame(() => (b.style.opacity = 1)));
    },
    note({ title, bullets = [], rect }) {
      boot(); const n = el("demo-note");
      n.innerHTML = `<h3>${esc(title)}</h3><ul>${bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>`;
      const W = window.innerWidth, w = 460;
      let left = W - w - 40;
      if (rect && rect.x + rect.width / 2 > W / 2) left = 40;
      if (rect && rect.width > W * 0.6) left = W - w - 40;
      Object.assign(n.style, { left: left + "px", bottom: "40px" });
      requestAnimationFrame(() => n.classList.add("show"));
    },
    hideNote() { const n = document.getElementById("demo-note"); if (n) n.classList.remove("show"); this.box(null); },
    card(html) { boot(); document.getElementById("demo-cursor").style.visibility = "hidden"; const c = el("demo-card"); c.innerHTML = html; requestAnimationFrame(() => c.classList.add("show")); },
    // Garde le carton affiché à travers un changement de page (null pour arrêter).
    cover(html) { save({ cover: html || null }); },
    hideCard() { const c = document.getElementById("demo-card"); if (c) { c.classList.remove("show"); setTimeout(() => { c.remove(); const k = document.getElementById("demo-cursor"); if (k) k.style.visibility = ""; }, 550); } },
  };
  const safeBoot = () => { if (document.documentElement) try { boot(); } catch {} };
  safeBoot();
  document.addEventListener("DOMContentLoaded", safeBoot);
  setInterval(safeBoot, 50);
  // Dès que <html> existe (avant le premier affichage), on remet carton et repère.
  const mo = new MutationObserver(() => { if (document.documentElement) { safeBoot(); if (document.body) mo.disconnect(); } });
  mo.observe(document, { childList: true, subtree: true });
})();
