import os
from unittest import TestCase, main
from scrapy.http import Response, ResponseBody
from scrapy.utils.decompressor import Decompressor

class ScrapyDecompressTest(TestCase):
    uncompressed_body = ''
    test_responses = {}
    decompressor = Decompressor()
    
    def setUp(self):
        self.datadir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sample_data', 'compressed')
        formats = ['tar', 'xml.bz2', 'xml.gz', 'zip']
        uncompressed_fd = open(os.path.join(self.datadir, 'feed-sample1.xml'), 'r')
        self.uncompressed_body = uncompressed_fd.read()
        uncompressed_fd.close()
        
        for format in formats:
            fd = open(os.path.join(self.datadir, 'feed-sample1.' + format), 'r')
            body = ResponseBody(fd.read())
            fd.close()
            self.test_responses[format] = Response('foo.com', 'http://foo.com/bar', body=body)
    
    def test_tar(self):
        ret = self.decompressor.extract(self.test_responses['tar'])
        if ret:
            self.assertEqual(ret.body.to_string(), self.uncompressed_body)
        
    def test_zip(self):
        ret = self.decompressor.extract(self.test_responses['zip'])
        if ret:
            self.assertEqual(ret.body.to_string(), self.uncompressed_body)
    
    def test_gz(self):
        ret = self.decompressor.extract(self.test_responses['xml.gz'])
        if ret:
            self.assertEqual(ret.body.to_string(), self.uncompressed_body)

    def test_bz2(self):
        ret = self.decompressor.extract(self.test_responses['xml.bz2'])
        if ret:
            self.assertEqual(ret.body.to_string(), self.uncompressed_body)
        
if __name__ == '__main__':
    main()
