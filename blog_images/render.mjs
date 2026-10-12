#!/usr/bin/env node
/**
 * render.mjs - 네이버 블로그용 타이틀 이미지 1장 + 서브 이미지 3장 생성기
 *
 * 사용법:
 *   node blog_images/render.mjs <spec.json> <출력폴더>
 *
 * spec.json 형식은 blog_images/example.json 참고.
 * spec.theme: "bold"(기본, 유튜브 썸네일형) 또는 "classic"(네이비·크림 카드형)
 * 출력: title.png, sub1.png, sub2.png, sub3.png (각 1080x1080)
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import * as bold from "./theme_bold.mjs";

const require = createRequire(import.meta.url);

function loadPlaywright() {
  const candidates = ["playwright", "/opt/node-tools/node_modules/playwright"];
  for (const c of candidates) {
    try {
      return require(c);
    } catch {}
  }
  const globalRoot = require("node:child_process")
    .execSync("npm root -g").toString().trim();
  return require(path.join(globalRoot, "playwright"));
}

const esc = (s = "") =>
  String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// 보험지기 브랜드 톤: 네이비 · 크림 · 오렌지 포인트
const BASE_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=block');
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1080px; }
body {
  font-family: 'Noto Sans KR', 'WenQuanYi Zen Hei', sans-serif;
  background: #F7F1E6; color: #13284A; word-break: keep-all;
  display: flex; flex-direction: column; padding: 84px 88px;
}
.brand { font-size: 26px; font-weight: 700; color: #13284A; opacity: .75; letter-spacing: .5px; }
.brand b { color: #E8772E; }
.foot { margin-top: auto; display: flex; justify-content: space-between; align-items: center;
        font-size: 24px; color: #5A6478; border-top: 2px solid #13284A22; padding-top: 28px; }
.label { display: inline-block; background: #13284A; color: #F7F1E6; font-weight: 700;
         font-size: 26px; padding: 10px 22px; border-radius: 999px; margin-bottom: 30px; }
h2 { font-size: 60px; line-height: 1.28; font-weight: 900; margin-bottom: 44px; }
h2 em { font-style: normal; color: #E8772E; }
`;

function titleHtml(t) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>${BASE_CSS}
  body { background: #13284A; color: #F7F1E6; }
  .brand { color: #F7F1E6; }
  .kicker { margin-top: 120px; font-size: 34px; font-weight: 700; color: #F2A65A; }
  .headline { margin-top: 26px; font-size: 96px; line-height: 1.22; font-weight: 900; }
  .headline em { font-style: normal; color: #F2A65A; }
  .bar { width: 120px; height: 10px; background: #E8772E; margin: 48px 0 36px; border-radius: 5px; }
  .sub { font-size: 36px; line-height: 1.5; color: #F7F1E6CC; }
  .foot { color: #F7F1E6AA; border-color: #F7F1E633; }
  </style></head><body>
  <div class="brand"><b>●</b> 지혜로운보험생활 · 보험지기</div>
  <div class="kicker">${esc(t.kicker)}</div>
  <div class="headline">${t.headline_html || esc(t.headline)}</div>
  <div class="bar"></div>
  <div class="sub">${esc(t.sub)}</div>
  <div class="foot"><span>가입보다 관리, 비교보다 관계</span><span>보험지기</span></div>
  </body></html>`;
}

function subHtml(s, idx) {
  let body = "";
  if (s.type === "table") {
    const [head, ...rows] = s.rows;
    body = `<table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  } else if (s.type === "check") {
    body = `<ul class="check">${s.items.map((i) => `<li><span class="box"></span>${esc(i)}</li>`).join("")}</ul>`;
  } else if (s.type === "cards") {
    body = `<div class="cards">${s.items.map((c) =>
      `<div class="card"><div class="ct">${esc(c.title)}</div><div class="cd">${esc(c.desc)}</div></div>`).join("")}</div>`;
  } else {
    body = `<ol class="list">${s.items.map((i, n) => `<li><span class="n">${n + 1}</span>${esc(i)}</li>`).join("")}</ol>`;
  }
  return `<!doctype html><html><head><meta charset="utf-8"><style>${BASE_CSS}
  table { width: 100%; border-collapse: collapse; font-size: 28px; }
  th { background: #13284A; color: #F7F1E6; padding: 18px 14px; font-weight: 700; text-align: left; }
  td { background: #FFFFFF; padding: 20px 14px; border-bottom: 2px solid #F7F1E6; line-height: 1.4; }
  td:last-child { font-weight: 700; color: #C65A17; }
  .list, .check { list-style: none; display: flex; flex-direction: column; gap: 22px; }
  .list li, .check li { background: #fff; border-radius: 20px; padding: 26px 30px; font-size: 34px;
                        line-height: 1.4; display: flex; gap: 22px; align-items: flex-start; font-weight: 500; }
  .n { flex: none; width: 52px; height: 52px; border-radius: 50%; background: #E8772E; color: #fff;
       display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 28px; }
  .box { flex: none; width: 40px; height: 40px; border: 4px solid #13284A; border-radius: 8px; margin-top: 4px; }
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
  .card { background: #fff; border-radius: 22px; padding: 30px; border-top: 10px solid #E8772E; }
  .ct { font-size: 36px; font-weight: 900; margin-bottom: 12px; }
  .cd { font-size: 27px; line-height: 1.45; color: #34425C; }
  </style></head><body>
  <div><span class="label">${esc(s.label || `POINT ${idx}`)}</span></div>
  <h2>${s.heading_html || esc(s.heading)}</h2>
  ${body}
  <div class="foot"><span>${esc(s.note || "개별 상황은 계약 내용과 최신 법령 기준으로 확인이 필요합니다")}</span><span>보험지기</span></div>
  </body></html>`;
}

async function main() {
  const [specPath, outDir] = process.argv.slice(2);
  if (!specPath || !outDir) {
    console.error("사용법: node blog_images/render.mjs <spec.json> <출력폴더>");
    process.exit(1);
  }
  const spec = JSON.parse(fs.readFileSync(specPath, "utf-8"));
  if (!spec.title || !Array.isArray(spec.subs) || spec.subs.length !== 3) {
    throw new Error("spec에는 title 1개와 subs 3개가 필요합니다.");
  }
  fs.mkdirSync(outDir, { recursive: true });

  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 } });

  spec.brand = spec.brand || "지혜로운보험생활 보험지기";
  const theme = spec.theme || "bold";
  const jobs = theme === "classic"
    ? [["title.png", titleHtml(spec.title)],
       ...spec.subs.map((s, i) => [`sub${i + 1}.png`, subHtml(s, i + 1)])]
    : [["title.png", bold.titleHtml(spec.title, spec)],
       ...spec.subs.map((s, i) => [`sub${i + 1}.png`, bold.subHtml(s, i + 1, spec)])];
  for (const [name, html] of jobs) {
    await page.setContent(html, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    const out = path.join(outDir, name);
    await page.screenshot({ path: out });
    console.log(`✅ ${out}`);
  }
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
