"""
Interactive Geospatial Climate Risk Dashboard (Global Multi-Region Edition).
Features:
- Global English Map Tiles (Esri World Street Map & Satellite).
- Search Any City / Place Name (Nominatim Global Geocoder).
- Click Anywhere on Map with robust 360-degree Longitude Normalization.
- Real-time Slider-driven GeoJSON Hazard Polygon Coloring.
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
  <title>SERVIR Global Risk Platform | Decision Support System</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    #map { height: calc(100vh - 84px); width: 100%; border-radius: 1rem; }
    .glass { background: rgba(15, 23, 42, 0.90); backdrop-filter: blur(14px); border: 1px solid rgba(255, 255, 255, 0.12); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen flex flex-col">

  <!-- Header -->
  <header class="h-20 border-b border-slate-800 px-6 flex items-center justify-between glass sticky top-0 z-50">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white font-black text-xl shadow-lg shadow-emerald-500/20">
        G
      </div>
      <div>
        <h1 class="font-bold text-base md:text-lg text-white tracking-wide">SERVIR Global Risk Platform</h1>
        <p class="text-xs text-slate-400">Earth Observation Decision Support & FastMCP Geospatial Engine</p>
      </div>
    </div>
    
    <div class="flex items-center gap-3">
      <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        Deterministic Mode Active
      </div>
      <a href="https://github.com/Huighlet/geospatial-risk-mcp-server" target="_blank" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition">
        GitHub Source
      </a>
    </div>
  </header>

  <!-- Main Content Grid -->
  <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 p-5">
    
    <!-- Left Sidebar: Controls & Analytics -->
    <div class="lg:col-span-4 flex flex-col gap-4 overflow-y-auto max-h-[calc(100vh-104px)] pr-1">
      
      <!-- Place Search & Hub Presets -->
      <div class="glass p-5 rounded-2xl flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-xs font-bold text-slate-300 uppercase tracking-wider">Search Any Location</label>
          <span id="search-status" class="text-[11px] text-emerald-400 font-medium">Global Geocoder</span>
        </div>
        
        <!-- Search Input Bar -->
        <div class="flex gap-2">
          <input 
            type="text" 
            id="search-input" 
            placeholder="Type city or place (e.g. Accra, Kumasi, Nairobi, Tokyo)..." 
            class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            onkeydown="if(event.key === 'Enter') searchLocation()"
          />
          <button 
            onclick="searchLocation()" 
            class="px-3.5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center justify-center">
            Find
          </button>
        </div>

        <!-- Preset Dropdown -->
        <div class="mt-1">
          <label class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Or Quick-Select UN/SERVIR Hub</label>
          <select id="region-select" onchange="changeRegion()" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer">
            <option value="bangkok">Thailand -- Bangkok Lowland Basin (13.75N, 100.50E)</option>
            <option value="vietnam">Vietnam -- Mekong Delta Floodplains (10.04N, 105.78E)</option>
            <option value="philippines">Philippines -- Manila Coastal Typhoon Zone (14.59N, 120.98E)</option>
            <option value="kenya">Kenya -- Rift Valley & Nairobi Basin (-1.29S, 36.82E)</option>
            <option value="ghana">Ghana -- Accra Coastal Plains & Volta Basin (5.60N, -0.18W)</option>
            <option value="bangladesh">Bangladesh -- Sundarbans Lowland Delta (22.50N, 89.50E)</option>
          </select>
        </div>
        
        <p class="text-[11px] text-slate-400 leading-relaxed border-t border-slate-800/80 pt-2">
          💡 <b>Interactive Map:</b> Click anywhere on the map to set a custom analysis point.
        </p>
      </div>

      <!-- Hazard Simulation Controls -->
      <div class="glass p-5 rounded-2xl flex flex-col gap-4">
        <div class="border-b border-slate-800 pb-2 flex items-center justify-between">
          <h2 class="font-bold text-xs text-slate-200 uppercase tracking-wider">Environmental Simulation Inputs</h2>
          <span class="text-[10px] text-emerald-400 font-mono" id="current-coords">Lat: 13.75 | Lon: 100.50</span>
        </div>

        <!-- Rainfall Slider -->
        <div>
          <div class="flex justify-between text-xs font-semibold mb-1">
            <span class="text-slate-300">24h Rainfall Forecast</span>
            <span id="val-rain" class="text-emerald-400 font-bold">135 mm</span>
          </div>
          <input type="range" id="input-rain" min="0" max="250" value="135" class="w-full accent-emerald-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          <div class="flex justify-between text-[10px] text-slate-500 mt-0.5">
            <span>0 mm (Dry)</span>
            <span>125 mm (Heavy)</span>
            <span>250 mm (Extreme)</span>
          </div>
        </div>

        <!-- Elevation Slider -->
        <div>
          <div class="flex justify-between text-xs font-semibold mb-1">
            <span class="text-slate-300">Surface Elevation (Above Sea Level)</span>
            <span id="val-elev" class="text-cyan-400 font-bold">2.5 m</span>
          </div>
          <input type="range" id="input-elev" min="0" max="100" step="0.5" value="2.5" class="w-full accent-cyan-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          <div class="flex justify-between text-[10px] text-slate-500 mt-0.5">
            <span>0 m (Sea Level)</span>
            <span>50 m</span>
            <span>100 m</span>
          </div>
        </div>

        <!-- Soil Absorption -->
        <div>
          <div class="flex justify-between text-xs font-semibold mb-1">
            <span class="text-slate-300">Soil Percolation Rate</span>
            <span id="val-soil" class="text-indigo-400 font-bold">0.35</span>
          </div>
          <input type="range" id="input-soil" min="0.0" max="1.0" step="0.05" value="0.35" class="w-full accent-indigo-500 cursor-pointer" oninput="updateValuesAndTrigger()">
          <div class="flex justify-between text-[10px] text-slate-500 mt-0.5">
            <span>0.0 (Impermeable Concrete)</span>
            <span>1.0 (Highly Porous)</span>
          </div>
        </div>
      </div>

      <!-- Live Computed Risk Metrics -->
      <div id="result-card" class="glass p-5 rounded-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Computed Risk Telemetry</span>
          <div id="risk-badge" class="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/40">
            HIGH
          </div>
        </div>
        
        <div class="flex items-baseline gap-2">
          <div class="text-4xl font-black text-white" id="risk-score">74.1</div>
          <div class="text-xs text-slate-400">/ 100 (Flood Vulnerability Index)</div>
        </div>

        <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 leading-relaxed" id="risk-action">
          Activate municipal drainage systems and issue public hazard alerts.
        </div>

        <!-- Export GeoJSON Layer Button -->
        <button onclick="downloadGeoJSON()" class="w-full py-2.5 px-3 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-500/30 transition flex items-center justify-center gap-2 shadow-md">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
          <span>Export RFC 7946 GeoJSON Layer</span>
        </button>
      </div>
      
    </div>

    <!-- Right Area: Interactive Leaflet Map -->
    <div class="lg:col-span-8 glass p-2 rounded-2xl relative shadow-2xl overflow-hidden">
      <div id="map"></div>
      
      <!-- Dynamic Map Legend -->
      <div class="absolute bottom-5 right-5 z-[1000] glass px-4 py-3 rounded-xl shadow-2xl flex flex-col gap-2 text-xs border border-slate-700/60">
        <div class="font-bold text-slate-300 text-[11px] uppercase tracking-wider border-b border-slate-700/60 pb-1 flex justify-between gap-4">
          <span>Hazard Severity</span>
          <span class="text-slate-400 text-[10px]">Real-Time GeoJSON</span>
        </div>
        <div class="flex items-center gap-2"><span class="w-3.5 h-3.5 rounded-md bg-red-500 shadow-sm shadow-red-500/50"></span> <span>Critical Risk (&ge;75)</span></div>
        <div class="flex items-center gap-2"><span class="w-3.5 h-3.5 rounded-md bg-orange-500 shadow-sm shadow-orange-500/50"></span> <span>High Risk (50-74)</span></div>
        <div class="flex items-center gap-2"><span class="w-3.5 h-3.5 rounded-md bg-amber-400 shadow-sm shadow-amber-400/50"></span> <span>Moderate Risk (25-49)</span></div>
        <div class="flex items-center gap-2"><span class="w-3.5 h-3.5 rounded-md bg-emerald-500 shadow-sm shadow-emerald-500/50"></span> <span>Low Risk (&lt;25)</span></div>
      </div>
    </div>

  </div>

  <script>
    // Region Presets
    const REGIONS = {
      bangkok: { lat: 13.7563, lon: 100.5018, elev: 2.5, rain: 135, name: "Bangkok Basin, Thailand" },
      vietnam: { lat: 10.0452, lon: 105.7469, elev: 1.8, rain: 160, name: "Mekong Delta, Vietnam" },
      philippines: { lat: 14.5995, lon: 120.9842, elev: 4.0, rain: 190, name: "Manila Bay, Philippines" },
      kenya: { lat: -1.2921, lon: 36.8219, elev: 1680.0, rain: 45, name: "Nairobi Basin, Kenya" },
      ghana: { lat: 5.6037, lon: -0.1870, elev: 20.0, rain: 75, name: "Accra Coastal Plains, Ghana" },
      bangladesh: { lat: 22.5000, lon: 89.5000, elev: 1.2, rain: 180, name: "Sundarbans Delta, Bangladesh" }
    };

    let currentLat = 13.7563;
    let currentLon = 100.5018;

    // Helper: Normalize longitude to [-180, 180] and clamp latitude to [-85, 85]
    function normalizeCoords(lat, lon) {
      let normLon = ((lon + 180) % 360 + 360) % 360 - 180;
      let clampLat = Math.max(-85, Math.min(85, lat));
      return { lat: clampLat, lon: normLon };
    }

    // Initialize Leaflet Map
    const map = L.map('map', { worldCopyJump: true }).setView([currentLat, currentLon], 9);
    
    // 1. ESRI World Street Map (English Labels Globally)
    const englishStreets = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, TomTom'
    }).addTo(map);

    // 2. ESRI High-Res Satellite Imagery
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri, i-cubed, USDA, USGS, AEX, GeoEye, GIS User Community'
    });

    // 3. OpenStreetMap
    const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    });

    // Layer Controls
    L.control.layers({
      "English World Street Map": englishStreets,
      "Satellite Imagery": satellite,
      "Standard OpenStreetMap": osm
    }, null, { position: 'topright' }).addTo(map);

    let geojsonLayer = null;
    let targetMarker = L.marker([currentLat, currentLon]).addTo(map).bindPopup("Current Risk Analysis Target");

    // Click anywhere on map to analyze that location!
    map.on('click', function(e) {
      const norm = normalizeCoords(e.latlng.lat, e.latlng.lng);
      currentLat = norm.lat;
      currentLon = norm.lon;

      targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`Target: ${currentLat.toFixed(3)}N, ${currentLon.toFixed(3)}E`).openPopup();
      document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
      document.getElementById('region-select').value = ""; // clear preset dropdown
      document.getElementById('search-status').innerText = "Target Selected";
      runSimulation();
    });

    // Search Location by Name via Nominatim Geocoding API
    async function searchLocation() {
      const query = document.getElementById('search-input').value.trim();
      if (!query) return;

      const statusEl = document.getElementById('search-status');
      statusEl.innerText = "Searching...";

      try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const results = await response.json();

        if (results && results.length > 0) {
          const top = results[0];
          const norm = normalizeCoords(parseFloat(top.lat), parseFloat(top.lon));
          currentLat = norm.lat;
          currentLon = norm.lon;

          map.flyTo([currentLat, currentLon], 10);
          targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`<b>${top.display_name.split(',')[0]}</b><br><span class="text-[11px] text-slate-500">${top.display_name}</span>`).openPopup();
          
          document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
          statusEl.innerText = `Located: ${top.display_name.split(',')[0]}`;
          
          runSimulation();
        } else {
          statusEl.innerText = "Location not found. Try another city.";
        }
      } catch (err) {
        console.error("Geocoding error:", err);
        statusEl.innerText = "Search service unavailable.";
      }
    }

    function changeRegion() {
      const selected = document.getElementById('region-select').value;
      if (!selected || !REGIONS[selected]) return;
      const r = REGIONS[selected];
      currentLat = r.lat;
      currentLon = r.lon;

      document.getElementById('input-elev').value = r.elev > 100 ? 50 : r.elev;
      document.getElementById('input-rain').value = r.rain;
      
      map.flyTo([currentLat, currentLon], 9);
      targetMarker.setLatLng([currentLat, currentLon]).bindPopup(r.name).openPopup();
      document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
      document.getElementById('search-status').innerText = r.name;
      
      updateValuesAndTrigger();
    }

    let debounceTimer = null;
    function updateValuesAndTrigger() {
      document.getElementById('val-rain').innerText = document.getElementById('input-rain').value + ' mm';
      document.getElementById('val-elev').innerText = document.getElementById('input-elev').value + ' m';
      document.getElementById('val-soil').innerText = document.getElementById('input-soil').value;
      
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runSimulation, 50); // fast 50ms response
    }

    async function runSimulation() {
      const rain = parseFloat(document.getElementById('input-rain').value);
      const elev = parseFloat(document.getElementById('input-elev').value);
      const soil = parseFloat(document.getElementById('input-soil').value);

      try {
        // 1. Call Backend API for Core Metrics
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
        
        if (!res.ok) {
          console.error("Backend error:", await res.text());
          return;
        }

        const data = await res.json();

        // Update Telemetry Card
        document.getElementById('risk-score').innerText = (data.flood_vulnerability_index || 0).toFixed(1);
        document.getElementById('risk-action').innerText = data.operational_guidance || "Normal monitoring.";
        
        const badge = document.getElementById('risk-badge');
        badge.innerText = data.severity_level || "UNKNOWN";
        if (data.severity_level === 'CRITICAL') {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse';
        } else if (data.severity_level === 'HIGH') {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-orange-500/20 text-orange-400 border border-orange-500/50';
        } else if (data.severity_level === 'MODERATE') {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/50';
        } else {
          badge.className = 'px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/50';
        }

        // 2. Draw and color the GeoJSON polygons based on these exact numbers
        await drawHazardZones(rain, elev, soil);
      } catch (err) {
        console.error("Simulation error:", err);
      }
    }

    async function drawHazardZones(rain, elev, soil) {
      try {
        const norm = normalizeCoords(currentLat, currentLon);
        const minLat = Math.max(-85, norm.lat - 0.65);
        const maxLat = Math.min(85, norm.lat + 0.65);
        let minLon = norm.lon - 0.75;
        let maxLon = norm.lon + 0.75;

        // Ensure valid longitude bounds
        if (minLon < -180) minLon = -180;
        if (maxLon > 180) maxLon = 180;

        const res = await fetch('/api/bounding-box-geojson', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            min_lat: minLat,
            min_lon: minLon,
            max_lat: maxLat,
            max_lon: maxLon,
            precipitation_mm: rain,
            elevation_meters: elev,
            soil_rate: soil
          })
        });

        if (!res.ok) {
          console.error("GeoJSON error:", await res.text());
          return;
        }

        const geojson = await res.json();

        if (geojsonLayer) {
          map.removeLayer(geojsonLayer);
        }

        geojsonLayer = L.geoJSON(geojson, {
          style: function(feature) {
            const score = feature.properties.risk_score;
            let color = '#10b981'; // Green (Low)
            let opacity = 0.35;
            if (score >= 75) {
              color = '#ef4444'; // Red (Critical)
              opacity = 0.55;
            } else if (score >= 50) {
              color = '#f97316'; // Orange (High)
              opacity = 0.45;
            } else if (score >= 25) {
              color = '#f59e0b'; // Amber (Moderate)
              opacity = 0.35;
            }
            
            return {
              color: color,
              weight: 2.5,
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
                  <div><b>Risk Score:</b> ${feature.properties.risk_score} / 100</div>
                  <div><b>Cell Elevation:</b> ${feature.properties.elevation_m} m</div>
                  <div><b>Rainfall:</b> ${feature.properties.precipitation_mm} mm</div>
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

    function downloadGeoJSON() {
      if (!latestGeoJSON) {
        alert("Please run a simulation first to generate the hazard layer.");
        return;
      }
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(latestGeoJSON, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `servir_hazard_layer_${currentLat.toFixed(2)}_${currentLon.toFixed(2)}.geojson`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
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
    # Normalize longitude & clamp latitude so out-of-bounds never throws 500
    lat = float(body.get("latitude", 0.0))
    lon = float(body.get("longitude", 0.0))
    norm_lon = ((lon + 180.0) % 360.0 + 360.0) % 360.0 - 180.0
    clamp_lat = max(-90.0, min(90.0, lat))
    body["latitude"] = clamp_lat
    body["longitude"] = norm_lon
    
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

    # Ensure max >= min
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
    precipitation_mm = float(body.get("precipitation_mm", 135.0))
    elevation_meters = float(body.get("elevation_meters", 2.5))
    soil_rate = float(body.get("soil_rate", 0.35))
    
    geojson_collection = RiskEngine.generate_bounding_box_risk_geojson(
        validated_bbox, 
        hazard_type="flood",
        precipitation_mm=precipitation_mm,
        elevation_meters=elevation_meters,
        soil_rate=soil_rate
    )
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
    print("[*] SERVIR Climate Risk Global Platform Starting...")
    print(" -> Dashboard URL: http://localhost:8000")
    print("=======================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
