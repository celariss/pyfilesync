from helpers import *

class TestHelpers:
    def test_value_with_unit_to_int(self):
        test_cases = [
            ('zzz', -1),
            ('100 bb', -1),
            (100, 100),
            ('100', 100),
            ('100B', 100),
            ('100 B', 100),
            ('\t 100 \t b ', 100),
            ('100 bytes', 100),
            ('100 byte', 100),
            ('100k', 100*1024),
            ('1 k', 1024),
            ('1 K', 1024),
            ('1 kb', 1024),
            ('1KB', 1024),
            ('1 m', 1024*1024),
            ('1 M', 1024*1024),
            ('1mb', 1024*1024),
            ('1 MB', 1024*1024),
            ('1 g', 1024*1024*1024),
            ('1G', 1024*1024*1024),
            ('1 gb', 1024*1024*1024),
            ('1 GB', 1024*1024*1024),
        ]

        for test_case in test_cases:
            value, expected = test_case
            assert value_with_unit_to_int(value, -1) == expected