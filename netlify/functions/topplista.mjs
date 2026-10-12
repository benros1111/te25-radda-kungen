// Topplistan. Körs på Netlify, inte i webbläsaren.
// GET  /api/topplista  -> de 10 bästa
// POST /api/topplista  -> spara ett nytt resultat { namn, mynt, svar }
import { getStore } from "@netlify/blobs";

const MULTIPLIKATOR = { latt: 1, medel: 1.5, svar: 2 }; // svårare = fler poäng
const MAX_MYNT = 250;   // fler mynt än så finns inte i spelet
const SPARA_ANTAL = 50; // så många resultat sparas
const VISA_ANTAL = 10;  // så många visas

const svar = (data, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { "content-type": "application/json", "cache-control": "no-store" }
});

export default async (req) => {
  const store = getStore({ name: "topplista", consistency: "strong" });
  const lista = (await store.get("lista", { type: "json" })) || [];

  if (req.method === "GET") return svar(lista.slice(0, VISA_ANTAL));

  if (req.method === "POST") {
    let data;
    try { data = await req.json(); } catch { return svar({ fel: "Fel data" }, 400); }

    // Namn: bara bokstäver, siffror och mellanslag, max 12 tecken
    const namn = String(data.namn || "").replace(/[^A-Za-zÅÄÖåäöÉé0-9 ]/g, "").trim().slice(0, 12);
    const mynt = Math.floor(Number(data.mynt));
    if (!namn) return svar({ fel: "Skriv ett namn" }, 400);
    if (!(data.svar in MULTIPLIKATOR)) return svar({ fel: "Fel svårighet" }, 400);
    if (!Number.isFinite(mynt) || mynt < 0 || mynt > MAX_MYNT) return svar({ fel: "Fel antal mynt" }, 400);

    const nytt = {
      namn, mynt, svar: data.svar,
      poang: Math.round(mynt * MULTIPLIKATOR[data.svar]),
      tid: Date.now()
    };
    lista.push(nytt);
    lista.sort((a, b) => b.poang - a.poang || a.tid - b.tid);
    const sparad = lista.slice(0, SPARA_ANTAL);
    await store.setJSON("lista", sparad);

    const plats = sparad.indexOf(nytt) + 1; // 0 = kom inte med
    return svar({ plats, lista: sparad.slice(0, VISA_ANTAL) });
  }

  return svar({ fel: "Fel metod" }, 405);
};

export const config = { path: "/api/topplista" };
