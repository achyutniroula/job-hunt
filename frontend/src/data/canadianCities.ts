export interface CanadianCity {
  city: string;
  province: string;
  provinceCode: string;
}

export const CANADIAN_CITIES: CanadianCity[] = [
  { city: "Remote", province: "Canada", provinceCode: "CA" },

  // Alberta
  { city: "Calgary", province: "Alberta", provinceCode: "AB" },
  { city: "Edmonton", province: "Alberta", provinceCode: "AB" },
  { city: "Fort McMurray", province: "Alberta", provinceCode: "AB" },
  { city: "Lethbridge", province: "Alberta", provinceCode: "AB" },
  { city: "Medicine Hat", province: "Alberta", provinceCode: "AB" },
  { city: "Red Deer", province: "Alberta", provinceCode: "AB" },

  // British Columbia
  { city: "Burnaby", province: "British Columbia", provinceCode: "BC" },
  { city: "Kelowna", province: "British Columbia", provinceCode: "BC" },
  { city: "Richmond", province: "British Columbia", provinceCode: "BC" },
  { city: "Surrey", province: "British Columbia", provinceCode: "BC" },
  { city: "Vancouver", province: "British Columbia", provinceCode: "BC" },
  { city: "Victoria", province: "British Columbia", provinceCode: "BC" },

  // Manitoba
  { city: "Brandon", province: "Manitoba", provinceCode: "MB" },
  { city: "Steinbach", province: "Manitoba", provinceCode: "MB" },
  { city: "Thompson", province: "Manitoba", provinceCode: "MB" },
  { city: "Winnipeg", province: "Manitoba", provinceCode: "MB" },

  // New Brunswick
  { city: "Fredericton", province: "New Brunswick", provinceCode: "NB" },
  { city: "Moncton", province: "New Brunswick", provinceCode: "NB" },
  { city: "Saint John", province: "New Brunswick", provinceCode: "NB" },

  // Newfoundland and Labrador
  { city: "Corner Brook", province: "Newfoundland and Labrador", provinceCode: "NL" },
  { city: "Gander", province: "Newfoundland and Labrador", provinceCode: "NL" },
  { city: "Mount Pearl", province: "Newfoundland and Labrador", provinceCode: "NL" },
  { city: "St. John's", province: "Newfoundland and Labrador", provinceCode: "NL" },

  // Northwest Territories
  { city: "Hay River", province: "Northwest Territories", provinceCode: "NT" },
  { city: "Inuvik", province: "Northwest Territories", provinceCode: "NT" },
  { city: "Yellowknife", province: "Northwest Territories", provinceCode: "NT" },

  // Nova Scotia
  { city: "Cape Breton", province: "Nova Scotia", provinceCode: "NS" },
  { city: "Dartmouth", province: "Nova Scotia", provinceCode: "NS" },
  { city: "Halifax", province: "Nova Scotia", provinceCode: "NS" },
  { city: "Truro", province: "Nova Scotia", provinceCode: "NS" },

  // Nunavut
  { city: "Arviat", province: "Nunavut", provinceCode: "NU" },
  { city: "Iqaluit", province: "Nunavut", provinceCode: "NU" },
  { city: "Rankin Inlet", province: "Nunavut", provinceCode: "NU" },

  // Ontario
  { city: "Brampton", province: "Ontario", provinceCode: "ON" },
  { city: "Hamilton", province: "Ontario", provinceCode: "ON" },
  { city: "Kingston", province: "Ontario", provinceCode: "ON" },
  { city: "London", province: "Ontario", provinceCode: "ON" },
  { city: "Mississauga", province: "Ontario", provinceCode: "ON" },
  { city: "Ottawa", province: "Ontario", provinceCode: "ON" },
  { city: "Toronto", province: "Ontario", provinceCode: "ON" },
  { city: "Waterloo", province: "Ontario", provinceCode: "ON" },

  // Prince Edward Island
  { city: "Charlottetown", province: "Prince Edward Island", provinceCode: "PE" },
  { city: "Summerside", province: "Prince Edward Island", provinceCode: "PE" },

  // Quebec
  { city: "Gatineau", province: "Quebec", provinceCode: "QC" },
  { city: "Laval", province: "Quebec", provinceCode: "QC" },
  { city: "Longueuil", province: "Quebec", provinceCode: "QC" },
  { city: "Montreal", province: "Quebec", provinceCode: "QC" },
  { city: "Quebec City", province: "Quebec", provinceCode: "QC" },
  { city: "Saguenay", province: "Quebec", provinceCode: "QC" },
  { city: "Sherbrooke", province: "Quebec", provinceCode: "QC" },

  // Saskatchewan
  { city: "Moose Jaw", province: "Saskatchewan", provinceCode: "SK" },
  { city: "Prince Albert", province: "Saskatchewan", provinceCode: "SK" },
  { city: "Regina", province: "Saskatchewan", provinceCode: "SK" },
  { city: "Saskatoon", province: "Saskatchewan", provinceCode: "SK" },

  // Yukon
  { city: "Dawson City", province: "Yukon", provinceCode: "YT" },
  { city: "Watson Lake", province: "Yukon", provinceCode: "YT" },
  { city: "Whitehorse", province: "Yukon", provinceCode: "YT" },
];

export const PROVINCES = Array.from(
  new Map(CANADIAN_CITIES.map((c) => [c.province, c.provinceCode])).entries()
).map(([province, provinceCode]) => ({ province, provinceCode }));
