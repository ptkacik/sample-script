import sample

import pytest


class TestShopifyClass(object):

    @pytest.fixture()
    def store_fixture(self):
        return sample.ShopifyStore("http://shop.fnatic.com/")

    @pytest.fixture()
    def products_url_fixture(self):
        return """
        Html content with shopify products
        <div class="products">
            <figure>
                <a href="/products/benq-rl2755hm-27-inch-gaming-monitor"></a>
            </figure>
            <figure>
                <a href="/collections/all/products/benq-rl2755hm-27-inch-gaming-monitor"></a>
            </figure>
            <figure>
                <a href="/aa-products/benq-rl2755hm-27-inch-gaming-monitor?GET=paramter"></a>
            </figure>
        </div>
        """

    @pytest.fixture()
    def product_fixture(self):
        products = [
            {
                "title": "Boost Control Mousepad",
                "image": {
                    "src": "image.png",
                }
            },
            {
                "title": "Boost Control Mousepad",
            }
        ]
        return products

    def test_products_urls(self, store_fixture, products_url_fixture):
        assert len(store_fixture.products_links(products_url_fixture)) == 2

    def test_product_title(self, store_fixture, product_fixture):
        for p in product_fixture:
            product = store_fixture.get_product_data(p)
            assert product["title"] == "Boost Control Mousepad"

    def test_product_image(self, store_fixture, product_fixture):
        for p in product_fixture:
            product = store_fixture.get_product_data(p)
            if "image" in p:
                assert product["image"] == "image.png"
            else:
                assert product["image"] == "-"


