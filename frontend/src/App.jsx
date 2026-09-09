import { useState } from "react";
import "./App.css";

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

function LeafIcon() {
  return <span className="feature-icon">⌁</span>;
}

function App() {
  const [page, setPage] = useState("home");
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState(
    "Show me Sentinel-2 imagery of Bengaluru from June 2024 with less than 10% cloud cover and calculate NDVI."
  );

  const submitQuery = () => {
    if (!query.trim()) return;

    setSubmittedQuery(query);
    setPage("dashboard");
    setQuery("");
  };

  const useExample = (text) => {
    setQuery(text);
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
        />
      ) : (
        <Dashboard
          query={query}
          setQuery={setQuery}
          submitQuery={submitQuery}
          submittedQuery={submittedQuery}
          setPage={setPage}
          useExample={useExample}
        />
      )}
    </div>
  );
}

/* =========================
   HOME PAGE
========================= */

function HomePage({
  query,
  setQuery,
  submitQuery,
  useExample,
  goToDashboard,
}) {
  return (
    <>
      <header className="navbar">
        <div className="brand">
          <div className="brand-mark">◒</div>
          <span>GeoQuery AI</span>
        </div>

        <nav>
          <button className="nav-link active">Home</button>
          <button className="nav-link">Use Cases</button>
          <button className="nav-link">About</button>
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
              <button className="primary-btn large" onClick={goToDashboard}>
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

        <section className="features-strip">
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
              onKeyDown={(e) => e.key === "Enter" && submitQuery()}
              placeholder="Ask something about the Earth..."
            />
            <button onClick={submitQuery}>→</button>
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

      <footer className="footer">
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

/* =========================
   DASHBOARD
========================= */

function Dashboard({
  query,
  setQuery,
  submitQuery,
  submittedQuery,
  setPage,
  useExample,
}) {
  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">◒</div>
          <strong>GeoQuery AI</strong>
        </div>

        <div className="sidebar-menu">
          <SidebarItem icon="⌕" text="New Query" active />
          <SidebarItem icon="♡" text="Saved" />
          <SidebarItem icon="◫" text="Explore" />
          <SidebarItem icon="⚙" text="Settings" />
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
            System operational
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

              <button onClick={() => useExample(examples[1])}>
                Vegetation
              </button>

              <button onClick={() => useExample(examples[2])}>
                Water bodies
              </button>

              <button onClick={() => useExample(examples[3])}>
                Land cover
              </button>
            </div>

            <button className="primary-btn" onClick={submitQuery}>
              Analyze
              <span>→</span>
            </button>
          </div>
        </section>

        <div className="dashboard-grid">
          <section className="result-column">
            <div className="result-header">
              <div>
                <span className="result-kicker">ANALYSIS RESULT</span>
                <h2>Bengaluru</h2>
                <p>Sentinel-2 L2A · 12 June 2024</p>
              </div>

              <button className="download-btn">
                ↓ <span>Download</span>
              </button>
            </div>

            <div className="map-card">
              <div className="map-toolbar">
                <button>+</button>
                <button>−</button>
              </div>

              <div className="map-type">NDVI⌄</div>

              <div className="satellite-map">
                <div className="map-grid"></div>
                <div className="map-road road-one"></div>
                <div className="map-road road-two"></div>
                <div className="map-road road-three"></div>
                <div className="map-road road-four"></div>

                <div className="city-boundary">
                  <span>Bengaluru</span>
                </div>

                <div className="map-location">
                  <span></span>
                </div>
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
                <strong>7%</strong>
              </div>

              <div>
                <span>Satellite</span>
                <strong>Sentinel-2</strong>
              </div>

              <div>
                <span>Resolution</span>
                <strong>10 m</strong>
              </div>
            </div>

            <div className="answer-card">
              <div className="answer-icon">✦</div>
              <div>
                <span className="answer-label">AI SUMMARY</span>
                <p>{submittedQuery}</p>
                <p>
                  The selected region shows relatively healthy vegetation,
                  with higher NDVI values in the eastern and southern areas.
                  Central urban areas show lower vegetation.
                </p>
              </div>
            </div>
          </section>

          <section className="analysis-column">
            <div className="analysis-tabs">
              <button className="active">Overview</button>
              <button>Time Series</button>
              <button>Insights</button>
            </div>

            <div className="analysis-title">
              <span className="result-kicker">VEGETATION ANALYSIS</span>
              <h2>NDVI Analysis</h2>
              <p>Bengaluru · 12 June 2024</p>
            </div>

            <div className="metric-grid">
              <Metric
                icon="⌁"
                value="0.63"
                label="Average NDVI"
                type="leaf"
              />

              <Metric
                icon="↓"
                value="0.12"
                label="Minimum"
                type="down"
              />

              <Metric
                icon="↑"
                value="0.89"
                label="Maximum"
                type="up"
              />

              <Metric
                icon="♣"
                value="74%"
                label="Vegetation Coverage"
                type="tree"
              />
            </div>

            <div className="charts-grid">
              <div className="chart-card">
                <div className="chart-header">
                  <div>
                    <strong>NDVI Distribution</strong>
                    <span>Pixel count by NDVI value</span>
                  </div>
                  <span className="chart-menu">•••</span>
                </div>

                <div className="bar-chart">
                  {[
                    18, 25, 31, 42, 55, 69, 82, 94, 100, 94, 83, 68, 51, 37,
                    26, 18,
                  ].map((height, index) => (
                    <div
                      className="bar"
                      style={{ height: `${height}%` }}
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
                    <strong>Land Cover</strong>
                    <span>Estimated distribution</span>
                  </div>
                  <span className="chart-menu">•••</span>
                </div>

                <div className="donut-area">
                  <div className="donut">
                    <div className="donut-hole">
                      <strong>100%</strong>
                      <span>Area</span>
                    </div>
                  </div>

                  <div className="land-legend">
                    <LegendItem label="Vegetation" value="42%" />
                    <LegendItem label="Built-up" value="28%" />
                    <LegendItem label="Agriculture" value="18%" />
                    <LegendItem label="Water" value="8%" />
                    <LegendItem label="Others" value="4%" />
                  </div>
                </div>
              </div>
            </div>

            <div className="insight-card">
              <div className="insight-symbol">✦</div>

              <div>
                <span className="answer-label">INSIGHT</span>
                <h3>Healthy vegetation detected</h3>
                <p>
                  The region shows relatively healthy vegetation, with higher
                  NDVI values in the eastern and southern areas. Central urban
                  areas show lower vegetation.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>

      <aside className="queries-panel">
        <div className="queries-header">
          <div>
            <span className="dashboard-kicker">YOUR WORK</span>
            <h2>My Queries</h2>
          </div>

          <button className="new-query-btn" onClick={() => setPage("home")}>
            +
          </button>
        </div>

        <div className="queries-list">
          {savedQueries.map((item) => (
            <div className="saved-query" key={item.title}>
              <div className="saved-icon">{item.icon}</div>

              <div className="saved-info">
                <strong>{item.title}</strong>
                <span>{item.date}</span>
              </div>

              <button>•••</button>
            </div>
          ))}
        </div>

        <div className="panel-footer">
          <button>View all queries →</button>
        </div>
      </aside>
    </div>
  );
}

/* =========================
   SMALL COMPONENTS
========================= */

function Feature({ icon, title, text }) {
  return (
    <div className="feature">
      <div className="feature-icon-box">{icon}</div>
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
      <span className="step-number">{number}</span>
      <div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </div>
  );
}

function SidebarItem({ icon, text, active }) {
  return (
    <button className={`sidebar-item ${active ? "active" : ""}`}>
      <span>{icon}</span>
      {text}
    </button>
  );
}

function Metric({ icon, value, label, type }) {
  return (
    <div className={`metric ${type}`}>
      <div className="metric-icon">{icon}</div>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

function LegendItem({ label, value }) {
  return (
    <div className="legend-item">
      <span className="legend-dot"></span>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;