import json
import time

import pandas as pd
import scrapy
import undetected_chromedriver as webdriver


class ProductSpider(scrapy.Spider):
    name = "product_spider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookies = {}
        self.human_check()

    def human_check(self):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        # options.add_argument("--headless")
        driver = webdriver.Chrome(options=options, version_main=132)
        driver.get("https://www.newegg.com")
        time.sleep(20)
        self.cookies = {
            cookie["name"]: cookie["value"] for cookie in driver.get_cookies()
        }
        driver.quit()

    def start_requests(self):
        df = pd.read_csv("./attachments/urls.csv", header=None)
        urls = df.iloc[:, 0].tolist()
        for url in urls:
            yield scrapy.Request(
                url=url, callback=self.parse_product, cookies=self.cookies
            )

    def parse_product(self, response):
        scripts = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        title, brand, price, ratings, description = None, None, None, None, None

        for script in scripts:
            try:
                data = json.loads(script)
                if "aggregateRating" in data:
                    title = data.get("name")
                    brand = data.get("brand")
                    price = data["offers"].get("price")
                    ratings = data["aggregateRating"].get("reviewCount")
                    description = data.get("description")
            except json.JSONDecodeError:
                self.logger.error("Failed to decode JSON from script.")

        NeweggItemNumber = response.url.split("/")[-1]
        ItemNumber = f"{NeweggItemNumber[-8:-6]}-{NeweggItemNumber[-6:-3]}-{NeweggItemNumber[-3:]}"

        yield self.request_reviews(
            NeweggItemNumber,
            ItemNumber,
            1,
            [],
            title,
            brand,
            price,
            ratings,
            description,
        )

    def fetch_reviews(
        self,
        response,
        NeweggItemNumber,
        ItemNumber,
        page_index,
        reviews,
        title,
        brand,
        price,
        ratings,
        description,
    ):
        try:
            api_response = json.loads(response.text)

            if (
                "SearchResult" in api_response
                and "CustomerReviewList" in api_response["SearchResult"]
            ):
                for review in api_response["SearchResult"]["CustomerReviewList"]:
                    reviews.append(
                        {
                            "reviewer_name": review.get("DisplayName", "N/A"),
                            "rating": review.get("Rating", "N/A"),
                            "review_title": review.get("Title", ""),
                            "review_body": f"Pros: {review.get('Pros', '')}\n Cons: {review.get('Cons', '')}\n Overall Review: {review.get('Comments', '')}",
                            "date": review.get("InDate", ""),
                            "verified": (
                                True if review.get("ApproveStates") == "Y" else False
                            ),
                        }
                    )

                # If more pages exist, request the next page
                if api_response["SearchResult"].get("ReviewPageCount", 0) > page_index:
                    page_index += 1
                    yield self.request_reviews(
                        NeweggItemNumber,
                        ItemNumber,
                        page_index,
                        reviews,
                        title,
                        brand,
                        price,
                        ratings,
                        description,
                    )
                else:
                    self.logger.info(f"Collected {len(reviews)} reviews.")
                    yield {
                        "title": title,
                        "brand": brand,
                        "price": price,
                        "ratings": ratings,
                        "description": description,
                        "reviews": reviews,
                    }
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON from API response.")
            yield {
                "title": title,
                "brand": brand,
                "price": price,
                "ratings": ratings,
                "description": description,
                "reviews": [],
            }

    def request_reviews(
        self,
        NeweggItemNumber,
        ItemNumber,
        page_index,
        reviews,
        title,
        brand,
        price,
        ratings,
        description,
    ):
        params = {
            "IsGetSummary": True,
            "IsGetTopReview": False,
            "IsGetItemProperty": True,
            "IsGetAllReviewCategory": False,
            "IsSearchWithoutStatistics": False,
            "IsGetFilterCount": False,
            "IsGetFeatures": True,
            "SearchProperty": {
                "CombineGroup": 3,
                "FilterDate": 0,
                "IsB2BExclusiveReviews": False,
                "IsBestCritialReview": False,
                "IsBestFavorableReview": False,
                "IsItemMarkOnly": False,
                "IsProductReviewSearch": True,
                "IsPurchaserReviewOnly": False,
                "IsResponsiveSite": False,
                "IsSmartPhone": False,
                "IsVendorResponse": False,
                "IsVideoReviewOnly": False,
                "ItemNumber": ItemNumber,
                "NeweggItemNumber": NeweggItemNumber,
                "PageIndex": page_index,
                "PerPageItemCount": 25,
                "RatingReviewDisplayType": 0,
                "ReviewTimeFilterType": 0,
                "RatingType": -1,
                "ReviewType": 3,
                "SearchKeywords": "",
                "SearchLanguage": "",
                "SellerId": "",
                "SortOrderType": 1,
                "TransNumber": 0,
                "WithImage": False,
                "HotKeyword": "",
                "HotKeywordList": [],
                "SearchkeywordsList": [],
            },
        }

        reviewRequestStr = json.dumps(params)
        url = f"https://www.newegg.com/product/api/ProductReview?reviewRequestStr={reviewRequestStr}"

        return scrapy.Request(
            url=url,
            callback=self.fetch_reviews,
            cb_kwargs={
                "NeweggItemNumber": NeweggItemNumber,
                "ItemNumber": ItemNumber,
                "page_index": page_index,
                "reviews": reviews,
                "title": title,
                "brand": brand,
                "price": price,
                "ratings": ratings,
                "description": description,
            },
        )
