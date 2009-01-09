from unittest import TestCase, main
from scrapy.http import Response, ResponseBody

class ResponseTest(TestCase):
    def test_init(self):
        # Response requires domain and url
        self.assertRaises(Exception, Response)
        self.assertRaises(Exception, Response, 'example.com')
        self.assertTrue(isinstance(Response('example.com', 'http://example.com/'), Response))
        # body can be str or None but not ResponseBody
        self.assertTrue(isinstance(Response('example.com', 'http://example.com/', body=None), Response))
        self.assertTrue(isinstance(Response('example.com', 'http://example.com/', body='body'), Response))
        self.assertRaises(AssertionError, Response, 'example.com', 'http://example.com/', body=ResponseBody('body', 'utf-8'))

class ResponseBodyTest(TestCase):
    unicode_string = u'\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442'

    def test_encoding(self):
        original_string = self.unicode_string.encode('cp1251')
        cp1251_body     = ResponseBody(original_string, 'cp1251')

        # check to_unicode
        self.assertTrue(isinstance(cp1251_body.to_unicode(), unicode))
        self.assertEqual(cp1251_body.to_unicode(), self.unicode_string)

        # check to_string using default encoding (declared when created)
        self.assertTrue(isinstance(cp1251_body.to_string(), str))
        self.assertEqual(cp1251_body.to_string(), original_string)

        # check to_string using arbitrary encoding
        self.assertTrue(isinstance(cp1251_body.to_string('utf-8'), str))
        self.assertEqual(cp1251_body.to_string('utf-8'), self.unicode_string.encode('utf-8'))

if __name__ == "__main__":
    main()
