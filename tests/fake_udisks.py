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
from twisted.internet.defer import Deferred

# TODO evand 2009-06-02: Move the common bits into a unittest.TestCase
# subclass like the Ubuntu One client does?
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

DISKS_IFACE = 'org.freedesktop.UDisks'
DEVICE_IFACE = 'org.freedesktop.UDisks.Device'
PROPS_IFACE = 'org.freedesktop.DBus.Properties'

class TestDbus(unittest.TestCase):
    def setUp(self):
        # TODO evand 2009-07-01: Move to a private bus.  See the notes in
        # test_udisks_backend.py
        self.bus = dbus.SessionBus()
        self.d = FakeUDisks(self.bus, '/org/freedesktop/UDisks')
        self.udisks = self.bus.get_object(DISKS_IFACE,
                                          '/org/freedesktop/UDisks')

    def tearDown(self):
        # FIXME evand 2009-07-06: There must be a better way...
        for dev in self.d.device_objects:
            dev.bus_name.get_bus().release_name(dev.bus_name.get_name())
            dev.remove_from_connection()
            del dev.bus_name
        self.d.bus_name.get_bus().release_name(self.d.bus_name.get_name())
        self.d.remove_from_connection()
        del self.d.bus_name

    def test_enumerate(self):
        d = Deferred()
        def handle_reply(result):
            d.callback(result)
        def handle_error(err):
            d.errback(err)
        self.udisks.EnumerateDevices(dbus_interface=DISKS_IFACE,
                            reply_handler=handle_reply,
                            error_handler=handle_error)
        return d

    def test_props(self):
        d = Deferred()
        def handle_reply(result):
            d.callback(result)
        def handle_error(err):
            d.errback(err)
        path = '/org/freedesktop/UDisks/devices/sdb'
        device = self.bus.get_object(DISKS_IFACE, path)
        device.Get(path,
                   'device-is-system-internal',
                   dbus_interface=PROPS_IFACE,
                   reply_handler=handle_reply,
                   error_handler=handle_error)
        return d

    def test_added(self):
        '''Fires the DeviceAdded signal.'''
        d = Deferred()
        def handle_reply(result):
            d.callback(result)
        def handle_error(err):
            d.errback(err)
        self.bus.add_signal_receiver(handle_reply,
                             signal_name='DeviceAdded',
                             dbus_interface=DISKS_IFACE,
                             path='/org/freedesktop/UDisks')

        self.udisks.emitDeviceAdded(reply_handler=lambda : None,
                                    error_handler=handle_error)
        return d

    def test_removed(self):
        '''Fires the DeviceRemoved signal.'''
        d = Deferred()
        def handle_reply(result):
            d.callback(result)
        def handle_error(err):
            d.errback(err)
        self.bus.add_signal_receiver(handle_reply,
                             signal_name='DeviceRemoved',
                             dbus_interface=DISKS_IFACE,
                             path='/org/freedesktop/UDisks')

        self.udisks.emitDeviceRemoved(reply_handler=lambda : None,
                                      error_handler=handle_error)
        return d

# XXX evand 2009-07-07: Built according to the udisks specification:
# http://hal.freedesktop.org/docs/udisks/

class FakeUDisks(dbus.service.Object):
    def __init__(self, bus, path):
        self.bus_name = dbus.service.BusName(DISKS_IFACE,
                                             bus)
        self.devices = {'/org/freedesktop/UDisks/devices/sdb' :
                            { 'device-is-system-internal' : False,
                              'device-is-drive' : True,
                              'device-is-optical-disc' : False,
                            },
                        '/org/freedesktop/UDisks/devices/sdb1' :
                            { 'device-is-system-internal' : False,
                              'device-is-drive' : False,
                              'device-is-partition' : True,
                              'partition-label' : 'test-label',
                              'device-is-optical-disc' : False,
                            },
                        '/org/freedesktop/UDisks/devices/scd0' :
                            { 'device-is-optical-disc' : True,
                            },
                       }
        dbus.service.Object.__init__(self, bus, path)

        self.device_objects = []
        for d in self.devices:
            self.device_objects.append(FakeUDisksDevice(bus, d,
                                       self.devices[d]))

    @dbus.service.method(DISKS_IFACE, out_signature='ao')
    def EnumerateDevices(self):
        return list(self.devices.keys())

    @dbus.service.signal(DISKS_IFACE, signature='o')
    def DeviceAdded(self, path):
        pass

    @dbus.service.method(DISKS_IFACE)
    def emitDeviceAdded(self):
        self.DeviceAdded('/org/freedesktop/UDisks/devices/sdc')
    
    @dbus.service.signal(DISKS_IFACE, signature='o')
    def DeviceRemoved(self, path):
        pass

    @dbus.service.method(DISKS_IFACE)
    def emitDeviceRemoved(self):
        self.DeviceRemoved('/org/freedesktop/UDisks/devices/sdc')
    
class FakeUDisksDevice(dbus.service.Object):
    def __init__(self, bus, path, props):
        self.props = props
        self.bus_name = dbus.service.BusName(DISKS_IFACE,
                                             bus)
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method(PROPS_IFACE, in_signature='ss', out_signature='v')
    def Get(self, iface, prop):
        return self.props[prop]

    @dbus.service.method(DEVICE_IFACE, in_signature='sas', out_signature='s')
    def FilesystemMount(self, filesystem_type, options):
        return '/tmp'
        
if __name__ == '__main__':
    import gobject
    f = FakeUDisks(dbus.SessionBus(), '/org/freedesktop/UDisks')
    gobject.MainLoop().run()
