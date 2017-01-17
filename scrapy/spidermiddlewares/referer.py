"""
RefererMiddleware: populates Request referer field, based on the Response which
originated it.
"""
from scrapy.http import Request, Response
from scrapy.exceptions import NotConfigured
from scrapy import signals
from scrapy.utils.python import to_native_str
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.misc import load_object
from scrapy.utils.url import strip_url


LOCAL_SCHEMES = ('about', 'blob', 'data', 'filesystem',)

POLICY_NO_REFERRER = "no-referrer"
POLICY_NO_REFERRER_WHEN_DOWNGRADE = "no-referrer-when-downgrade"
POLICY_SAME_ORIGIN = "same-origin"
POLICY_ORIGIN = "origin"
POLICY_STRICT_ORIGIN = "strict-origin"
POLICY_ORIGIN_WHEN_CROSS_ORIGIN = "origin-when-cross-origin"
POLICY_STRICT_ORIGIN_WHEN_CROSS_ORIGIN = "strict-origin-when-cross-origin"
POLICY_UNSAFE_URL = "unsafe-url"
POLICY_SCRAPY_DEFAULT = "scrapy-default"


class ReferrerPolicy(object):

    NOREFERRER_SCHEMES = LOCAL_SCHEMES

    def referrer(self, response, request):
        raise NotImplementedError()

    def stripped_referrer(self, r):
        return self.strip_url(r)

    def origin_referrer(self, r):
        return self.strip_url(r, origin_only=True)

    def strip_url(self, r, origin_only=False):
        """
        https://www.w3.org/TR/referrer-policy/#strip-url

        If url is null, return no referrer.
        If url's scheme is a local scheme, then return no referrer.
        Set url's username to the empty string.
        Set url's password to null.
        Set url's fragment to null.
        If the origin-only flag is true, then:
            Set url's path to null.
            Set url's query to null.
        Return url.
        """
        if r is None or not r.url:
            return None
        parsed_url = urlparse_cached(r)
        if parsed_url.scheme not in self.NOREFERRER_SCHEMES:
            return strip_url(parsed_url,
                             strip_credentials=True,
                             strip_fragment=True,
                             strip_default_port=True,
                             origin_only=origin_only)

    def origin(self, r):
        """Return serialized origin (scheme, host, path) for a request or response URL."""
        return self.strip_url(r, origin_only=True)

    def potentially_trustworthy(self, r):
        # Note: this does not follow https://w3c.github.io/webappsec-secure-contexts/#is-url-trustworthy
        parsed_url = urlparse_cached(r)
        if parsed_url.scheme in ('data',):
            return False
        return self.tls_protected(r)

    def tls_protected(self, r):
        return urlparse_cached(r).scheme in ('https', 'ftps')


class NoReferrerPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-no-referrer

    The simplest policy is "no-referrer", which specifies that no referrer information
    is to be sent along with requests made from a particular request client to any origin.
    The header will be omitted entirely.
    """
    name = POLICY_NO_REFERRER

    def referrer(self, response, request):
        return None


class NoReferrerWhenDowngradePolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-no-referrer-when-downgrade

    The "no-referrer-when-downgrade" policy sends a full URL along with requests
    from a TLS-protected environment settings object to a potentially trustworthy URL,
    and requests from clients which are not TLS-protected to any origin.

    Requests from TLS-protected clients to non-potentially trustworthy URLs,
    on the other hand, will contain no referrer information.
    A Referer HTTP header will not be sent.

    This is a user agent's default behavior, if no policy is otherwise specified.
    """
    name = POLICY_NO_REFERRER_WHEN_DOWNGRADE

    def referrer(self, response, request):
        if not self.tls_protected(response) or self.tls_protected(request):
            return self.stripped_referrer(response)


class SameOriginPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-same-origin

    The "same-origin" policy specifies that a full URL, stripped for use as a referrer,
    is sent as referrer information when making same-origin requests from a particular request client.

    Cross-origin requests, on the other hand, will contain no referrer information.
    A Referer HTTP header will not be sent.
    """
    name = POLICY_SAME_ORIGIN

    def referrer(self, response, request):
        if self.origin(response) == self.origin(request):
            return self.stripped_referrer(response)


class OriginPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-origin

    The "origin" policy specifies that only the ASCII serialization
    of the origin of the request client is sent as referrer information
    when making both same-origin requests and cross-origin requests
    from a particular request client.
    """
    name = POLICY_ORIGIN

    def referrer(self, response, request):
        return self.origin_referrer(response)


class StrictOriginPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-strict-origin

    The "strict-origin" policy sends the ASCII serialization
    of the origin of the request client when making requests:
    - from a TLS-protected environment settings object to a potentially trustworthy URL, and
    - from non-TLS-protected environment settings objects to any origin.

    Requests from TLS-protected request clients to non- potentially trustworthy URLs,
    on the other hand, will contain no referrer information.
    A Referer HTTP header will not be sent.
    """
    name = POLICY_STRICT_ORIGIN

    def referrer(self, response, request):
        if ((urlparse_cached(response).scheme == 'https' and
             self.potentially_trustworthy(request))
             or urlparse_cached(response).scheme == 'http'):
            return self.origin_referrer(response)


class OriginWhenCrossOriginPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-origin-when-cross-origin

    The "origin-when-cross-origin" policy specifies that a full URL,
    stripped for use as a referrer, is sent as referrer information
    when making same-origin requests from a particular request client,
    and only the ASCII serialization of the origin of the request client
    is sent as referrer information when making cross-origin requests
    from a particular request client.
    """
    name = POLICY_ORIGIN_WHEN_CROSS_ORIGIN

    def referrer(self, response, request):
        origin = self.origin(response)
        if origin == self.origin(request):
            return self.stripped_referrer(response)
        else:
            return origin


class StrictOriginWhenCrossOriginPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-strict-origin-when-cross-origin

    The "strict-origin-when-cross-origin" policy specifies that a full URL,
    stripped for use as a referrer, is sent as referrer information
    when making same-origin requests from a particular request client,
    and only the ASCII serialization of the origin of the request client
    when making cross-origin requests:

    - from a TLS-protected environment settings object to a potentially trustworthy URL, and
    - from non-TLS-protected environment settings objects to any origin.

    Requests from TLS-protected clients to non- potentially trustworthy URLs,
    on the other hand, will contain no referrer information.
    A Referer HTTP header will not be sent.
    """
    name = POLICY_STRICT_ORIGIN_WHEN_CROSS_ORIGIN

    def referrer(self, response, request):
        origin = self.origin(response)
        if origin == self.origin(request):
            return self.stripped_referrer(response)
        elif ((urlparse_cached(response).scheme in ('https', 'ftps') and
               self.potentially_trustworthy(request))
              or urlparse_cached(response).scheme == 'http'):
            return self.origin_referrer(response)


class UnsafeUrlPolicy(ReferrerPolicy):
    """
    https://www.w3.org/TR/referrer-policy/#referrer-policy-unsafe-url

    The "unsafe-url" policy specifies that a full URL, stripped for use as a referrer,
    is sent along with both cross-origin requests
    and same-origin requests made from a particular request client.

    Note: The policy's name doesn't lie; it is unsafe.
    This policy will leak origins and paths from TLS-protected resources
    to insecure origins.
    Carefully consider the impact of setting such a policy for potentially sensitive documents.
    """
    name = POLICY_UNSAFE_URL

    def referrer(self, response, request):
        return self.stripped_referrer(response)


class LegacyPolicy(ReferrerPolicy):
    def referrer(self, response, request):
        return response.url


class DefaultReferrerPolicy(NoReferrerWhenDowngradePolicy):

    NOREFERRER_SCHEMES = LOCAL_SCHEMES + ('file', 's3')
    name = POLICY_SCRAPY_DEFAULT


_policy_classes = {p.name: p for p in (
    NoReferrerPolicy,
    NoReferrerWhenDowngradePolicy,
    SameOriginPolicy,
    OriginPolicy,
    StrictOriginPolicy,
    OriginWhenCrossOriginPolicy,
    StrictOriginWhenCrossOriginPolicy,
    UnsafeUrlPolicy,
    DefaultReferrerPolicy,
)}

class RefererMiddleware(object):

    def __init__(self, settings=None):
        self.default_policy = DefaultReferrerPolicy
        if settings is not None:
            policy = settings.get('REFERER_POLICY')
            if policy is not None:
                # expect a string for the path to the policy class
                try:
                    self.default_policy = load_object(policy)
                except ValueError:
                    # otherwise try to interpret the string as standard
                    # https://www.w3.org/TR/referrer-policy/#referrer-policies
                    try:
                        self.default_policy = _policy_classes[policy.lower()]
                    except:
                        raise NotConfigured("Unknown referrer policy name %r" % policy)

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('REFERER_ENABLED'):
            raise NotConfigured
        mw = cls(crawler.settings)
        crawler.signals.connect(mw.request_scheduled, signal=signals.request_scheduled)
        return mw

    def policy(self, response, request):
        # policy set in request's meta dict takes precedence over default policy
        policy_name = request.meta.get('referrer_policy')
        if policy_name is None:
            policy_name = to_native_str(
                response.headers.get('Referrer-Policy', '').decode('latin1'))

        cls = _policy_classes.get(policy_name.lower(), self.default_policy)
        return cls()

    def process_spider_output(self, response, result, spider):
        def _set_referer(r):
            if isinstance(r, Request):
                referrer = self.policy(response, r).referrer(response, r)
                if referrer is not None:
                    r.headers.setdefault('Referer', referrer)
            return r
        return (_set_referer(r) for r in result or ())

    def request_scheduled(self, request, spider):
        # check redirected request to patch "Referer" header if necessary
        redirected_urls = request.meta.get('redirect_urls', [])
        if redirected_urls:
            request_referrer = request.headers.get('Referer')
            # we don't patch the referrer value if there is none
            if request_referrer is not None:
                faked_response = Response(redirected_urls[0])
                policy_referrer = self.policy(faked_response,
                    request).referrer(faked_response, request)
                if policy_referrer != request_referrer:
                    if policy_referrer is None:
                        request.headers.pop('Referer')
                    else:
                        request.headers['Referer'] = policy_referrer
