import logging
import csv
import re

from bs4 import BeautifulSoup
import requests

LOGGER = logging.getLogger(name=__file__)


# Store classes should be placed in separate file
# but for purpose of this task is not necessary
class BaseStore(object):

    base_browse_url = None

    def __init__(self, store_url):
        self.store_url = store_url

    def products(self, url=None, count=5):
        """Download products info
        """
        if url is None:
            url = self.base_browse_url

        url = "{store_url}{url}".format(
            store_url=self.store_url,
            url=url
        )
        return self._products(url, count)

    def _products(self, url, count):
        """Download products information from given url
        """
        products_data = []

        response = requests.get(url)

        if response.ok:
            product_links = self.products_links(response.content)
            for p in product_links[:count]:
                product = self.product_data(p)
                if product:
                    products_data.append(self.get_product_data(product))

        return products_data

    def get_product_data(self, product_data):
        raise NotImplementedError

    def products_links(self, content):
        """Method for finding product's links in given content.
        """
        raise NotImplementedError

    def product_data(self, product_url):
        """Get product info"""
        raise NotImplementedError


class ShopifyStore(BaseStore):
    base_browse_url = "/collections/all/"

    def get_product_data(self, product_data):
        product = {"title": product_data["title"], "image": "-"}

        if product_data.get("image", None):
            product["image"] = product_data["image"]["src"]

        return product

    # Shopify specific products selector
    def products_links(self, content):
        links = []

        product_selectors = [
            'a[href^=/products/]',
            'a[href^=%sproducts/]' % self.base_browse_url
        ]
        soup = BeautifulSoup(content, "lxml")

        for selector in product_selectors:
            for a in soup.select(selector):
                href = a.attrs.get("href")
                # Remove GET parameters
                # The query component is indicated by the first question mark
                product_url = href.split("?")[0]
                if product_url not in links:
                    # we can use set() because we need preserve order of links
                    links.append(product_url)

        return [l for l in links]

    def product_data(self, product_url):
        """Fetch product data.
        """
        url = "{store_url}{product_slug}.json".format(
            store_url=self.store_url,
            product_slug=product_url
        )

        response = requests.get(url)
        if not response.ok:
            logging.debug("No product '%s' found", url)
            return None

        return response.json()["product"]


class StoreDownloader(object):

    def _read_csv(self, source_file):
        """Read csv file with store urls
        """
        stores = set()

        with open(source_file, 'rb') as f:
            reader = csv.reader(f)
            # skip header
            next(reader, None)
            for store in reader:
                #url = store["url"]
                url = store[0]
                if not url.startswith("http"):
                    url = "http://{url}".format(url=url)
                stores.add(url)

        return stores

    def read_stores(self, source_file):
        """Return unique set of store to process
        """
        stores = []

        if source_file.lower().endswith(".csv"):
            stores = self._read_csv(source_file)

        # We can define more reader methods like .json, .xls etc..

        return stores

    def _find_pattern(self, content, pattern):
        return re.findall(pattern, content)

    def _find_links(self, content, selector):
        soup = BeautifulSoup(content, "lxml")
        links = set()
        for a in soup.select(selector):
            links.add(a.attrs.get("href"))

        return links

    def find_emails(self, content):
        """Find emails addresses in given content
        """
        # Simple regex from stackoverflow
        email_regex = r'[\w\.-]+@[\w\.-]+'
        return {e for e in self._find_pattern(content, email_regex) if e}

    def find_fb_links(self, content):
        return self._find_links(content, "a[href*=facebook.com]")

    def find_twitter_links(self, content):
        return self._find_links(content, "a[href*=twitter.com]")

    # We are logging for emails, facebook and twitter links
    def find_links(self, store_url, pages_to_process=None):
        """Search for required informations
        """

        data = {
            "emails": set(),
            "facebook": set(),
            "twitter": set()
        }

        if pages_to_process is None:
            pages_to_process = (
                "/about-us/",
                "/about/",
                "/contact/",
                "/contact-us/"
            )

        for page in pages_to_process:
            url = "{store_url}{page}".format(
                store_url=store_url,
                page=page
            )
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                # skip all 4XX 5XX pages
                continue

            # emails
            data["emails"].update(self.find_emails(response.content))

            # FB
            data["facebook"].update(self.find_fb_links(response.content))

            # Twitter
            data["twitter"].update(self.find_twitter_links(response.content))

        return data

    def get_store_class(self, store_url):
        """Store class can be dynamically selected
        """
        
        #if "myshopify.com" in store_url:
        #    return ShopifyStore

        #if "mybigecommerce.com" in store_url:
        #    return BigEcommerceStore

        return ShopifyStore

    # export data to csv file
    def export(self, output_file, output_data):
        """Write output data to csv
        """
        with open(output_file, "wb") as f:
            writer = csv.writer(f)
            for store, data in output_data.iteritems():
                row = [store]
                # links
                for link_type, links in data["links"].iteritems():
                    row.append(",".join(links))
                # products data
                for product in data["products"]:
                    for attr in product.values():
                        row.append(attr.encode("UTF-8"))
                writer.writerow(row)

    def process(self, source_file, output_file=None):
        output_data = {}

        stores = self.read_stores(source_file)

        for store in stores:
            data = {}

            store_handler = self.get_store_class(store)(store)

            # 1. Find required information on pages
            # This is not store related method - it just contnet parsing
            try:
                data["links"] = self.find_links(store)
            except requests.exceptions.RequestException:
                # Skip stores which not exits
                # Should export also contains not existing domains ?
                #data[store] = None
                continue

            # 2. Find products
            # Store related method
            data["products"] = store_handler.products()

            output_data[store] = data

        if output_file and output_data:
            self.export(output_file, output_data)

        return output_data
