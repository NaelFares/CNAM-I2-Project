// Valeurs de `users.music_preference` / `users.smoking_preference` telles que
// stockees en base (cf. backend/api/schemas.py) et leurs libelles d'affichage.

export const MUSIC_OPTIONS = [
  { value: "peu_importe", label: "Peu importe" },
  { value: "avec", label: "Avec musique" },
  { value: "sans", label: "Sans musique" },
];

export const SMOKING_OPTIONS = [
  { value: "peu_importe", label: "Peu importe" },
  { value: "non_fumeur", label: "Non-fumeur" },
  { value: "fumeur", label: "Fumeur" },
];

// Nombre de places passager : borne alignee sur MAX_CAR_SEATS cote backend.
export const MAX_CAR_SEATS = 8;

function labelOf(options, value) {
  return options.find((option) => option.value === value)?.label ?? "";
}

export function musicLabel(value) {
  return labelOf(MUSIC_OPTIONS, value);
}

export function smokingLabel(value) {
  return labelOf(SMOKING_OPTIONS, value);
}

// Les valeurs "peu importe" ne sont pas affichees sur les cards : elles
// n'apprennent rien au lecteur et alourdissent la lecture.
export function tripPreferenceBadges(user) {
  if (!user) return [];
  const badges = [];
  if (user.music_preference && user.music_preference !== "peu_importe") {
    badges.push(musicLabel(user.music_preference));
  }
  if (user.smoking_preference && user.smoking_preference !== "peu_importe") {
    badges.push(smokingLabel(user.smoking_preference));
  }
  return badges;
}
