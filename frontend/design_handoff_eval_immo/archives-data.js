/* eslint-disable */
// Éval Immo — Archives (completed/archived dossiers)

const ARCHIVES = [
  // 2026
  { id: "2026-0411", addr: "4218, rue Cartier",                city: "Plateau-Mont-Royal",      type: "Duplex",              year: 1923, area: 2410, value: 895000,  client: "Succession Bélanger",          mandate: "Successoral",  completedAt: "2026-05-18", reviewer: "M. Tremblay" },
  { id: "2026-0397", addr: "312, av. Bloomfield",              city: "Outremont",               type: "Maison unifamiliale", year: 1936, area: 1920, value: 1485000, client: "Cabinet Lévesque & Tremblay",  mandate: "Litige",       completedAt: "2026-05-12", reviewer: "M. Tremblay" },
  { id: "2026-0384", addr: "8654, rue Christophe-Colomb",      city: "Villeray",                type: "Triplex",             year: 1962, area: 2840, value: 1245000, client: "Investissements Bourassa",     mandate: "Acquisition",  completedAt: "2026-05-08", reviewer: "M. Tremblay" },
  { id: "2026-0362", addr: "1455, rue Drummond, app. 2204",    city: "Centre-ville",            type: "Condo",               year: 2021, area: 980,  value: 685000,  client: "RBC — refinancement",          mandate: "Refinancement", completedAt: "2026-04-28", reviewer: "M. Tremblay" },
  { id: "2026-0331", addr: "158, av. Lansdowne",               city: "Westmount",               type: "Maison unifamiliale", year: 1925, area: 2980, value: 1875000, client: "Famille Charest",              mandate: "Pré-vente",    completedAt: "2026-04-22", reviewer: "É. Lapointe" },
  { id: "2026-0318", addr: "44, ch. Belvédère",                city: "Westmount",               type: "Maison unifamiliale", year: 1908, area: 4280, value: 3450000, client: "Succession Bergeron",          mandate: "Successoral",  completedAt: "2026-04-04", reviewer: "M. Tremblay" },
  { id: "2026-0289", addr: "1180, rue de Bleury, app. 1808",   city: "Centre-ville",            type: "Condo",               year: 2018, area: 1240, value: 845000,  client: "Banque Nationale",             mandate: "Hypothécaire", completedAt: "2026-03-26", reviewer: "M. Tremblay" },
  { id: "2026-0254", addr: "5621, rue Waverly",                city: "Mile End",                type: "Triplex",             year: 1905, area: 3340, value: 1340000, client: "Coopérative d'habitation Plateau", mandate: "Acquisition", completedAt: "2026-03-12", reviewer: "É. Lapointe" },
  { id: "2026-0228", addr: "362, av. Roslyn",                  city: "Westmount",               type: "Maison unifamiliale", year: 1922, area: 3120, value: 2185000, client: "Étude Goldberg",               mandate: "Litige",       completedAt: "2026-02-28", reviewer: "M. Tremblay" },
  { id: "2026-0204", addr: "8124, rue de Lanaudière",          city: "Villeray",                type: "Triplex",             year: 1958, area: 2640, value: 875000,  client: "M. & Mme Lafontaine",          mandate: "Pré-vente",    completedAt: "2026-02-14", reviewer: "M. Tremblay" },
  { id: "2026-0182", addr: "78, av. Grosvenor",                city: "Westmount",               type: "Maison unifamiliale", year: 1931, area: 2840, value: 1985000, client: "Caisse Desjardins — Outremont", mandate: "Hypothécaire", completedAt: "2026-02-02", reviewer: "M. Tremblay" },
  { id: "2026-0156", addr: "2 Square Westmount, app. 802",     city: "Centre-ville",            type: "Condo",               year: 2019, area: 1480, value: 1085000, client: "Me Anne Beauchamp, notaire",   mandate: "Donation",     completedAt: "2026-01-22", reviewer: "É. Lapointe" },

  // 2025
  { id: "2025-0418", addr: "5412, av. de l'Esplanade",         city: "Mile End",                type: "Duplex",              year: 1918, area: 2580, value: 1085000, client: "Banque Royale",                mandate: "Hypothécaire", completedAt: "2025-12-19", reviewer: "M. Tremblay" },
  { id: "2025-0394", addr: "2100, rue Saint-Patrick",          city: "Pointe-Saint-Charles",    type: "Immeuble à revenus",  year: 1985, area: 5400, value: 2480000, client: "Société de portefeuille Lachine", mandate: "Acquisition", completedAt: "2025-12-04", reviewer: "M. Tremblay" },
  { id: "2025-0372", addr: "67, av. Wood",                     city: "Westmount",               type: "Maison unifamiliale", year: 1912, area: 3240, value: 2685000, client: "Étude Goldberg",               mandate: "Litige",       completedAt: "2025-11-22", reviewer: "É. Lapointe" },
  { id: "2025-0341", addr: "4892, av. du Parc",                city: "Mile End",                type: "Duplex",              year: 1908, area: 2150, value: 945000,  client: "Caisse Desjardins",            mandate: "Refinancement", completedAt: "2025-10-30", reviewer: "M. Tremblay" },
  { id: "2025-0318", addr: "220, ch. de la Côte-Sainte-Catherine", city: "Outremont",           type: "Maison unifamiliale", year: 1955, area: 2680, value: 1620000, client: "Me Anne Beauchamp",            mandate: "Donation",     completedAt: "2025-10-12", reviewer: "M. Tremblay" },
  { id: "2025-0287", addr: "5780, av. Coronation",             city: "Notre-Dame-de-Grâce",     type: "Maison unifamiliale", year: 1936, area: 1640, value: 810000,  client: "TD Canada Trust",              mandate: "Hypothécaire", completedAt: "2025-09-26", reviewer: "É. Lapointe" },
  { id: "2025-0259", addr: "412, av. Davaar",                  city: "Outremont",               type: "Maison unifamiliale", year: 1924, area: 1680, value: 1195000, client: "M. & Mme Fortier",             mandate: "Pré-vente",    completedAt: "2025-09-08", reviewer: "M. Tremblay" },
  { id: "2025-0233", addr: "1124, rue Marie-Anne E.",          city: "Plateau-Mont-Royal",      type: "Triplex",             year: 1912, area: 2980, value: 1095000, client: "Banque Nationale",             mandate: "Hypothécaire", completedAt: "2025-08-20", reviewer: "M. Tremblay" },

  // 2024
  { id: "2024-0381", addr: "198, av. Outremont",               city: "Outremont",               type: "Maison unifamiliale", year: 1936, area: 1720, value: 1180000, client: "Famille Charbonneau",          mandate: "Successoral",  completedAt: "2024-12-04", reviewer: "M. Tremblay" },
  { id: "2024-0342", addr: "3640, rue Wellington",             city: "Verdun",                  type: "Triplex",             year: 1925, area: 2840, value: 780000,  client: "Caisse Desjardins",            mandate: "Hypothécaire", completedAt: "2024-10-22", reviewer: "É. Lapointe" },
  { id: "2024-0298", addr: "6234, boul. Saint-Joseph E.",      city: "Rosemont",                type: "Triplex",             year: 1955, area: 2520, value: 858000,  client: "M. Pellerin",                  mandate: "Pré-vente",    completedAt: "2024-09-14", reviewer: "M. Tremblay" },
  { id: "2024-0241", addr: "1840, rue Wellington",             city: "Pointe-Saint-Charles",    type: "Triplex",             year: 1918, area: 2680, value: 720000,  client: "Investissements Bourassa",     mandate: "Acquisition",  completedAt: "2024-07-26", reviewer: "M. Tremblay" }
];

// Compute year + month label
function yearOf(s) { return s.slice(0,4); }
function fmtDate(s) {
  const months = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
  const [y, mo, d] = s.split("-").map(Number);
  return `${d} ${months[mo-1]} ${y}`;
}
ARCHIVES.forEach(a => { a.completedLabel = fmtDate(a.completedAt); a.year = yearOf(a.completedAt); });

window.ARCHIVES = ARCHIVES;
