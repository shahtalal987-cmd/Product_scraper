import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time
import pandas as pd
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),

    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


# --------------------------------------------------
# COMMON FUNCTIONS
# --------------------------------------------------

def fetch_page(url, filename):

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
        },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print("HTML LENGTH:", len(response.text))

        if response.status_code != 200:
            print("Amazon request failed.")
            return []

        response.raise_for_status()

        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)

        print(f"HTML saved to: {filename}")

        return response.text

    except requests.exceptions.Timeout:
        print("ERROR: Request timed out.")

    except requests.exceptions.ConnectionError:
        print("ERROR: Connection failed.")

    except requests.exceptions.HTTPError as error:
        print(f"ERROR: HTTP error - {error}")

    except requests.exceptions.RequestException as error:
        print(f"ERROR: Request failed - {error}")

    return None


def clean_text(element):

    if element:
        return element.get_text(" ", strip=True)

    return None


def clean_amazon_price(price_text):

    if not price_text:
        return None

    price_text = price_text.replace("\xa0", " ")
    price_text = price_text.replace("PKR", "")
    price_text = price_text.replace("$", "")
    price_text = price_text.replace(",", "")
    price_text = price_text.strip()

    # Example:
    # 8,310.98.98 → 8310.98
    parts = price_text.split(".")

    if len(parts) >= 2:
        price_text = parts[0] + "." + parts[1]

    try:
        return float(price_text)

    except ValueError:
        return None


def clean_amazon_rating(rating_text):

        if not rating_text:
         return None

        try:
          return float(
          rating_text.split()[0]
          )

        except (ValueError, IndexError):
          return None


def scrape_amazon_availability(product_url):

    if not product_url:
        return None

    try:
        response = requests.get(
            product_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/153.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9"
            },
            timeout=30
        )

        print(
            "Availability request:",
            response.status_code,
            product_url[:80]
        )

        if response.status_code != 200:
            return None

        html = response.text
        html_lower = html.lower()

        if (
            "bm-verify" in html_lower
            or "robot check" in html_lower
            or "captcha" in html_lower
        ):
            print(
                "Amazon verification page detected "
                "for availability."
            )
            return None

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        availability_element = soup.select_one(
            "#availability span"
        )

        if availability_element:

            availability = availability_element.get_text(
                " ",
                strip=True
            )

            if availability:
                return availability

        return None

    except requests.exceptions.RequestException as error:

        print(
            "Availability request error:",
            error
        )

        return None



def scrape_amazon_description(product_url):

    if not product_url:
        return None

    try:
        response = requests.get(
            product_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/153.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9"
            },
            timeout=30
        )

        print(
            "Description request:",
            response.status_code,
            product_url[:80]
        )

        if response.status_code != 200:
            return None

        html = response.text
        html_lower = html.lower()

        # Amazon verification / CAPTCHA page
        if (
            "bm-verify" in html_lower
            or "robot check" in html_lower
            or "captcha" in html_lower
        ):
            print("Amazon verification page detected for description.")
            return None

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # Main product description
        description_element = soup.select_one(
            "#productDescription"
        )

        if description_element:
            description = description_element.get_text(
                " ",
                strip=True
            )

            if description:
              return description

        # Backup: feature bullets
        bullets = soup.select(
            "#feature-bullets ul li span.a-list-item"
        )

        if bullets:
            description = " ".join(
                bullet.get_text(" ", strip=True)
                for bullet in bullets
            )

            if description:
                return description

        return None

    except requests.exceptions.RequestException as error:
        print("Description request error:", error)
        return None


# --------------------------------------------------
# AMAZON
# --------------------------------------------------


def scrape_amazon(url, page=1):


    parsed_url = urlparse(url)

    query_params = parse_qs(parsed_url.query)

    query_params["page"] = [str(page)]

    url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query_params, doseq=True),
            parsed_url.fragment
        )
    )

    print(f"\nAmazon Page {page}")
    print(f"REQUEST URL: {url}")

    # YAHAN tumhara existing Amazon code start hoga

    products = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1"
    }

    response = None

    # -------------------------
    # REQUEST WITH RETRIES
    # -------------------------

    for attempt in range(1, 4):

        try:

            print(
                f"Amazon request attempt {attempt}/3"
            )

            time.sleep(3 + attempt)

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

            print(
                "Status Code:",
                response.status_code
            )

            print(
                "HTML LENGTH:",
                len(response.text)
            )

            # Normal Amazon search page
            if (
                response.status_code == 200
                and len(response.text) > 100000
            ):
                break

            # Verification/challenge
            if (
                "captcha" in response.text.lower()
                or "robot" in response.text.lower()
                or "verify" in response.text.lower()
                or len(response.text) < 10000
            ):

                print(
                    "Amazon verification/challenge detected."
                )

                if attempt < 3:

                    wait_time = 10 * attempt

                    print(
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

        except requests.RequestException as e:

            print(
                "Amazon request error:",
                e
            )

            if attempt < 3:
                time.sleep(10 * attempt)

    # -------------------------
    # REQUEST FAILED
    # -------------------------

    if response is None:

        print(
            "Amazon request failed."
        )

        return []

    # -------------------------
    # SAVE DEBUG HTML
    # -------------------------

    with open(
        "data/amazon_debug.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(response.text)

    print(
        "Amazon debug HTML saved."
    )

    # -------------------------
    # BOT VERIFICATION CHECK
    # -------------------------
    

    # -------------------------
    # BEAUTIFULSOUP
    # -------------------------

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # -------------------------
    # PRODUCT CARDS
    # -------------------------

    cards = soup.select(
        'div[data-component-type="s-search-result"]'
    )

    print(
        "Amazon product cards found:",
        len(cards)
    )

    if not cards:

        print(
            "Amazon page did not contain product cards."

        )

        return []

    # -------------------------
    # LOOP PRODUCTS
    # -------------------------

    for card in cards:

        try:

            # -------------------------
            # NAME
            # -------------------------

            name_element = card.select_one(
                "h2 span"
            )

            name = (
                name_element.get_text(
                    " ",
                    strip=True
                )
                if name_element
                else None
            )

            # -------------------------
            # PRICE
            # -------------------------

            price = None

            price_element = card.select_one(
                ".a-price .a-offscreen"
            )

            if price_element:

                price_text = price_element.get_text(
                    strip=True
                )

                try:

                    cleaned_price = (
                        price_text
                        .replace("$", "")
                        .replace("PKR", "")
                        .replace(",", "")
                        .strip()
                    )

                    price = float(cleaned_price)

                except ValueError:
                    price = None


                    if price is None:

                        whole_element = card.select_one(
                            ".a-price-whole"
                        )

                        fraction_element = card.select_one(
                            ".a-price-fraction"
                        )

                    if whole_element:

                        whole=whole_element.get_text(
                            strip=True

                        ).replace(",", "").replace(".", "")

                        fraction = (
                            fraction_element.get_text(
                                strip=True
                            )

                            if fraction_element
                            else "80"
                        )

                        try:
                            price = float(
                                f"{whole}.{fraction}"
                            )

                        except ValueError:
                            price = None


                    if price is None:
                       print("\nPRICE NOT FOUND")
                       print("PRODUCT:", name)

                       price_debug = card.select_one(".a-price")

                    if price_debug:
                       print("PRICE HTML:")
                       print(price_debug.prettify())
                    else:
                       print("NO .a-price FOUND")

                       print("CARD TEXT:")
                       print(card.get_text(" ", strip=True)[:1000])



            # -------------------------
            # RATING
            # -------------------------

            rating = None

            rating_element = card.select_one(
                "span.a-icon-alt"
            )

            if rating_element:

                rating_text = rating_element.get_text(
                    strip=True
                )

                rating = clean_amazon_rating(
                    rating_text
                )

            # -------------------------
            # PRODUCT URL
            # -------------------------


                product_url = None

                url_element = card.select_one(
                    "a.a-link-normal.s-no-outline"
                )

                if not url_element:
                    url_element = card.select_one(
                        "a[href*='/dp/']"
                    )

                if not url_element:
                    url_element = card.select_one(
                        "a[href*='/gp/product/']"
    )

                if url_element and url_element.get("href"):
                    product_url = url_element.get("href")

                    if product_url.startswith("/"):
                        product_url = "https://www.amazon.com" + product_url

            # -------------------------
            # AVAILABILITY
            # -------------------------
            

                availability = None

# Complete card text
                card_text = card.get_text(" ", strip=True)

# Common Amazon availability patterns
                availability_patterns = [
                    r"\bIn Stock\b",
                    r"\bin stock\b",
                    r"Only \d+ left in stock",
                    r"Only \d+ left in stock - order soon",
                    r"\bCurrently unavailable\b",
                    r"\bTemporarily out of stock\b",
                    r"Usually ships within .+?(?=\s|$)",
                ]

                for pattern in availability_patterns:

                    match = re.search(
                         pattern,
                         card_text,
                         re.IGNORECASE
                    )

                    if match:

                       availability = match.group(0).strip()

                       break
            # -------------------------
            # DESCRIPTION
            # -------------------------

            description = None

            # Detail page verification ki wajah
            # se description unavailable ho sakti hai.

            if product_url:

                description = scrape_amazon_description(
                    product_url
                )

            # -------------------------
            # PRODUCT RECORD
            # -------------------------

            product = {

                "name": name,

                "price": price,

                "rating": rating,

                "availability": availability,

                "url": product_url,

                "category": "Wireless Headphones",

                "description": description
            }

            products.append(product)

        except Exception as e:

            print(
                "Amazon product skipped:",
                e
            )

    print(
        "Amazon products extracted:",
        len(products)
    )


    unique_products = []
    seen_urls =set()

    for product in products:

        product_url = product.get("url")

        if product_url and product_url not in seen_urls:
            seen_urls.add(product_url)
            unique_products.append(product)


    products = unique_products

    print(
        "Unique amazon products:",
        len(products)
    )


    valid_products = []

    for product in products:

        if not product.get("name"):
            continue

        if not product.get("url"):
            continue

        valid_products.append(product)

    products = valid_products

    print(
        "Valid Amazon products:",
        len(products)
    )

    return products


# --------------------------------------------------
# ALIBABA CLEAN FUNCTIONS
# --------------------------------------------------

def clean_alibaba_price(price_text):
    if not price_text:
        return None, None

    # Example: PKR 1,868 - 2,023
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", price_text)

    numbers = [
        float(number.replace(",", ""))
        for number in numbers
    ]

    if len(numbers) >= 2:
        return numbers[0], numbers[1]

    elif len(numbers) == 1:
        return numbers[0], numbers[0]

    return None, None


def clean_alibaba_sold(sold_text):
    if not sold_text:
        return None

    # Example: 1,337 sold
    match = re.search(r"([\d,]+)\s*sold", sold_text, re.I)

    if match:
        return int(match.group(1).replace(",", ""))

    return None


def clean_alibaba_rating(rating_text):
    if not rating_text:
        return None

    # Example: 4.8 /5.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*5", rating_text)

    if match:
        return float(match.group(1))

    return None

def find_price_in_container(container):

    if not container:
        return None

    # First try known Alibaba components
    selectors = [
        '[data-component="ProductPrice"]',
        '[class*="price"]',
        '[class*="Price"]',
        '[data-testid*="price"]',
        '[data-test*="price"]'
    ]

    for selector in selectors:

        element = container.select_one(selector)

        text = clean_text(element)

        if text and re.search(r"\d", text):
            return text

    # Fallback: search text inside container
    text = container.get_text(" ", strip=True)

    if text:

        price_match = re.search(
            r"(?:US\s*)?\$?\s*\d+(?:,\d{3})*(?:\.\d+)?"
            r"(?:\s*[-~]\s*(?:US\s*)?\$?\s*\d+(?:,\d{3})*(?:\.\d+)?)?",
            text,
            re.IGNORECASE
        )

        if price_match:
            return price_match.group(0)

    return None


def find_sold_in_container(container):

    if not container:
        return None

    selectors = [
        '[data-component="ProductSales"]',
        '[class*="sales"]',
        '[class*="Sales"]',
        '[class*="sold"]',
        '[class*="Sold"]',
        '[class*="orders"]',
        '[class*="Orders"]'
    ]

    for selector in selectors:

        element = container.select_one(selector)

        text = clean_text(element)

        if text:
            sold = clean_alibaba_sold(text)

            if sold is not None:
                return sold

    # Fallback
    text = container.get_text(" ", strip=True)

    if text:

        sold_match = re.search(
            r"[\d,.]+\s*[KkMm]?\s*\+?\s*(?:sold|orders?)",
            text,
            re.IGNORECASE
        )

        if sold_match:
            return clean_alibaba_sold(
                sold_match.group(0)
            )

    return None


def find_rating_in_container(container):

    if not container:
        return None

    selectors = [
        '[data-component="ProductReviewsCompact"]',
        '[class*="rating"]',
        '[class*="Rating"]',
        '[class*="review"]',
        '[class*="Review"]'
    ]

    for selector in selectors:

        elements = container.select(selector)

        for element in elements:

            text = clean_text(element)

            rating = clean_alibaba_rating(text)

            if rating is not None and 0 <= rating <= 5:
                return rating

    # Fallback
    text = container.get_text(" ", strip=True)

    ratings = re.findall(
        r"\b([0-5](?:\.\d)?)\b",
        text
    )

    for rating in ratings:

        try:

            value = float(rating)

            if 0 <= value <= 5:
                return value

        except ValueError:
            continue

    return None


def find_description_in_container(container, name):

    if not container:
        return None

    selectors = [
        '[class*="description"]',
        '[class*="Description"]',
        '[data-component*="Description"]'
    ]

    for selector in selectors:

        element = container.select_one(selector)

        text = clean_text(element)

        if text and text != name:
            return text

    return None


# --------------------------------------------------
# ALIBABA
# --------------------------------------------------


def scrape_alibaba_product_details(product_url):
    print(f"\nFetching detail page:")
    print(product_url)

    try:
        response = requests.get(
            product_url,
            headers=HEADERS,
            timeout=15
        )

        print(f"Detail page status: {response.status_code}")

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for script in soup.find_all("script"):

         script_text = script.get_text()

        if "Brightblue" in script_text or "description" in script_text.lower():
         print("RELEVANT SCRIPT FOUND")
         print(script_text[:3000]) 
         "break"



        # SAVE DETAIL HTML FOR INSPECTION
        with open(
        "data/alibaba_detail.html",
        "w",
        encoding="utf-8"
        ) as file:
            
         file.write(response.text)

        print("Detail HTML saved to: data/alibaba_detail.html")

        

        

        for element in soup.find_all(string=re.compile("Description", re.I)):
            print("Found:", element.strip())

        # Alibaba product description
        description = None

        description_selectors = [
            ".detail-desc-decorate-richtext",
            ".product-description",
            "[class*='product-description']",
            "[class*='description']"
        ]

        for selector in description_selectors:
            element = soup.select_one(selector)

            if element:
                description = element.get_text(
                    " ",
                    strip=True
                )

                if description:
                    break

        return description

    except requests.exceptions.Timeout:
        print("Detail page timeout.")
        return None

    except requests.exceptions.RequestException as error:
        print(f"Detail page request error: {error}")
        return None



def scrape_alibaba(url, pages=1):
    print("\n========== ALIBABA ==========")

    all_products = []

    for page in range(1, pages + 1):
        print(f"\n----- Alibaba Page {page} -----")

        parsed_url = urlparse(url)

        query_params = parse_qs(parsed_url.query)

        query_params["page"] = [str(page)]

        new_query = urlencode(query_params, doseq=True)

        page_url = urlunparse(

        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        )
    )
        print(page_url)

        print(f"REQUEST URL: {page_url}")

        filename = f"data/alibaba_page_{page}.html"

        html = fetch_page(page_url, filename)

        if not html:
            print(f"Page {page} failed. Moving to next page...")
            continue

        print("Alibaba URL:", page_url)
        print("Alibaba HTML length:", len(html))

        soup = BeautifulSoup(html, "html.parser")


        print("Alibaba page title:", soup.title.get_text(strip=True) if soup.title else "No title")
        print("Alibaba product-title links:", len(soup.select("a.product-title")))
        print("Alibaba product-title text:", len(soup.select(".product-title")))
        print("Alibaba links:", len(soup.select("a[href]")))

        for link in soup.select("a[href]"):
            text = link.get_text(" ", strip=True)
            href = link.get("href", "")

            if text and ("headphone" in text.lower() or "earphone" in text.lower()):
                print("POSSIBLE PRODUCT:", text[:120])
                print("PRODUCT URL:", href[:200])


        cards = soup.select("a.product-title")

        print(
            f"Alibaba products found on page {page}: {len(cards)}"
        )

        page_products = []

        for card in cards:
            try:
                title_element = card.select_one("h2")
                name = clean_text(title_element)

                product_url = card.get("href")

                if product_url:
                    product_url = urljoin(
                        "https://www.alibaba.com",
                        product_url
                    )

                # Complete product card text
                card_text = clean_text(
                    card.parent.parent.parent
                )

                # -------------------------
                # PRICE
                # -------------------------

                price_match = re.search(
                    r"PKR\s*([\d,\s]+)\s*-\s*([\d,\s]+)",
                    card_text,
                    re.I
                )

                price_min = None
                price_max = None

                if price_match:
                    price_min = float(
                        re.sub(
                            r"\s+",
                            "",
                            price_match.group(1)
                        ).replace(",", "")
                    )

                    price_max = float(
                        re.sub(
                            r"\s+",
                            "",
                            price_match.group(2)
                        ).replace(",", "")
                    )

                # -------------------------
                # SOLD
                # -------------------------

                sold_match = re.search(
                    r"([\d,]+)\s*sold",
                    card_text,
                    re.I
                )

                sold = None

                if sold_match:
                    sold = int(
                        sold_match.group(1).replace(",", "")
                    )

                # -------------------------
                # RATING
                # -------------------------

                rating_match = re.search(
                    r"(\d+(?:\.\d+)?)\s*/\s*5\.0",
                    card_text
                )

                rating = None

                if rating_match:
                    rating = float(
                        rating_match.group(1)
                    )

                # -------------------------
                # REVIEWS
                # -------------------------

                reviews_match = re.search(
                    r"\(([\d,]+)\s*Reviews\)",
                    card_text,
                    re.I
                )

                reviews = None

                if reviews_match:
                    reviews = int(
                        reviews_match.group(1).replace(",", "")
                    )

                # -------------------------
                # PRODUCT
                # -------------------------


                # -------------------------
                # DETAIL PAGE
                # -------------------------

                description = scrape_alibaba_product_details(
                product_url
)

               

                product = {
                    "source": "Alibaba",
                    "name": name,
                    "price_min": price_min,
                    "price_max": price_max,
                    "rating": rating,
                    "reviews": reviews,
                    "availability": "Available",
                    "sold": sold,
                    "url": product_url,
                    "category": "Wireless Headphones",
                    "description": description,
                }

                page_products.append(product)

            except Exception as error:
                print(
                    f"Product skipped on page {page}: {error}"
                )

        all_products.extend(page_products)

        print(
            f"Page {page} successfully added: "
            f"{len(page_products)} products"
        )

    # -------------------------
    # REMOVE DUPLICATES
    # -------------------------

    unique_products = []

    seen_urls = set()

    for product in all_products:
        product_url = product.get("url")

        if product_url and product_url not in seen_urls:
            seen_urls.add(product_url)
            unique_products.append(product)

    print("\n================================")
    print(
        f"Total unique Alibaba products: "
        f"{len(unique_products)}"
    )
    print("================================")

    return unique_products


# --------------------------------------------------
# EBAY
# --------------------------------------------------

def scrape_ebay_from_html(file_path):

    print("\n========== EBAY ==========")

    # -------------------------
    # READ SAVED HTML
    # -------------------------

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            html = file.read()

    except Exception as e:
        print(f"eBay HTML file error: {e}")
        return []

    print(f"HTML LENGTH: {len(html)}")

    soup = BeautifulSoup(html, "html.parser")

    # -------------------------
    # PRODUCT CARDS
    # -------------------------

    cards = soup.select(
       "li.s-card"
    )

    print(f"eBay product cards found: {len(cards)}")

    products = []

    # -------------------------
    # LOOP THROUGH CARDS
    # -------------------------

    for card in cards:

        try:

            # -------------------------
            # LISTING ID
            # -------------------------

            listing_id = card.get(
                "data-listingid"
            )

            # Skip cards without real listing ID
            if not listing_id:
                continue

            # -------------------------
            # NAME
            # -------------------------

            name_element = card.select_one(
                ".s-card__title"
            )

            name = (
                name_element.get_text(
                    " ",
                    strip=True
                )
                if name_element
                else None
            )

            # Skip empty / placeholder cards
            if not name:
                continue

            if name.lower() == "shop on ebay":
                continue

            # -------------------------
            # PRICE
            # -------------------------

            price_element = card.select_one(
                ".s-card__price"
            )

            price_text = (
                price_element.get_text(
                    " ",
                    strip=True
                )
                if price_element
                else None
            )

            price = None

            if price_text:

                import re

                price_match = re.search(
                    r"[\d,]+(?:\.\d+)?",
                    price_text
                )

                if price_match:

                    price = float(
                        price_match.group(
                            0
                        ).replace(",", "")
                    )

            # -------------------------
            # STATUS / CONDITION
            # -------------------------



            availability = None

            availability_selectors = [
                ".s-card__subtitle",
                ".s-card__caption",
                "[class*='availability']",
                "[class*='quantity']"
            ]

            for selector in availability_selectors:
                availability_element = card.select_one(selector)

                if availability_element:
                    availability_text = availability_element.get_text(
                        " ",
                        strip=True
                    )

                    if availability_text:
                        availability = availability_text
                        break

            # -------------------------
            # URL
            # -------------------------

            url_element = card.select_one(
                "a.s-card__link"
            )

            product_url = (
                url_element.get("href")
                if url_element
                else None
            )

            
            # -------------------------
            # DETAIL PAGE: RATING + DESCRIPTION
            # -------------------------

            description = None
            rating = None

            if product_url:

                try:
                    product_url = urljoin(
                        "https://www.ebay.com",
                        product_url
                    )

                    headers = {
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/155.0.0.0 Safari/537.36"
                        ),
                        "Accept-Language": "en-US,en;q=0.9"
                    }

                    session = requests.Session()

                    detail_response = session.get(
                        product_url,
                        headers=headers,
                        timeout=20
                    )

                    print(
                        f"Detail page status for {listing_id}: "
                        f"{detail_response.status_code}"
                    )

                    if detail_response.status_code == 200:

                        detail_html = detail_response.text

                        # Detect verification/challenge pages
                        detail_soup = BeautifulSoup(
                            detail_html,
                            "html.parser"
                        )

                        page_title = (
                            detail_soup.title.get_text(
                                " ",
                                strip=True
                            ).lower()
                            if detail_soup.title
                            else ""
                        )

                        if (
                            "pardon our interruption" in page_title
                            or "checking your browser" in detail_html.lower()
                        ):
                            print(
                                f"Verification page for {listing_id}; "
                                "rating/description skipped."
                            )

                        else:
                            # -------------------------
                            # RATING FROM JSON-LD
                            # -------------------------

                            rating_match = re.search(
                                r'"aggregateRating"\s*:\s*\{'
                                r'[^{}]*?"ratingValue"\s*:\s*"?'
                                r'([0-5](?:\.\d+)?)',
                                detail_html,
                                re.DOTALL
                            )

                            if rating_match:
                                rating = float(
                                    rating_match.group(1)
                                )

                            # -------------------------
                            # FIND SELLER DESCRIPTION IFRAME
                            # -------------------------

                            iframe = detail_soup.select_one(
                                "iframe#desc_ifr"
                            )

                            if iframe:
                                iframe_src = iframe.get("src")

                                if iframe_src:
                                    description_url = urljoin(
                                        product_url,
                                        iframe_src
                                    )

                                    description_response = session.get(
                                        description_url,
                                        headers=headers,
                                        timeout=20
                                    )

                                    print(
                                        "Description page status:",
                                        description_response.status_code
                                    )

                                    if (
                                        description_response.status_code
                                        == 200
                                    ):
                                        description_soup = BeautifulSoup(
                                            description_response.text,
                                            "html.parser"
                                        )

                                        for unwanted in description_soup(
                                            ["script", "style", "noscript"]
                                        ):
                                            unwanted.decompose()

                                        description = (
                                            description_soup.get_text(
                                                " ",
                                                strip=True
                                            )
                                        )

                                        if not description:
                                            description = None

                            print("Rating:", rating)
                            print(
                                "Description extracted:",
                                bool(description)
                            )

                    else:
                        print(
                            f"Detail page unavailable for {listing_id}: "
                            f"{detail_response.status_code}"
                        )

                    session.close()

                except requests.RequestException as e:
                    print(
                        f"eBay request error for {listing_id}: {e}"
                    )

                except Exception as e:
                    print(
                        f"eBay detail extraction error "
                        f"for {listing_id}: {e}"
                    )

            # -------------------------
            # FINAL PRODUCT
            # -------------------------

            product = {
                "name": name,
                "price": price,
                "rating": rating,
                "availability": availability,
                "url": product_url,
                "category": "Wireless Headphones",
                "description": description,
                "listing_id": listing_id
            }

            products.append(product)

        except Exception as e:

            print(
                f"eBay product extraction error: {e}"
            )

    # -------------------------
    # REMOVE DUPLICATES
    # -------------------------

    unique_products = []
    seen_ids = set()

    for product in products:

        listing_id = product.get(
            "listing_id"
        )

        if listing_id not in seen_ids:

            seen_ids.add(listing_id)

            unique_products.append(
                product
            )

    print(
        f"Unique eBay products: "
        f"{len(unique_products)}"
    )

    return unique_products




def scrape_ebay_auto_saved_pages(pages=2):
    import os
    import pandas as pd

    print("\n========== EBAY SAVED HTML PAGINATION ==========")

    # Page 1 and page 2 saved HTML files
    file_paths = [
        "data/ebay.html",
        "data/ebay_page2.html"
    ]

    all_products = []

    for page_number, file_path in enumerate(file_paths[:pages], start=1):
        print(f"\nScraping saved page {page_number}: {file_path}")

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        try:
            products = scrape_ebay_from_html(file_path)

            if products:
                all_products.extend(products)
                print(f"Products extracted: {len(products)}")
            else:
                print("No products returned from this page.")

        except Exception as error:
            print(f"Error on page {page_number}: {error}")

    # Remove duplicate listings
    unique_products = []
    seen = set()

    for product in all_products:
        key = product.get("listing_id")

        if not key:
            key = product.get("url") or product.get("name")

        if key and key not in seen:
            seen.add(key)
            unique_products.append(product)

    print(f"\nTotal unique eBay products: {len(unique_products)}")

    if not unique_products:
        print("No products found. Check the HTML files and scraper output.")
        return []

    # Create output folder automatically
    os.makedirs("output", exist_ok=True)

    df = pd.DataFrame(unique_products)

    csv_path = "output/ebay_products.csv"
    excel_path = "output/ebay_products.xlsx"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(excel_path, index=False)

    print(f"\nCSV saved: {csv_path}")
    print(f"Excel saved: {excel_path}")
    print(f"Total saved records: {len(df)}")

    return unique_products

# --------------------------------------------------
# MAIN TEST
# --------------------------------------------------

if __name__ == "__main__":

    amazon_url = (
        "https://www.amazon.com/s?k=wireless+headphones"
    )

    alibaba_url = (
        "https://www.alibaba.com/countrysearch/"
        "CN/wireless-headphones.html"
    )

    ebay_url = (
        "https://www.ebay.com/sch/i.html"
        "?_nkw=wireless+headphones"
    )

    amazon_products = scrape_amazon(
        amazon_url
    )

    alibaba_products = scrape_alibaba(
        alibaba_url,
        pages=3
    )

    ebay_products = scrape_ebay_from_html(
        ebay_url
    )

    print(
        "Amazon products:",
        len(amazon_products)
    )

    print(
        "Alibaba products:",
        len(alibaba_products)
    )

    print(
        "eBay products:",
        len(ebay_products)
    )

    all_products = (
        amazon_products
        + alibaba_products
        + ebay_products
    )

    print("\n==============================")
    print(
        "TOTAL PRODUCTS:",
        len(all_products)
    )
    print("==============================")

    for product in all_products[:10]:

        print("\nProduct:")

        for key, value in product.items():

            print(
                f"{key}: {value}"
            )

