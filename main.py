import pandas as pd

from scraper.scraper import scrape_alibaba, scrape_amazon, scrape_ebay_auto_saved_pages


amazon_url = "https://www.amazon.com/s?k=wireless+headphones"
alibaba_url = "https://www.alibaba.com/countrysearch/CN/wireless-headphones.html"
ebay_url = "https://www.ebay.com/sch/i.html?_nkw=wireless+headphones"


# ================= AMAZON =================

amazon_products = []

for page in range(1, 4):

    page_products = scrape_amazon(
        amazon_url,
        page=page
    )

    amazon_products.extend(page_products)


print(f"\nTotal Amazon products: {len(amazon_products)}")

for product in amazon_products:
    print(product)


# ================= ALIBABA =================

alibaba_products = scrape_alibaba(
    alibaba_url,
    pages=3
)

print(f"\nTotal Alibaba products: {len(alibaba_products)}")

for product in alibaba_products:
    print(product)

ebay_products = scrape_ebay_auto_saved_pages(pages=2)

print(f"\nTotal eBay products: {len(ebay_products)}")

for product in ebay_products:
    print(product)


# ================= SAVE DATA =================

amazon_df = pd.DataFrame(amazon_products)

amazon_df.to_csv(
    "output/amazon_products.csv",
    index=False
)

amazon_df.to_excel(
    "output/amazon_products.xlsx",
    index=False
)


alibaba_df = pd.DataFrame(alibaba_products)

alibaba_df.to_csv(
    "output/alibaba_products.csv",
    index=False
)

alibaba_df.to_excel(
    "output/alibaba_products.xlsx",
    index=False
)


ebay_df = pd.DataFrame(ebay_products)

ebay_df.to_csv(
    "output/ebay_products.csv",
    index=False
)

ebay_df.to_excel(
    "output/ebay_products.xlsx",
    index=False
)

print("eBay CSV: output/ebay_products.csv")
print("eBay Excel: output/ebay_products.xlsx")


print("\nData saved successfully!")

print("Amazon CSV: output/amazon_products.csv")
print("Amazon Excel: output/amazon_products.xlsx")

print("Alibaba CSV: output/alibaba_products.csv")
print("Alibaba Excel: output/alibaba_products.xlsx")