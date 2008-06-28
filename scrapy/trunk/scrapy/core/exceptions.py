"""
Scrapy core exceptions
"""

# Internal

class UsageError(Exception):
    """Incorrect usage of the core API"""
    pass

class NotConfigured(Exception):
    """Indicates a missing configuration situation"""
    pass

# HTTP and crawling

class IgnoreRequest(Exception):
    """Indicates a decision was made not to process a request"""
    pass

class DontCloseDomain(Exception):
    """Request the domain not to be closed yet"""
    pass
    
class HttpException(Exception):
    def __init__(self, status, message, response):
        if not message:
            from twisted.web import http
            message = http.responses.get(int(status))

        self.status = status
        self.message = message
        self.response = response
        Exception.__init__(self, status, message, response)

    def __str__(self):
        return '%s %s' % (self.status, self.message)

# Items

class DropItem(Exception):
    """Drop item from the item pipeline"""
    pass

