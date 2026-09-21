// Valeurs de `users.music_preference` / `users.smoking_preference` telles que
// stockees en base (cf. backend/api/schemas.py) et leurs libelles d'affichage.

export const MUSIC_OPTIONS = [
  { value: "peu_importe", label: "Peu importe" },
  { value: "avec", label: "Avec musique" },
  { value: "sans", label: "Sans musique" },
];

// Styles musicaux : l'ordre et les valeurs doivent rester alignes sur
// MUSIC_GENRE_VALUES (backend/api/constants.py), qui fait foi a la validation.
export const MUSIC_GENRE_OPTIONS = [
  { value: "pop", label: "Pop" },
  { value: "rap", label: "Rap" },
  { value: "rnb", label: "R&B" },
  { value: "shatta", label: "Shatta" },
  { value: "latino", label: "Latino" },
  { value: "reggae", label: "Reggae" },
  { value: "afrobeat", label: "Afrobeat" },
  { value: "rock", label: "Rock" },
  { value: "metal", label: "Métal" },
  { value: "electro", label: "Électro" },
  { value: "jazz", label: "Jazz" },
  { value: "classique", label: "Classique" },
  { value: "variete_francaise", label: "Variété française" },
  { value: "kpop", label: "K-pop" },
  { value: "soul_funk", label: "Soul / Funk" },
  { value: "country", label: "Country" },
];

// Aligne sur MAX_MUSIC_GENRES cote backend.
export const MAX_MUSIC_GENRES = 5;

// Les styles n'ont de sens que si la musique est acceptee (cf. User.wants_music).
export function wantsMusic(musicPreference) {
  return musicPreference === "avec" || musicPreference === "peu_importe";
}

export function musicGenreLabel(value) {
  return MUSIC_GENRE_OPTIONS.find((option) => option.value === value)?.label ?? value;
}

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
  // Les styles se suffisent a eux-memes : "Rap" dit deja qu'il y a de la
  // musique, inutile de le doubler d'un badge "Avec musique".
  for (const genre of user.music_genres ?? []) {
    badges.push(musicGenreLabel(genre));
  }
  if (user.smoking_preference && user.smoking_preference !== "peu_importe") {
    badges.push(smokingLabel(user.smoking_preference));
  }
  return badges;
}
