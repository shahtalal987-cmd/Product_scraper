import requests
from bs4 import BeautifulSoup

# 1. Read saved eBay HTML
with open("data/ebay.html", "r", encoding="utf-8") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")

cards = soup.select("li.s-card")

# Inspect the actual HTML of the third product card
card = cards[2]

print("\n========== CARD HTML DEBUG ==========")
print(card.prettify()[:12000])

print("\n========== RATING RELATED HTML ==========")
for element in card.select(
    '[aria-label*="star" i], '
    '[aria-label*="rating" i], '
    '[class*="rating"], '
    '[class*="star"]'
):
    print(element.get_text(" ", strip=True))
    print("ARIA:", element.get("aria-label"))
    print("CLASS:", element.get("class"))

print("\n========== ALL LINKS CONTAINING ITEM IDS ==========")
for link in card.select("a[href]"):
    href = link.get("href", "")
    if "/itm/" in href or "ebaydesc" in href:
        print("TEXT:", link.get_text(" ", strip=True))
        print("URL:", href)



print("Total product cards:", len(cards))

# Test first 3 products
for i, card in enumerate(cards[:3], start=1):
    print(f"\n========== PRODUCT {i} ==========")

    # Product title
    title_tag = card.select_one(
        ".s-card__title"
    )
    title = title_tag.get_text(" ", strip=True) if title_tag else None
    print("Title:", title)

    # 2. Test rating
    rating = None

    rating_tag = card.select_one(
        ".x-star-rating span"
    )

    if rating_tag:
        rating_text = rating_tag.get_text(" ", strip=True)
        print("Rating text:", rating_text)

        import re
        match = re.search(r"\b([0-5](?:\.\d+)?)\b", rating_text)
        if match:
            rating = float(match.group(1))

    print("Rating:", rating)

    # 3. Test description URL
    description_url = None

    item_link = card.select_one(
        "a.s-card__link"
    )

    if item_link:
        product_url = item_link.get("href")
        print("Product URL:", product_url)

    # Search description links present in the saved card HTML
    for link in card.select("a[href]"):
        href = link.get("href", "")

        if "ebaydesc.com/itmdesc/" in href:
            description_url = href
            break

    print("Description URL:", description_url)

    # 4. Test description-page request, only if URL exists
    if description_url:
        try:
            response = requests.get(
                description_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/130.0.0.0 Safari/537.36"
                    )
                },
                timeout=15
            )

            print("Description page status:", response.status_code)

            if response.status_code == 200:
                description_soup = BeautifulSoup(
                    response.text, "html.parser"
                )

                description_text = description_soup.get_text(
                    " ", strip=True
                )

                print(
                    "Description preview:",
                    description_text[:500] or "Empty description"
                )
            else:
                print(
                    "Description unavailable through this request."
                )

        except requests.RequestException as error:
            print("Description request error:", error)

    else:
        print("No description URL found in this product card.")

