/* ============================================================
   app.js — Indeed Scraper dashboard
   ============================================================ */
'use strict';

// ── Data ─────────────────────────────────────────────────────

const DEFAULT_IT_KEYWORDS = [
  'software engineer', 'developer', 'backend developer', 'frontend developer',
  'full-stack developer', 'data engineer', 'cloud engineer', 'DevOps',
  'IT support', 'QA tester', 'cybersecurity',
];

// Single source of truth — all official Canadian cities with coordinates + province.
// PROVINCE_CITIES and the city datalist are both derived from this array.
const CITY_COORDS = [
  // ── Ontario (52 cities) ─────────────────────────────────────
  {name:'Toronto, ON',              province:'Ontario',               lat:43.6532,  lng:-79.3832},
  {name:'Ottawa, ON',               province:'Ontario',               lat:45.4215,  lng:-75.6972},
  {name:'Mississauga, ON',          province:'Ontario',               lat:43.5890,  lng:-79.6441},
  {name:'Brampton, ON',             province:'Ontario',               lat:43.7315,  lng:-79.7624},
  {name:'Hamilton, ON',             province:'Ontario',               lat:43.2557,  lng:-79.8711},
  {name:'London, ON',               province:'Ontario',               lat:42.9849,  lng:-81.2453},
  {name:'Markham, ON',              province:'Ontario',               lat:43.8561,  lng:-79.3370},
  {name:'Vaughan, ON',              province:'Ontario',               lat:43.8361,  lng:-79.4985},
  {name:'Kitchener, ON',            province:'Ontario',               lat:43.4516,  lng:-80.4925},
  {name:'Windsor, ON',              province:'Ontario',               lat:42.3149,  lng:-83.0364},
  {name:'Richmond Hill, ON',        province:'Ontario',               lat:43.8828,  lng:-79.4403},
  {name:'Oakville, ON',             province:'Ontario',               lat:43.4675,  lng:-79.6877},
  {name:'Burlington, ON',           province:'Ontario',               lat:43.3255,  lng:-79.7990},
  {name:'Greater Sudbury, ON',      province:'Ontario',               lat:46.4921,  lng:-80.9930},
  {name:'Oshawa, ON',               province:'Ontario',               lat:43.8971,  lng:-78.8658},
  {name:'Barrie, ON',               province:'Ontario',               lat:44.3894,  lng:-79.6903},
  {name:'St. Catharines, ON',       province:'Ontario',               lat:43.1594,  lng:-79.2469},
  {name:'Cambridge, ON',            province:'Ontario',               lat:43.3616,  lng:-80.3144},
  {name:'Kingston, ON',             province:'Ontario',               lat:44.2312,  lng:-76.4860},
  {name:'Guelph, ON',               province:'Ontario',               lat:43.5448,  lng:-80.2482},
  {name:'Thunder Bay, ON',          province:'Ontario',               lat:48.3809,  lng:-89.2477},
  {name:'Waterloo, ON',             province:'Ontario',               lat:43.4668,  lng:-80.5164},
  {name:'Brantford, ON',            province:'Ontario',               lat:43.1394,  lng:-80.2644},
  {name:'Ajax, ON',                 province:'Ontario',               lat:43.8509,  lng:-79.0205},
  {name:'Whitby, ON',               province:'Ontario',               lat:43.8975,  lng:-78.9429},
  {name:'Pickering, ON',            province:'Ontario',               lat:43.8354,  lng:-79.0894},
  {name:'Niagara Falls, ON',        province:'Ontario',               lat:43.1069,  lng:-79.0819},
  {name:'Peterborough, ON',         province:'Ontario',               lat:44.3091,  lng:-78.3197},
  {name:'Sault Ste. Marie, ON',     province:'Ontario',               lat:46.5218,  lng:-84.3461},
  {name:'Kawartha Lakes, ON',       province:'Ontario',               lat:44.3519,  lng:-78.7439},
  {name:'Sarnia, ON',               province:'Ontario',               lat:42.9995,  lng:-82.3090},
  {name:'Welland, ON',              province:'Ontario',               lat:42.9923,  lng:-79.2484},
  {name:'North Bay, ON',            province:'Ontario',               lat:46.3091,  lng:-79.4608},
  {name:'Belleville, ON',           province:'Ontario',               lat:44.1628,  lng:-77.3832},
  {name:'Timmins, ON',              province:'Ontario',               lat:48.4758,  lng:-81.3305},
  {name:'Cornwall, ON',             province:'Ontario',               lat:45.0275,  lng:-74.7295},
  {name:'Stratford, ON',            province:'Ontario',               lat:43.3708,  lng:-80.9822},
  {name:'Quinte West, ON',          province:'Ontario',               lat:44.1956,  lng:-77.5632},
  {name:'Woodstock, ON',            province:'Ontario',               lat:43.1307,  lng:-80.7467},
  {name:'Norfolk County, ON',       province:'Ontario',               lat:42.8453,  lng:-80.3883},
  {name:'Clarence-Rockland, ON',    province:'Ontario',               lat:45.4833,  lng:-75.2000},
  {name:'Brockville, ON',           province:'Ontario',               lat:44.5895,  lng:-75.6879},
  {name:'St. Thomas, ON',           province:'Ontario',               lat:42.7762,  lng:-81.1985},
  {name:'Elliot Lake, ON',          province:'Ontario',               lat:46.3838,  lng:-82.6558},
  {name:'Temiskaming Shores, ON',   province:'Ontario',               lat:47.5150,  lng:-79.6823},
  {name:'Kenora, ON',               province:'Ontario',               lat:49.7662,  lng:-94.4894},
  {name:'Dryden, ON',               province:'Ontario',               lat:49.7831,  lng:-92.8378},
  {name:'Owen Sound, ON',           province:'Ontario',               lat:44.5670,  lng:-80.9393},
  {name:'Orillia, ON',              province:'Ontario',               lat:44.5994,  lng:-79.4192},
  {name:'Pembroke, ON',             province:'Ontario',               lat:45.8263,  lng:-77.1139},
  {name:'Port Colborne, ON',        province:'Ontario',               lat:42.8869,  lng:-79.2517},
  {name:'Thorold, ON',              province:'Ontario',               lat:43.1183,  lng:-79.1974},
  // ── British Columbia (30 cities) ────────────────────────────
  {name:'Vancouver, BC',            province:'British Columbia',      lat:49.2827,  lng:-123.1207},
  {name:'Surrey, BC',               province:'British Columbia',      lat:49.1913,  lng:-122.8490},
  {name:'Burnaby, BC',              province:'British Columbia',      lat:49.2488,  lng:-122.9805},
  {name:'Richmond, BC',             province:'British Columbia',      lat:49.1666,  lng:-123.1336},
  {name:'Kelowna, BC',              province:'British Columbia',      lat:49.8880,  lng:-119.4960},
  {name:'Abbotsford, BC',           province:'British Columbia',      lat:49.0504,  lng:-122.3045},
  {name:'Coquitlam, BC',            province:'British Columbia',      lat:49.2838,  lng:-122.7932},
  {name:'Langley, BC',              province:'British Columbia',      lat:49.1044,  lng:-122.6602},
  {name:'Saanich, BC',              province:'British Columbia',      lat:48.4839,  lng:-123.3815},
  {name:'Delta, BC',                province:'British Columbia',      lat:49.0847,  lng:-123.0586},
  {name:'Kamloops, BC',             province:'British Columbia',      lat:50.6745,  lng:-120.3273},
  {name:'Nanaimo, BC',              province:'British Columbia',      lat:49.1659,  lng:-123.9401},
  {name:'Victoria, BC',             province:'British Columbia',      lat:48.4284,  lng:-123.3656},
  {name:'Chilliwack, BC',           province:'British Columbia',      lat:49.1579,  lng:-121.9514},
  {name:'Prince George, BC',        province:'British Columbia',      lat:53.9171,  lng:-122.7497},
  {name:'Vernon, BC',               province:'British Columbia',      lat:50.2671,  lng:-119.2720},
  {name:'Penticton, BC',            province:'British Columbia',      lat:49.4991,  lng:-119.5937},
  {name:'Maple Ridge, BC',          province:'British Columbia',      lat:49.2193,  lng:-122.5984},
  {name:'New Westminster, BC',      province:'British Columbia',      lat:49.2069,  lng:-122.9111},
  {name:'North Vancouver, BC',      province:'British Columbia',      lat:49.3198,  lng:-123.0724},
  {name:'West Vancouver, BC',       province:'British Columbia',      lat:49.3663,  lng:-123.1597},
  {name:'Port Coquitlam, BC',       province:'British Columbia',      lat:49.2624,  lng:-122.7813},
  {name:'Port Moody, BC',           province:'British Columbia',      lat:49.2838,  lng:-122.8322},
  {name:'Langford, BC',             province:'British Columbia',      lat:48.4503,  lng:-123.5026},
  {name:'Campbell River, BC',       province:'British Columbia',      lat:50.0163,  lng:-125.2445},
  {name:'Fort St. John, BC',        province:'British Columbia',      lat:56.2518,  lng:-120.8519},
  {name:'Cranbrook, BC',            province:'British Columbia',      lat:49.5124,  lng:-115.7697},
  {name:'Prince Rupert, BC',        province:'British Columbia',      lat:54.3150,  lng:-130.3208},
  {name:'Courtenay, BC',            province:'British Columbia',      lat:49.6869,  lng:-124.9938},
  {name:'Terrace, BC',              province:'British Columbia',      lat:54.5164,  lng:-128.5986},
  // ── Alberta (24 cities) ─────────────────────────────────────
  {name:'Calgary, AB',              province:'Alberta',               lat:51.0447,  lng:-114.0719},
  {name:'Edmonton, AB',             province:'Alberta',               lat:53.5461,  lng:-113.4938},
  {name:'Red Deer, AB',             province:'Alberta',               lat:52.2681,  lng:-113.8112},
  {name:'Lethbridge, AB',           province:'Alberta',               lat:49.6956,  lng:-112.8451},
  {name:'St. Albert, AB',           province:'Alberta',               lat:53.6303,  lng:-113.6254},
  {name:'Medicine Hat, AB',         province:'Alberta',               lat:50.0405,  lng:-110.6764},
  {name:'Grande Prairie, AB',       province:'Alberta',               lat:55.1707,  lng:-118.7884},
  {name:'Airdrie, AB',              province:'Alberta',               lat:51.2917,  lng:-114.0144},
  {name:'Spruce Grove, AB',         province:'Alberta',               lat:53.5448,  lng:-113.9007},
  {name:'Leduc, AB',                province:'Alberta',               lat:53.2597,  lng:-113.5497},
  {name:'Fort Saskatchewan, AB',    province:'Alberta',               lat:53.7126,  lng:-113.0132},
  {name:'Beaumont, AB',             province:'Alberta',               lat:53.3567,  lng:-113.4163},
  {name:'Lloydminster, AB',         province:'Alberta',               lat:53.2784,  lng:-110.0054},
  {name:'Chestermere, AB',          province:'Alberta',               lat:51.0506,  lng:-113.8235},
  {name:'Lacombe, AB',              province:'Alberta',               lat:52.4680,  lng:-113.7378},
  {name:'Camrose, AB',              province:'Alberta',               lat:53.0175,  lng:-112.8268},
  {name:'Wetaskiwin, AB',           province:'Alberta',               lat:52.9691,  lng:-113.3769},
  {name:'Brooks, AB',               province:'Alberta',               lat:50.5642,  lng:-111.8992},
  {name:'Cold Lake, AB',            province:'Alberta',               lat:54.4641,  lng:-110.1774},
  {name:'Hinton, AB',               province:'Alberta',               lat:53.4103,  lng:-117.5638},
  {name:'Okotoks, AB',              province:'Alberta',               lat:50.7264,  lng:-113.9750},
  {name:'Cochrane, AB',             province:'Alberta',               lat:51.1897,  lng:-114.4683},
  {name:'Strathmore, AB',           province:'Alberta',               lat:51.0381,  lng:-113.4005},
  {name:'Fort McMurray, AB',        province:'Alberta',               lat:56.7265,  lng:-111.3803},
  // ── Quebec (30 cities) ──────────────────────────────────────
  {name:'Montreal, QC',             province:'Quebec',                lat:45.5017,  lng:-73.5673},
  {name:'Quebec City, QC',          province:'Quebec',                lat:46.8139,  lng:-71.2080},
  {name:'Laval, QC',                province:'Quebec',                lat:45.5736,  lng:-73.6930},
  {name:'Gatineau, QC',             province:'Quebec',                lat:45.4765,  lng:-75.7013},
  {name:'Longueuil, QC',            province:'Quebec',                lat:45.5312,  lng:-73.5185},
  {name:'Sherbrooke, QC',           province:'Quebec',                lat:45.4042,  lng:-71.8929},
  {name:'Saguenay, QC',             province:'Quebec',                lat:48.4279,  lng:-71.0663},
  {name:'Lévis, QC',                province:'Quebec',                lat:46.7027,  lng:-71.2380},
  {name:'Trois-Rivières, QC',       province:'Quebec',                lat:46.3432,  lng:-72.5439},
  {name:'Terrebonne, QC',           province:'Quebec',                lat:45.7022,  lng:-73.6441},
  {name:'Saint-Jean-sur-Richelieu, QC', province:'Quebec',           lat:45.3080,  lng:-73.2618},
  {name:'Repentigny, QC',           province:'Quebec',                lat:45.7422,  lng:-73.4615},
  {name:'Brossard, QC',             province:'Quebec',                lat:45.4581,  lng:-73.4588},
  {name:'Drummondville, QC',        province:'Quebec',                lat:45.8836,  lng:-72.4822},
  {name:'Saint-Jérôme, QC',         province:'Quebec',                lat:45.7773,  lng:-74.0028},
  {name:'Granby, QC',               province:'Quebec',                lat:45.4000,  lng:-72.7333},
  {name:'Blainville, QC',           province:'Quebec',                lat:45.6724,  lng:-73.8817},
  {name:'Mirabel, QC',              province:'Quebec',                lat:45.6502,  lng:-74.0876},
  {name:'Shawinigan, QC',           province:'Quebec',                lat:46.5702,  lng:-72.7468},
  {name:'Dollard-des-Ormeaux, QC',  province:'Quebec',                lat:45.4947,  lng:-73.8124},
  {name:'Châteauguay, QC',          province:'Quebec',                lat:45.3809,  lng:-73.7504},
  {name:'Saint-Hyacinthe, QC',      province:'Quebec',                lat:45.6270,  lng:-72.9558},
  {name:'Mascouche, QC',            province:'Quebec',                lat:45.7487,  lng:-73.6028},
  {name:'Rimouski, QC',             province:'Quebec',                lat:48.4476,  lng:-68.5232},
  {name:'Victoriaville, QC',        province:'Quebec',                lat:46.0594,  lng:-71.9645},
  {name:'Rouyn-Noranda, QC',        province:'Quebec',                lat:48.2363,  lng:-79.0162},
  {name:'Sept-Îles, QC',            province:'Quebec',                lat:50.2033,  lng:-66.3913},
  {name:'Alma, QC',                 province:'Quebec',                lat:48.5501,  lng:-71.6535},
  {name:'Joliette, QC',             province:'Quebec',                lat:46.0217,  lng:-73.4446},
  {name:'Saint-Georges, QC',        province:'Quebec',                lat:46.1177,  lng:-70.6696},
  // ── Manitoba (11 cities) ────────────────────────────────────
  {name:'Winnipeg, MB',             province:'Manitoba',              lat:49.8951,  lng:-97.1384},
  {name:'Brandon, MB',              province:'Manitoba',              lat:49.8483,  lng:-99.9500},
  {name:'Steinbach, MB',            province:'Manitoba',              lat:49.5257,  lng:-96.6844},
  {name:'Thompson, MB',             province:'Manitoba',              lat:55.7435,  lng:-97.8558},
  {name:'Portage la Prairie, MB',   province:'Manitoba',              lat:49.9726,  lng:-98.2926},
  {name:'Winkler, MB',              province:'Manitoba',              lat:49.1825,  lng:-97.9417},
  {name:'Selkirk, MB',              province:'Manitoba',              lat:50.1440,  lng:-96.8835},
  {name:'Morden, MB',               province:'Manitoba',              lat:49.1926,  lng:-98.0841},
  {name:'Dauphin, MB',              province:'Manitoba',              lat:51.1487,  lng:-100.0543},
  {name:'The Pas, MB',              province:'Manitoba',              lat:53.8245,  lng:-101.2398},
  {name:'Flin Flon, MB',            province:'Manitoba',              lat:54.7735,  lng:-101.8617},
  // ── Saskatchewan (12 cities) ────────────────────────────────
  {name:'Saskatoon, SK',            province:'Saskatchewan',          lat:52.1332,  lng:-106.6700},
  {name:'Regina, SK',               province:'Saskatchewan',          lat:50.4452,  lng:-104.6189},
  {name:'Prince Albert, SK',        province:'Saskatchewan',          lat:53.2033,  lng:-105.7531},
  {name:'Moose Jaw, SK',            province:'Saskatchewan',          lat:50.3934,  lng:-105.5519},
  {name:'Swift Current, SK',        province:'Saskatchewan',          lat:50.2859,  lng:-107.7978},
  {name:'Yorkton, SK',              province:'Saskatchewan',          lat:51.2139,  lng:-102.4629},
  {name:'North Battleford, SK',     province:'Saskatchewan',          lat:52.7767,  lng:-108.2862},
  {name:'Estevan, SK',              province:'Saskatchewan',          lat:49.1395,  lng:-102.9868},
  {name:'Weyburn, SK',              province:'Saskatchewan',          lat:49.6617,  lng:-103.8527},
  {name:'Melfort, SK',              province:'Saskatchewan',          lat:52.8620,  lng:-104.6090},
  {name:'Humboldt, SK',             province:'Saskatchewan',          lat:52.2006,  lng:-105.1223},
  {name:'Lloydminster, SK',         province:'Saskatchewan',          lat:53.2784,  lng:-110.0054},
  // ── Nova Scotia (10 cities) ─────────────────────────────────
  {name:'Halifax, NS',              province:'Nova Scotia',           lat:44.6488,  lng:-63.5752},
  {name:'Cape Breton, NS',          province:'Nova Scotia',           lat:46.1368,  lng:-60.1942},
  {name:'Truro, NS',                province:'Nova Scotia',           lat:45.3651,  lng:-63.2814},
  {name:'New Glasgow, NS',          province:'Nova Scotia',           lat:45.5854,  lng:-62.6467},
  {name:'Amherst, NS',              province:'Nova Scotia',           lat:45.8290,  lng:-64.2162},
  {name:'Kentville, NS',            province:'Nova Scotia',           lat:45.0762,  lng:-64.4978},
  {name:'Yarmouth, NS',             province:'Nova Scotia',           lat:43.8371,  lng:-66.1171},
  {name:'Bridgewater, NS',          province:'Nova Scotia',           lat:44.3761,  lng:-64.5214},
  {name:'Antigonish, NS',           province:'Nova Scotia',           lat:45.6233,  lng:-61.9959},
  {name:'Sydney, NS',               province:'Nova Scotia',           lat:46.1368,  lng:-60.1942},
  // ── New Brunswick (10 cities) ───────────────────────────────
  {name:'Moncton, NB',              province:'New Brunswick',         lat:46.0878,  lng:-64.7782},
  {name:'Saint John, NB',           province:'New Brunswick',         lat:45.2733,  lng:-66.0633},
  {name:'Fredericton, NB',          province:'New Brunswick',         lat:45.9636,  lng:-66.6431},
  {name:'Miramichi, NB',            province:'New Brunswick',         lat:47.0236,  lng:-65.4986},
  {name:'Edmundston, NB',           province:'New Brunswick',         lat:47.3736,  lng:-68.3237},
  {name:'Bathurst, NB',             province:'New Brunswick',         lat:47.6168,  lng:-65.6535},
  {name:'Campbellton, NB',          province:'New Brunswick',         lat:48.0060,  lng:-66.6730},
  {name:'Dieppe, NB',               province:'New Brunswick',         lat:46.0870,  lng:-64.7253},
  {name:'Riverview, NB',            province:'New Brunswick',         lat:46.0602,  lng:-64.7998},
  {name:'Oromocto, NB',             province:'New Brunswick',         lat:45.8477,  lng:-66.4800},
  // ── Newfoundland & Labrador (10 cities) ─────────────────────
  {name:"St. John's, NL",           province:'Newfoundland & Labrador', lat:47.5615, lng:-52.7126},
  {name:'Corner Brook, NL',         province:'Newfoundland & Labrador', lat:48.9500, lng:-57.9333},
  {name:'Mount Pearl, NL',          province:'Newfoundland & Labrador', lat:47.5199, lng:-52.8058},
  {name:'Conception Bay South, NL', province:'Newfoundland & Labrador', lat:47.5127, lng:-53.0283},
  {name:'Grand Falls-Windsor, NL',  province:'Newfoundland & Labrador', lat:48.9302, lng:-55.6631},
  {name:'Paradise, NL',             province:'Newfoundland & Labrador', lat:47.5324, lng:-52.8690},
  {name:'Happy Valley-Goose Bay, NL',province:'Newfoundland & Labrador',lat:53.3002, lng:-60.4211},
  {name:'Gander, NL',               province:'Newfoundland & Labrador', lat:48.9544, lng:-54.6079},
  {name:'Labrador City, NL',        province:'Newfoundland & Labrador', lat:52.9441, lng:-66.9092},
  {name:'Marystown, NL',            province:'Newfoundland & Labrador', lat:47.1674, lng:-55.1654},
  // ── Prince Edward Island (4 cities) ─────────────────────────
  {name:'Charlottetown, PE',        province:'Prince Edward Island',  lat:46.2382,  lng:-63.1311},
  {name:'Summerside, PE',           province:'Prince Edward Island',  lat:46.3970,  lng:-63.7891},
  {name:'Stratford, PE',            province:'Prince Edward Island',  lat:46.2214,  lng:-63.0870},
  {name:'Cornwall, PE',             province:'Prince Edward Island',  lat:46.2327,  lng:-63.2197},
];

// Derive PROVINCE_CITIES from CITY_COORDS (single source of truth)
const PROVINCE_CITIES = {};
CITY_COORDS.forEach(c => {
  if (!PROVINCE_CITIES[c.province]) PROVINCE_CITIES[c.province] = [];
  PROVINCE_CITIES[c.province].push(c.name);
});

// ── State ─────────────────────────────────────────────────────
let allJobs     = [];
let displayJobs = [];
let currentPage = 1;
const PAGE_SIZE = 200;
let sortCol = '', sortDir = 'asc';
let filterRemote = false, filterSalary = false;

let scrapeQueue    = [];
let queueRunning   = false;
let stopRequested  = false;
let currentJobId   = null;

let itKeywords = [...DEFAULT_IT_KEYWORDS];
let locMode    = 'city';   // 'city' | 'province'

let filterLevel = '';     // '' | 'intern' | 'junior' | 'mid' | 'senior' | 'lead' | 'principal' | 'manager' | 'executive' | 'unknown'
let filterIT    = false;  // true = show only is_it_job===true
let _backendLastCount = 0; // resets per city — tracks backend job count so incremental fetch works across multi-city queues

// ── API ───────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = { method, headers: {'Content-Type':'application/json'} };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch('/api' + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({detail: res.statusText}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ── IT Mode ───────────────────────────────────────────────────
function toggleITMode() {
  const on = document.getElementById('it-mode-toggle').checked;
  document.getElementById('query-normal').style.display = on ? 'none' : 'flex';
  document.getElementById('query-it').style.display     = on ? 'block' : 'none';
  if (on) renderITTags();
}

function renderITTags() {
  const container = document.getElementById('it-tags');
  container.innerHTML = itKeywords.map((kw, i) =>
    `<span class="kw-tag">${esc(kw)}<button class="kw-remove" onclick="removeKeyword(${i})">×</button></span>`
  ).join('');
}

function removeKeyword(i) {
  itKeywords.splice(i, 1);
  renderITTags();
}

function addITKeyword(e) {
  if (e.key !== 'Enter') return;
  const inp = document.getElementById('it-tag-input');
  const val = inp.value.trim();
  if (val && !itKeywords.includes(val)) {
    itKeywords.push(val);
    renderITTags();
  }
  inp.value = '';
}

function getQuery() {
  const on = document.getElementById('it-mode-toggle').checked;
  return on ? itKeywords.join(' ') : document.getElementById('q-query').value.trim();
}

// ── Location mode ─────────────────────────────────────────────
function setLocMode(mode) {
  locMode = mode;
  document.getElementById('loc-city').style.display     = mode === 'city'     ? 'flex' : 'none';
  document.getElementById('loc-province').style.display = mode === 'province' ? 'flex' : 'none';
  document.getElementById('tab-city').classList.toggle('active',     mode === 'city');
  document.getElementById('tab-province').classList.toggle('active', mode === 'province');
}

function updateRadius(val) {
  document.getElementById('radius-val').textContent = val;
}

// ── Location expansion ────────────────────────────────────────
function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371, dLat = (lat2-lat1)*Math.PI/180, dLng = (lng2-lng1)*Math.PI/180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLng/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

function getLocations() {
  if (locMode === 'province') {
    const prov = document.getElementById('q-province').value;
    if (!prov) { alert('Please select a province.'); return null; }
    return PROVINCE_CITIES[prov] || [];
  }
  // City mode
  const city = document.getElementById('q-location').value.trim();
  if (!city) { alert('Please enter a city.'); return null; }
  const radius = parseInt(document.getElementById('q-radius').value) || 0;
  if (radius === 0) return [city];

  // Find anchor coordinates
  const anchor = CITY_COORDS.find(c => c.name.toLowerCase() === city.toLowerCase())
               || CITY_COORDS.find(c => c.name.toLowerCase().startsWith(city.toLowerCase().split(',')[0]));
  if (!anchor) return [city]; // unknown city — just use it directly

  const nearby = CITY_COORDS
    .filter(c => haversineKm(anchor.lat, anchor.lng, c.lat, c.lng) <= radius)
    .map(c => c.name);
  return nearby.length ? nearby : [city];
}

function getPages() {
  const id = locMode === 'province' ? 'q-pages-p' : 'q-pages';
  return parseInt(document.getElementById(id).value) || 10;
}

// ── Scrape queue ──────────────────────────────────────────────
async function startScrape() {
  const query = getQuery();
  if (!query) { alert('Please enter a job title or enable IT Mode.'); return; }
  const locations = getLocations();
  if (!locations) return;
  const pages = getPages();

  // Reset accumulated jobs for a fresh search
  allJobs = []; displayJobs = []; currentPage = 1;
  renderTable();

  scrapeQueue = locations.map(loc => ({query, location: loc, pages}));
  stopRequested = false;
  await processQueue();
}

async function processQueue() {
  if (queueRunning) return;
  queueRunning = true;
  setButtonState(true);

  while (scrapeQueue.length > 0 && !stopRequested) {
    const {query, location, pages, resume = false} = scrapeQueue.shift();
    const remaining = scrapeQueue.length;
    document.getElementById('queue-info').textContent =
      remaining > 0 ? `${remaining + 1} location(s) remaining` : '';

    _backendLastCount = 0; // reset per-city so incremental fetch works correctly
    try {
      await api('POST', '/scrape', {query, location, pages, resume});
    } catch (e) {
      if (e.message.includes('already running')) {
        // Backend still finishing previous — wait and retry
        scrapeQueue.unshift({query, location, pages});
        await sleep(3000);
        continue;
      }
      continue; // skip failed queue item
    }

    await waitForCompletion();
    await fetchAndMergeResults();
  }

  document.getElementById('queue-info').textContent = '';
  queueRunning = false;
  setButtonState(false);
}

async function stopScrape() {
  stopRequested = true;
  scrapeQueue = [];
  try { await api('DELETE', '/scrape/stop'); } catch(_) {}
}

// ── Results — incremental fetch ───────────────────────────────
let _fetching = false;
const _renderedIds = new Set(); // job_ids currently in the DOM

/**
 * Fetch /api/results, merge new jobs into allJobs.
 * incremental=true → append only new rows to the DOM (no full re-render).
 * incremental=false → do a full applyFilters() + renderTable() afterwards.
 */
async function fetchAndMergeResults(incremental = false) {
  if (_fetching) return;
  _fetching = true;
  try {
    const data = await api('GET', '/results?page=1&limit=5000');
    console.log(`[DEBUG] /api/results → total=${data.total}, returned=${(data.jobs||[]).length}, allJobs=${allJobs.length}`);

    const incoming = data.jobs || [];
    const existingIds = new Set(allJobs.map(j => j.job_id).filter(Boolean));
    const fresh = incoming.filter(j => !existingIds.has(j.job_id));

    if (fresh.length === 0) return;

    allJobs.push(...fresh);
    console.log(`[DEBUG] +${fresh.length} new jobs → allJobs total: ${allJobs.length}`);

    if (incremental && currentPage === 1 && !sortCol && !filterRemote && !filterSalary
        && !filterIT && !filterLevel
        && !document.getElementById('f-location').value
        && !document.getElementById('f-company').value) {
      // Live stream: append only new rows, no full table rebuild
      _appendRows(fresh);
      _updateResultsCount();
    } else {
      applyFilters(); // full re-render (handles sort/filter/pagination)
    }
  } catch (e) {
    console.error('[DEBUG] fetchAndMergeResults error:', e);
  } finally {
    _fetching = false;
  }
}

const _LEVEL_LABELS = {
  intern: 'Intern', junior: 'Junior', mid: 'Mid', senior: 'Senior',
  lead: 'Lead', principal: 'Principal', manager: 'Manager', executive: 'Executive',
};
const _LEVEL_COLORS = {
  intern: '#94a3b8', junior: '#60a5fa', mid: '#34d399',
  senior: '#f59e0b', lead: '#f97316', principal: '#a78bfa',
  manager: '#ec4899', executive: '#ef4444',
};

/** Build the 10 <td> cells for one job row (no <tr> wrapper). */
function _buildRowCells(job) {
  const remote = job.remote
    ? '<span class="tag tag-yes">Yes</span>'
    : '<span class="tag tag-no">No</span>';
  const url = job.url
    ? `<a href="${esc(job.url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:var(--accent)">&#x2197;</a>`
    : '—';
  const lvl = job.level && job.level !== 'unknown' ? job.level : null;
  const levelCell = lvl
    ? `<span class="level-badge" style="background:${_LEVEL_COLORS[lvl]||'#64748b'}20;color:${_LEVEL_COLORS[lvl]||'#64748b'};border:1px solid ${_LEVEL_COLORS[lvl]||'#64748b'}40">${_LEVEL_LABELS[lvl]||lvl}</span>`
    : '<span style="color:#555">—</span>';
  return `<td title="${esc(job.title||'')}">${esc(job.title||'—')}</td>
<td title="${esc(job.company||'')}">${esc(job.company||'—')}</td>
<td title="${esc(job.location||'')}">${esc(job.location||'—')}</td>
<td>${levelCell}</td>
<td>${esc(job.salary||'—')}</td>
<td>${esc(job.posted_date||'—')}</td>
<td>${esc(job.employment_type||'—')}</td>
<td>${remote}</td>
<td>${job.company_rating != null ? job.company_rating.toFixed(1) : '—'}</td>
<td>${url}</td>`;
}

/** Append only truly new rows to the tbody without rebuilding anything. */
function _appendRows(jobs) {
  const tbody = document.getElementById('jobs-body');
  // Remove the empty-state placeholder if present
  if (tbody.querySelector('.empty-state')) tbody.innerHTML = '';

  jobs.forEach(job => {
    if (!job.job_id || _renderedIds.has(job.job_id)) return;
    _renderedIds.add(job.job_id);
    const tr = document.createElement('tr');
    tr.innerHTML = _buildRowCells(job);
    tr.style.cursor = 'pointer';
    const jid = job.job_id;
    tr.addEventListener('click', () => openModal(jid));
    tbody.appendChild(tr);
  });

  _updateLiveCounter();
}

function _updateResultsCount() {
  const total = allJobs.length;
  document.getElementById('results-count').textContent =
    total > 0 ? `— ${total} job${total !== 1 ? 's' : ''}` : '';
}

function _updateLiveCounter() {
  const el = document.getElementById('live-counter');
  if (!el) return;
  if (queueRunning) {
    el.textContent = `⚡ ${allJobs.length} jobs found so far…`;
    el.style.display = 'block';
  } else {
    el.style.display = 'none';
  }
}

// ── Filtering ─────────────────────────────────────────────────
function applyFilters() {
  const loc = document.getElementById('f-location').value.toLowerCase();
  const co  = document.getElementById('f-company').value.toLowerCase();
  filterLevel = document.getElementById('f-level').value;
  displayJobs = allJobs.filter(j => {
    if (loc && !(j.location||'').toLowerCase().includes(loc)) return false;
    if (co  && !(j.company ||'').toLowerCase().includes(co))  return false;
    if (filterLevel && (j.level || 'unknown') !== filterLevel) return false;
    if (filterRemote && !j.remote)   return false;
    if (filterSalary && !j.salary)   return false;
    if (filterIT     && !j.is_it_job) return false;
    return true;
  });
  if (sortCol) applySortToDisplay();
  currentPage = 1;
  renderTable();
}

function toggleIT() {
  filterIT = !filterIT;
  document.getElementById('f-it').classList.toggle('active', filterIT);
  applyFilters();
}

function clearFilters() {
  document.getElementById('f-location').value = '';
  document.getElementById('f-company').value  = '';
  document.getElementById('f-level').value    = '';
  filterRemote = false; filterSalary = false; filterIT = false; filterLevel = '';
  document.getElementById('f-remote').classList.remove('active');
  document.getElementById('f-salary').classList.remove('active');
  document.getElementById('f-it').classList.remove('active');
  applyFilters();
}

function toggleRemote() { filterRemote = !filterRemote; document.getElementById('f-remote').classList.toggle('active', filterRemote); applyFilters(); }
function toggleSalary() { filterSalary = !filterSalary; document.getElementById('f-salary').classList.toggle('active', filterSalary); applyFilters(); }

// ── Sorting ───────────────────────────────────────────────────
function sortBy(col) {
  sortDir = sortCol === col ? (sortDir === 'asc' ? 'desc' : 'asc') : 'asc';
  sortCol = col;
  document.querySelectorAll('thead th').forEach(th => th.classList.remove('sort-asc','sort-desc'));
  const cols = ['title','company','location','salary','posted_date','employment_type','remote','company_rating'];
  const idx = cols.indexOf(col);
  if (idx >= 0) document.querySelectorAll('thead th')[idx].classList.add(sortDir === 'asc' ? 'sort-asc' : 'sort-desc');
  applySortToDisplay();
  currentPage = 1;
  renderTable();
}

function applySortToDisplay() {
  displayJobs.sort((a, b) => {
    let av = a[sortCol] ?? '', bv = b[sortCol] ?? '';
    if (typeof av === 'boolean') av = av ? 1 : 0;
    if (typeof bv === 'boolean') bv = bv ? 1 : 0;
    return (av < bv ? -1 : av > bv ? 1 : 0) * (sortDir === 'asc' ? 1 : -1);
  });
}

// ── Table rendering (full rebuild) ────────────────────────────
function renderTable() {
  const tbody = document.getElementById('jobs-body');
  const total = displayJobs.length;

  _renderedIds.clear(); // reset incremental tracker on full rebuild
  _updateResultsCount();
  _updateLiveCounter();

  if (total === 0) {
    tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state">
      <div class="icon">${allJobs.length > 0 ? '🔎' : '🔍'}</div>
      <p>${allJobs.length > 0 ? 'No jobs match your filters.' : 'Run a search to see results here.'}</p>
    </div></td></tr>`;
    document.getElementById('pagination').style.display = 'none';
    return;
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (currentPage > totalPages) currentPage = totalPages;
  const start = (currentPage - 1) * PAGE_SIZE;
  const slice = displayJobs.slice(start, start + PAGE_SIZE);

  tbody.innerHTML = slice.map(job => {
    if (job.job_id) _renderedIds.add(job.job_id);
    return `<tr onclick="openModal('${esc(job.job_id||'')}')">${_buildRowCells(job)}</tr>`;
  }).join('');

  const pag = document.getElementById('pagination');
  pag.style.display = 'flex';
  document.getElementById('page-info').textContent = `Showing ${start+1}–${Math.min(start+PAGE_SIZE,total)} of ${total}`;
  document.getElementById('page-num').textContent  = `Page ${currentPage} / ${totalPages}`;
  document.getElementById('btn-prev').disabled = currentPage <= 1;
  document.getElementById('btn-next').disabled = currentPage >= totalPages;
}

function changePage(delta) {
  currentPage = Math.max(1, Math.min(currentPage + delta, Math.ceil(displayJobs.length / PAGE_SIZE)));
  renderTable();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

// ── Modal ─────────────────────────────────────────────────────
function openModal(jobId) {
  const job = allJobs.find(j => j.job_id === jobId);
  if (!job) return;
  currentJobId = jobId;
  document.getElementById('modal-title').textContent   = job.title   || 'Untitled';
  document.getElementById('modal-company').textContent = job.company || '';
  const chips = [
    job.location        && metaChip('📍', job.location),
    job.salary          && metaChip('💰', job.salary),
    job.posted_date     && metaChip('🕒', job.posted_date),
    job.employment_type && metaChip('💼', job.employment_type),
    job.remote != null  && metaChip('🌐', job.remote ? 'Remote' : 'On-site'),
    job.company_rating  && metaChip('⭐', job.company_rating.toFixed(1)),
  ].filter(Boolean);
  document.getElementById('modal-meta').innerHTML = chips.join('');
  document.getElementById('modal-desc').textContent = job.description || 'No description available.';
  const urlEl = document.getElementById('modal-url');
  urlEl.href = job.url || '#';
  urlEl.style.display = job.url ? '' : 'none';
  document.getElementById('job-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function metaChip(icon, value) { return `<span class="meta-chip">${icon} <b>${esc(String(value))}</b></span>`; }
function closeModal(e) { if (e.target === document.getElementById('job-modal')) closeModalBtn(); }
function closeModalBtn() { document.getElementById('job-modal').classList.add('hidden'); document.body.style.overflow = ''; currentJobId = null; }
function copyDescription() {
  const desc = document.getElementById('modal-desc').textContent;
  navigator.clipboard.writeText(desc).then(() => {
    const btn = document.querySelector('.modal-footer button');
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  });
}
function exportSinglePdf() { if (currentJobId) window.open(`/api/export/pdf/${encodeURIComponent(currentJobId)}`, '_blank'); }

// ── Status UI ─────────────────────────────────────────────────
function updateStatusBar(data) {
  const map = {
    idle:      '<span class="badge badge-idle">Idle</span>',
    running:   '<span class="badge badge-running"><span class="spinner"></span> Running</span>',
    completed: '<span class="badge badge-completed">Completed</span>',
    stopped:   '<span class="badge badge-stopped">Stopped</span>',
    failed:    '<span class="badge badge-failed">Failed</span>',
  };
  document.getElementById('stat-status').innerHTML    = map[data.status] || `<span class="badge">${data.status}</span>`;
  document.getElementById('stat-jobs').textContent    = allJobs.length || data.jobs_count || 0;
  document.getElementById('stat-pages').textContent   = data.pages_total ? `${data.pages_done}/${data.pages_total}` : '—';
  document.getElementById('stat-elapsed').textContent = data.elapsed_time ? formatTime(data.elapsed_time) : '—';
  document.getElementById('stat-proxy').textContent   = data.proxy_errors ?? 0;
}

function setButtonState(running) {
  document.getElementById('btn-start').disabled = running;
  document.getElementById('btn-stop').disabled  = !running;
  document.getElementById('btn-start').innerHTML = running
    ? '<span class="spinner"></span> Scraping…'
    : 'Start Scraping';
  const moreBtn = document.getElementById('btn-more');
  if (moreBtn) moreBtn.style.display = (!running && allJobs.length > 0) ? 'inline-flex' : 'none';
  _updateLiveCounter();
}

async function getMoreJobs() {
  const query = getQuery();
  const locations = getLocations();
  if (!query || !locations) return;
  const pages = getPages();
  scrapeQueue = locations.map(loc => ({query, location: loc, pages, resume: true}));
  stopRequested = false;
  await processQueue();
}

// ── Polling — incremental during run, full render on finish ───
async function waitForCompletion() {
  return new Promise(resolve => {
    const iv = setInterval(async () => {
      let data;
      try { data = await api('GET', '/scrape/status'); } catch(_) { return; }
      updateStatusBar(data);
      updateLogs(data.logs || []);
      // Fetch when backend has more jobs than last time we fetched for THIS city.
      // _backendLastCount resets to 0 each time a new city starts so it works
      // correctly across multi-city radius/province queues.
      if (data.jobs_count > _backendLastCount) {
        _backendLastCount = data.jobs_count;
        await fetchAndMergeResults(true);
      }
      if (['completed','failed','stopped','idle'].includes(data.status)) {
        clearInterval(iv);
        resolve();
      }
    }, 2000);
  });
}

// ── Logs ──────────────────────────────────────────────────────
let _renderedLogs = 0;
function updateLogs(lines) {
  const box = document.getElementById('log-box');
  if (lines.length > _renderedLogs) {
    lines.slice(_renderedLogs).forEach(line => {
      const p = document.createElement('p');
      const ll = line.toLowerCase();
      if (ll.includes('error')||ll.includes('fatal')) p.className = 'error';
      else if (ll.includes('warn')||ll.includes('block')||ll.includes('proxy')) p.className = 'warn';
      p.textContent = line;
      box.appendChild(p);
    });
    _renderedLogs = lines.length;
    if (box.classList.contains('open')) box.scrollTop = box.scrollHeight;
  }
  document.getElementById('log-count').textContent = `(${lines.length} lines)`;
}

function toggleLog() {
  const toggle = document.getElementById('log-toggle');
  const box    = document.getElementById('log-box');
  const open   = box.classList.toggle('open');
  toggle.classList.toggle('open', open);
  if (open) box.scrollTop = box.scrollHeight;
}

// ── Export ────────────────────────────────────────────────────
function exportExcel() { window.open('/api/export/excel', '_blank'); }
function exportPdf()   { window.open('/api/export/pdf',   '_blank'); }

// ── Utilities ─────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function formatTime(s) { const m=Math.floor(s/60); return m>0?`${m}m ${Math.floor(s%60)}s`:`${Math.floor(s)}s`; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Init ──────────────────────────────────────────────────────
(async function init() {
  // Populate city autocomplete datalist
  const dl = document.getElementById('city-list');
  if (dl) {
    const frag = document.createDocumentFragment();
    CITY_COORDS.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.name;
      frag.appendChild(opt);
    });
    dl.appendChild(frag);
  }

  renderITTags();
  try {
    const data = await api('GET', '/scrape/status');
    updateStatusBar(data);
    updateLogs(data.logs || []);
    if (data.status === 'running') setButtonState(true);
    if (data.jobs_count > 0) await fetchAndMergeResults(false);
  } catch(_) {}
})();
