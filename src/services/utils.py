from collections import namedtuple
from urllib.parse import urlencode, urlunparse

Components = namedtuple(
    typename="Components",
    field_names=["scheme", "netloc", "url", "path", "query", "fragment"],
)


def build_url(query_params: dict, url: str):
    return urlunparse(
        Components(
            scheme="http",
            netloc="localhost:8000",
            query=urlencode(query_params),
            url=url,
            path=None,
            fragment=None,
        )
    )
