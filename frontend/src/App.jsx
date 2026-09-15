import { useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const examples = [
  "Show me Sentinel-2 imagery of Bengaluru from June 2024 with less than 10% cloud cover and calculate NDVI.",
  "Vegetation in Bengaluru",
  "Water bodies in Karnataka",
  "Compare land cover over time",
  "Urban expansion analysis",
];

const savedQueries = [
  {
    icon: "🌿",
    title: "NDVI for Bengaluru",
    date: "12 June 2024",
  },
  {
    icon: "💧",
    title: "Water bodies in Karnataka",
    date: "05 May 2024",
  },
  {
    icon: "🏙",
    title: "Urban expansion (2018–2024)",
    date: "20 April 2024",
  },
  {
    icon: "🗺",
    title: "Land cover change",
    date: "10 March 2024",
  },
];

/* =========================================================
   Helpers
========================================================= */

function findValue(obj, possibleKeys) {
  if (!obj || typeof obj !== "object") return null;

  for (const key of possibleKeys) {
    if (
      Object.prototype.hasOwnProperty.call(obj, key) &&
      obj[key] !== null &&
      obj[key] !== undefined
    ) {
      return obj[key];
    }
  }

  for (const value of Object.values(obj)) {
    if (value && typeof value === "object") {
      const found = findValue(value, possibleKeys);
      if (found !== null && found !== undefined) return found;
    }
  }

  return null;
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "—";

  const number = Number(value);

  if (Number.isNaN(number)) return String(value);

  return number.toFixed(digits);
}

function formatLocationName(result) {
  return (
    result?.resolved_location?.name ||
    result?.query_plan?.location_name ||
    result?.structured_query?.location ||
    "Selected region"
  );
}

function formatAnalysisType(result) {
  const type =
    result?.query?.interpreted_as ||
    result?.query_plan?.analysis_type ||
    result?.structured_query?.analysis_type ||
    "";

  if (!type) return "Earth Observation Analysis";

  return String(type)
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getAnalysisMetrics(result) {
  const analysis = result?.analysis || {};

  const type = String(
    result?.query?.interpreted_as ||
      result?.query_plan?.analysis_type ||
      result?.structured_query?.analysis_type ||
      "ndvi"
  ).toLowerCase();

  const isNDWI = type.includes("ndwi");
  const isChange = type.includes("change");

  return {
    average: findValue(
      analysis,
      isNDWI
        ? ["mean_ndwi", "average_ndwi", "avg_ndwi", "mean", "average"]
        : ["mean_ndvi", "average_ndvi", "avg_ndvi", "mean", "average"]
    ) ?? null,

    minimum: findValue(
      analysis,
      isNDWI
        ? ["min_ndwi", "minimum_ndwi", "min", "minimum"]
        : ["min_ndvi", "minimum_ndvi", "min", "minimum"]
    ) ?? null,

    maximum: findValue(
      analysis,
      isNDWI
        ? ["max_ndwi", "maximum_ndwi", "max", "maximum"]
        : ["max_ndvi", "maximum_ndvi", "max", "maximum"]
    ) ?? null,

    coverage: findValue(
      analysis,
      isNDWI
        ? ["water_coverage_percent", "water_coverage", "water_percentage", "water_percent"]
        : ["vegetation_coverage", "vegetation_percentage", "vegetation_percent", "vegetation_coverage_percent"]
    ) ?? null,

    changedArea:
      findValue(analysis, [
        "changed_area_percent",
        "changed_area",
        "change_percent",
      ]) ?? null,

    urbanExpansion:
      findValue(analysis, [
        "urban_expansion_percent",
        "urban_expansion",
      ]) ?? null,

    vegetationChange:
      findValue(analysis, [
        "vegetation_change_percent",
        "vegetation_change",
      ]) ?? null,

    waterChange:
      findValue(analysis, [
        "water_change_percent",
        "water_change",
      ]) ?? null,

    cloudCover:
      findValue(result, [
        "cloud_cover",
        "cloudCover",
        "max_cloud_cover",
      ]) ?? null,

    satellite:
      findValue(result, [
        "satellite",
        "platform",
        "mission",
        "collection",
      ]) ?? null,

    date:
      findValue(result, [
        "datetime",
        "date",
        "acquisition_date",
        "scene_datetime",
      ]) ?? null,
  };
}

function getSceneInfo(result) {
  const scene =
    result?.analysis?.scene ||
    result?.analysis?.selected_scene ||
    result?.analysis?.best_scene ||
    result?.query_plan?.scene ||
    {};

  return {
    id: scene?.id || "Satellite scene",
    datetime: scene?.datetime || scene?.date || null,
    cloudCover:
      scene?.cloud_cover ??
      scene?.cloudCover ??
      null,
  };
}

function getMapEndpoint(result) {
  const type = String(
    result?.query?.interpreted_as ||
      result?.query_plan?.analysis_type ||
      result?.structured_query?.analysis_type ||
      "ndvi"
  ).toLowerCase();

  if (type.includes("change")) return null;
  if (type.includes("weather")) return "/weather-graph/combined";
  if (type.includes("ndwi") && !type.includes("ndvi")) return "/ndwi-map";
  return "/ndvi-map";
}

function getDownloadEndpoint(result) {
  const explicit = findValue(result, [
    "download_geotiff",
    "downloadGeoTiff",
    "download_url",
    "downloadUrl",
  ]);

  if (typeof explicit === "string" && explicit.trim()) {
    return explicit;
  }

  const type = String(
    result?.query?.interpreted_as ||
      result?.query_plan?.analysis_type ||
      result?.structured_query?.analysis_type ||
      "ndvi"
  ).toLowerCase();

  if (type.includes("change")) return "/download/change-geotiff";
  if (type.includes("ndwi") && !type.includes("ndvi")) return "/download/ndwi-geotiff";
  if (type.includes("weather")) return null;
  return "/download/ndvi-geotiff";
}

/* =========================================================
   Main App
========================================================= */

function App() {
  const [page, setPage] = useState("home");
  const [query, setQuery] = useState("");

  const [submittedQuery, setSubmittedQuery] = useState(
    "Show me Sentinel-2 imagery of Bengaluru from June 2024 with less than 10% cloud cover and calculate NDVI."
  );

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submitQuery = async (customQuery = null) => {
    const text = (customQuery ?? query).trim();

    if (!text) return;

    setSubmittedQuery(text);
    setQuery("");
    setPage("dashboard");
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            `Backend returned ${response.status}`
        );
      }

      setResult(data);
    } catch (err) {
      console.error("GeoQuery API error:", err);

      setError(
        err?.message ||
          "Unable to connect to GeoQuery AI backend."
      );

      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const useExample = (text) => {
    setQuery(text);
  };

  const trySampleQuery = () => {
    const sample = examples[0];

    setQuery("");
    submitQuery(sample);
  };

  return (
    <div className="app">
      {page === "home" ? (
        <HomePage
          query={query}
          setQuery={setQuery}
          submitQuery={submitQuery}
          useExample={useExample}
          goToDashboard={() => setPage("dashboard")}
          trySampleQuery={trySampleQuery}
        />
      ) : (
        <Dashboard
          query={query}
          setQuery={setQuery}
          submitQuery={submitQuery}
          submittedQuery={submittedQuery}
          setPage={setPage}
          setResult={setResult}
          useExample={useExample}
          result={result}
          loading={loading}
          error={error}
        />
      )}
    </div>
  );
}

/* =========================================================
   HOME PAGE
========================================================= */

function HomePage({
  query,
  setQuery,
  submitQuery,
  useExample,
  goToDashboard,
  trySampleQuery,
}) {
  return (
    <>
      <header className="navbar">
        <div className="brand">
          <div className="brand-mark">◒</div>
          <span>GeoQuery AI</span>
        </div>

        <nav>
          <button
            className="nav-link active"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            Home
          </button>
          <button
            className="nav-link"
            onClick={() =>
              document.getElementById("use-cases")?.scrollIntoView({
                behavior: "smooth",
              })
            }
          >
            Use Cases
          </button>
          <button
            className="nav-link"
            onClick={() =>
              document.getElementById("about")?.scrollIntoView({
                behavior: "smooth",
              })
            }
          >
            About
          </button>
        </nav>

        <button className="primary-btn nav-cta" onClick={goToDashboard}>
          Get Started
          <span>→</span>
        </button>
      </header>

      <main className="home">
        <section className="hero-section">
          <div className="hero-content">
            <div className="eyebrow">
              <span className="eyebrow-dot"></span>
              AI-powered Earth observation
            </div>

            <h1>
              Ask the Earth,
              <br />
              <span>Find Answers.</span>
            </h1>

            <p className="hero-description">
              Explore, analyze and visualize satellite data in natural
              language — simple, fast, meaningful.
            </p>

            <div className="hero-actions">
              <button
                className="primary-btn large"
                onClick={trySampleQuery}
              >
                Try a Sample Query
                <span>→</span>
              </button>

              <button
                className="secondary-btn large"
                onClick={() =>
                  document
                    .getElementById("how-it-works")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                See how it works
              </button>
            </div>
          </div>

          <div className="hero-visual">
            <div className="earth-card">
              <div className="orbit orbit-one"></div>
              <div className="orbit orbit-two"></div>

              <div className="earth">
                <div className="earth-glow"></div>
                <div className="continent continent-one"></div>
                <div className="continent continent-two"></div>
                <div className="continent continent-three"></div>
                <div className="earth-grid"></div>
              </div>

              <div className="satellite">
                <div className="satellite-body"></div>
                <div className="satellite-panel left"></div>
                <div className="satellite-panel right"></div>
              </div>

              <div className="floating-label label-top">
                <span>●</span> Earth observation
              </div>

              <div className="floating-label label-bottom">
                <span>✦</span> AI insights
              </div>
            </div>
          </div>
        </section>

        <section className="features-strip" id="use-cases">
          <Feature
            icon="▥"
            title="Environment"
            text="Monitor vegetation and ecosystems"
          />

          <Feature
            icon="⌂"
            title="Urban Planning"
            text="Understand how cities change"
          />

          <Feature
            icon="♧"
            title="Agriculture"
            text="Analyze crops and land health"
          />

          <Feature
            icon="♢"
            title="Water Resources"
            text="Discover and monitor water bodies"
          />
        </section>

        <section className="how-section" id="how-it-works">
          <div className="section-heading">
            <span className="section-kicker">HOW IT WORKS</span>

            <h2>From a question to an Earth insight.</h2>

            <p>
              GeoQuery AI turns natural-language questions into useful
              geospatial analysis.
            </p>
          </div>

          <div className="steps">
            <Step
              number="01"
              title="Ask"
              text="Describe what you want to know about a location."
            />

            <Step
              number="02"
              title="Discover"
              text="AI finds relevant satellite scenes and geospatial data."
            />

            <Step
              number="03"
              title="Analyze"
              text="Run indices and spatial analysis on the required area."
            />

            <Step
              number="04"
              title="Understand"
              text="Receive visual results, insights and downloadable outputs."
            />
          </div>
        </section>

        <section className="query-preview-section">
          <div>
            <span className="section-kicker">START EXPLORING</span>

            <h2>Ask your first question.</h2>

            <p>
              No complicated GIS workflow. Just describe what you need.
            </p>
          </div>

          <div className="home-query-box">
            <div className="search-symbol">⌕</div>

            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  submitQuery();
                }
              }}
              placeholder="Ask something about the Earth..."
            />

            <button onClick={() => submitQuery()}>→</button>
          </div>

          <div className="example-row">
            {examples.slice(1).map((example) => (
              <button
                key={example}
                onClick={() => useExample(example)}
                className="example-chip"
              >
                {example}
              </button>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer" id="about">
        <div className="brand">
          <div className="brand-mark small">◒</div>
          <span>GeoQuery AI</span>
        </div>

        <span>Making Earth observation easier for everyone.</span>

        <span>© 2026 GeoQuery AI</span>
      </footer>
    </>
  );
}

/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard({
  query,
  setQuery,
  submitQuery,
  submittedQuery,
  setPage,
  setResult,
  useExample,
  result,
  loading,
  error,
}) {
  const locationName = formatLocationName(result);
  const analysisType = formatAnalysisType(result);
  const metrics = getAnalysisMetrics(result);
  const scene = getSceneInfo(result);
  const [mapZoom, setMapZoom] = useState(1);
  const [activeTab, setActiveTab] = useState("overview");
  const [showSettings, setShowSettings] = useState(false);
  const [showSaved, setShowSaved] = useState(false);
  const [mapImageError, setMapImageError] = useState(false);

  useEffect(() => {
    setMapImageError(false);
  }, [result]);

  const displayDate =
    scene.datetime ||
    metrics.date ||
    "Waiting for analysis";

  const cloudCover =
    scene.cloudCover ??
    metrics.cloudCover;

  const answer =
    result?.answer ||
    result?.analysis?.answer ||
    "Submit a query to receive an AI-generated Earth observation insight.";

  const mapEndpoint = getMapEndpoint(result);
  const downloadEndpoint = getDownloadEndpoint(result);

  const mapUrl = result && !result?.analysis?.error && mapEndpoint
    ? `${API_BASE}${mapEndpoint}?t=${Date.now()}`
    : null;

  const handleDownload = () => {
    if (!result || result?.analysis?.error || loading) return;

    if (!downloadEndpoint) {
      window.alert("A downloadable file is not available for this analysis.");
      return;
    }

    window.open(`${API_BASE}${downloadEndpoint}`, "_blank");
  };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">◒</div>
          <strong>GeoQuery AI</strong>
        </div>

        <div className="sidebar-menu">
          <SidebarItem
            icon="⌕"
            text="New Query"
            active
            onClick={() => {
              setResult(null);
              setSubmittedQuery("");
              setQuery("");
              setPage("home");
            }}
          />

          <SidebarItem
            icon="♡"
            text="Saved"
            onClick={() => setShowSaved(true)}
          />

          <SidebarItem
            icon="◫"
            text="Explore"
            onClick={() => {
              document.querySelector(".dashboard-grid")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }}
          />

          <SidebarItem
            icon="⚙"
            text="Settings"
            onClick={() => setShowSettings(true)}
          />
        </div>

        <div className="sidebar-bottom">
          <div className="help-card">
            <span>✦</span>

            <div>
              <strong>Need help?</strong>
              <p>Ask GeoQuery AI anything.</p>
            </div>
          </div>

          <div className="profile">
            <div className="avatar">B</div>

            <div>
              <strong>Bhagyajyothi</strong>
              <span>Researcher</span>
            </div>

            <span className="profile-more">•••</span>
          </div>
        </div>
      </aside>

      <main className="dashboard-main">
        <div className="dashboard-topbar">
          <div>
            <span className="dashboard-kicker">NEW QUERY</span>
            <h1>Explore the Earth</h1>
          </div>

          <div className="status-pill">
            <span></span>

            {loading
              ? "Analyzing..."
              : error
              ? "Connection issue"
              : "System operational"}
          </div>
        </div>

        <section className="query-card">
          <div className="query-card-top">
            <div className="query-label">
              <span className="search-circle">⌕</span>

              <div>
                <strong>What would you like to know?</strong>
                <span>Ask in natural language</span>
              </div>
            </div>

            <span className="shortcut">Enter ↵</span>
          </div>

          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Example: Show me Sentinel-2 imagery of Bengaluru from June 2024..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submitQuery();
              }
            }}
          />

          <div className="query-card-bottom">
            <div className="quick-actions">
              <span>Try:</span>

              <button onClick={() => submitQuery(examples[1])}>
                Vegetation
              </button>

              <button onClick={() => submitQuery(examples[2])}>
                Water bodies
              </button>

              <button onClick={() => submitQuery(examples[3])}>
                Land cover
              </button>
            </div>

            <button
              className="primary-btn"
              onClick={() => submitQuery()}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Analyze"}
              <span>{loading ? "…" : "→"}</span>
            </button>
          </div>
        </section>

        {error && (
          <div
            style={{
              marginTop: "16px",
              padding: "14px 18px",
              borderRadius: "12px",
              background: "#fff1f1",
              border: "1px solid #ffd3d3",
              color: "#b42318",
              fontSize: "14px",
            }}
          >
            <strong>Analysis failed:</strong> {error}
          </div>
        )}

        <div className="dashboard-grid">
          <section className="result-column">
            <div className="result-header">
              <div>
                <span className="result-kicker">
                  ANALYSIS RESULT
                </span>

                <h2>{locationName}</h2>

                <p>
                  {result
                    ? `${analysisType} · ${displayDate}`
                    : "Run a query to see real satellite results"}
                </p>
              </div>

              <button
                className="download-btn"
                onClick={handleDownload}
                disabled={!result || Boolean(result?.analysis?.error) || loading}
                title={!result ? "Run an analysis first" : "Download generated GeoTIFF"}
              >
                ↓ <span>Download</span>
              </button>
            </div>

            <div className="map-card">
            <div className="map-toolbar">
              <button
                onClick={() =>
                  setMapZoom((zoom) => Math.min(zoom + 0.25, 2.5))
                }
                title="Zoom in"
              >
                +
              </button>

              <button
                onClick={() =>
                  setMapZoom((zoom) => Math.max(zoom - 0.25, 1))
                }
                title="Zoom out"
              >
                −
              </button>
            </div>
              <div className="map-type">
                {result ? analysisType : "NDVI"}⌄
              </div>

              <div
                className="satellite-map"
                style={{
                  overflow: "hidden",
                }}
              >
                {mapUrl && !mapImageError ? (
                  <img
                    src={mapUrl}
                    alt={`${analysisType} map for ${locationName}`}
                    onError={() => setMapImageError(true)}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      display: "block",
                      transform: `scale(${mapZoom})`,
                      transformOrigin: "center center",
                      transition: "transform 0.2s ease",
                    }}
                  />
                ) : (
                  <>
                    <div className="map-grid"></div>
                    <div className="map-road road-one"></div>
                    <div className="map-road road-two"></div>
                    <div className="map-road road-three"></div>
                    <div className="map-road road-four"></div>
                    <div className="city-boundary">
                      <span>{locationName}</span>
                    </div>
                    <div className="map-location">
                      <span></span>
                    </div>
                  </>
                )}
              </div>

              <div className="map-legend">
                <div className="gradient"></div>

                <div className="legend-labels">
                  <span>-1</span>
                  <span>0</span>
                  <span>+1</span>
                </div>
              </div>
            </div>

            <div className="map-meta">
              <div>
                <span>Cloud cover</span>

                <strong>
                  {cloudCover !== null
                    ? `${formatNumber(cloudCover, 0)}%`
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Satellite</span>

                <strong>
                  {metrics.satellite ||
                    "Sentinel-2"}
                </strong>
              </div>

              <div>
                <span>Resolution</span>

                <strong>{findValue(result, ["resolution", "resolution_m", "spatial_resolution"]) ?? "10 m"}</strong>
              </div>
            </div>

            <div className="answer-card">
              <div className="answer-icon">✦</div>

              <div>
                <span className="answer-label">
                  AI SUMMARY
                </span>

                <p>{submittedQuery}</p>

                <p>
                  {loading
                    ? "GeoQuery AI is processing your request and analyzing the relevant geospatial data..."
                    : answer}
                </p>
              </div>
            </div>
          </section>

          <section className="analysis-column">
            <div className="analysis-tabs">
              <button
                className={activeTab === "overview" ? "active" : ""}
                onClick={() => setActiveTab("overview")}
              >
                Overview
              </button>

              <button
                className={activeTab === "timeseries" ? "active" : ""}
                onClick={() => setActiveTab("timeseries")}
              >
                Time Series
              </button>

              <button
                className={activeTab === "insights" ? "active" : ""}
                onClick={() => setActiveTab("insights")}
              >
                Insights
              </button>
            </div>

            {activeTab === "overview" && (
              <>
            <div className="analysis-title">
              <span className="result-kicker">
                {result
                  ? analysisType.toUpperCase()
                  : "VEGETATION ANALYSIS"}
              </span>

              <h2>
                {result
                  ? `${analysisType}`
                  : "NDVI Analysis"}
              </h2>

              <p>
                {result
                  ? `${locationName} · ${displayDate}`
                  : "Run a query to generate analysis"}
              </p>
            </div>

            <div className="metric-grid">
              <Metric
                icon="⌁"
                value={
                  analysisType.toLowerCase().includes("change")
                    ? metrics.changedArea !== null
                      ? `${formatNumber(metrics.changedArea)}%`
                      : "—"
                    : metrics.average !== null
                    ? formatNumber(metrics.average)
                    : "—"
                }
                label={
                  analysisType.toLowerCase().includes("ndwi")
                    ? "Average NDWI"
                    : analysisType.toLowerCase().includes("change")
                    ? "Changed Area"
                    : "Average NDVI"
                }
                type="leaf"
              />

              <Metric
                icon="↓"
                value={
                  analysisType.toLowerCase().includes("change")
                    ? metrics.urbanExpansion !== null
                      ? `${formatNumber(metrics.urbanExpansion)}%`
                      : "—"
                    : metrics.minimum !== null
                    ? formatNumber(metrics.minimum)
                    : "—"
                }
                label={
                  analysisType.toLowerCase().includes("change")
                    ? "Urban Expansion"
                    : "Minimum"
                }
                type="down"
              />

              <Metric
                icon="↑"
                value={
                  analysisType.toLowerCase().includes("change")
                    ? metrics.vegetationChange !== null
                      ? `${formatNumber(metrics.vegetationChange)}%`
                      : "—"
                    : metrics.maximum !== null
                    ? formatNumber(metrics.maximum)
                    : "—"
                }
                label={
                  analysisType.toLowerCase().includes("change")
                    ? "Vegetation Change"
                    : "Maximum"
                }
                type="up"
              />

              <Metric
                icon="♣"
                value={
                  analysisType.toLowerCase().includes("change")
                    ? metrics.waterChange !== null
                      ? `${formatNumber(metrics.waterChange)}%`
                      : "—"
                    : metrics.coverage !== null
                    ? `${formatNumber(metrics.coverage, 0)}%`
                    : "—"
                }
                label={
                  analysisType.toLowerCase().includes("ndwi")
                    ? "Water Coverage"
                    : analysisType.toLowerCase().includes("change")
                    ? "Water Change"
                    : "Vegetation Coverage"
                }
                type="tree"
              />
            </div>

            <div className="charts-grid">
              <div className="chart-card">
                <div className="chart-header">
                  <div>
                    <strong>
                      {analysisType.toLowerCase().includes("ndwi")
                        ? "NDWI Distribution"
                        : analysisType.toLowerCase().includes("change")
                        ? "Change Distribution"
                        : "NDVI Distribution"}
                    </strong>
                    <span>
                      {analysisType.toLowerCase().includes("ndwi")
                        ? "Pixel count by NDWI value"
                        : analysisType.toLowerCase().includes("change")
                        ? "Change analysis distribution"
                        : "Pixel count by NDVI value"}
                    </span>
                  </div>

                  <button
                    className="chart-menu"
                    onClick={() => window.alert("Chart options will use backend data when available.")}
                    title="Chart options"
                  >
                    •••
                  </button>
                </div>

                <div className="bar-chart">
                  {[
                    18,
                    25,
                    31,
                    42,
                    55,
                    69,
                    82,
                    94,
                    100,
                    94,
                    83,
                    68,
                    51,
                    37,
                    26,
                    18,
                  ].map((height, index) => (
                    <div
                      className="bar"
                      style={{
                        height: `${height}%`,
                      }}
                      key={index}
                    ></div>
                  ))}
                </div>

                <div className="axis">
                  <span>-1.0</span>
                  <span>-0.5</span>
                  <span>0</span>
                  <span>0.5</span>
                  <span>1.0</span>
                </div>
              </div>

              <div className="chart-card">
                <div className="chart-header">
                  <div>
                    <strong>
                      {analysisType.toLowerCase().includes("ndwi")
                        ? "Water Analysis"
                        : analysisType.toLowerCase().includes("change")
                        ? "Change Summary"
                        : "Land Cover"}
                    </strong>
                    <span>
                      {analysisType.toLowerCase().includes("ndwi")
                        ? "Estimated water distribution"
                        : analysisType.toLowerCase().includes("change")
                        ? "Estimated change distribution"
                        : "Estimated land distribution"}
                    </span>
                  </div>

                  <button
                    className="chart-menu"
                    onClick={() => window.alert("Chart options will use backend data when available.")}
                    title="Chart options"
                  >
                    •••
                  </button>
                </div>

                <div className="donut-area">
                  <div className="donut">
                    <div className="donut-hole">
                      <strong>100%</strong>
                      <span>Area</span>
                    </div>
                  </div>

                  <div className="land-legend">
                    <LegendItem
                      label="Vegetation"
                      value="—"
                    />

                    <LegendItem
                      label="Built-up"
                      value="—"
                    />

                    <LegendItem
                      label="Agriculture"
                      value="—"
                    />

                    <LegendItem
                      label="Water"
                      value="—"
                    />

                    <LegendItem
                      label="Others"
                      value="—"
                    />
                  </div>
                </div>
              </div>
            </div>

              </>
            )}

            {activeTab === "timeseries" && (
              <div className="chart-card" style={{ minHeight: "300px" }}>
                <div className="chart-header">
                  <div>
                    <strong>NDVI Time Series</strong>
                    <span>Satellite observations over time</span>
                  </div>
                </div>
                <div style={{
                  padding: "40px 10px",
                  textAlign: "center",
                  color: "#64748b",
                }}>
                  <strong style={{ display: "block", fontSize: "32px", color: "#12365a", marginBottom: "8px" }}>
                    {metrics.average !== null ? formatNumber(metrics.average) : "—"}
                  </strong>
                  <span>
                    Current average NDVI for {locationName}
                    {displayDate !== "Waiting for analysis" ? ` · ${displayDate}` : ""}
                  </span>
                  <p style={{ marginTop: "18px", fontSize: "13px" }}>
                    Additional historical observations will appear here when the backend returns time-series data.
                  </p>
                </div>
              </div>
            )}

            {activeTab === "insights" && (
              <div className="insight-card" style={{ marginTop: "24px" }}>
                <div className="insight-symbol">✦</div>
                <div>
                  <span className="answer-label">INSIGHT</span>
                  <h3>{result ? "AI analysis completed" : "Ready for analysis"}</h3>
                  <p>
                    {result
                      ? answer
                      : "Enter a natural-language question above and GeoQuery AI will analyze the requested region."}
                  </p>
                </div>
              </div>
            )}

            {activeTab === "overview" && (
            <div className="insight-card">
              <div className="insight-symbol">✦</div>

              <div>
                <span className="answer-label">
                  INSIGHT
                </span>

                <h3>
                  {loading
                    ? "Analyzing your region..."
                    : result
                    ? "AI analysis completed"
                    : "Ready for analysis"}
                </h3>

                <p>
                  {loading
                    ? "GeoQuery AI is retrieving and analyzing the relevant Earth observation data."
                    : result
                    ? answer
                    : "Enter a natural-language question above and GeoQuery AI will analyze the requested region."}
                </p>
              </div>
            </div>
            )}
          </section>
        </div>
      </main>

      <aside className="queries-panel">
        <div className="queries-header">
          <div>
            <span className="dashboard-kicker">
              YOUR WORK
            </span>

            <h2>My Queries</h2>
          </div>

          <button
            className="new-query-btn"
            onClick={() => {
              setResult(null);
              setSubmittedQuery("");
              setQuery("");
              setPage("home");
            }}
          >
            +
          </button>
        </div>

        <div className="queries-list">
          {savedQueries.map((item) => (
            <div
              className="saved-query"
              key={item.title}
            >
              <div className="saved-icon">
                {item.icon}
              </div>

              <div className="saved-info">
                <strong>{item.title}</strong>
                <span>{item.date}</span>
              </div>

              <button
                onClick={() => submitQuery(item.title)}
                title="Run this saved query"
              >
                ↗
              </button>
            </div>
          ))}
        </div>

        <div className="panel-footer">
          <button
            onClick={() => {
              document.querySelector(".queries-list")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }}
          >
            View all queries →
          </button>
        </div>
      </aside>
      {showSettings && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
          }}
          onClick={() => setShowSettings(false)}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "16px",
              padding: "24px",
              width: "360px",
              boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
              }}
            >
              <h2 style={{ margin: 0 }}>Settings</h2>

              <button
                onClick={() => setShowSettings(false)}
                style={{
                  border: "none",
                  background: "transparent",
                  fontSize: "22px",
                  cursor: "pointer",
                }}
              >
                ×
              </button>
            </div>

            <p style={{ color: "#64748b", marginBottom: "18px" }}>
              GeoQuery AI settings
            </p>

            <div
              style={{
                padding: "14px",
                borderRadius: "10px",
                background: "#f8fafc",
                marginBottom: "12px",
              }}
            >
              <strong>API Status</strong>
              <div style={{ marginTop: "5px", color: "#16a34a" }}>
                ● Connected
              </div>
            </div>

            <div
              style={{
                padding: "14px",
                borderRadius: "10px",
                background: "#f8fafc",
              }}
            >
              <strong>Analysis Mode</strong>
              <div style={{ marginTop: "5px", color: "#64748b" }}>
                Demo Mode
              </div>
            </div>
          </div>
        </div>
      )}
      {showSaved && (
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.35)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999,
        }}
        onClick={() => setShowSaved(false)}
      >
        <div
          style={{
            background: "#ffffff",
            borderRadius: "16px",
            padding: "24px",
            width: "420px",
            maxWidth: "90%",
            boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "20px",
            }}
          >
            <h2 style={{ margin: 0 }}>Saved Queries</h2>

            <button
              onClick={() => setShowSaved(false)}
              style={{
                border: "none",
                background: "transparent",
                fontSize: "22px",
                cursor: "pointer",
              }}
            >
              ×
            </button>
          </div>

          {savedQueries.map((item) => (
            <div
              key={item.title}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "14px 0",
                borderBottom: "1px solid #eef2f6",
              }}
            >
              <span style={{ fontSize: "20px" }}>{item.icon}</span>

              <div style={{ flex: 1 }}>
                <strong style={{ display: "block" }}>{item.title}</strong>
                <span style={{ color: "#64748b", fontSize: "13px" }}>
                  {item.date}
                </span>
              </div>

              <button
                onClick={() => {
                  setShowSaved(false);
                  submitQuery(item.title);
                }}
                style={{
                  border: "none",
                  background: "#12365a",
                  color: "#fff",
                  borderRadius: "8px",
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
              >
                Run
              </button>
            </div>
          ))}
        </div>
      </div>
    )}
    </div>
  );
}

/* =========================================================
   SMALL COMPONENTS
========================================================= */

function Feature({ icon, title, text }) {
  return (
    <div className="feature">
      <div className="feature-icon-box">
        {icon}
      </div>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>
    </div>
  );
}

function Step({ number, title, text }) {
  return (
    <div className="step">
      <span className="step-number">
        {number}
      </span>

      <div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </div>
  );
}

function SidebarItem({
  icon,
  text,
  active,
  onClick,
}) {
  return (
    <button
      className={`sidebar-item ${
        active ? "active" : ""
      }`}
      onClick={onClick}
    >
      <span>{icon}</span>
      {text}
    </button>
  );
}

function Metric({
  icon,
  value,
  label,
  type,
}) {
  return (
    <div className={`metric ${type}`}>
      <div className="metric-icon">
        {icon}
      </div>

      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

function LegendItem({
  label,
  value,
}) {
  return (
    <div className="legend-item">
      <span className="legend-dot"></span>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;