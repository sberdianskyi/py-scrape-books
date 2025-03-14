import scrapy
from scrapy import Selector
from scrapy.http import Response
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By

from books.items import BooksItem

options = Options()
options.add_argument("--headless")

# ran to write the file with books data: scrapy crawl book -O books.jl


class BookSpider(scrapy.Spider):
    name = "book"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.driver = webdriver.Chrome(options=options)

    def closed(self, reason: str):
        self.driver.close()

    def parse(self, response: Response, **kwargs):
        for book_card in response.css("article.product_pod"):
            yield self._parse_book_details(response, book_card)

        next_page = response.css("li.next > a::attr(href)").get()
        if next_page is not None:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def _parse_book_details(self, response: Response, book_card: Selector) -> BooksItem:
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

        absolute_url = response.urljoin(book_card.css("h3 > a::attr(href)").get())

        self.driver.get(absolute_url)
        book_details = self.driver.find_element(By.CLASS_NAME, "product_page")
        breadcrumb = self.driver.find_element(By.CLASS_NAME, "breadcrumb")

        item = BooksItem()
        item["title"] = book_details.find_element(By.TAG_NAME, "h1").text
        item["price"] = book_details.find_element(By.CLASS_NAME, "price_color").text

        availability_row = book_details.find_element(
            By.XPATH, "//tr[contains(., 'Availability')]"
        )
        item["amount_in_stock"] = (
            availability_row.find_element(By.XPATH, ".//td")
            .text.replace("(", "")
            .split(" ")[2]
        )

        item["rating"] = rating_map.get(
            book_details.find_element(By.CLASS_NAME, "star-rating")
            .get_attribute("class")
            .split()[-1]
        )

        item["category"] = (
            breadcrumb.find_elements(By.TAG_NAME, "li")[2]
            .find_element(By.TAG_NAME, "a")
            .text
        )
        item["description"] = (
            book_details.find_element(By.ID, "product_description")
            .find_element(By.XPATH, "following-sibling::p[1]")
            .text
        )

        upc_row = book_details.find_element(By.XPATH, "//tr[contains(., 'UPC')]")
        item["upc"] = upc_row.find_element(By.XPATH, ".//td").text

        return item
