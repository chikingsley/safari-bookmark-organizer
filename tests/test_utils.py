from safari_bookmark_organizer.utils import extract_domain


class TestExtractDomain:
    def test_https(self) -> None:
        assert extract_domain("https://example.com/path") == "example.com"

    def test_http(self) -> None:
        assert extract_domain("http://example.com") == "example.com"

    def test_strips_www(self) -> None:
        assert extract_domain("https://www.example.com/page") == "example.com"

    def test_empty_string(self) -> None:
        assert extract_domain("") == ""

    def test_subdomain(self) -> None:
        assert extract_domain("https://docs.python.org/3/") == "docs.python.org"

    def test_no_protocol(self) -> None:
        assert extract_domain("example.com/path") == "example.com"
