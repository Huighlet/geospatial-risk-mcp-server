"""
Interactive Geospatial Climate Risk Dashboard (GeoRisk Decision Support System).
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
import json
import urllib.request
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
  <title>GeoRisk Platform | Multi-Hazard Decision Support System</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    #map { height: 475px; width: 100%; border-radius: 0.75rem; }
    .panel { background: #0b1120; border: 1px solid #1e293b; }
    .stat-box { background: #070d19; border: 1px solid #1e293b; }
    .scrollbar-thin::-webkit-scrollbar { width: 5px; }
    .scrollbar-thin::-webkit-scrollbar-thumb { background: #334155; border-radius: 9999px; }

    /* Dark GIS Leaflet Popup Override */
    .leaflet-popup-content-wrapper {
      background: #0b1120 !important;
      color: #f1f5f9 !important;
      border: 1px solid #334155 !important;
      border-radius: 0.6rem !important;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.75) !important;
    }
    .leaflet-popup-tip {
      background: #0b1120 !important;
      border: 1px solid #334155 !important;
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen flex flex-col selection:bg-emerald-500 selection:text-slate-950">

  <!-- Header -->
  <header class="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-950/95 sticky top-0 z-50">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="font-bold text-sm md:text-base text-white tracking-tight">GeoRisk Platform</h1>
          <span class="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">DSS v2.4</span>
        </div>
        <p class="text-[11px] text-slate-400 font-medium">Earth Observation Multi-Hazard Intelligence · FastMCP Decision Support</p>
      </div>
    </div>
    
    <!-- Hazard Mode Switcher -->
    <div class="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-lg">
      <button id="mode-flood-btn" onclick="setHazardMode('flood')" class="px-3 py-1 rounded-md text-xs font-semibold transition bg-emerald-600 text-white shadow-sm flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-white"></span>
        <span>Flood Inundation</span>
      </button>
      <button id="mode-drought-btn" onclick="setHazardMode('drought')" class="px-3 py-1 rounded-md text-xs font-semibold transition text-slate-400 hover:text-slate-200 flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-transparent"></span>
        <span>Agricultural Drought</span>
      </button>
    </div>

    <div class="hidden sm:flex items-center gap-3">
      <a href="https://github.com/Huighlet/geospatial-risk-mcp-server" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition flex items-center gap-1.5">
        <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"></path></svg>
        <span>GitHub Repository</span>
      </a>
    </div>
  </header>

  <!-- Main Grid -->
  <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4">
    
    <!-- Left Sidebar: Controls, Scenarios & Advisory -->
    <div class="lg:col-span-5 flex flex-col gap-3.5 overflow-y-auto max-h-[calc(100vh-80px)] pr-1 scrollbar-thin">
      
      <!-- Target Location Domain & Regional Observatories -->
      <div class="panel p-3.5 rounded-xl flex flex-col gap-2.5">
        <div class="flex items-center justify-between">
          <label class="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Target Geographic Domain</label>
          <span id="search-status" class="text-[10px] text-emerald-400 font-mono">Nominatim Geocoder API · Online</span>
        </div>
        
        <div class="flex gap-2">
          <input 
            type="text" 
            id="search-input" 
            placeholder="Search city, province, or coordinates..." 
            class="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            onkeydown="if(event.key === 'Enter') searchLocation()"
          />
          <button 
            onclick="searchLocation()" 
            class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition">
            Locate
          </button>
        </div>

        <!-- Regional Observatories -->
        <div class="flex flex-wrap gap-1.5 pt-1">
          <span class="text-[10px] font-bold text-slate-500 self-center uppercase tracking-wider mr-1">Observatories:</span>
          <button onclick="jumpToHub('keta')" class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60 transition">Keta (West Africa)</button>
          <button onclick="jumpToHub('bangkok')" class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60 transition">Bangkok (Chao Phraya)</button>
          <button onclick="jumpToHub('kenya')" class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60 transition">Nairobi (Rift Valley)</button>
          <button onclick="jumpToHub('vietnam')" class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60 transition">Mekong Delta</button>
          <button onclick="jumpToHub('philippines')" class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60 transition">Manila Bay</button>
        </div>
      </div>

      <!-- Climate Change Scenario Selectors (Sendai Framework Projections) -->
      <div class="panel p-3.5 rounded-xl flex flex-col gap-2">
        <label class="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Climate Change Scenario Projections</label>
        <div class="grid grid-cols-3 gap-2">
          <button onclick="applyScenario('baseline')" class="px-2.5 py-2 rounded-lg text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition flex flex-col">
            <span class="text-[10px] font-semibold text-slate-400">Baseline</span>
            <span class="text-xs font-bold text-emerald-400 mt-0.5">10-Yr Return</span>
            <span class="text-[10px] text-slate-500 font-mono mt-0.5">45 mm</span>
          </button>
          <button onclick="applyScenario('monsoon')" class="px-2.5 py-2 rounded-lg text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition flex flex-col">
            <span class="text-[10px] font-semibold text-slate-400">2030 (+1.5°C)</span>
            <span class="text-xs font-bold text-amber-400 mt-0.5">SSP2-4.5</span>
            <span class="text-[10px] text-slate-500 font-mono mt-0.5">120 mm</span>
          </button>
          <button onclick="applyScenario('extreme')" class="px-2.5 py-2 rounded-lg text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition flex flex-col">
            <span class="text-[10px] font-semibold text-slate-400">2050 (Extreme)</span>
            <span class="text-xs font-bold text-red-400 mt-0.5">SSP5-8.5</span>
            <span class="text-[10px] text-slate-500 font-mono mt-0.5">210 mm</span>
          </button>
        </div>
      </div>

      <!-- Simulation Sliders (Dynamic for Flood vs Drought) -->
      <div class="panel p-3.5 rounded-xl flex flex-col gap-3">
        <div class="border-b border-slate-800 pb-2 flex items-center justify-between">
          <h2 class="font-bold text-xs text-slate-200 uppercase tracking-wider" id="slider-panel-title">Hydrologic Parameters</h2>
          <span class="text-[10px] text-emerald-400 font-mono" id="current-coords">Lat: 5.92 | Lon: 0.99</span>
        </div>

        <!-- FLOOD INPUTS -->
        <div id="flood-controls" class="space-y-3">
          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">24h Rainfall Forecast</span>
              <span id="val-rain" class="text-emerald-400 font-mono font-bold">135 mm</span>
            </div>
            <input type="range" id="input-rain" min="0" max="250" value="135" class="w-full accent-emerald-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="text-[9px] text-slate-500 font-mono mt-0.5">Sensor: NASA GPM IMERG Early Run (0.1° × 0.1°)</div>
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Surface Elevation (Above Sea Level)</span>
              <span id="val-elev" class="text-cyan-400 font-mono font-bold">2.5 m</span>
            </div>
            <input type="range" id="input-elev" min="0" max="200" step="0.5" value="2.5" class="w-full accent-cyan-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="flex justify-between text-[9px] text-slate-500 font-mono mt-0.5">
              <span>Sensor: NASADEM / SRTM v3 (30m HGT)</span>
              <span id="elev-badge" class="text-cyan-400 cursor-pointer hover:underline" onclick="fetchTerrainElevation(currentLat, currentLon)" title="Auto-detected from live SRTM satellite DEM">Live SRTM Auto-Detect</span>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Soil Porosity & Percolation Rate</span>
              <span id="val-soil" class="text-indigo-400 font-mono font-bold">0.35</span>
            </div>
            <input type="range" id="input-soil" min="0.0" max="1.0" step="0.05" value="0.35" class="w-full accent-indigo-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="flex justify-between text-[9px] text-slate-500 font-mono mt-0.5">
              <span>Parameter: USDA-NRCS Curve</span>
              <span class="text-slate-500">0.05 Clay · 0.85 Sand</span>
            </div>
          </div>
        </div>

        <!-- DROUGHT INPUTS (Initially Hidden) -->
        <div id="drought-controls" class="space-y-3 hidden">
          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Topsoil Moisture Content</span>
              <span id="val-moist" class="text-amber-400 font-mono font-bold">18 %</span>
            </div>
            <input type="range" id="input-moist" min="0" max="100" value="18" class="w-full accent-amber-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="flex justify-between text-[9px] text-slate-500 font-mono mt-0.5">
              <span>Sensor: NASA SMAP L4 Global (9 km)</span>
              <span class="text-slate-600">0% Arid · 100% Saturated</span>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Land Surface Temperature</span>
              <span id="val-temp" class="text-red-400 font-mono font-bold">38 °C</span>
            </div>
            <input type="range" id="input-temp" min="15" max="55" value="38" class="w-full accent-red-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="text-[9px] text-slate-500 font-mono mt-0.5">Sensor: MODIS / VIIRS Terra-Aqua L3 Thermal (1 km)</div>
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-300">Vegetation Health Index (NDVI)</span>
              <span id="val-ndvi" class="text-emerald-400 font-mono font-bold">0.24</span>
            </div>
            <input type="range" id="input-ndvi" min="-0.2" max="1.0" step="0.02" value="0.24" class="w-full accent-emerald-500 cursor-pointer" oninput="updateValuesAndTrigger()">
            <div class="text-[9px] text-slate-500 font-mono mt-0.5">Sensor: Sentinel-2 MSI / MODIS 16-Day NDVI Composite</div>
          </div>
        </div>
      </div>

      <!-- Live Computed Risk Metrics & Advisory Actions -->
      <div id="result-card" class="panel p-3.5 rounded-xl flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider" id="metric-title">Computed Flood Vulnerability</span>
          <div id="risk-badge" class="px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/30">
            HIGH
          </div>
        </div>
        
        <div class="flex items-baseline gap-2">
          <div class="text-3xl font-extrabold text-white font-mono" id="risk-score">69.8</div>
          <div class="text-xs text-slate-400 font-medium" id="scale-label">/ 100 Index</div>
        </div>

        <div class="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans" id="risk-action">
          Activate municipal drainage systems and issue public hazard alerts.
        </div>

        <div class="grid grid-cols-2 gap-2 pt-1">
          <!-- Operational SITREP Briefing Button -->
          <button onclick="generateSITREPBriefing()" class="py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center justify-center gap-1.5 shadow-sm">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            <span>Operational SITREP</span>
          </button>

          <!-- Export GeoJSON Layer -->
          <button onclick="downloadGeoJSON()" class="py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center justify-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            <span>Export RFC 7946</span>
          </button>
        </div>
      </div>
      
    </div>

    <!-- Right Area: Map & Live Risk Response Curve -->
    <div class="lg:col-span-7 flex flex-col gap-3.5">
      
      <!-- Interactive Map Card -->
      <div class="panel p-2 rounded-xl relative shadow-xl overflow-hidden flex flex-col gap-1.5">
        <div class="flex items-center justify-between px-2 pt-0.5 text-xs text-slate-400">
          <div class="flex items-center gap-2.5">
            <span class="font-bold text-[10px] text-slate-300 uppercase tracking-wider">Spatial Risk Domain</span>
            <div class="flex items-center gap-1.5 bg-slate-900/90 px-2 py-0.5 rounded border border-slate-800 text-[10px]">
              <span class="text-slate-500 uppercase">Alpha:</span>
              <input type="range" id="opacity-slider" min="10" max="90" value="45" class="w-16 accent-emerald-500 cursor-pointer" oninput="setGridOpacity(this.value)">
              <span id="val-opacity" class="font-mono text-slate-300">45%</span>
            </div>
            <button id="toggle-grid-btn" onclick="toggleGridVisibility()" class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
              Hide Grid
            </button>
          </div>
          <div class="hidden sm:flex items-center gap-1 font-mono text-[10px] text-slate-400">
            <span class="text-slate-500 uppercase">Cursor:</span>
            <span id="cursor-coords" class="text-emerald-400 font-semibold">05.9200°N, 00.9900°E</span>
          </div>
        </div>
        <div id="map"></div>
        
        <!-- Map Legend -->
        <div class="absolute bottom-5 right-5 z-[1000] panel px-3 py-2 rounded-lg shadow-xl flex flex-col gap-1.5 text-xs border border-slate-700/80">
          <div class="font-bold text-slate-300 text-[10px] uppercase tracking-wider border-b border-slate-700/80 pb-1">
            Hazard Severity Scale
          </div>
          <div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm bg-red-500"></span> <span class="text-[11px] text-slate-300">Critical (&ge;75)</span></div>
          <div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm bg-orange-500"></span> <span class="text-[11px] text-slate-300">High (50-74)</span></div>
          <div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm bg-amber-400"></span> <span class="text-[11px] text-slate-300">Moderate (25-49)</span></div>
          <div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span> <span class="text-[11px] text-slate-300">Low (&lt;25)</span></div>
        </div>
      </div>

      <!-- Live Vulnerability Response Chart (Chart.js) -->
      <div class="panel p-3.5 rounded-xl">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider" id="chart-title">Topographic Sensitivity Response Curve</h3>
          <span class="text-[11px] text-slate-400 font-mono" id="chart-subtitle">Vulnerability vs. Rainfall (0 - 250mm)</span>
        </div>
        <div class="h-32">
          <canvas id="riskChart"></canvas>
        </div>
      </div>

    </div>

  </div>

  <!-- Operational Situation Report (Modal) -->
  <div id="ai-modal" class="fixed inset-0 z-[2000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="panel max-w-2xl w-full p-6 rounded-2xl border border-slate-700 shadow-2xl flex flex-col gap-4 animate-in fade-in duration-150">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center gap-2.5">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <div>
            <h3 class="font-bold text-white text-sm md:text-base" id="ai-modal-title">GeoRisk Rapid Assessment & Situation Report</h3>
            <p class="text-[11px] text-slate-400">UN Sendai Framework Rapid Assessment Protocol</p>
          </div>
        </div>
        <button onclick="closeAIModal()" class="text-slate-400 hover:text-white text-base font-bold px-2 py-1 rounded hover:bg-slate-800">✕</button>
      </div>

      <div class="space-y-3 text-xs leading-relaxed max-h-[60vh] overflow-y-auto pr-1 scrollbar-thin">
        <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <span class="text-slate-400 uppercase font-bold text-[10px] block">Readiness Priority</span>
          <div class="text-sm font-extrabold text-emerald-400 font-mono mt-0.5" id="ai-priority">--</div>
        </div>

        <div>
          <span class="text-slate-300 uppercase font-bold text-[10px] block mb-1">Directives for Civil Defense</span>
          <ul class="list-disc pl-4 space-y-1 text-slate-300" id="ai-directives"></ul>
        </div>

        <div class="grid grid-cols-2 gap-3 pt-1">
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
            <span class="text-slate-400 uppercase font-bold text-[10px] block mb-1">Critical Infrastructure Risk</span>
            <p class="text-slate-300" id="ai-infra">--</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
            <span class="text-slate-400 uppercase font-bold text-[10px] block mb-1">Agricultural & Livelihood Impact</span>
            <p class="text-slate-300" id="ai-agri">--</p>
          </div>
        </div>

        <div class="text-[10px] text-slate-500 border-t border-slate-800 pt-2" id="ai-assurance">
          Standard: UN Sendai Framework for Disaster Risk Reduction (2015–2030) · Rapid Response Protocol.
        </div>
      </div>

      <button onclick="closeAIModal()" class="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition">
        Close Briefing
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

    // GIS Standard Metric Scale Bar
    L.control.scale({ metric: true, imperial: false, position: 'bottomleft' }).addTo(map);

    // Live Mouse Cursor Coordinates Tracking
    map.on('mousemove', function(e) {
      const norm = normalizeCoords(e.latlng.lat, e.latlng.lng);
      const latDir = norm.lat >= 0 ? 'N' : 'S';
      const lonDir = norm.lon >= 0 ? 'E' : 'W';
      const el = document.getElementById('cursor-coords');
      if (el) {
        el.innerText = `${Math.abs(norm.lat).toFixed(4)}°${latDir}, ${Math.abs(norm.lon).toFixed(4)}°${lonDir}`;
      }
    });

    let currentOpacity = 0.45;
    let gridVisible = true;

    function setGridOpacity(val) {
      currentOpacity = parseFloat(val) / 100.0;
      document.getElementById('val-opacity').innerText = Math.round(val) + '%';
      if (geojsonLayer) {
        geojsonLayer.eachLayer(function(layer) {
          layer.setStyle({
            fillOpacity: gridVisible ? currentOpacity : 0.0,
            opacity: gridVisible ? Math.min(1.0, currentOpacity + 0.3) : 0.0
          });
        });
      }
    }

    function toggleGridVisibility() {
      gridVisible = !gridVisible;
      const btn = document.getElementById('toggle-grid-btn');
      if (gridVisible) {
        btn.innerText = "Hide Grid";
        btn.className = "px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition";
      } else {
        btn.innerText = "Show Grid";
        btn.className = "px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-950 hover:bg-emerald-900 text-emerald-400 border border-emerald-700 transition";
      }
      if (geojsonLayer) {
        geojsonLayer.eachLayer(function(layer) {
          layer.setStyle({
            fillOpacity: gridVisible ? currentOpacity : 0.0,
            opacity: gridVisible ? Math.min(1.0, currentOpacity + 0.3) : 0.0
          });
        });
      }
    }

    // Precision Vector Reticle (Replaces cartoon blue pin)
    const precisionReticle = L.divIcon({
      className: 'custom-reticle',
      html: `
        <div style="position: relative; width: 28px; height: 28px; transform: translate(-14px, -14px); pointer-events: none;">
          <div style="position: absolute; inset: 0; border: 1.5px solid #10b981; border-radius: 9999px; background: rgba(16, 185, 129, 0.15);"></div>
          <div style="position: absolute; top: 13px; left: 2px; width: 24px; height: 1.5px; background: #10b981;"></div>
          <div style="position: absolute; top: 2px; left: 13px; width: 1.5px; height: 24px; background: #10b981;"></div>
          <div style="position: absolute; top: 11px; left: 11px; width: 6px; height: 6px; background: #34d399; border-radius: 9999px; box-shadow: 0 0 6px #10b981;"></div>
        </div>
      `,
      iconSize: [0, 0]
    });

    let geojsonLayer = null;
    let targetMarker = L.marker([currentLat, currentLon], { icon: precisionReticle }).addTo(map).bindPopup("Current Risk Target");

    // Auto-detect real terrain elevation from SRTM DEM
    async function fetchTerrainElevation(lat, lon) {
      const elevBadge = document.getElementById('elev-badge');
      if (elevBadge) elevBadge.innerText = "Querying SRTM...";
      try {
        const res = await fetch(`/api/terrain-elevation?lat=${lat}&lon=${lon}`);
        if (res.ok) {
          const data = await res.json();
          if (data && typeof data.elevation === 'number') {
            const rawElev = data.elevation;
            const sliderVal = Math.max(0, Math.min(200, rawElev));
            document.getElementById('input-elev').value = sliderVal;
            document.getElementById('val-elev').innerText = `${rawElev} m`;
            if (elevBadge) {
              elevBadge.innerText = rawElev > 200 ? `SRTM: ${rawElev}m (Highland)` : `SRTM: ${rawElev}m (Live)`;
            }
            // Auto-calibrate soil porosity: coastal/wetlands have low percolation (0.20)
            if (rawElev <= 5.0) {
              document.getElementById('input-soil').value = '0.20';
              document.getElementById('val-soil').innerText = '0.20';
            }
          }
        }
      } catch (err) {
        console.warn("Elevation query fallback:", err);
      } finally {
        if (elevBadge && !elevBadge.innerText.startsWith('SRTM')) {
          elevBadge.innerText = "Live SRTM Auto-Detect";
        }
        runSimulation();
      }
    }

    // Click anywhere on map
    map.on('click', async function(e) {
      const norm = normalizeCoords(e.latlng.lat, e.latlng.lng);
      currentLat = norm.lat;
      currentLon = norm.lon;
      currentLocationName = `${currentLat.toFixed(2)}N, ${currentLon.toFixed(2)}E`;

      targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`<b>Target Coordinates</b><br><span class="text-[11px] text-slate-400">${currentLat.toFixed(3)}°N, ${currentLon.toFixed(3)}°E</span>`).openPopup();
      document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
      document.getElementById('search-status').innerText = "Querying Terrain...";
      await fetchTerrainElevation(currentLat, currentLon);
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
          const parts = top.display_name.split(',').map(s => s.trim());
          currentLocationName = parts[0];
          const subLocation = parts.slice(1, 3).join(', ');

          map.flyTo([currentLat, currentLon], 10);
          targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`<b>${currentLocationName}</b>${subLocation ? `<br><span class="text-[11px] text-slate-400">${subLocation}</span>` : ''}`).openPopup();
          document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
          statusEl.innerText = `Located: ${currentLocationName}`;
          await fetchTerrainElevation(currentLat, currentLon);
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
      const parts = h.name.split(',').map(s => s.trim());
      const hubName = parts[0];
      const hubRegion = parts.slice(1).join(', ');
      map.flyTo([currentLat, currentLon], 10);
      targetMarker.setLatLng([currentLat, currentLon]).bindPopup(`<b>${hubName}</b>${hubRegion ? `<br><span class="text-[11px] text-slate-400">${hubRegion}</span>` : ''}`).openPopup();
      document.getElementById('current-coords').innerText = `Lat: ${currentLat.toFixed(2)} | Lon: ${currentLon.toFixed(2)}`;
      document.getElementById('search-status').innerText = hubName;
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
      const metricTitle = document.getElementById('metric-title');
      const scaleLabel = document.getElementById('scale-label');
      const chartTitle = document.getElementById('chart-title');
      const chartSubtitle = document.getElementById('chart-subtitle');

      if (mode === 'drought') {
        droughtBtn.className = "px-3 py-1 rounded-md text-xs font-semibold transition bg-amber-600 text-white shadow-sm flex items-center gap-1.5";
        floodBtn.className = "px-3 py-1 rounded-md text-xs font-semibold transition text-slate-400 hover:text-slate-200 flex items-center gap-1.5";
        floodControls.classList.add('hidden');
        droughtControls.classList.remove('hidden');
        panelTitle.innerText = "Agro-Meteorological Parameters";
        metricTitle.innerText = "Computed Drought Index";
        scaleLabel.innerText = "/ 100 Index";
        if (chartTitle) chartTitle.innerText = "Agro-Climatic Sensitivity Response Curve";
        if (chartSubtitle) chartSubtitle.innerText = "Drought Index vs. Topsoil Moisture (0 - 100%)";
      } else {
        floodBtn.className = "px-3 py-1 rounded-md text-xs font-semibold transition bg-emerald-600 text-white shadow-sm flex items-center gap-1.5";
        droughtBtn.className = "px-3 py-1 rounded-md text-xs font-semibold transition text-slate-400 hover:text-slate-200 flex items-center gap-1.5";
        droughtControls.classList.add('hidden');
        floodControls.classList.remove('hidden');
        panelTitle.innerText = "Hydrologic Parameters";
        metricTitle.innerText = "Computed Flood Vulnerability";
        scaleLabel.innerText = "/ 100 Index";
        if (chartTitle) chartTitle.innerText = "Topographic Sensitivity Response Curve";
        if (chartSubtitle) chartSubtitle.innerText = "Vulnerability vs. Rainfall (0 - 250mm)";
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
          badge.className = 'px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/30';
        } else if (severity === 'HIGH') {
          badge.className = 'px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider bg-orange-500/10 text-orange-400 border border-orange-500/30';
        } else if (severity === 'MODERATE') {
          badge.className = 'px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30';
        } else {
          badge.className = 'px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';
        }

        // Draw 16-cell GeoJSON Grid
        await drawHazardZones(rain, elev, soil, moist, temp, ndvi);

        // Update Sensitivity Chart dynamically
        updateChart(elev, soil, moist, temp, ndvi);
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
            if (score >= 75) {
              color = '#ef4444';
            } else if (score >= 50) {
              color = '#f97316';
            } else if (score >= 25) {
              color = '#f59e0b';
            }
            return {
              color: color,
              weight: 1.5,
              opacity: gridVisible ? Math.min(1.0, currentOpacity + 0.3) : 0.0,
              fillColor: color,
              fillOpacity: gridVisible ? currentOpacity : 0.0
            };
          },
          onEachFeature: function(feature, layer) {
            layer.bindPopup(`
              <div class="font-sans text-xs p-1">
                <div class="font-bold text-white border-b border-slate-700 pb-1 mb-1.5 flex justify-between items-center gap-2">
                  <span class="font-mono text-[11px] text-emerald-400 font-bold">${feature.properties.cell_id}</span>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-white ${feature.properties.severity === 'CRITICAL' ? 'bg-red-600' : feature.properties.severity === 'HIGH' ? 'bg-orange-500' : feature.properties.severity === 'MODERATE' ? 'bg-amber-500' : 'bg-emerald-600'}">${feature.properties.severity}</span>
                </div>
                <div class="space-y-1 text-slate-300">
                  <div class="flex justify-between"><span>Risk Index:</span> <b class="text-white font-mono">${feature.properties.risk_score} / 100</b></div>
                  <div class="flex justify-between"><span>Hazard:</span> <span class="font-mono uppercase text-[10px] text-slate-400">${feature.properties.hazard_type}</span></div>
                  <div class="flex justify-between"><span>Centroid:</span> <span class="font-mono text-slate-400 text-[10px]">${feature.properties.centroid.lat}°N, ${feature.properties.centroid.lon}°E</span></div>
                </div>
                <div class="mt-2 text-[10px] text-slate-300 leading-normal bg-slate-900/90 p-2 rounded border border-slate-800">
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

    // Chart.js Sensitivity Curve (Dynamically switches for Flood vs Drought)
    function updateChart(elev, soil, moist, temp, ndvi) {
      let labels = [];
      let riskScores = [];
      let strokeColor = '#10b981';
      let fillColor = 'rgba(16, 185, 129, 0.15)';
      let datasetLabel = 'Vulnerability Index';

      if (activeHazard === 'drought') {
        const moistSteps = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
        labels = moistSteps.map(m => m + '%');
        riskScores = moistSteps.map(m => {
          const mFactor = Math.max(0.0, 1.0 - (m / 60.0));
          const tFactor = Math.max(0.0, Math.min(1.0, ((temp || 38.0) - 20.0) / 25.0));
          const vFactor = Math.max(0.0, 1.0 - Math.max(0.0, ndvi !== undefined ? ndvi : 0.24));
          return ((mFactor * 0.45 + tFactor * 0.35 + vFactor * 0.20) * 100).toFixed(1);
        });
        strokeColor = '#f59e0b';
        fillColor = 'rgba(245, 158, 11, 0.15)';
        datasetLabel = 'Drought Stress Index';
      } else {
        const rainSteps = [0, 30, 60, 90, 120, 150, 180, 210, 240];
        labels = rainSteps.map(r => r + 'mm');
        riskScores = rainSteps.map(r => {
          const elevFactor = elev <= 0 ? 1.0 : (elev < 50 ? Math.max(0.1, 1.0 - (elev/50.0)) : 0.2);
          const precipFactor = Math.min(1.0, r / 250.0);
          const runoffFactor = 1.0 - (soil || 0.35);
          return ((elevFactor * 0.45 + precipFactor * 0.40 + runoffFactor * 0.15) * 100).toFixed(1);
        });
        strokeColor = '#10b981';
        fillColor = 'rgba(16, 185, 129, 0.15)';
        datasetLabel = 'Flood Vulnerability Index';
      }

      const ctx = document.getElementById('riskChart').getContext('2d');
      if (riskChart) {
        riskChart.data.labels = labels;
        riskChart.data.datasets[0].label = datasetLabel;
        riskChart.data.datasets[0].data = riskScores;
        riskChart.data.datasets[0].borderColor = strokeColor;
        riskChart.data.datasets[0].backgroundColor = fillColor;
        riskChart.update();
      } else {
        riskChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: datasetLabel,
              data: riskScores,
              borderColor: strokeColor,
              backgroundColor: fillColor,
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
      downloadAnchor.setAttribute("download", `georisk_${activeHazard}_layer_${currentLat.toFixed(2)}_${currentLon.toFixed(2)}.geojson`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }

    // Operational SITREP Rapid Disaster Assessment Generator
    async function generateSITREPBriefing() {
      const score = parseFloat(document.getElementById('risk-score').innerText) || 50;
      const severity = document.getElementById('risk-badge').innerText || "MODERATE";
      const rain = parseFloat(document.getElementById('input-rain').value);
      const elev = parseFloat(document.getElementById('input-elev').value);
      const soil = parseFloat(document.getElementById('input-soil').value);

      const res = await fetch('/api/sitrep-briefing', {
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
    const generateAIBriefing = generateSITREPBriefing;

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

async def api_sitrep_briefing(request: Request):
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

async def api_terrain_elevation(request: Request):
    try:
        lat = float(request.query_params.get("lat", 0.0))
        lon = float(request.query_params.get("lon", 0.0))
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        req = urllib.request.Request(url, headers={"User-Agent": "GeoRiskPlatform/2.4"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            elevations = data.get("elevation", [2.5])
            elev = round(float(elevations[0]), 1)
            return JSONResponse({"elevation": elev, "source": "NASADEM/SRTM v3"})
    except Exception as exc:
        return JSONResponse({"elevation": 2.5, "source": "Default Baseline", "error": str(exc)})

app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/api/flood-risk", api_flood_risk, methods=["POST"]),
        Route("/api/drought-risk", api_drought_risk, methods=["POST"]),
        Route("/api/bounding-box-geojson", api_bounding_box, methods=["POST"]),
        Route("/api/sitrep-briefing", api_sitrep_briefing, methods=["POST"]),
        Route("/api/ai-briefing", api_sitrep_briefing, methods=["POST"]),
        Route("/api/terrain-elevation", api_terrain_elevation, methods=["GET"]),
    ]
)

if __name__ == "__main__":
    print("\n=======================================================")
    print("[*] GeoRisk Decision Support System (DSS) Starting...")
    print(" -> Dashboard URL: http://localhost:8000")
    print("=======================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
