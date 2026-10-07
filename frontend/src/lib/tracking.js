// Libelles du suivi de covoiturage. Les valeurs proviennent du backend
// (backend/services/ride_tracking.py et models/ride_selection.py).

export const STATUS_LABELS = {
  pending: "En attente de prise en charge",
  picking_up: "Prise en charge à confirmer",
  on_board: "En route",
  arriving: "Fin de course à confirmer",
  completed: "Course terminée",
  cancelled: "Annulée",
};

export const STATUS_VARIANTS = {
  pending: "info",
  picking_up: "info",
  on_board: "primary",
  arriving: "primary",
  completed: "success",
  cancelled: "danger",
};

// Intitule du bouton, selon l'etape que l'utilisateur doit confirmer.
export const STEP_LABELS = {
  picked_up: "J'ai récupéré mon passager",
  on_board: "Je suis bien dans le véhicule",
  completed: "La course est terminée",
  arrived: "Je suis arrivé à destination",
};

export function statusLabel(status) {
  return STATUS_LABELS[status] ?? status;
}

export function statusVariant(status) {
  return STATUS_VARIANTS[status] ?? "info";
}

export function stepLabel(step) {
  return STEP_LABELS[step] ?? "Confirmer";
}

export function isFinished(status) {
  return status === "completed" || status === "cancelled";
}

/**
 * Message affiche quand l'utilisateur n'a rien a confirmer dans l'immediat.
 * Le suivi repose sur une double confirmation : il faut donc dire clairement
 * qu'on attend l'autre partie, sinon l'absence de bouton passe pour un bug.
 */
export function waitingMessage(tracking) {
  if (isFinished(tracking.status)) return "";

  const isDriver = tracking.my_role === "driver";
  const mineConfirmed = isDriver ? tracking.driver_picked_up_at : tracking.passenger_onboard_at;
  const theirsConfirmed = isDriver ? tracking.passenger_onboard_at : tracking.driver_picked_up_at;

  if (mineConfirmed && !theirsConfirmed) {
    return isDriver
      ? "En attente de la confirmation de votre passager."
      : "En attente de la confirmation de votre conducteur.";
  }
  return "En attente de la confirmation de l'autre participant.";
}

/**
 * Les quatre confirmations dans l'ordre, pour afficher la progression.
 */
export function confirmationSteps(tracking) {
  return [
    { label: "Conducteur : passager récupéré", at: tracking.driver_picked_up_at },
    { label: "Passager : à bord", at: tracking.passenger_onboard_at },
    { label: "Conducteur : course terminée", at: tracking.driver_completed_at },
    { label: "Passager : arrivé à destination", at: tracking.passenger_arrived_at },
  ];
}
