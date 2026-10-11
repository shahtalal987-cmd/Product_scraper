
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
from scraper.scraper import scrape_ebay_auto_saved_pages, scrape_alibaba, scrape_amazon
import pandas as pd
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "ebay_products.csv"


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status": "Backend connected",
        "message": "Python API is running."
    })


@app.route("/api/download", methods=["GET"])
def download_csv():
    source = request.args.get("source", "ebay").lower()

    allowed_sources = ["amazon", "alibaba", "ebay"]

    if source not in allowed_sources:
        return jsonify({"error": "Invalid website."}), 400

    csv_path = BASE_DIR / "output" / f"{source}_products.csv"

    if not csv_path.exists():
        return jsonify({
            "error": "CSV file not found. Run scraping first."
        }), 404

    return send_file(
        csv_path,
        as_attachment=True,
        download_name=f"{source}_products.csv",
        mimetype="text/csv"
    )

@app.route("/api/scrape", methods=["POST"])
def start_scraping():
    data = request.get_json(silent=True) or {}

    product_name = (data.get("product") or "").strip()
    source = (data.get("source") or "eBay").strip().lower()

    if not product_name:
        return jsonify({
            "success": False,
            "message": "Please enter a product name.",
            "products": []
        }), 400

    try:
        if source == "amazon":
            search_url = (
                "https://www.amazon.com/s?k="
                + quote_plus(product_name)
            )
            products = scrape_amazon(search_url, page=1)

        elif source == "alibaba":
            search_url = (
                "https://www.alibaba.com/trade/search?SearchText="
                + quote_plus(product_name)
            )
            products = scrape_alibaba(search_url, pages=2)

        elif source == "ebay":
            # eBay currently reads your existing saved HTML files.
            products = scrape_ebay_auto_saved_pages(pages=2)

        else:
            return jsonify({
                "success": False,
                "message": "Unsupported website selected.",
                "products": []
            }), 400

        # Save results in CSV and Excel
        output_dir = BASE_DIR / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = output_dir / f"{source}_products.csv"
        excel_path = output_dir / f"{source}_products.xlsx"

        df = pd.DataFrame(products)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        df.to_excel(excel_path, index=False)

        return jsonify({
            "success": True,
            "message": (
                f"{source.title()} scraping completed. "
                f"{len(products)} products found."
            ),
            "products": products
        })

    except Exception as error:
        print(f"Scraping API error: {error}")

        return jsonify({
            "success": False,
            "message": str(error),
            "products": []
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
