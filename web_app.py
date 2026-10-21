"""
Interactive Geospatial Climate Risk Dashboard.
Combines FastAPI with a modern, responsive Leaflet map interface for visual testing.
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
  <title>SERVIR Climate Risk Platform | Decision Support</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    #map { height: calc(100vh - 80px); width: 100%; border-radius: 0.75rem; }
    .glass { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen flex flex-col">

  <!-- Header -->
  <header class="h-20 border-b border-slate-800 px-6 flex items-center justify-between glass sticky top-0 z-50">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-xl">
        GIS
      </div>
      <div>
        <h1 class="font-bold text-lg text-white tracking-wide">SERVIR Global Risk Platform</h1>
        <p class="text-xs text-slate-400">Deterministic Climate Analytics & GeoJSON Decision Engine</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        FastMCP Engine Online
      </span>
      <a href="https://github.com/Huighlet/geospatial-risk-mcp-server" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition">
        GitHub Repo
      </a>
    </div>
  </header>

  <!-- Main Content Grid -->
  <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
    
    <!-- Left Sidebar: Controls & Analytics -->
    <div class="lg:col-span-4 flex flex-col gap-5 overflow-y-auto max-h-[calc(100vh-110px)] pr-1">
      
      <!-- Control Panel Card -->
      <div class="glass p-5 rounded-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 class="font-semibold text-sm text-slate-200 uppercase tracking-wider">Hazard Simulation Inputs</h2>
          <span class="text-xs text-slate-400">Bangkok Basin (13.75°N, 100.50°E)</span>
        </div>

        <!-- Rainfall Slider -->
        <div>
          <div class="flex justify-between text-xs font-medium mb-1.5">
            <span class="text-slate-300">24h Rainfall Forecast</span>
            <span id="val-rain" class="text-emerald-400 font-bold">135 mm</span>
          </div>
          <input type="range" id="input-rain" min="0" max="250" value="135" class="w-full accent-emerald-500 cursor-pointer" oninput="updateValues()">
          <div class="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>0 mm (Dry)</span>
            <span>125 mm (Heavy)</span>
            <span>250 mm (Extreme)</span>
          </div>
        </div>

        <!-- Elevation Slider -->
        <div>
          <div class="flex justify-between text-xs font-medium mb-1.5">
            <span class="text-slate-300">Surface Elevation (Above Sea Level)</span>
            <span id="val-elev" class="text-cyan-400 font-bold">2.5 m</span>
          </div>
          <input type="range" id="input-elev" min="0" max="100" step="0.5" value="2.5" class="w-full accent-cyan-500 cursor-pointer" oninput="updateValues()">
          <div class="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>0 m (Sea Level)</span>
            <span>50 m</span>
            <span>100 m</span>
          </div>
        </div>

        <!-- Soil Absorption -->
        <div>
          <div class="flex justify-between text-xs font-medium mb-1.5">
            <span class="text-slate-300">Soil Percolation Rate</span>
            <span id="val-soil" class="text-indigo-400 font-bold">0.35</span>
          </div>
          <input type="range" id="input-soil" min="0.0" max="1.0" step="0.05" value="0.35" class="w-full accent-indigo-500 cursor-pointer" oninput="updateValues()">
          <div class="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>0.0 (Impermeable Concrete)</span>
            <span>1.0 (Highly Porous)</span>
          </div>
        </div>

        <button onclick="runSimulation()" class="w-full mt-2 py-3 px-4 rounded-xl font-semibold text-sm bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2">
          <span>Run Deterministic Assessment</span>
        </button>
      </div>

      <!-- Telemetry Output Card -->
      <div id="result-card" class="glass p-5 rounded-2xl flex flex-col gap-4">
        <h3 class="font-semibold text-xs text-slate-400 uppercase tracking-wider">Computed Risk Metrics</h3>
        
        <div class="flex items-center justify-between">
          <div>
            <div class="text-3xl font-extrabold text-white" id="risk-score">--</div>
            <div class="text-xs text-slate-400 mt-0.5">Flood Vulnerability Index (0-100)</div>
          </div>
          <div id="risk-badge" class="px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-300">
            Awaiting Input
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 leading-relaxed" id="risk-action">
          Click "Run Deterministic Assessment" to calculate flood vulnerability and generate GeoJSON hazard layers.
        </div>
      </div>
      
    </div>

    <!-- Right Area: Interactive Leaflet Map -->
    <div class="lg:col-span-8 glass p-3 rounded-2xl relative">
      <div id="map"></div>
      
      <!-- Map Overlay Legend -->
      <div class="absolute bottom-6 right-6 z-[1000] glass px-4 py-3 rounded-xl shadow-xl flex flex-col gap-2 text-xs">
        <div class="font-bold text-slate-300 text-[11px] uppercase tracking-wider border-b border-slate-700/60 pb-1">Hazard Severity</div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-red-500"></span> <span>Critical / High (&gt;60)</span></div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-amber-500"></span> <span>Moderate Risk (30-60)</span></div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-emerald-500"></span> <span>Low Risk (&lt;30)</span></div>
      </div>
    </div>

  </div>

  <script>
    // Initialize Leaflet Map centered on Bangkok / Gulf of Thailand
    const map = L.map('map').setView([13.7563, 100.5018], 9);
    
    // Add 100% Free OpenStreetMap & Satellite Layers (Zero API Key Required)
    const streetLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });

    // Layer Toggle Controls
    L.control.layers({
      "OpenStreetMap (Streets)": streetLayer,
      "Satellite Imagery": satelliteLayer
    }, null, { position: 'topright' }).addTo(map);

    let geojsonLayer = null;

    function updateValues() {
      document.getElementById('val-rain').innerText = document.getElementById('input-rain').value + ' mm';
      document.getElementById('val-elev').innerText = document.getElementById('input-elev').value + ' m';
      document.getElementById('val-soil').innerText = document.getElementById('input-soil').value;
    }

    async function runSimulation() {
      const rain = parseFloat(document.getElementById('input-rain').value);
      const elev = parseFloat(document.getElementById('input-elev').value);
      const soil = parseFloat(document.getElementById('input-soil').value);

      // Call Backend API
      const res = await fetch('/api/flood-risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: 13.7563,
          longitude: 100.5018,
          elevation_meters: elev,
          precipitation_mm: rain,
          soil_absorption_rate: soil
        })
      });
      const data = await res.json();

      // Update Telemetry Card
      document.getElementById('risk-score').innerText = data.flood_vulnerability_index;
      document.getElementById('risk-action').innerText = data.operational_guidance;
      
      const badge = document.getElementById('risk-badge');
      badge.innerText = data.severity_level;
      if (data.severity_level === 'CRITICAL') {
        badge.className = 'px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/40';
      } else if (data.severity_level === 'HIGH') {
        badge.className = 'px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-orange-500/20 text-orange-400 border border-orange-500/40';
      } else if (data.severity_level === 'MODERATE') {
        badge.className = 'px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/40';
      } else {
        badge.className = 'px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
      }

      // Fetch and draw GeoJSON polygons
      drawHazardZones();
    }

    async function drawHazardZones() {
      const res = await fetch('/api/bounding-box-geojson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          min_lat: 13.0,
          min_lon: 100.0,
          max_lat: 14.5,
          max_lon: 101.5
        })
      });
      const geojson = await res.json();

      if (geojsonLayer) {
        map.removeLayer(geojsonLayer);
      }

      geojsonLayer = L.geoJSON(geojson, {
        style: function(feature) {
          const score = feature.properties.risk_score;
          let color = '#10b981';
          if (score > 60) color = '#ef4444';
          else if (score > 30) color = '#f59e0b';
          
          return {
            color: color,
            weight: 2,
            opacity: 0.8,
            fillColor: color,
            fillOpacity: 0.35
          };
        },
        onEachFeature: function(feature, layer) {
          layer.bindPopup(`
            <div class="font-sans text-xs">
              <div class="font-bold text-slate-900 border-b pb-1 mb-1">${feature.properties.cell_id}</div>
              <div><b>Hazard:</b> ${feature.properties.hazard_type}</div>
              <div><b>Risk Score:</b> ${feature.properties.risk_score}</div>
              <div><b>Severity:</b> ${feature.properties.severity}</div>
            </div>
          `);
        }
      }).addTo(map);

      map.fitBounds(geojsonLayer.getBounds());
    }

    // Auto-run once on load
    runSimulation();
  </script>
</body>
</html>
"""

async def homepage(request: Request):
    return HTMLResponse(HTML_DASHBOARD)

async def api_flood_risk(request: Request):
    body = await request.json()
    validated = FloodVulnerabilityInput(**body)
    return JSONResponse(RiskEngine.calculate_flood_index(validated))

async def api_drought_risk(request: Request):
    body = await request.json()
    validated = DroughtAssessmentInput(**body)
    return JSONResponse(RiskEngine.calculate_drought_index(validated))

async def api_bounding_box(request: Request):
    body = await request.json()
    validated = BoundingBox(**body)
    geojson_collection = RiskEngine.generate_bounding_box_risk_geojson(validated)
    return JSONResponse(geojson_collection.model_dump())

app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/api/flood-risk", api_flood_risk, methods=["POST"]),
        Route("/api/drought-risk", api_drought_risk, methods=["POST"]),
        Route("/api/bounding-box-geojson", api_bounding_box, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    print("\n=======================================================")
    print("[*] SERVIR Climate Risk Web Platform Starting...")
    print(" -> Dashboard URL: http://localhost:8000")
    print("=======================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
