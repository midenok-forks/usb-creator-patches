#!/usr/bin/python

# Copyright (C) 2009 Canonical Ltd.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from twisted.trial import unittest
#from twisted.internet.defer import Deferred
import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

from usbcreator.backends.udisks import UDisksBackend

import subprocess, os

class TestUDisksBackend(unittest.TestCase):
    def setUp(self):
        fake_udisks = os.path.join(os.path.dirname(__file__),
                                      'fake_udisks.py')
        self.proc = subprocess.Popen(['python', fake_udisks])
        import time
        time.sleep(1)
        #self._startDBus()
        self.bus = dbus.SessionBus()
        self.backend = UDisksBackend(bus=self.bus)
    def tearDown(self):
        self.proc.terminate()
        self.proc.wait()
        #self._stopDBus()

    # XXX evand 2009-06-03: Uninteresting bit of code to test, as we test our
    # fake EnumerateDevices and signal handling elsewhere.

    #def test_detect_devices(self):
    #    d = Deferred()
    #    def handle_reply(res):
    #        print(res)
    #        d.callback(res)
    #    self.backend.detect_devices(cb=handle_reply)
    #    return d

    def test_disk_added(self):
        d = '/org/freedesktop/UDisks/devices/sdb'
        self.backend._device_added(d)

    def test_partition_added(self):
        d = '/org/freedesktop/UDisks/devices/sdb1'
        self.backend._device_added(d)

    def test_cd_added(self):
        d = '/org/freedesktop/UDisks/devices/scd0'
        self.backend._device_added(d)

    # XXX evand 2009-06-03: Just use the 3 second delay for now, then come back
    # to this.  Getting the tests done and the core code written is more
    # important.
    #def _startDBus(self):
    #    """Start our own session bus daemon for testing."""
    #    config_file = os.path.join(os.path.dirname(os.getcwd()), "tests",
    #                               "dbus-session.conf")
    #    dbus_args = ["--fork",
    #                 "--config-file=" + config_file,
    #                 "--print-address"]
    #    p = subprocess.Popen(['/bin/dbus-daemon'] + dbus_args,
    #                         bufsize=4096, stdout=subprocess.PIPE,
    #                         universal_newlines=True)
    #    data = p.stdout

    #    self.dbus_address = "".join(data.readlines()).strip()
    #    self.dbus_pid = p.pid + 1

    #    if self.dbus_address != "":
    #        os.environ["DBUS_SESSION_BUS_ADDRESS"] = self.dbus_address
    #    else:
    #        os.kill(self.dbus_pid, signal.SIGKILL)
    #        raise DBusLaunchError("There was a problem launching dbus-daemon.")

    #def _stopDBus(self):
    #    """Stop our DBus session bus daemon."""
    #    del os.environ["DBUS_SESSION_BUS_ADDRESS"]
    #    os.kill(self.dbus_pid, signal.SIGKILL)

