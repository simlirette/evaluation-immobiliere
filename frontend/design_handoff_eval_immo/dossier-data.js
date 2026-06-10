/* eslint-disable */
// Éval Immo — dossier detail extras (comparables, activity, documents)

const DOSSIER_DETAILS = {
  "2026-0418": {
    lotArea: 4820,
    stories: 2,
    bedrooms: 4,
    bathrooms: 2,
    parking: "Garage attaché (1)",
    yearReno: 2009,
    cadastral: "1 870 421",
    municipalRoll: 1185000,
    notes:
      "Maison de prestige sur lot d'angle, fenestration d'origine restaurée, " +
      "toiture refaite 2019. Quartier mature, valeurs en hausse soutenue.",
    contact: {
      org: "Banque Nationale du Canada",
      person: "Mtre. Sylvie Gagné",
      role: "Notaire — service hypothécaire",
      phone: "514 394-8421",
      email: "sgagne@bnc.ca"
    },
    comps: [
      {
        addr: "198, av. Outremont",
        soldAt: "2026-02-15",
        soldLabel: "15 fév. 2026",
        area: 1720,
        price: 1285000,
        distance: 0.4,
        adj: -2.1,
        note: "Similaire — réno 2018"
      },
      {
        addr: "87, av. Maplewood",
        soldAt: "2026-01-28",
        soldLabel: "28 janv. 2026",
        area: 1905,
        price: 1410000,
        distance: 0.6,
        adj: 1.4,
        note: "Lot plus petit"
      },
      {
        addr: "412, av. Davaar",
        soldAt: "2025-11-12",
        soldLabel: "12 nov. 2025",
        area: 1680,
        price: 1195000,
        distance: 0.8,
        adj: -4.8,
        note: "Sans garage"
      },
      {
        addr: "156, av. Bernard O.",
        soldAt: "2025-09-04",
        soldLabel: "4 sept. 2025",
        area: 2050,
        price: 1525000,
        distance: 1.1,
        adj: 3.2,
        note: "Coin commerçant"
      },
      {
        addr: "25, av. Vincent-d'Indy",
        soldAt: "2025-12-08",
        soldLabel: "8 déc. 2025",
        area: 1780,
        price: 1350000,
        distance: 0.9,
        adj: 0.6,
        note: "État comparable"
      }
    ],
    activity: [
      { who: "Maxime Tremblay",  what: "a ajouté 2 comparables", when: "il y a 2 h" },
      { who: "Maxime Tremblay",  what: "a confirmé le mandat hypothécaire", when: "hier" },
      { who: "Système",          what: "registre OEAQ synchronisé", when: "il y a 3 jours" },
      { who: "Mtre. S. Gagné",   what: "a ouvert le dossier", when: "il y a 5 jours" },
      { who: "Maxime Tremblay",  what: "a importé les données du rôle", when: "12 mai 2026" }
    ],
    documents: [
      { name: "Mandat signé.pdf",        size: "184 Ko", when: "12 mai",  type: "pdf" },
      { name: "Photos extérieures.zip",  size: "8.2 Mo", when: "18 mai",  type: "zip" },
      { name: "Photos intérieures.zip",  size: "12 Mo",  when: "20 mai",  type: "zip" },
      { name: "Rôle d'évaluation 2024.csv", size: "12 Ko", when: "12 mai", type: "csv" },
      { name: "Plan d'arpentage 2009.pdf", size: "1.4 Mo", when: "14 mai", type: "pdf" }
    ]
  }
};

window.DOSSIER_DETAILS = DOSSIER_DETAILS;
