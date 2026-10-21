// Formats d'affichage communs, en francais (virgule decimale, mois en minuscules).
const MINUTES = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 });

export function formatMinutes(value) {
  const minutes = Number(value);
  return Number.isFinite(minutes) ? `${MINUTES.format(Math.max(0, minutes))} min` : "—";
}

function toDate(value) {
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatTime(value) {
  const date = toDate(value);
  return date ? date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) : "";
}

// "lundi 26 octobre"
export function formatDay(value) {
  const date = toDate(value);
  return date ? date.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" }) : "";
}

// "lun. 26 oct. · 08:00"
export function formatShortDateTime(value) {
  const date = toDate(value);
  if (!date) return "Horaire non défini";
  const day = date.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });
  return `${day} · ${formatTime(date)}`;
}

export function isSameDay(a, b = new Date()) {
  const first = toDate(a);
  const second = toDate(b);
  return Boolean(first && second && first.toDateString() === second.toDateString());
}

export function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}
