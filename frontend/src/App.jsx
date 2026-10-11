import { useState } from "react";
import "./App.css";

function App() {
  const [product, setProduct] = useState("");
  const [status, setStatus] = useState("Ready to scrape");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [source, setSource] = useState("eBay");

  const startScraping = async () => {
    if (!product.trim()) {
      alert("Please enter a product name.");
      return;
    }

    setLoading(true);
    setStatus(`Scraping ${source} pages...`);
    setProducts([]);

    try {
      const response = await fetch(
        "http://product-scraper-6c1z.vercel.app/api/scrape",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            product: product.trim(),
            source: source,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Scraping failed.");
      }

      setProducts(data.products || []);
      setStatus(data.message);
    } catch (error) {
      setStatus(`Error: ${error.message}`);
      console.error("Scraping error:", error);
    } finally {
      setLoading(false);
    }
  };



 const downloadCSV = () => {
  window.location.href =
    `http://product-scraper-6c1z.vercel.app/api/download?source=${source.toLowerCase()}`;
};


  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">Product<span>Scraper</span></div>
        <p className="menu-label">WORKSPACE</p>
        <div className="menu-item active">⌕ &nbsp; Product Scraper</div>
        <div className="menu-item">▤ &nbsp; Export Data</div>
        <div className="sidebar-bottom"></div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h2>Product Scraper</h2>
            <p>Collect and export e-commerce product data</p>
          </div>
          <span className="status-badge">● Ready</span>
        </header>

        <section className="welcome">
          <p className="eyebrow">DATA COLLECTION WORKSPACE</p>
          <h1>Find products. Collect data.</h1>
          <p>Enter a product keyword to start your scraping workflow.</p>
        </section>

        <section className="panel">
          <h3>Search Products</h3>
          <p className="muted">
            Enter the name of the product you want to collect.
          </p>

          <form onSubmit={(e) => {
            e.preventDefault();
            startScraping();
          }}>
            <label htmlFor="product">Product name</label>
            <div className="search-row">
              <input
                id="product"
                type="text"
                placeholder="e.g. wireless headphones"
                value={product}
                onChange={(e) => setProduct(e.target.value)}
              />

              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
              >
                <option value="Amazon">Amazon</option>
                <option value="Alibaba">Alibaba</option>
                <option value="eBay">eBay</option>
              </select>



              <button type="submit" disabled={loading}>
                {loading ? "Scraping..." : "▶ Start Scraping"}
              </button>
            </div>
          </form>

          <div className="status-line">
            <span className={loading ? "status-dot working" : "status-dot"} />
            <span>{status}</span>
          </div>
        </section>

        <section className="results-header">
          <div>
            <h3>Scraping Results</h3>
            <p className="muted">Products collected during this session</p>
          </div>
          <button className="download-btn" onClick={downloadCSV}>
            ↓ Download CSV
          </button>
        </section>

        <section className="stats">
          <div className="stat-card">
            <p>Total Products</p>
            <h2>{products.length}</h2>
          </div>
          <div>
            <p></p>
            <h2 ></h2>
          </div>
          <div className="stat-card">
            <p>Export Format</p>
            <h2>CSV</h2>
          </div>
        </section>

        <footer></footer>
      </main>
    </div>
  );
}

export default App;
