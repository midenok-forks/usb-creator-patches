from usbcreator.frontends.winui import WinuiFrontend
from usbcreator.backends.windows import WindowsBackend
import unittest

class TestWindowsFrontend(unittest.TestCase):
    def test_frontend(self):
        backend = WindowsBackend()
        WinuiFrontend(backend)
