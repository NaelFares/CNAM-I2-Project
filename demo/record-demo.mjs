// Enregistre la vidéo de démo Stud'Ride (capture réelle du navigateur, ~3 min).
// Prérequis : stack lancée (scripts/start-local.ps1) avec un seed FRAIS,
// car le scénario envoie une demande, accepte une demande et note une course.
// Usage : node record-demo.mjs            (vitesse normale)
//         FAST=1 node record-demo.mjs     (répétition rapide, sans pauses)
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, renameSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = process.env.APP_URL || "http://localhost:3000";
const FAST = process.env.FAST === "1";
const PASSWORD = "Test1234!";
const CSV = resolve(HERE, "../backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv");
const OUT = join(HERE, "output");
const W = 1600, H = 900;

const ACCOUNTS = {
  import: { email: "etudiant34@studride-test.fr" },    // Maëlys, CNAM
  passenger: { email: "etudiant01@studride-test.fr" }, // Léa, INSA
  driver: { email: "etudiant30@studride-test.fr" },    // Julie, N7
};

rmSync(join(OUT, "raw"), { recursive: true, force: true });
mkdirSync(join(OUT, "raw"), { recursive: true });

const browser = await chromium.launch({ headless: !process.env.HEADED });
const context = await browser.newContext({
  viewport: { width: W, height: H },
  recordVideo: { dir: join(OUT, "raw"), size: { width: W, height: H } },
  locale: "fr-FR",
});
// Police des annotations embarquée : aucun chargement réseau, donc pas de flicker.
const fontCSS = [500, 600, 700, 800].map((w) => `@font-face{font-family:'Poppins';font-weight:${w};font-display:block;src:url(data:font/woff2;base64,${readFileSync(join(HERE, "fonts", `poppins-${w}.woff2`)).toString("base64")}) format('woff2')}`).join("");
await context.addInitScript({ content: `window.__demoFontCSS = ${JSON.stringify(fontCSS)};` });
await context.addInitScript({ content: readFileSync(join(HERE, "overlay.js"), "utf8") });
const page = await context.newPage();
const t0 = Date.now();
const onFail = async (e) => { console.error(e.message.split("\n")[0]); try { await page.screenshot({ path: join(OUT, "fail.png") }); } catch {} process.exit(1); };
process.on("unhandledRejection", onFail); process.on("uncaughtException", onFail);

// ---------- helpers ----------
const wait = (ms) => page.waitForTimeout(FAST ? Math.min(ms, 120) : ms);
let mouse = { x: W / 2, y: H / 2 };

// Déplacement de souris « humain » : un arc sur tout le trajet (jamais droit),
// avec une légère ondulation, vitesse douce, sans correction à l'arrivée.
const rnd = (a, b) => a + Math.random() * (b - a);
async function moveTo(x, y) {
  const sx = mouse.x, sy = mouse.y, d = Math.hypot(x - sx, y - sy);
  if (d < 3) return;
  const ms = Math.min(850, 300 + d * 0.5) * rnd(0.9, 1.1);
  const steps = FAST ? 2 : Math.max(12, Math.round(ms / 16));
  const nx = -(y - sy) / d, ny = (x - sx) / d;           // perpendiculaire au trajet
  const side = Math.random() < 0.5 ? -1 : 1;
  const arc = side * Math.min(120, d * rnd(0.12, 0.22)); // creux de la courbe
  const c1 = rnd(0.2, 0.4), c2 = rnd(0.6, 0.8);
  const p1 = { x: sx + (x - sx) * c1 + nx * arc, y: sy + (y - sy) * c1 + ny * arc };
  const p2 = { x: sx + (x - sx) * c2 + nx * arc * rnd(0.4, 0.9), y: sy + (y - sy) * c2 + ny * arc * rnd(0.4, 0.9) };
  const wob = rnd(1.5, 3.5), freq = rnd(1.5, 2.5), phase = rnd(0, 6.28);
  for (let i = 1; i <= steps; i++) {
    const t = i / steps, e = 0.5 - Math.cos(Math.PI * t) / 2; // accélère puis ralentit
    const u = 1 - e;
    const bx = u ** 3 * sx + 3 * u * u * e * p1.x + 3 * u * e * e * p2.x + e ** 3 * x;
    const by = u ** 3 * sy + 3 * u * u * e * p1.y + 3 * u * e * e * p2.y + e ** 3 * y;
    const w = Math.sin(e * Math.PI * freq + phase) * wob * Math.sin(Math.PI * e);
    await page.mouse.move(bx + nx * w, by + ny * w);
    if (!FAST) await page.waitForTimeout(ms / steps);
  }
  mouse = { x, y };
}

async function reveal(loc) {
  await loc.waitFor({ state: "visible", timeout: 30000 });
  const off = await loc.evaluate((n) => { const r = n.getBoundingClientRect(); return r.top < 90 || r.bottom > innerHeight - 20; });
  if (off) {
    await loc.evaluate((n) => n.scrollIntoView({ behavior: "smooth", block: n.getBoundingClientRect().height > innerHeight * 0.6 ? "start" : "center" }));
    await wait(600);
  }
}

async function click(loc) {
  loc = loc.first();
  await reveal(loc);
  const b = await loc.boundingBox();
  await moveTo(b.x + b.width / 2, b.y + b.height / 2);
  await wait(150);
  await loc.click();
  await wait(250);
}

// Frappe humaine : ~8 caractères/s, irrégulière.
async function type(loc, text) {
  await click(loc);
  await loc.first().fill("");
  let burst = rnd(0.8, 1.2);
  for (const [i, ch] of [...text].entries()) {
    await page.keyboard.type(ch);
    if (FAST) continue;
    if (Math.random() < 0.15) burst = rnd(0.7, 1.4); // le rythme change par moments
    let ms = rnd(150, 250) * burst;
    if (/[@.\s]/.test(ch)) ms += rnd(120, 300);       // petite hésitation sur @ . espace
    if (i > 2 && Math.random() < 0.05) ms += rnd(450, 900); // on « réfléchit »
    await page.waitForTimeout(ms);
  }
  await wait(200);
}

// Annotation : cadre orange en fondu autour de la zone + encadré de texte.
async function annotate(title, bullets, { target, ms = 4200 } = {}) {
  let rect = null;
  if (target) { const loc = target.first(); await reveal(loc); rect = await loc.boundingBox(); }
  await page.evaluate(({ rect, title, bullets }) => { window.__demo.box(rect); window.__demo.note({ title, bullets, rect }); }, { rect, title, bullets });
  await wait(ms * 0.72);
  await page.evaluate(() => window.__demo.hideNote());
  await wait(350);
}

async function card(html, ms, { keep = false } = {}) {
  await page.evaluate((h) => window.__demo.card(h), html);
  await wait(ms);
  if (keep) return; // le carton suivant remplace celui-ci sans montrer la page
  await page.evaluate(() => window.__demo.hideCard());
  await wait(550);
}
const LOGO = '<img src="/logo.png" alt="">';
const PARTS = ["Import du planning par IA", "Parcours passager", "Parcours conducteur"];
async function chapter(n) {
  await page.evaluate(() => window.__demo.tag(0));
  await card(`${LOGO}<div class="num">${n}</div><h1>${PARTS[n - 1]}</h1>`, 1600);
  await page.evaluate((n) => window.__demo.tag(n), n);
}

// Connexion : les champs sont déjà remplis, on clique seulement sur « Se connecter ».
async function login(acc) {
  await page.goto(`${APP}/login`);
  await page.waitForSelector("input[type=email]");
  await page.fill("input[type=email]", acc.email);
  await page.fill("input[type=password]", PASSWORD);
  await wait(600);
  await click(page.getByRole("button", { name: "Se connecter" }));
  await page.waitForURL((u) => !u.pathname.startsWith("/login"));
  await wait(600);
}
async function logout() {
  await click(page.getByRole("button", { name: "Déconnexion" }));
  await page.waitForURL(/\/login/);
}
const nav = (label) => click(page.locator("header nav").getByRole("link", { name: label }));

// ---------- scénario ----------
await page.goto(`${APP}/login`);
await page.waitForSelector("input[type=email]");
await page.evaluate(() => { window.__demo.tag(0); });
const introAt = (Date.now() - t0) / 1000;
await card(`${LOGO}<div class="parts">${PARTS.map((p, i) => `<div><b>${i + 1}</b>${p}</div>`).join("")}</div>`, 2800, { keep: true });

// ===== 1. Import CSV par IA (Maëlys, CNAM) =====
await chapter(1);
await login(ACCOUNTS.import);
await nav("Planning");
await click(page.getByRole("button", { name: /Importer un planning|Réimporter/ }));
await page.locator("input[type=file]").setInputFiles(CSV);
await wait(500);
await annotate("Import d'un emploi du temps", [
  "Le fichier exporté de l'ENT, tel quel",
  "L'IA comprend toute seule son format",
], { target: page.getByRole("button", { name: /\.csv/ }) });
await click(page.locator("label:has-text('Mode confidentialité') input"));
await annotate("Mode confidentialité", [
  "Les cours de l'étudiant ne sont pas envoyés à l'IA",
  "Seule la structure du fichier est analysée",
], { target: page.locator("label:has-text('Mode confidentialité')") });
await click(page.getByRole("button", { name: "Prévisualiser" }));
await page.getByText("Vérifier l'import").waitFor({ timeout: 90000 });
await wait(900);
await annotate("40 cours détectés", [
  "On vérifie avant d'enregistrer",
], { target: page.locator("div").filter({ has: page.getByText("Vérifier l'import") }).filter({ has: page.getByRole("button", { name: "Confirmer l'import" }) }).last(), ms: 3500 });
await click(page.getByRole("button", { name: "Confirmer l'import" }));
await wait(1000);
await annotate("Le planning est prêt", [
  "Chaque jour de cours donne un aller et un retour",
], { ms: 3500 });
await logout();

// ===== 2. Passager (Léa, INSA) =====
await chapter(2);
await login(ACCOUNTS.passenger);
await annotate("Un seul compte, deux rôles", [
  "On peut être passager un jour, conducteur un autre",
], { ms: 3800 });
await nav("Covoiturage");
await click(page.getByRole("tab", { name: "Ma semaine de cours" }));
await click(page.getByRole("button", { name: "Rechercher" }));
await page.locator(".matches-explorer").waitFor({ timeout: 60000 });
await wait(1000);
await annotate("Toute la semaine en une recherche", [
  "Les propositions de chaque jour, à partir des cours",
], { target: page.locator("div").filter({ has: page.getByText("ALLER", { exact: false }) }).filter({ hasText: "26" }).filter({ hasText: "30" }).last(), ms: 4000 });
const camille = page.locator("article").filter({ hasText: "Camille Roux" }).first();
await click(camille.getByText("Camille Roux"));
await wait(1100);
await annotate("Un conducteur qui passe sur la route", [
  "Camille passe près de chez Léa",
  "Petit détour : moins de 8 minutes",
  "Les trajets sont classés du meilleur au moins bon",
], { target: page.locator(".matches-explorer"), ms: 5500 });
await click(camille.getByRole("button", { name: /Choisir/ }));
await page.waitForURL(/\/matches\/recap\//);
await wait(1000);
await click(page.getByRole("button", { name: "Envoyer la demande" }));
await wait(900);
await nav("Mes courses");
await wait(900);
await annotate("Suivi du trajet du jour", [
  "Chaque étape est confirmée des deux côtés",
], { target: page.getByText("En cours").locator("xpath=ancestor::section[1]"), ms: 3800 });
await click(page.getByRole("button", { name: /Je suis arrivé/ }));
await wait(900);
await click(page.getByRole("button", { name: "Noter la course" }));
await click(page.getByRole("radio", { name: "5 étoiles" }));
await type(page.getByPlaceholder("Un commentaire ? (facultatif)"), "Super trajet, merci !");
await click(page.getByRole("button", { name: "Envoyer ma note" }));
await click(page.getByRole("button", { name: "Confirmer" }));
await annotate("On note après chaque course", [
  "La note construit la réputation du conducteur",
], { ms: 3500 });
await logout();

// ===== 3. Conducteur (Julie, N7) =====
await chapter(3);
await login(ACCOUNTS.driver);
await nav("Covoiturage");
await click(page.getByRole("tab", { name: "Conducteur" }));
await wait(1000);
await annotate("Les demandes reçues", [
  "Où et quand prendre chaque passager",
  "Le détour que ça ajoute",
], { target: page.locator("section, div").filter({ has: page.getByText("Demandes à traiter") }).filter({ has: page.getByRole("button", { name: "Accepter" }) }).last(), ms: 4500 });
const firstReq = page.locator("li, article, div.card").filter({ hasText: "Charlie Nicolas" }).filter({ has: page.getByRole("button", { name: "Accepter" }) }).first();
await click(firstReq.getByRole("button", { name: "Accepter" }));
await wait(800);
await click(page.locator(".calendar-chip").filter({ hasText: "08:00" }).nth(2));
await wait(1000);
await annotate("Le trajet de jeudi", [
  "Le passager est confirmé",
  "Les arrêts dans l'ordre, avec leurs horaires",
], { target: page.locator("aside, [role=dialog]").first(), ms: 4200 });
await page.keyboard.press("Escape");
await page.locator("[role=dialog] button[aria-label*='ermer'], aside button[aria-label*='ermer']").first().click({ timeout: 1500 }).catch(() => {});
await wait(500);
await click(page.getByRole("button", { name: "Proposer un trajet" }));
await wait(800);
await annotate("Proposer un trajet", [
  "Départ et arrivée déjà remplis depuis le profil",
  "Quelques clics suffisent",
], { target: page.locator("div").filter({ has: page.getByRole("heading", { name: "Proposer un trajet" }) }).filter({ hasText: "Heure" }).last(), ms: 4000 });

await page.evaluate(() => window.__demo.tag(0));
await card(`${LOGO}<h1>Merci !</h1>`, 2800);

const video = page.video();
const tEnd = (Date.now() - t0) / 1000;
await context.close();
await browser.close();
const webm = join(OUT, "studride-demo.webm");
renameSync(await video.path(), webm);
rmSync(join(OUT, "raw"), { recursive: true, force: true });

// MP4 1080p, en coupant la page blanche du début.
try {
  const mp4 = join(OUT, "studride-demo.mp4");
  // La vidéo ne commence qu'au premier affichage de page : on recale la coupe
  // du début à partir de la fin (qui, elle, coïncide avec tEnd).
  const probe = execFileSync("ffprobe", ["-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "format=duration", "-of", "csv=p=0", webm]).toString().trim();
  const dur = Number(probe) || tEnd;
  const startAt = Math.max(0, introAt - (tEnd - dur) - 0.05);
  execFileSync("ffmpeg", ["-y", "-ss", String(startAt), "-i", webm,
    "-vf", "scale=1920:1080:flags=lanczos,fps=30", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], { stdio: "ignore" });
  rmSync(webm);
  console.log("OK", mp4);
} catch {
  console.log("ffmpeg indisponible, vidéo :", webm);
}
