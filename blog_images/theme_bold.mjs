/**
 * theme_bold.mjs - 유튜브 썸네일형 "볼드" 테마 (파란 배경 · 흰/노랑 굵은 글씨 · 인물 컷)
 *
 * headline_html / heading_html 안에서
 *   <em>…</em>  노란색 강조
 *   <i>…</i>    노란색 + 작은 글씨 (예: "일까요?")
 *   <br>        줄바꿈
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

const esc = (s = "") =>
  String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// 인물 컷: 썸네일 오른쪽에 들어가는 보험지기 사진
const PRESENTERS = { point: "presenter_point.webp", three: "presenter_three.webp", doc: "presenter_doc.webp" };

function presenterUri(name) {
  const file = PRESENTERS[name];
  if (!file) return null;
  const buf = fs.readFileSync(path.join(HERE, "assets", file));
  return `data:image/webp;base64,${buf.toString("base64")}`;
}

// 카드·라벨용 아이콘 (24x24 기준 단순 도형)
const ICONS = {
  doc: `<rect x="4" y="2" width="13" height="18" rx="2" fill="#fff" stroke="#123E9C" stroke-width="1.6"/><path d="M7 7h7M7 10h7M7 13h4" stroke="#2F6BFF" stroke-width="1.6" stroke-linecap="round"/><circle cx="17" cy="17" r="5" fill="#1F5BFF"/><path d="M14.6 17l1.6 1.6 3-3.2" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
  family: `<path d="M2 11 12 3l10 8" stroke="#1F5BFF" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="8" cy="11" r="2.4" fill="#123E9C"/><circle cx="16" cy="11" r="2.4" fill="#123E9C"/><circle cx="12" cy="14" r="2" fill="#2F8BFF"/><path d="M4 21c0-3 2-5 4-5s4 2 4 5M12 21c0-3 2-5 4-5s4 2 4 5" fill="#123E9C"/><path d="M9 21c0-2.4 1.4-4 3-4s3 1.6 3 4" fill="#2F8BFF"/>`,
  coins: `<ellipse cx="9" cy="17" rx="6" ry="2.5" fill="#F7C51E" stroke="#B88A00"/><ellipse cx="9" cy="14" rx="6" ry="2.5" fill="#FFD84A" stroke="#B88A00"/><ellipse cx="9" cy="11" rx="6" ry="2.5" fill="#FFE27A" stroke="#B88A00"/><circle cx="17" cy="14" r="5.5" fill="#FFD21F" stroke="#123E9C" stroke-width="1.4"/><path d="M14.5 12l1.2 4 1.3-3 1.3 3 1.2-4M14.3 13.6h5.4" stroke="#123E9C" stroke-width="1.1" fill="none" stroke-linejoin="round"/>`,
  receipt: `<path d="M5 2h12v19l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4-2 1.4z" fill="#fff" stroke="#123E9C" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 7h6M8 10h6M8 13h4" stroke="#2F6BFF" stroke-width="1.6" stroke-linecap="round"/>`,
  calendar: `<rect x="3" y="5" width="18" height="16" rx="2.5" fill="#fff" stroke="#123E9C" stroke-width="1.6"/><path d="M3 9.5h18" stroke="#123E9C" stroke-width="1.6"/><rect x="3" y="5" width="18" height="4.5" rx="2" fill="#1F5BFF"/><path d="M8 3v4M16 3v4" stroke="#123E9C" stroke-width="1.8" stroke-linecap="round"/><path d="M8.5 15l2.2 2.2 4.6-4.6" stroke="#1F5BFF" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
  shield: `<path d="M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5z" fill="#1F5BFF" stroke="#123E9C" stroke-width="1.2"/><path d="M8.5 12l2.5 2.5 4.5-5" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
  alert: `<path d="M12 3 2 20h20z" fill="#FFD21F" stroke="#123E9C" stroke-width="1.5" stroke-linejoin="round"/><path d="M12 9v5" stroke="#123E9C" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="17" r="1.2" fill="#123E9C"/>`,
  people: `<circle cx="9" cy="8" r="3.2" fill="#123E9C"/><circle cx="16.5" cy="9" r="2.6" fill="#2F8BFF"/><path d="M3 20c0-3.6 2.7-6 6-6s6 2.4 6 6z" fill="#123E9C"/><path d="M13 20c.2-3 1.8-5 3.5-5 2 0 4 2 4 5z" fill="#2F8BFF"/>`,
  calc: `<rect x="5" y="2" width="14" height="20" rx="2.5" fill="#fff" stroke="#123E9C" stroke-width="1.6"/><rect x="7.5" y="4.5" width="9" height="4" rx="1" fill="#1F5BFF"/><g fill="#123E9C"><circle cx="9" cy="12" r="1.1"/><circle cx="12" cy="12" r="1.1"/><circle cx="15" cy="12" r="1.1"/><circle cx="9" cy="15.5" r="1.1"/><circle cx="12" cy="15.5" r="1.1"/><circle cx="15" cy="15.5" r="1.1"/><circle cx="9" cy="19" r="1.1"/><circle cx="12" cy="19" r="1.1"/></g><rect x="14" y="18" width="2" height="2.2" rx=".6" fill="#FFD21F"/>`,
  check: `<circle cx="12" cy="12" r="10" fill="#1F5BFF"/><path d="M7 12.5l3.2 3.2L17 9" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
};

const icon = (name, size) =>
  `<svg width="${size}" height="${size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">${ICONS[name] || ICONS.doc}</svg>`;

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@500;700;900&display=block');
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1080px; overflow: hidden; }
body {
  position: relative; word-break: keep-all; color: #fff;
  font-family: 'Noto Sans KR', 'WenQuanYi Zen Hei', sans-serif;
  background:
    radial-gradient(circle at 78% 30%, #4D8BFF 0%, rgba(77,139,255,0) 45%),
    radial-gradient(circle at 15% 85%, #2F6BFF 0%, rgba(47,107,255,0) 40%),
    linear-gradient(160deg, #0B3BB0 0%, #1554E0 55%, #0A2F8F 100%);
}
.bokeh { position: absolute; inset: 0; pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(255,255,255,.10) 0 38px, transparent 39px),
    radial-gradient(circle, rgba(255,255,255,.07) 0 60px, transparent 61px),
    radial-gradient(circle, rgba(255,255,255,.06) 0 26px, transparent 27px);
  background-size: 420px 380px, 560px 520px, 300px 260px;
  background-position: 40px 60px, 300px 200px, 120px 400px; }
.presenter { position: absolute; right: 0; bottom: 92px; z-index: 1; }
.content { position: relative; z-index: 2; padding: 56px 56px 0; }
.badge { display: inline-block; padding: 16px 40px; border-radius: 999px;
  background: linear-gradient(180deg, #0D2A7A, #081C57); border: 4px solid #5FA2FF;
  box-shadow: 0 0 22px rgba(95,162,255,.85), inset 0 0 14px rgba(95,162,255,.35);
  font-family: 'Black Han Sans', sans-serif; font-size: 44px; letter-spacing: 1px; }
.badge em { font-style: normal; color: #FFE600; }
.headline { font-family: 'Black Han Sans', sans-serif; line-height: 1.12; letter-spacing: -1px;
  text-shadow:
    -6px -6px 0 #0A1A4A, 6px -6px 0 #0A1A4A, -6px 6px 0 #0A1A4A, 6px 6px 0 #0A1A4A,
    0 -7px 0 #0A1A4A, 0 7px 0 #0A1A4A, -7px 0 0 #0A1A4A, 7px 0 0 #0A1A4A,
    10px 14px 0 rgba(4,14,48,.55); }
.headline em, .headline i { font-style: normal; color: #FFE600; }
.headline i { font-size: .72em; }
.subpill { display: inline-flex; align-items: center; gap: 18px; margin-top: 34px;
  background: #fff; color: #0B1F4D; border: 6px solid #2F7BFF; border-radius: 34px;
  padding: 18px 34px 18px 22px; box-shadow: 0 10px 0 rgba(4,14,48,.35);
  font-family: 'Black Han Sans', sans-serif; font-size: 56px; letter-spacing: -1px; }
.subpill em { font-style: normal; color: #1F5BFF; }
.callout { display: inline-flex; align-items: center; gap: 16px;
  background: #0B1F4D; border: 5px solid #FFE600; border-radius: 999px; padding: 16px 40px;
  font-family: 'Black Han Sans', sans-serif; font-size: 44px; letter-spacing: -.5px;
  box-shadow: 0 8px 0 rgba(4,14,48,.4); }
.callout em { font-style: normal; color: #FFE600; }
.foot { position: absolute; left: 0; right: 0; bottom: 0; height: 120px; z-index: 3;
  display: flex; align-items: center; justify-content: center; }
.foot svg { position: absolute; inset: 0; }
.foot span { position: relative; font-size: 40px; font-weight: 900; letter-spacing: 1px;
  padding-bottom: 8px; border-bottom: 4px solid #5FA2FF; }
`;

const FOOT = (brand) => `<div class="foot">
  <svg viewBox="0 0 1080 120" preserveAspectRatio="none"><path d="M0 34 C 260 -6, 520 54, 1080 18 L1080 120 L0 120 Z" fill="#0A2A86"/><path d="M0 34 C 260 -6, 520 54, 1080 18" stroke="#5FA2FF" stroke-width="5" fill="none"/></svg>
  <span>${esc(brand)}</span></div>`;

function page(inner, { presenter, presenterHeight = 900, brand }) {
  const uri = presenter ? presenterUri(presenter) : null;
  const img = uri ? `<img class="presenter" src="${uri}" style="height:${presenterHeight}px">` : "";
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head><body>
  <div class="bokeh"></div>${img}<div class="content">${inner}</div>${FOOT(brand)}</body></html>`;
}

export function titleHtml(t, spec) {
  const size = t.headline_size || 132;
  const inner = `
    <div class="badge">${t.badge_html || esc(t.badge || "보험·세금 상식 블로그")}</div>
    <div class="headline" style="font-size:${size}px;margin-top:34px">${t.headline_html || esc(t.headline)}</div>
    ${t.sub || t.sub_html ? `<div class="subpill">${icon(t.sub_icon || "doc", 76)}<span>${t.sub_html || esc(t.sub)}</span></div>` : ""}`;
  return page(inner, { presenter: t.presenter ?? "doc", presenterHeight: 930, brand: spec.brand });
}

function cardsBlock(items, withPresenter) {
  const n = items.length;
  const cols = n === 4 ? 2 : n;
  const maxW = withPresenter && n <= 3 ? 840 : 968;
  return `<div style="display:grid;grid-template-columns:repeat(${cols},1fr);gap:22px;margin-top:${n === 4 ? 30 : 58}px;max-width:${maxW}px">
    ${items.map((c, i) => `<div style="position:relative;background:#fff;border:5px solid #7FB2FF;border-radius:30px;
        padding:${n === 4 ? "26px 26px 24px" : "58px 18px 24px"};color:#0B1F4D;text-align:center;box-shadow:0 0 18px rgba(127,178,255,.7)">
        ${n === 4 ? "" : `<div style="position:absolute;top:-38px;left:50%;transform:translateX(-50%);width:76px;height:76px;border-radius:50%;
          background:#1F5BFF;border:5px solid #fff;display:flex;align-items:center;justify-content:center;
          font-family:'Black Han Sans';font-size:44px;color:#fff;box-shadow:0 0 12px rgba(31,91,255,.6)">${i + 1}</div>`}
        <div style="font-family:'Black Han Sans';font-size:${n === 4 ? 42 : 46}px;line-height:1.18;letter-spacing:-1px">${c.title_html || esc(c.title)}</div>
        <div style="margin:${n === 4 ? "10px 0 6px" : "18px 0 10px"};display:flex;justify-content:center">${icon(c.icon || "doc", n === 4 ? 92 : 150)}</div>
        ${c.desc ? `<div style="font-size:${n === 4 ? 25 : 24}px;font-weight:700;line-height:1.4;color:#34425C">${esc(c.desc)}</div>` : ""}
      </div>`).join("")}</div>`;
}

function tableBlock(rows) {
  const [head, ...body] = rows;
  return `<div style="margin-top:36px;background:#fff;border:5px solid #7FB2FF;border-radius:30px;overflow:hidden;
      box-shadow:0 0 18px rgba(127,178,255,.7)">
    <table style="width:100%;border-collapse:collapse;color:#0B1F4D;font-size:30px">
      <thead><tr>${head.map((h) => `<th style="background:#0B2C8C;color:#fff;padding:22px 18px;text-align:left;
        font-family:'Black Han Sans';font-size:34px;font-weight:400">${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${body.map((r, ri) => `<tr style="background:${ri % 2 ? "#F1F6FF" : "#fff"}">${r.map((c, ci) =>
        `<td style="padding:22px 18px;line-height:1.35;font-weight:${ci === 0 ? 900 : 700};${ci === r.length - 1 ? "color:#1F5BFF" : ""}">${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody>
    </table></div>`;
}

function checkBlock(items, withPresenter) {
  return `<div style="margin-top:30px;display:flex;flex-direction:column;gap:14px;max-width:${withPresenter ? 720 : 968}px">
    ${items.map((t) => `<div style="display:flex;align-items:center;gap:18px;background:#fff;color:#0B1F4D;border-radius:24px;
        padding:20px 26px;border:4px solid #7FB2FF;font-size:31px;font-weight:900;line-height:1.3;letter-spacing:-.5px">
        <span style="flex:none">${icon("check", 46)}</span><span>${esc(t)}</span></div>`).join("")}</div>`;
}

export function subHtml(s, idx, spec) {
  const type = s.type || "list";
  const defaultPresenter = type === "table" ? null : type === "cards" && s.items.length === 4 ? null : type === "check" ? "doc" : "three";
  const presenter = s.presenter === undefined ? defaultPresenter : s.presenter;
  let body;
  if (type === "cards") body = cardsBlock(s.items, !!presenter);
  else if (type === "table") body = tableBlock(s.rows);
  else body = checkBlock(s.items, !!presenter);
  const size = s.heading_size || 96;
  const inner = `
    <div class="badge" style="font-size:40px;padding:14px 36px">${s.badge_html || esc(s.label || `체크 ${idx}`)}</div>
    <div class="headline" style="font-size:${size}px;margin-top:26px">${s.heading_html || esc(s.heading)}</div>
    ${body}
    ${s.callout || s.callout_html ? `<div style="margin-top:34px">
      <div class="callout"><span>${s.callout_html || esc(s.callout)}</span></div></div>` : ""}`;
  return page(inner, { presenter, presenterHeight: type === "check" ? 760 : 820, brand: spec.brand });
}
