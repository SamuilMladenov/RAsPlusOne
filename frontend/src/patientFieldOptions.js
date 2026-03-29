/** Matches backend enum string values (models.py / schemas). Used for random START + destination. */

export const RESPIRATION_VALUES = [
  "Not Breathing",
  "< 10 / min",
  "10 - 30 / min",
  "> 30 / min",
];

export const PERFUSION_VALUES = [
  "Radial pulse present",
  "No radial pulse",
  "Capillary refill < 2 sec",
  "Capillary refill > 2 sec",
  "Severe bleeding",
];

export const MENTAL_VALUES = ["Alert", "Unresponsive", "Cannot follow commands"];

export const DESTINATION_VALUES = [
  "General Hospital",
  "Trauma Center",
  "Burn Unit",
];

/** Triage levels used by bulk emergency (black excluded). */
export const EMERGENCY_TRIAGE_VALUES = ["red", "yellow", "green"];

export function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function randomClinicalFields() {
  return {
    respiration: pickRandom(RESPIRATION_VALUES),
    perfusion: pickRandom(PERFUSION_VALUES),
    mental_status: pickRandom(MENTAL_VALUES),
    destination: pickRandom(DESTINATION_VALUES),
  };
}

/** One synthetic patient for POST /emergencies/ (same shape as backend EmergencyPatientInput). */
export function randomEmergencyPatient() {
  const c = randomClinicalFields();
  return {
    triage_priority: pickRandom(EMERGENCY_TRIAGE_VALUES),
    destination: c.destination,
    respiration: c.respiration,
    perfusion: c.perfusion,
    mental_status: c.mental_status,
  };
}
