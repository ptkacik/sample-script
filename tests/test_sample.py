import os
import sample
import requests.exceptions

import pytest

downloader = sample.StoreDownloader()


class TestDownloaderClass(object):

    @pytest.fixture()
    def csv_fixture(self):
        return os.path.join(os.path.dirname(__file__), 'sample.csv')

    @pytest.fixture(params=[
        ("This content contais email@emails.com and also tralala@tralala.sk",
        set({"email@emails.com", "tralala@tralala.sk"})),
        ("No emails found", set())])
    def emails_fixture(self, request):
        return request.param

    @pytest.fixture(params=[
        ("HMTL with facebook <a href='http://www.facebook.com/tralala'>link</a>",
        set({"http://www.facebook.com/tralala"})
        ),("No FB link <a href='http://www.twitter.com/a'", set())])
    def facebook_fixture(self, request):
        return request.param

    def test_read_stores(self, csv_fixture):
        stores = downloader.read_stores(csv_fixture) 
        assert len(stores) == 3

    def test_emails(self, emails_fixture):
        content, result = emails_fixture
        assert downloader.find_emails(content) == result

    def test_facebook_link(self, facebook_fixture):
        content, result = facebook_fixture
        assert downloader.find_fb_links(content) == result

    def test_url_error(self):
        not_exists_url = "http://storie1.sk"
        with pytest.raises(requests.exceptions.RequestException):
            downloader.find_links(not_exists_url)




