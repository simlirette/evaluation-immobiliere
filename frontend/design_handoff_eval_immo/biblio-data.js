/* eslint-disable */
// Éval Immo — Bibliothèque (reference data)
//
// Four collections feed the four tabs:
//   VENTES      — comparable property sales
//   MARCHES     — neighbourhood market indicators (sparkline series)
//   COUTS       — construction cost references
//   TAUX        — capitalization rates by property type / segment

const VENTES = [
  // Outremont
  { id: "V-2026-118", addr: "198, av. Outremont",         district: "Outremont",          type: "Maison unifamiliale", year: 1936, area: 1720, lot: 4200, price: 1285000, soldAt: "2026-02-15", source: "JLR",       used: 4 },
  { id: "V-2026-104", addr: "87, av. Maplewood",          district: "Outremont",          type: "Maison unifamiliale", year: 1948, area: 1905, lot: 3900, price: 1410000, soldAt: "2026-01-28", source: "Centris",   used: 3 },
  { id: "V-2025-318", addr: "412, av. Davaar",            district: "Outremont",          type: "Maison unifamiliale", year: 1924, area: 1680, lot: 3650, price: 1195000, soldAt: "2025-11-12", source: "JLR",       used: 2 },
  { id: "V-2025-301", addr: "156, av. Bernard O.",        district: "Outremont",          type: "Duplex",              year: 1929, area: 2050, lot: 3200, price: 1525000, soldAt: "2025-09-04", source: "Centris",   used: 1 },
  { id: "V-2025-330", addr: "25, av. Vincent-d'Indy",     district: "Outremont",          type: "Maison unifamiliale", year: 1952, area: 1780, lot: 4100, price: 1350000, soldAt: "2025-12-08", source: "JLR",       used: 2 },

  // Plateau-Mont-Royal
  { id: "V-2026-098", addr: "4218, rue Cartier",          district: "Plateau-Mont-Royal", type: "Duplex",              year: 1923, area: 2410, lot: 2100, price: 895000,  soldAt: "2026-01-22", source: "Centris",   used: 1 },
  { id: "V-2025-289", addr: "3678, rue Saint-Hubert",     district: "Plateau-Mont-Royal", type: "Triplex",             year: 1908, area: 3120, lot: 2500, price: 1180000, soldAt: "2025-12-19", source: "JLR",       used: 0 },
  { id: "V-2025-271", addr: "4521, av. de l'Hôtel-de-Ville", district: "Plateau-Mont-Royal", type: "Duplex",           year: 1915, area: 2240, lot: 2050, price: 940000,  soldAt: "2025-10-30", source: "Centris",   used: 2 },
  { id: "V-2025-260", addr: "1124, rue Marie-Anne E.",    district: "Plateau-Mont-Royal", type: "Triplex",             year: 1912, area: 2980, lot: 2400, price: 1095000, soldAt: "2025-10-04", source: "JLR",       used: 1 },

  // Westmount
  { id: "V-2026-082", addr: "362, av. Roslyn",            district: "Westmount",          type: "Maison unifamiliale", year: 1922, area: 3120, lot: 5400, price: 2185000, soldAt: "2026-02-08", source: "Centris",   used: 1 },
  { id: "V-2025-310", addr: "44, ch. Belvédère",          district: "Westmount",          type: "Maison unifamiliale", year: 1908, area: 4280, lot: 7800, price: 3450000, soldAt: "2025-11-20", source: "JLR",       used: 0 },
  { id: "V-2025-244", addr: "78, av. Grosvenor",          district: "Westmount",          type: "Maison unifamiliale", year: 1931, area: 2840, lot: 4900, price: 1985000, soldAt: "2025-08-15", source: "Centris",   used: 1 },

  // Mile End
  { id: "V-2026-067", addr: "5412, av. de l'Esplanade",   district: "Mile End",           type: "Duplex",              year: 1918, area: 2580, lot: 2400, price: 1085000, soldAt: "2026-01-12", source: "Centris",   used: 3 },
  { id: "V-2025-298", addr: "5621, rue Waverly",          district: "Mile End",           type: "Triplex",             year: 1905, area: 3340, lot: 2600, price: 1340000, soldAt: "2025-11-04", source: "JLR",       used: 2 },
  { id: "V-2025-256", addr: "5180, rue Clark",            district: "Mile End",           type: "Duplex",              year: 1911, area: 2210, lot: 2200, price: 925000,  soldAt: "2025-09-18", source: "Centris",   used: 1 },

  // Villeray
  { id: "V-2025-285", addr: "8124, rue de Lanaudière",    district: "Villeray",           type: "Triplex",             year: 1958, area: 2640, lot: 2900, price: 875000,  soldAt: "2025-10-22", source: "JLR",       used: 2 },
  { id: "V-2025-228", addr: "7918, rue Saint-Denis",      district: "Villeray",           type: "Duplex",              year: 1942, area: 1980, lot: 2750, price: 690000,  soldAt: "2025-07-30", source: "Centris",   used: 0 },
  { id: "V-2025-321", addr: "8654, rue Christophe-Colomb",district: "Villeray",           type: "Triplex",             year: 1962, area: 2840, lot: 3000, price: 1245000, soldAt: "2025-12-02", source: "JLR",       used: 1 },

  // Rosemont
  { id: "V-2025-242", addr: "5680, 10e avenue",           district: "Rosemont",           type: "Duplex",              year: 1948, area: 1860, lot: 3200, price: 745000,  soldAt: "2025-08-08", source: "Centris",   used: 1 },
  { id: "V-2025-219", addr: "6234, boul. Saint-Joseph E.",district: "Rosemont",           type: "Triplex",             year: 1955, area: 2520, lot: 3100, price: 925000,  soldAt: "2025-07-14", source: "JLR",       used: 0 },

  // NDG
  { id: "V-2026-055", addr: "4218, av. Marcil",           district: "Notre-Dame-de-Grâce",type: "Duplex",              year: 1928, area: 2180, lot: 3100, price: 925000,  soldAt: "2026-01-02", source: "Centris",   used: 0 },
  { id: "V-2025-273", addr: "5780, av. Coronation",       district: "Notre-Dame-de-Grâce",type: "Maison unifamiliale", year: 1936, area: 1640, lot: 3400, price: 810000,  soldAt: "2025-10-12", source: "JLR",       used: 1 },

  // Verdun
  { id: "V-2025-238", addr: "3640, rue Wellington",       district: "Verdun",             type: "Triplex",             year: 1925, area: 2840, lot: 2500, price: 845000,  soldAt: "2025-08-02", source: "Centris",   used: 0 },
  { id: "V-2025-208", addr: "1180, rue de l'Église",      district: "Verdun",             type: "Duplex",              year: 1932, area: 1920, lot: 2400, price: 625000,  soldAt: "2025-06-25", source: "JLR",       used: 1 },

  // Pointe-Saint-Charles
  { id: "V-2025-261", addr: "2100, rue Saint-Patrick",    district: "Pointe-Saint-Charles", type: "Immeuble à revenus", year: 1985, area: 5400, lot: 4800, price: 2480000, soldAt: "2025-09-30", source: "JLR",       used: 1 },
  { id: "V-2025-225", addr: "1840, rue Wellington",       district: "Pointe-Saint-Charles", type: "Triplex",            year: 1918, area: 2680, lot: 2300, price: 780000,  soldAt: "2025-07-22", source: "Centris",   used: 0 },

  // Saint-Henri
  { id: "V-2025-280", addr: "4318, rue Notre-Dame O.",    district: "Saint-Henri",        type: "Duplex",              year: 1922, area: 2240, lot: 2400, price: 815000,  soldAt: "2025-10-26", source: "JLR",       used: 0 },

  // Centre-ville
  { id: "V-2026-038", addr: "1455, rue Drummond, #2204",  district: "Centre-ville",       type: "Condo",               year: 2021, area: 980,  lot: null, price: 685000,  soldAt: "2026-01-08", source: "Centris",   used: 1 },
  { id: "V-2025-294", addr: "1180, rue de Bleury, #1808", district: "Centre-ville",       type: "Condo",               year: 2018, area: 1240, lot: null, price: 845000,  soldAt: "2025-10-18", source: "JLR",       used: 0 },
  { id: "V-2025-264", addr: "2 Square Westmount, #802",   district: "Centre-ville",       type: "Condo",               year: 2019, area: 1480, lot: null, price: 1085000, soldAt: "2025-09-22", source: "Centris",   used: 2 }
];

// Helper to format date label
function ymdToLabel(s) {
  const m = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
  const [y, mo, d] = s.split("-").map(Number);
  return `${d} ${m[mo-1]} ${y}`;
}
VENTES.forEach(v => { v.soldLabel = ymdToLabel(v.soldAt); v.ppsf = v.area ? v.price / v.area : null; });

const DISTRICTS = [...new Set(VENTES.map(v => v.district))];
const TYPES     = [...new Set(VENTES.map(v => v.type))];
const SOURCES   = [...new Set(VENTES.map(v => v.source))];

// Pre-computed market indicators per neighbourhood (sparkline = 8 quarters)
const MARCHES = [
  { district: "Outremont",            median: 745, ppsfLow: 685, ppsfHigh: 820, dom: 22, ytd: +3.4, n: 38, trend: [682, 695, 708, 712, 720, 728, 736, 745] },
  { district: "Plateau-Mont-Royal",   median: 612, ppsfLow: 540, ppsfHigh: 705, dom: 28, ytd: +2.1, n: 92, trend: [580, 588, 592, 598, 604, 608, 610, 612] },
  { district: "Westmount",            median: 820, ppsfLow: 720, ppsfHigh: 1050, dom: 41, ytd: +4.8, n: 24, trend: [754, 768, 778, 790, 798, 808, 815, 820] },
  { district: "Mile End",             median: 558, ppsfLow: 488, ppsfHigh: 642, dom: 24, ytd: +2.6, n: 46, trend: [530, 535, 542, 546, 550, 552, 555, 558] },
  { district: "Villeray",             median: 412, ppsfLow: 365, ppsfHigh: 478, dom: 32, ytd: +1.8, n: 64, trend: [392, 396, 400, 403, 406, 408, 410, 412] },
  { district: "Rosemont",             median: 384, ppsfLow: 340, ppsfHigh: 442, dom: 35, ytd: +1.2, n: 78, trend: [370, 372, 375, 377, 380, 381, 382, 384] },
  { district: "Notre-Dame-de-Grâce",  median: 428, ppsfLow: 380, ppsfHigh: 502, dom: 30, ytd: +2.0, n: 52, trend: [402, 408, 412, 416, 420, 423, 425, 428] },
  { district: "Verdun",               median: 358, ppsfLow: 310, ppsfHigh: 410, dom: 26, ytd: +2.9, n: 58, trend: [332, 338, 342, 346, 350, 354, 356, 358] },
  { district: "Pointe-Saint-Charles", median: 392, ppsfLow: 340, ppsfHigh: 458, dom: 38, ytd: +1.4, n: 28, trend: [378, 380, 382, 385, 387, 389, 391, 392] },
  { district: "Saint-Henri",          median: 388, ppsfLow: 335, ppsfHigh: 452, dom: 34, ytd: +1.6, n: 34, trend: [370, 374, 378, 381, 384, 385, 387, 388] },
  { district: "Centre-ville",         median: 695, ppsfLow: 580, ppsfHigh: 880, dom: 52, ytd: -0.8, n: 114, trend: [710, 708, 705, 702, 700, 698, 696, 695] }
];

// Construction cost references (cost approach reference table)
const COUTS = [
  { category: "Maison unifamiliale", quality: "Économique",  rate: 218, unit: "$/pi²", source: "Marshall & Swift", updated: "2026-01" },
  { category: "Maison unifamiliale", quality: "Standard",    rate: 268, unit: "$/pi²", source: "Marshall & Swift", updated: "2026-01" },
  { category: "Maison unifamiliale", quality: "Supérieur",   rate: 342, unit: "$/pi²", source: "Marshall & Swift", updated: "2026-01" },
  { category: "Maison unifamiliale", quality: "Luxe",        rate: 485, unit: "$/pi²", source: "Marshall & Swift", updated: "2026-01" },
  { category: "Duplex",              quality: "Standard",    rate: 244, unit: "$/pi²", source: "APCHQ",           updated: "2025-Q4" },
  { category: "Duplex",              quality: "Supérieur",   rate: 312, unit: "$/pi²", source: "APCHQ",           updated: "2025-Q4" },
  { category: "Triplex",             quality: "Standard",    rate: 232, unit: "$/pi²", source: "APCHQ",           updated: "2025-Q4" },
  { category: "Triplex",             quality: "Supérieur",   rate: 296, unit: "$/pi²", source: "APCHQ",           updated: "2025-Q4" },
  { category: "Condo (tour)",        quality: "Standard",    rate: 358, unit: "$/pi²", source: "APCHQ",           updated: "2025-Q4" },
  { category: "Condo (tour)",        quality: "Supérieur",   rate: 432, unit: "$/pi²", source: "APCHQ",           updated: "2025-Q4" },
  { category: "Immeuble à revenus",  quality: "Locatif standard", rate: 218, unit: "$/pi²", source: "APCHQ",     updated: "2025-Q4" },
  { category: "Garage",              quality: "Détaché",     rate: 142, unit: "$/pi²", source: "Marshall & Swift", updated: "2026-01" },
  { category: "Sous-sol fini",       quality: "Standard",    rate: 98,  unit: "$/pi²", source: "Marshall & Swift", updated: "2026-01" }
];

// Cap rate references
const TAUX = [
  { segment: "Immeuble à revenus — résidentiel",            zone: "Centre", capLow: 4.2, capHigh: 5.1, vacancy: 1.8 },
  { segment: "Immeuble à revenus — résidentiel",            zone: "Périphérie", capLow: 5.0, capHigh: 6.2, vacancy: 2.4 },
  { segment: "Multilogements (6+ unités)",                  zone: "Centre", capLow: 4.0, capHigh: 4.8, vacancy: 1.5 },
  { segment: "Multilogements (6+ unités)",                  zone: "Périphérie", capLow: 4.8, capHigh: 5.9, vacancy: 2.2 },
  { segment: "Commercial — rez-de-chaussée commerçant",    zone: "Centre", capLow: 5.2, capHigh: 6.4, vacancy: 4.2 },
  { segment: "Commercial — rez-de-chaussée commerçant",    zone: "Plateau / Mile End", capLow: 4.8, capHigh: 5.9, vacancy: 3.5 },
  { segment: "Industriel léger",                            zone: "Anjou / Saint-Laurent", capLow: 5.8, capHigh: 6.9, vacancy: 2.8 },
  { segment: "Bureau — Classe A",                           zone: "Centre", capLow: 6.0, capHigh: 7.2, vacancy: 12.4 },
  { segment: "Bureau — Classe B",                           zone: "Centre", capLow: 6.8, capHigh: 8.0, vacancy: 16.8 },
  { segment: "Stationnement étagé",                         zone: "Centre", capLow: 5.5, capHigh: 6.5, vacancy: 6.0 }
];

window.VENTES   = VENTES;
window.MARCHES  = MARCHES;
window.COUTS    = COUTS;
window.TAUX     = TAUX;
window.DISTRICTS = DISTRICTS;
window.VENTE_TYPES = TYPES;
window.VENTE_SOURCES = SOURCES;
