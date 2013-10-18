import logging

from gi.repository import GUdev
from gi.repository import GLib

from usbcreator.backends.base import Backend
from usbcreator import misc

KNOWN_IDS = {
    'ID_VENDOR_ID': ('18d1',),
    'ID_MODEL_ID': ('4e40', 'd001',),
}

class FastbootBackend(Backend):
    def __init__(self):
        Backend.__init__(self)
        logging.debug('FastbootBackend')
        self.client = GUdev.Client(subsystems=['usb'])
        
    def on_uevent(self, action, device):
        logging.debug('action: %s' % action)
        logging.debug('device: %s' % device.get_sysfs_path())

        for key,ids in KNOWN_IDS.items():
            result = device.get_property(key)
            if result not in ids:
                logging.debug('Unknown %s: %s' % (key, result))
                return
            
        [logging.debug('%s=%s' % (k, device.get_property(k))) for k in device.get_property_keys()]
        
        key = device.get_property('ID_SERIAL_SHORT')
        
        if action == 'add':
            self.targets[key] = {
                'vendor'     : device.get_property('ID_VENDOR_FROM_DATABASE'),
                'model'      : device.get_property('ID_MODEL'),
                'label'      : '',
                'device'     : device.get_property('ID_SERIAL_SHORT'),
                'status'     : misc.CAN_USE,
                }
            if misc.callable(self.target_added_cb):
                self.target_added_cb(key)
        elif action == 'remove':
            self._device_removed(key)
            
    def detect_devices(self):
        def _on_uevent(client, action, device):
            self.on_uevent(action, device)
            
        self.client.connect('uevent', _on_uevent)
        # Just in case, go over already attached devices
        for device in self.client.query_by_subsystem('usb'):
            self.on_uevent('add', device)

    def update_free(self):
        # No progress yet.
        return True

    def _is_casper_cd(self, filename):
        # no cds for us
        return None    

    def unmount(self):
        return

    def shutdown(self):
        return
