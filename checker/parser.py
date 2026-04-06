from bs4 import BeautifulSoup


def build_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")