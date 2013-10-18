from usbcreator.backends.windows import WindowsBackend
import unittest

class TestWindowsBackend(unittest.TestCase):
    def test_backend(self):
        b = WindowsBackend()
        b.detect_devices()

    def test_format(self):
        b = WindowsBackend()
        b._device_added(u'E:\\')
        b.format(u'E:\\')
