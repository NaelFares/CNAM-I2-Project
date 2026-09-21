// Valeurs de `users.gender` telles que stockees en base
// (cf. backend/api/constants.py) et leurs libelles d'affichage.

export const GENDER_OPTIONS = [
  { value: "homme", label: "Homme" },
  { value: "femme", label: "Femme" },
  { value: "autre", label: "Autre" },
];

export function genderLabel(value) {
  return GENDER_OPTIONS.find((option) => option.value === value)?.label ?? "Non renseigné";
}

// L'option "entre femmes" d'une recherche est reservee aux utilisatrices ; le
// backend la refuse aux autres (MATCHES_LADIES_ONLY_FORBIDDEN), le front se
// contente de masquer la case.
export function canUseLadiesOnly(profile) {
  return profile?.gender === "femme";
}
