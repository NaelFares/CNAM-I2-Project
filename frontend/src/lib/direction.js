// Sens d'un trajet. Le backend renvoie soit la cle ("to_campus" / "from_campus"),
// soit le libelle ("Vers le campus" / "Depuis le campus") selon les routes.
export function isOutbound(rideType) {
  const value = String(rideType || "");
  return value === "to_campus" || value.startsWith("Vers");
}

export function directionLabel(rideType) {
  return isOutbound(rideType) ? "Aller" : "Retour";
}
