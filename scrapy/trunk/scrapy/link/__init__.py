"""
LinkExtractor provides en efficient way to extract links from pages
"""

from scrapy.utils.python import FixedSGMLParser
from scrapy.utils.url import urljoin_rfc as urljoin

class LinkExtractor(FixedSGMLParser):
    """LinkExtractor are used to extract links from web pages. They are
    instantiated and later "applied" to a Response using the extract_urls
    method which must receive a Response object and return a dict whoose keys
    are the (absolute) urls to follow, and its values any arbitrary data. In
    this case the values are the text of the hyperlink.

    This is the base LinkExtractor class that provides enough basic
    functionality for extracting links to follow, but you could override this
    class or create a new one if you need some additional functionality. The
    only requisite is that the new (or overrided) class must provide a
    extract_urls method that receives a Response and returns a dict with the
    links to follow as its keys.

    The constructor arguments are:

    * tag (string or function)
      * a tag name which is used to search for links (defaults to "a")
      * a function which receives a tag name and returns whether to scan it
    * attr (string or function)
      * an attribute name which is used to search for links (defaults to "href")
      * a function which receives an attribute name and returns whether to scan it
    """

    def __init__(self, tag="a", attr="href"):
        FixedSGMLParser.__init__(self)
        self.scan_tag = tag if callable(tag) else lambda t: t == tag
        self.scan_attr = attr if callable(attr) else lambda a: a == attr
        self.current_link = None

    def extract_urls(self, response, unique=False):
        self.reset()
        self.unique = unique
        self.feed(response.body.to_string())
        self.close()
        
        base_url = self.base_url if self.base_url else response.url
        ret = []
        for link in self.links:
            link.url = urljoin(base_url, link.url).strip()
            ret.append(link)
        return ret

    def reset(self):
        FixedSGMLParser.reset(self)
        self.links = []
        self.base_url = None

    def unknown_starttag(self, tag, attrs):
        if tag == 'base':
            self.base_url = dict(attrs).get('href')
        if self.scan_tag(tag):
            for attr, value in attrs:
                if self.scan_attr(attr):
                    if not self.unique or not value in [link.url for link in self.links]:
                        link = Link(url=value)
                        self.links.append(link)
                        self.current_link = link

    def unknown_endtag(self, tag):
        self.current_link = None

    def handle_data(self, data):
        if self.current_link and not self.current_link.text:
            self.current_link.text = data

    def matches(self, url):
        """This extractor matches with any url, since
        it doesn't contain any patterns"""
        return True


class Link(object):
    """
    Link objects represent an extracted link by the LinkExtractor.
    At the moment, it contains just the url and link text.
    """

    __slots__ = 'url', 'text'

    def __init__(self, url, text=''):
        self.url = url
        self.text = text

    def __eq__(self, other):
        return self.url == other.url and self.text == other.text
