"""
This module provides some useful functions for working with
scrapy.http.Request objects
"""

import hashlib

from scrapy.utils.url import canonicalize_url

def request_fingerprint(request, include_headers=()):
    """
    Return the request fingerprint.
    
    The request fingerprint is a hash that uniquely identifies the resource the
    request points to. For example, take the following two urls:
    
    http://www.example.com/query?id=111&cat=222
    http://www.example.com/query?cat=222&id=111

    Even though those are two different URLs both point to the same resource
    and are equivalent (ie. they should return the same response).

    Another example are cookies used to store session ids. Suppose the
    following page is only accesible to authenticated users:
    
    http://www.example.com/members/offers.html

    Lot of sites use a cookie to store the session id, which adds a random
    component to the HTTP Request and thus should be ignored when calculating
    the fingerprint. 
    
    For this reason, request headers are ignored by default when calculating
    the fingeprint. If you want to include specific headers use the
    include_headers argument, which is a list of Request headers to include.

    """

    if include_headers:
        include_headers = [h.lower() for h in sorted(include_headers)]
        cachekey = 'fingerprint' + '_'.join(include_headers)
    else:
        cachekey = 'fingerprint'

    try:
        return request._cache[cachekey]
    except KeyError:
        fp = hashlib.sha1()
        fp.update(request.method)
        fp.update(canonicalize_url(request.url))
        fp.update(request.body or '')
        for hdr in include_headers:
            if hdr in request.headers:
                fp.update(hdr)
                fp.update(request.headers.get(hdr, ''))
        fphash = fp.hexdigest()
        request._cache[cachekey] = fphash
        return fphash

def request_info(request):
    """Return a short string with request info including method, url and
    fingeprint. Mainly used for debugging
    """
    fp = request_fingerprint(request)
    return "<Request: %s %s (%s..)>" % (request.method, request.url, fp[:8])

