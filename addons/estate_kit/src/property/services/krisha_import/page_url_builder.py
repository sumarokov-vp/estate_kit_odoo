from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class PageUrlBuilder:
    def build(self, base_url: str, page: int) -> str:
        parsed = urlparse(base_url)
        query_pairs = [(key, value) for key, value in parse_qsl(parsed.query) if key != "page"]
        query_pairs.append(("page", str(page)))
        new_query = urlencode(query_pairs)
        return urlunparse(parsed._replace(query=new_query))
