const $ = (selector) => document.querySelector(selector);
const statusNode = $("#model-status");
const resultsNode = $("#results");
const errorNode = $("#form-error");
const analyzeButton = $("#analyze");
let demoConfig = null;

const riskColors = {
  LOW: "#2f9e63",
  MODERATE: "#d9a514",
  HIGH: "#e97824",
  CRITICAL: "#ca3d36",
};

function setForecast(values) {
  $("#rain24").value = values.rain_24h_mm;
  $("#rain72").value = values.rain_72h_mm;
  $("#forecast6").value = values.forecast_rain_6h_mm;
  $("#forecast12").value = values.forecast_rain_12h_mm;
}

async function bootstrap() {
  try {
    const [healthResponse, configResponse] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/demo/config"),
    ]);
    if (!healthResponse.ok || !configResponse.ok) throw new Error("API no disponible");
    const health = await healthResponse.json();
    demoConfig = await configResponse.json();
    statusNode.textContent = `Modelo ${health.model_version} listo`;
    statusNode.className = "status status-ok";
    setForecast(demoConfig.forecast_presets.storm);
    analyzeButton.disabled = false;
  } catch (error) {
    statusNode.textContent = "Modelo no disponible";
    statusNode.className = "status status-error";
    errorNode.textContent = error.message;
  }
}

document.querySelectorAll(".preset").forEach((button) => {
  button.addEventListener("click", () => {
    if (!demoConfig) return;
    document.querySelectorAll(".preset").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    setForecast(demoConfig.forecast_presets[button.dataset.preset]);
  });
});

$("#geolocate").addEventListener("click", () => {
  const message = $("#location-message");
  if (!navigator.geolocation) {
    message.textContent = "Este navegador no ofrece geolocalización; se mantiene la ubicación manual.";
    return;
  }
  message.textContent = "Solicitando ubicación…";
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      $("#latitude").value = coords.latitude.toFixed(5);
      $("#longitude").value = coords.longitude.toFixed(5);
      message.textContent = "Ubicación actualizada. Las rutas siguen siendo simuladas.";
    },
    () => { message.textContent = "Permiso rechazado; se mantiene la ubicación manual."; },
    { enableHighAccuracy: false, timeout: 8000 },
  );
});

function payloadFromForm() {
  return {
    location: {
      latitude: Number($("#latitude").value),
      longitude: Number($("#longitude").value),
    },
    forecast: {
      rain_24h_mm: Number($("#rain24").value),
      rain_72h_mm: Number($("#rain72").value),
      forecast_rain_6h_mm: Number($("#forecast6").value),
      forecast_rain_12h_mm: Number($("#forecast12").value),
    },
    safety_margin_minutes: 40,
  };
}

function formatTime(value) {
  if (!value) return "No alcanza nivel crítico";
  return new Intl.DateTimeFormat("es-AR", { hour: "2-digit", minute: "2-digit", timeZoneName: "short" }).format(new Date(value));
}

function sparkline(points, color) {
  const values = points.map((point) => point.risk_score);
  const coordinates = values.map((value, index) => {
    const x = values.length === 1 ? 0 : (index / (values.length - 1)) * 240;
    return `${x.toFixed(1)},${(50 - value * 45).toFixed(1)}`;
  }).join(" ");
  return `<svg class="sparkline" viewBox="0 0 240 54" aria-label="Evolución del riesgo"><line x1="0" y1="18.5" x2="240" y2="18.5" stroke="#e6c3bf" stroke-dasharray="4 4"/><polyline points="${coordinates}" style="stroke:${color}"/></svg>`;
}

function renderCards(routes) {
  const container = $("#route-cards");
  container.innerHTML = routes.map((route) => {
    const color = riskColors[route.risk_level];
    return `<article class="route-card" style="--risk-color:${color}">
      <header><h3>${route.name}</h3><span class="risk-value">${Math.round(route.peak_risk_score * 100)}%</span></header>
      <div class="route-meta">
        <div><small>Nivel máximo</small><strong>${route.risk_level}</strong></div>
        <div><small>Tramo crítico</small><strong>${route.critical_segment_id || "—"}</strong></div>
        <div><small>Hora crítica</small><strong>${formatTime(route.critical_time)}</strong></div>
        <div><small>Última salida</small><strong>${formatTime(route.last_safe_departure)}</strong></div>
      </div>
      ${sparkline(route.timeline, color)}
    </article>`;
  }).join("");
}

function projectRoutes(routes, location) {
  const all = routes.flatMap((route) => route.geometry.coordinates);
  all.push([location.longitude, location.latitude]);
  const xs = all.map((point) => point[0]);
  const ys = all.map((point) => point[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const width = Math.max(maxX - minX, 0.0001), height = Math.max(maxY - minY, 0.0001);
  const project = ([longitude, latitude]) => [50 + ((longitude - minX) / width) * 700, 450 - ((latitude - minY) / height) * 400];
  const layer = $("#route-layer");
  layer.innerHTML = "";
  routes.forEach((route) => {
    const points = route.geometry.coordinates.map(project);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    line.setAttribute("points", points.map((point) => point.join(",")).join(" "));
    line.setAttribute("class", "route-line");
    line.setAttribute("stroke", riskColors[route.risk_level]);
    layer.appendChild(line);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", points.at(-1)[0]); label.setAttribute("y", points.at(-1)[1] - 13);
    label.setAttribute("class", "route-label"); label.textContent = route.name.replace(" (demo)", "");
    layer.appendChild(label);
  });
  const [x, y] = project([location.longitude, location.latitude]);
  const marker = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  marker.setAttribute("cx", x); marker.setAttribute("cy", y); marker.setAttribute("r", 11);
  marker.setAttribute("class", "location-dot"); layer.appendChild(marker);
}

function renderResult(data) {
  const trigger = $("#trigger-card");
  trigger.className = `trigger-card ${data.triggered ? "triggered" : "not-triggered"}`;
  trigger.textContent = data.triggered
    ? `Pronóstico activado: supera el umbral de ${data.trigger_threshold_mm} mm en 12 h.`
    : `Sin trigger automático: no supera ${data.trigger_threshold_mm} mm en 12 h. El análisis se ejecutó manualmente.`;
  $("#alerts").innerHTML = data.alerts.length
    ? data.alerts.map((alert) => `<div class="alert">${alert.title}<small>${alert.message}</small></div>`).join("")
    : "<div class=\"trigger-card not-triggered\">No se detectaron rutas críticas en este escenario.</div>";
  renderCards(data.routes);
  projectRoutes(data.routes, data.location);
  resultsNode.classList.remove("hidden");
  resultsNode.scrollIntoView({ behavior: "smooth", block: "start" });
}

analyzeButton.addEventListener("click", async () => {
  errorNode.textContent = "";
  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analizando rutas…";
  try {
    const response = await fetch("/api/demo/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payloadFromForm()),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail[0].msg : data.detail);
    renderResult(data);
  } catch (error) {
    errorNode.textContent = error.message || "No se pudo completar el análisis.";
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Lanzar pronóstico y analizar";
  }
});

bootstrap();
