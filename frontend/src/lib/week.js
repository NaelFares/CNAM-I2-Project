export function localDateIso(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function mondayIso(value) {
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return null;
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  return localDateIso(date);
}

function daysFromMonday(monday, count) {
  if (!monday) return [];
  const first = new Date(`${monday}T12:00:00`);
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(first);
    date.setDate(first.getDate() + index);
    return {
      iso: localDateIso(date),
      label: new Intl.DateTimeFormat("fr-FR", {
        weekday: "long", day: "numeric", month: "long",
      }).format(date),
    };
  });
}

export function schoolWeekDays(monday) {
  return daysFromMonday(monday, 5);
}

export function calendarWeekDays(monday) {
  return daysFromMonday(monday, 7);
}

export function shiftWeek(monday, offset) {
  if (!monday) return null;
  const date = new Date(`${monday}T12:00:00`);
  date.setDate(date.getDate() + offset * 7);
  return localDateIso(date);
}

export function ridesForWeek(rides, monday) {
  const days = calendarWeekDays(monday);
  if (!days.length) return [];
  return rides.filter((ride) => {
    const day = String(ride.ride_time || "").slice(0, 10);
    return days[0].iso <= day && day <= days[6].iso;
  }).sort((a, b) => String(a.ride_time).localeCompare(String(b.ride_time)));
}

export function matchesForDay(matches, day) {
  return matches.filter((match) => String(match.ride_time || "").slice(0, 10) === day);
}
