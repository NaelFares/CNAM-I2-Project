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
