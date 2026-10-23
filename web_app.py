"""
Interactive Geospatial Climate Risk Dashboard (NASA SERVIR Advanced Edition).
Features:
- Multi-Hazard Toggle: Flood Inundation vs Agricultural Drought.
- Climate Change Scenario Presets: Baseline 10-Yr, 2030 Monsoon +1.5C, 2050 Extreme RCP 8.5.
- Quick Regional Hub Pills (Bangkok, Keta Lagoon, Nairobi, Mekong Delta, Manila).
- Bounded "Explain with AI Risk Analyst" (Sendai Framework SITREP Generator).
- Live Chart.js Risk Response Curve.
- High-Resolution 16-Cell (4x4) GeoJSON Hazard Grid with Real-Time Coloring.
- One-Click RFC 7946 GeoJSON Export.
"""

import sys
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from services.risk_engine import RiskEngine
from models import FloodVulnerabilityInput, DroughtAssessmentInput, BoundingBox

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SERVIR Global Risk Platform | Advanced Decision Support</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    #map { height: 520px; width: 100%; border-radius: 1rem; }
    .glass { background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.12); }
    .scrollbar-thin::-webkit-scrollbar { width: 5px; }
    .scrollbar-thin::-webkit-scrollbar-thumb { background: #334155; border-radius: 9999px; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen flex flex-col">

  <!-- Header -->
  <header class="h-20 border-b border-slate-800 px-6 flex items-center justify-between glass sticky top-0 z-50">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center text-white font-black text-xl shadow-lg shadow-emerald-500/20">
        S
      </div>
      <div>
        <h1 class="font-bold text-base md:text-lg text-white tracking-wide">SERVIR Global Risk Platform</h1>
        <p class="text-xs text-slate-400">Earth Observation Decision Support & FastMCP Multi-Hazard Engine</p>
      </div>
    </div>
    
    <!-- Hazard Mode Switcher -->
    <div class="flex items-center bg-slate-900 border border-slate-700 p-1 rounded-xl">
      <button id="mode-flood-btn" onclick="setHazardMode('flood')" class="px-3 py-1.5 rounded-lg text-xs font-bold transition bg-emerald-500 text-white shadow-md">
        🌊 Flood Inundation
      </button>
      <button id="mode-drought-btn" onclick="setHazardMode('drought')" class="px-3 py-1.5 rounded-lg text-xs font-bold transition text-slate-400 hover:text-white">
        ☀️ Agricultural Drought
      </button>
    </div>

    <div class="hidden sm:flex items-center gap-3">
      <a href="https://github.com/Huighlet/geospatial-risk-mcp-server" target="_blank" class="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
        GitHub Source
      </a>
    </div>
  </header>

  <!-- Main Grid -->
  <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 p-5">
    
    <!-- Left Sidebar: Controls, Scenarios & AI -->
    <div class="lg:col-span-5 flex flex-col gap-4 overflow-y-auto max-h-[calc(100vh-100px)] pr-1 scrollbar-thin">
      
      <!-- Location Search & Fast Hub Pills -->
      <div class="glass p-4 rounded-2xl flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Target Location Search</label>
          <span id="search-status" class="text-[11px] text-emerald-400 font-mono">Global Geocoder Active</span>
        </div>
        
        <div class="flex gap-2">
          <input 
            type="text" 
            id="search-input" 
            placeholder="Type city or place (e.g. Keta, Accra, Nairobi, Bangkok)..." 
            class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            onkeydown="if(event.key === 'Enter') searchLocation()"
          />
          <button 
            onclick="searchLocation()" 
            class="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition">
            Find
          </button>
        </div>

        <!-- Quick Hub Pills (Replaces clunky dropdown) -->
        <div class="flex flex-wrap gap-1.5 pt-1">
          <span class="text-[10px] text-slate-400 self-center mr-1">Hubs:</span>
          <button onclick="jumpToHub('keta')" class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">🇬🇭 Keta</button>
          <button onclick="jumpToHub('bangkok')" class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">🇹🇭 Bangkok</button>
          <button onclick="jumpToHub('kenya')" class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">🇰🇪 Nairobi</button>
          <button onclick="jumpToHub('vietnam')" class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">🇻🇳 Mekong</button>
          <button onclick="jumpToHub('philippines')" class="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">🇵🇭 Manila</button>
        </div>
      </div>

      <!-- Climate Change Scenario Selectors (SERVIR Requirement) -->
      <div class="glass p-4 rounded-2xl flex flex-col gap-2.5">
        <label class="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Climate Change Scenario Comparison</label>
        <div class="grid grid-cols-3 gap-2">
          <button onclick="applyScenario('baseline')" class="px-2 py-2 rounded-xl text-center bg-slate-900 hover:bg-slate-800 border border-slate-700 transition flex flex-col items-center">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Baseline</span>
            <span class="text-xs font-bold text-emerald-400 mt-0.5">10-Yr Storm</span>
            <span class="text-[9px] text-slate-500">45 mm</span>
          </button>
          <button onclick="applyScenario('monsoon')" class="px-2 py-2 rounded-xl text-center bg-slate-900 hover:bg-slate-800 border border-slate-700 transition flex flex-col items-center">
            <span class="text-[10px] font-bold text-slate-400 uppercase">2030 (+1.5°C)</span>
            <span class="text-xs font-bold text-amber-400 mt-0.5">Intense Monsoon</span>
            <span class="text-[9px] text-slate-500">120 mm</span>
          </button>
          <button onclick="applyScenario('extreme')" class="px-2 py-2 rounded-xl text-center bg-slate-900 hover:bg-slate-800 border border-slate-700 transition flex flex-col items-center">
            <span class="text-[10px] font-bold text-slate-400 uppercase">2050 (RCP 8.5)</span>
            <span class="text-xs font-bold text-red-400 mt-0.5">100-Yr Disaster</span>
            <span class="text-[9px] text-slate-500">210 mm</span>
          </button>
        </div>
      </div>

      <!-- Simulation Sliders (Dynamic for Flood vs Drought) -->
      <div class="glass p-4 rounded-2xl flex flex-col gap-3.5">
        <div class="border-b border-slate-800 pb-2 flex items-center justify-between">
          <h2 class="font-bold text-xs text-slate-200 uppercase tracking-wider" id="slider-panel-title">Hydrologic Parameters</h2>
          <span class="text-[10px] text-emerald-400 font-mono" id="current-coords">Lat: 5.92 | Lon: 0.99</span>
        </div>

        <!-- FLOOD INPUTS -->
        <div id="flood-controls" class="space-y-3">
          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">24h Rainfall Forecast</span>
              <span id="val-rain" class="text-emerald-400 font-bold">135 mm</span>
            </div>
            <input type="range" id="input-rain" min="0" max="250" value="135" class="w-full accent-emerald-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Surface Elevation (Above Sea Level)</span>
              <span id="val-elev" class="text-cyan-400 font-bold">2.5 m</span>
            </div>
            <input type="range" id="input-elev" min="0" max="100" step="0.5" value="2.5" class="w-full accent-cyan-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Soil Percolation Rate</span>
              <span id="val-soil" class="text-indigo-400 font-bold">0.35</span>
            </div>
            <input type="range" id="input-soil" min="0.0" max="1.0" step="0.05" value="0.35" class="w-full accent-indigo-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          </div>
        </div>

        <!-- DROUGHT INPUTS (Initially Hidden) -->
        <div id="drought-controls" class="space-y-3 hidden">
          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Topsoil Moisture Content</span>
              <span id="val-moist" class="text-amber-400 font-bold">18 %</span>
            </div>
            <input type="range" id="input-moist" min="0" max="100" value="18" class="w-full accent-amber-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="flex justify-between text-[10px] text-slate-500 mt-0.5"><span>0% (Arid)</span><span>50% (Adequate)</span><span>100% (Saturated)</span></div>
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Land Surface Temperature</span>
              <span id="val-temp" class="text-red-400 font-bold">38 °C</span>
            </div>
            <input type="range" id="input-temp" min="15" max="55" value="38" class="w-full accent-red-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Vegetation Health Index (NDVI)</span>
              <span id="val-ndvi" class="text-emerald-400 font-bold">0.24</span>
            </div>
            <input type="range" id="input-ndvi" min="-0.2" max="1.0" step="0.02" value="0.24" class="w-full accent-emerald-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          </div>
        </div>
      </div>

      <!-- Live Computed Risk Metrics & AI Explain Button -->
      <div id="result-card" class="glass p-4 rounded-2xl flex flex-col gap-3.5">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider" id="metric-title">Computed Vulnerability Index</span>
          <div id="risk-badge" class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/40">
            HIGH
          </div>
        </div>
        
        <div class="flex items-baseline gap-2">
          <div class="text-4xl font-black text-white" id="risk-score">69.8</div>
          <div class="text-xs text-slate-400" id="scale-label">/ 100 (Flood Vulnerability Index)</div>
        </div>

        <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 leading-relaxed" id="risk-action">
          Activate municipal drainage systems and issue public hazard alerts.
        </div>

        <div class="grid grid-cols-2 gap-2 pt-1">
          <!-- Bounded AI Briefing Button -->
          <button onclick="generateAIBriefing()" class="py-2.5 px-3 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-md transition flex items-center justify-center gap-1.5">
            <span>✨ Explain with AI</span>
          </button>

          <!-- Export GeoJSON Layer -->
          <button onclick="downloadGeoJSON()" class="py-2.5 px-3 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-500/30 transition flex items-center justify-center gap-1.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            <span>Export GeoJSON</span>
          </button>
        </div>
      </div>
      
    </div>

    <!-- Right Area: Map & Live Risk Response Curve -->
    <div class="lg:col-span-7 flex flex-col gap-4">
      
      <!-- Interactive Map Card -->
      <div class="glass p-2 rounded-2xl relative shadow-2xl overflow-hidden">
        <div id="map"></div>
        
        <!-- Map Legend -->
        <div class="absolute bottom-5 right-5 z-[1000] glass px-3.5 py-2.5 rounded-xl shadow-2xl flex flex-col gap-1.5 text-xs border border-slate-700/60">
          <div class="font-bold text-slate-300 text-[10px] uppercase tracking-wider border-b border-slate-700/60 pb-1 flex justify-between gap-3">
            <span>16-Cell Grid Hazard</span>
            <span class="text-slate-400 text-[9px]">4x4 GeoJSON</span>
          </div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-red-500 shadow-sm shadow-red-500/50"></span> <span class="text-[11px]">Critical (&ge;75)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-orange-500 shadow-sm shadow-orange-500/50"></span> <span class="text-[11px]">High (50-74)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-amber-400 shadow-sm shadow-amber-400/50"></span> <span class="text-[11px]">Moderate (25-49)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-emerald-500 shadow-sm shadow-emerald-500/50"></span> <span class="text-[11px]">Low (&lt;25)</span></div>
        </div>
      </div>

      <!-- Live Vulnerability Response Chart (Chart.js) -->
      <div class="glass p-4 rounded-2xl">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider">Topographic Sensitivity Response Curve</h3>
          <span class="text-[11px] text-slate-400">Vulnerability vs. Rainfall (0 - 250mm)</span>
        </div>
        <div class="h-32">
          <canvas id="riskChart"></canvas>
        </div>
      </div>

    </div>

  </div>

  <!-- Bounded AI Situation Report (Modal) -->
  <div id="ai-modal" class="fixed inset-0 z-[2000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="glass max-w-2xl w-full p-6 rounded-3xl border border-emerald-500/40 shadow-2xl flex flex-col gap-4 animate-in fade-in duration-200">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <h3 class="font-bold text-white text-base" id="ai-modal-title">SERVIR Bounded AI Situation Report</h3>
        </div>
        <button onclick="closeAIModal()" class="text-slate-400 hover:text-white text-lg font-bold">✕</button>
      </div>

      <div class="space-y-3 text-xs leading-relaxed max-h-[60vh] overflow-y-auto pr-1 scrollbar-thin">
        <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
          <span class="text-slate-400 uppercase font-bold text-[10px] block">Readiness Priority</span>
          <div class="text-sm font-extrabold text-emerald-400 mt-0.5" id="ai-priority">--</div>
        </div>

        <div>
          <span class="text-slate-300 uppercase font-bold text-[10px] block mb-1">Directives for Civil Defense</span>
          <ul class="list-disc pl-4 space-y-1 text-slate-300" id="ai-directives"></ul>
        </div>

        <div class="grid grid-cols-2 gap-3 pt-1">
          <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span class="text-slate-400 uppercase font-bold text-[10px] block mb-1">Critical Infrastructure Risk</span>
            <p class="text-slate-300" id="ai-infra">--</p>
          </div>
          <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span class="text-slate-400 uppercase font-bold text-[10px] block mb-1">Agricultural & Livelihood Impact</span>
            <p class="text-slate-300" id="ai-agri">--</p>
          </div>
        </div>

        <div class="text-[10px] text-slate-500 italic border-t border-slate-800 pt-2" id="ai-assurance">
          Sendai Framework compliant. Deterministic calculation source.
        </div>
      </div>

      <button onclick="closeAIModal()" class="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition">
        Close Advisory
      </button>
    </div>
  </div>

  <script>
    let activeHazard = "flood";
    let currentLat = 5.92;
    let currentLon = 0.99;
    let currentLocationName = "Keta, Volta Region, Ghana";
    let latestGeoJSON = null;
    let riskChart = null;

    // Normalize coordinates to [-180, 180] and [-85, 85]
    function normalizeCoords(lat, lon) {
      let normLon = ((lon + 180) % 360 + 360) % 360 - 180;
      let clampLat = Math.max(-85, Math.min(85, lat));
      return { lat: clampLat, lon: normLon };
    }

    // Initialize Leaflet Map
    const map = L.map('map', { worldCopyJump: true }).setView([currentLat, currentLon], 10);
    
    // 1. ESRI World Street Map (English Labels Globally)
    const englishStreets = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; TomTom, USGS'
    }).addTo(map);

    // 2. ESRI High-Res Satellite
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri, Maxar'
    });

    // 3. OpenStreetMap
    const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    });

    L.control.layers({
      "English World Street Map": englishStreets,
      "Satellite Imagery": satellite,
      "Standard OpenStreetMap": osm
    }, null, { position: 'topright' }).addTo(map);

    let geojsonLayer = null;
    let targetMarker = L.marker([currentLat, currentLon]).addTo(map).bindPopup("Current Risk Target");

    // Click anywhere on map
    map.on('click', function(e) {
      const norm = normalizeCoords(e.latlng.lat, e.latlng.lng);
      currentLat = norm.lat;
      currentLon = norm.lon;
      currentLocationName = `${currentLat.toFixed(2)}N, ${currentLon.toFixed(2)}E`;

      targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`Target: ${currentLocationName}`).openPopup();
      document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
      document.getElementById('search-status').innerText = "Target Selected";
      runSimulation();
    });

    // Global Place Search (Nominatim)
    async function searchLocation() {
      const query = document.getElementById('search-input').value.trim();
      if (!query) return;
      const statusEl = document.getElementById('search-status');
      statusEl.innerText = "Locating...";

      try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const results = await response.json();
        if (results && results.length > 0) {
          const top = results[0];
          const norm = normalizeCoords(parseFloat(top.lat), parseFloat(top.lon));
          currentLat = norm.lat;
          currentLon = norm.lon;
          currentLocationName = top.display_name.split(',')[0];

          map.flyTo([currentLat, currentLon], 10);
          targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`<b>${currentLocationName}</b><br><span class="text-[11px] text-slate-500">${top.display_name}</span>`).openPopup();
          document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
          statusEl.innerText = `Located: ${currentLocationName}`;
          runSimulation();
        } else {
          statusEl.innerText = "Location not found.";
        }
      } catch (err) {
        statusEl.innerText = "Search error.";
      }
    }

    // Fast Hub Pills
    const HUBS = {
      keta: { lat: 5.92, lon: 0.99, elev: 2.5, rain: 108, name: "Keta, Volta Region, Ghana" },
      bangkok: { lat: 13.7563, lon: 100.5018, elev: 2.5, rain: 135, name: "Bangkok Basin, Thailand" },
      kenya: { lat: -1.2921, lon: 36.8219, elev: 45.0, rain: 45, name: "Nairobi Basin, Kenya" },
      vietnam: { lat: 10.0452, lon: 105.7469, elev: 1.8, rain: 160, name: "Mekong Delta, Vietnam" },
      philippines: { lat: 14.5995, lon: 120.9842, elev: 4.0, rain: 190, name: "Manila Bay, Philippines" }
    };

    function jumpToHub(key) {
      if (!HUBS[key]) return;
      const h = HUBS[key];
      currentLat = h.lat;
      currentLon = h.lon;
      currentLocationName = h.name;
      document.getElementById('input-elev').value = h.elev;
      document.getElementById('input-rain').value = h.rain;
      map.flyTo([currentLat, currentLon], 10);
      targetMarker.setLatLng([currentLat, currentLon]).bindPopup(h.name).openPopup();
      document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
      document.getElementById('search-status').innerText = h.name.split(',')[0];
      updateValuesAndTrigger();
    }

    // Hazard Mode Switching
    function setHazardMode(mode) {
      activeHazard = mode;
      const floodBtn = document.getElementById('mode-flood-btn');
      const droughtBtn = document.getElementById('mode-drought-btn');
      const floodControls = document.getElementById('flood-controls');
      const droughtControls = document.getElementById('drought-controls');
      const panelTitle = document.getElementById('slider-panel-title');
      const scaleLabel = document.getElementById('scale-label');

      if (mode === 'drought') {
        droughtBtn.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition bg-amber-500 text-white shadow-md";
        floodBtn.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition text-slate-400 hover:text-white";
        floodControls.classList.add('hidden');
        droughtControls.classList.remove('hidden');
        panelTitle.innerText = "Agro-Meteorological Parameters";
        scaleLabel.innerText = "/ 100 (Drought Stress Index)";
      } else {
        floodBtn.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition bg-emerald-500 text-white shadow-md";
        droughtBtn.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition text-slate-400 hover:text-white";
        droughtControls.classList.add('hidden');
        floodControls.classList.remove('hidden');
        panelTitle.innerText = "Hydrologic Parameters";
        scaleLabel.innerText = "/ 100 (Flood Vulnerability Index)";
      }
      runSimulation();
    }

    // Scenario Comparisons
    function applyScenario(sc) {
      if (sc === 'baseline') {
        document.getElementById('input-rain').value = 45;
        document.getElementById('input-moist').value = 45;
      } else if (sc === 'monsoon') {
        document.getElementById('input-rain').value = 120;
        document.getElementById('input-moist').value = 25;
      } else if (sc === 'extreme') {
        document.getElementById('input-rain').value = 210;
        document.getElementById('input-moist').value = 8;
      }
      updateValuesAndTrigger();
    }

    let debounceTimer = null;
    function updateValuesAndTrigger() {
      document.getElementById('val-rain').innerText = document.getElementById('input-rain').value + ' mm';
      document.getElementById('val-elev').innerText = document.getElementById('input-elev').value + ' m';
      document.getElementById('val-soil').innerText = document.getElementById('input-soil').value;
      document.getElementById('val-moist').innerText = document.getElementById('input-moist').value + ' %';
      document.getElementById('val-temp').innerText = document.getElementById('input-temp').value + ' °C';
      document.getElementById('val-ndvi').innerText = document.getElementById('input-ndvi').value;
      
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runSimulation, 50);
    }

    async function runSimulation() {
      const rain = parseFloat(document.getElementById('input-rain').value);
      const elev = parseFloat(document.getElementById('input-elev').value);
      const soil = parseFloat(document.getElementById('input-soil').value);
      const moist = parseFloat(document.getElementById('input-moist').value);
      const temp = parseFloat(document.getElementById('input-temp').value);
      const ndvi = parseFloat(document.getElementById('input-ndvi').value);

      try {
        let score = 0;
        let severity = "LOW";
        let guidance = "";

        if (activeHazard === 'drought') {
          const res = await fetch('/api/drought-risk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              soil_moisture_pct: moist,
              surface_temp_celsius: temp,
              baseline_ndvi: ndvi
            })
          });
          const d = await res.json();
          score = d.composite_drought_index;
          severity = d.classification;
          guidance = d.operational_guidance;
        } else {
          const res = await fetch('/api/flood-risk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              latitude: currentLat,
              longitude: currentLon,
              elevation_meters: elev,
              precipitation_mm: rain,
              soil_absorption_rate: soil
            })
          });
          const d = await res.json();
          score = d.flood_vulnerability_index;
          severity = d.severity_level;
          guidance = d.operational_guidance;
        }

        document.getElementById('risk-score').innerText = score.toFixed(1);
        document.getElementById('risk-action').innerText = guidance;
        
        const badge = document.getElementById('risk-badge');
        badge.innerText = severity;
        if (severity === 'CRITICAL') {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse';
        } else if (severity === 'HIGH') {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-orange-500/20 text-orange-400 border border-orange-500/50';
        } else if (severity === 'MODERATE') {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/50';
        } else {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/50';
        }

        // Draw 16-cell GeoJSON Grid
        await drawHazardZones(rain, elev, soil, moist, temp, ndvi);

        // Update Sensitivity Chart
        updateChart(elev, soil);
      } catch (err) {
        console.error("Simulation error:", err);
      }
    }

    async function drawHazardZones(rain, elev, soil, moist, temp, ndvi) {
      try {
        const norm = normalizeCoords(currentLat, currentLon);
        const minLat = Math.max(-85, norm.lat - 0.55);
        const maxLat = Math.min(85, norm.lat + 0.55);
        let minLon = Math.max(-180, norm.lon - 0.65);
        let maxLon = Math.min(180, norm.lon + 0.65);

        const res = await fetch('/api/bounding-box-geojson', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            min_lat: minLat,
            min_lon: minLon,
            max_lat: maxLat,
            max_lon: maxLon,
            hazard_type: activeHazard,
            precipitation_mm: rain,
            elevation_meters: elev,
            soil_rate: soil,
            soil_moisture_pct: moist,
            surface_temp_celsius: temp,
            baseline_ndvi: ndvi,
            grid_resolution: 4 // 16 cells!
          })
        });

        if (!res.ok) return;
        const geojson = await res.json();

        if (geojsonLayer) {
          map.removeLayer(geojsonLayer);
        }

        geojsonLayer = L.geoJSON(geojson, {
          style: function(feature) {
            const score = feature.properties.risk_score;
            let color = '#10b981';
            let opacity = 0.35;
            if (score >= 75) {
              color = '#ef4444';
              opacity = 0.55;
            } else if (score >= 50) {
              color = '#f97316';
              opacity = 0.45;
            } else if (score >= 25) {
              color = '#f59e0b';
              opacity = 0.35;
            }
            return {
              color: color,
              weight: 2,
              opacity: 0.9,
              fillColor: color,
              fillOpacity: opacity
            };
          },
          onEachFeature: function(feature, layer) {
            layer.bindPopup(`
              <div class="font-sans text-xs p-1">
                <div class="font-bold text-slate-900 border-b pb-1 mb-1.5 flex justify-between items-center">
                  <span>${feature.properties.cell_id}</span>
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-bold text-white ${feature.properties.severity === 'CRITICAL' ? 'bg-red-600' : feature.properties.severity === 'HIGH' ? 'bg-orange-500' : feature.properties.severity === 'MODERATE' ? 'bg-amber-500' : 'bg-emerald-600'}">${feature.properties.severity}</span>
                </div>
                <div class="space-y-0.5 text-slate-700">
                  <div><b>Risk Index:</b> ${feature.properties.risk_score} / 100</div>
                  <div><b>Hazard:</b> ${feature.properties.hazard_type.toUpperCase()}</div>
                </div>
                <div class="mt-2 text-[11px] text-slate-600 italic bg-slate-100 p-1.5 rounded border border-slate-200">
                  ${feature.properties.guidance}
                </div>
              </div>
            `);
          }
        }).addTo(map);

        latestGeoJSON = geojson;
      } catch (err) {
        console.error("drawHazardZones error:", err);
      }
    }

    // Chart.js Sensitivity Curve
    function updateChart(elev, soil) {
      const rainSteps = [0, 30, 60, 90, 120, 150, 180, 210, 240];
      const riskScores = rainSteps.map(r => {
        const elevFactor = elev <= 0 ? 1.0 : (elev < 50 ? Math.max(0.1, 1.0 - (elev/50.0)) : 0.2);
        const precipFactor = Math.min(1.0, r / 250.0);
        const runoffFactor = 1.0 - (soil || 0.35);
        return ((elevFactor * 0.45 + precipFactor * 0.40 + runoffFactor * 0.15) * 100).toFixed(1);
      });

      const ctx = document.getElementById('riskChart').getContext('2d');
      if (riskChart) {
        riskChart.data.datasets[0].data = riskScores;
        riskChart.update();
      } else {
        riskChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: rainSteps.map(r => r + 'mm'),
            datasets: [{
              label: 'Vulnerability Index',
              data: riskScores,
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              fill: true,
              tension: 0.35,
              borderWidth: 2,
              pointRadius: 2.5
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } },
              y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }
            },
            plugins: { legend: { display: false } }
          }
        });
      }
    }

    // Download GeoJSON
    function downloadGeoJSON() {
      if (!latestGeoJSON) {
        alert("Please run a simulation first to generate the hazard layer.");
        return;
      }
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(latestGeoJSON, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `servir_${activeHazard}_layer_${currentLat.toFixed(2)}_${currentLon.toFixed(2)}.geojson`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }

    // AI Bounded Situation Report
    async function generateAIBriefing() {
      const score = parseFloat(document.getElementById('risk-score').innerText) || 50;
      const severity = document.getElementById('risk-badge').innerText || "MODERATE";
      const rain = parseFloat(document.getElementById('input-rain').value);
      const elev = parseFloat(document.getElementById('input-elev').value);
      const soil = parseFloat(document.getElementById('input-soil').value);

      const res = await fetch('/api/ai-briefing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hazard: activeHazard,
          score: score,
          severity: severity,
          rainfall: rain,
          elevation: elev,
          soil: soil,
          location_name: currentLocationName
        })
      });
      const data = await res.json();

      document.getElementById('ai-modal-title').innerText = data.situation_report;
      document.getElementById('ai-priority').innerText = data.readiness_priority;
      document.getElementById('ai-infra').innerText = data.critical_infrastructure_risk;
      document.getElementById('ai-agri').innerText = data.agricultural_livelihood_impact;
      document.getElementById('ai-assurance').innerText = data.assurance_note;

      const directivesUl = document.getElementById('ai-directives');
      directivesUl.innerHTML = "";
      data.civil_protection_directives.forEach(item => {
        const li = document.createElement('li');
        li.innerText = item;
        directivesUl.appendChild(li);
      });

      document.getElementById('ai-modal').classList.remove('hidden');
    }

    function closeAIModal() {
      document.getElementById('ai-modal').classList.add('hidden');
    }

    // Initial calculation on page load
    runSimulation();
  </script>
</body>
</html>
"""

async def homepage(request: Request):
    return HTMLResponse(HTML_DASHBOARD)

async def api_flood_risk(request: Request):
    body = await request.json()
    lat = float(body.get("latitude", 0.0))
    lon = float(body.get("longitude", 0.0))
    body["longitude"] = ((lon + 180.0) % 360.0 + 360.0) % 360.0 - 180.0
    body["latitude"] = max(-90.0, min(90.0, lat))
    validated = FloodVulnerabilityInput(**body)
    return JSONResponse(RiskEngine.calculate_flood_index(validated))

async def api_drought_risk(request: Request):
    body = await request.json()
    validated = DroughtAssessmentInput(**body)
    return JSONResponse(RiskEngine.calculate_drought_index(validated))

async def api_bounding_box(request: Request):
    body = await request.json()
    min_lat = max(-90.0, min(90.0, float(body["min_lat"])))
    max_lat = max(-90.0, min(90.0, float(body["max_lat"])))
    min_lon = max(-180.0, min(180.0, float(body["min_lon"])))
    max_lon = max(-180.0, min(180.0, float(body["max_lon"])))

    if max_lat < min_lat:
        min_lat, max_lat = max_lat, min_lat
    if max_lon < min_lon:
        min_lon, max_lon = max_lon, min_lon

    validated_bbox = BoundingBox(
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
    )
    hazard_type = body.get("hazard_type", "flood")
    precipitation_mm = float(body.get("precipitation_mm", 135.0))
    elevation_meters = float(body.get("elevation_meters", 2.5))
    soil_rate = float(body.get("soil_rate", 0.35))
    soil_moisture_pct = float(body.get("soil_moisture_pct", 20.0))
    surface_temp_celsius = float(body.get("surface_temp_celsius", 35.0))
    baseline_ndvi = float(body.get("baseline_ndvi", 0.25))
    grid_resolution = int(body.get("grid_resolution", 4))
    
    geojson_collection = RiskEngine.generate_bounding_box_risk_geojson(
        validated_bbox, 
        hazard_type=hazard_type,
        precipitation_mm=precipitation_mm,
        elevation_meters=elevation_meters,
        soil_rate=soil_rate,
        soil_moisture_pct=soil_moisture_pct,
        surface_temp_celsius=surface_temp_celsius,
        baseline_ndvi=baseline_ndvi,
        grid_resolution=grid_resolution
    )
    return JSONResponse(geojson_collection.model_dump())

async def api_ai_briefing(request: Request):
    body = await request.json()
    hazard = body.get("hazard", "flood")
    score = float(body.get("score", 50.0))
    severity = body.get("severity", "MODERATE")
    rainfall = float(body.get("rainfall", 100.0))
    elevation = float(body.get("elevation", 10.0))
    soil = float(body.get("soil", 0.5))
    location_name = body.get("location_name", "Target Region")

    briefing = RiskEngine.generate_bounded_ai_briefing(
        hazard=hazard,
        score=score,
        severity=severity,
        rainfall=rainfall,
        elevation=elevation,
        soil=soil,
        location_name=location_name
    )
    return JSONResponse(briefing)

app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/api/flood-risk", api_flood_risk, methods=["POST"]),
        Route("/api/drought-risk", api_drought_risk, methods=["POST"]),
        Route("/api/bounding-box-geojson", api_bounding_box, methods=["POST"]),
        Route("/api/ai-briefing", api_ai_briefing, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    print("\n=======================================================")
    print("[*] SERVIR Advanced Climate Risk Platform Starting...")
    print(" -> Dashboard URL: http://localhost:8000")
    print("=======================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
