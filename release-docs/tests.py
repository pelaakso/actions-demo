import unittest

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_lower(self):
        self.assertEqual('FOO'.lower(), 'foo')

