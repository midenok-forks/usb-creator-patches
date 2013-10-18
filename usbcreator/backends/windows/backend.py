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

from usbcreator.backends.base import Backend
from usbcreator import misc
import os
import ctypes
import ctypes.wintypes
import logging

DRIVE_TYPES = ['unknown',
               'no_root_dir',
               'removeable',
               'localdisk',
               'remotedisk',
               'cdrom',
               'ramdisk']

def get_device_num_for_letter(source):
    class STORAGE_DEVICE_NUMBER(ctypes.Structure):
        _fields_ = [("DeviceType", ctypes.wintypes.DWORD),
                    ("DeviceNumber", ctypes.wintypes.ULONG),
                    ("PartitionNumber", ctypes.wintypes.ULONG)]

    GENERIC_READ = (-2147483648)
    FILE_SHARE_READ = 1
    OPEN_EXISTING = 3
    INVALID_HANDLE_VALUE = 4294967295L
    NULL = 0
    IOCTL_STORAGE_GET_DEVICE_NUMBER = 0x2D1080

    CreateFileW = ctypes.windll.kernel32.CreateFileW
    DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
    if not os.path.isfile(source):
        # Strip the last character from the source (\).
        source = os.path.join('\\\\.\\', source[:2])
    source_h = CreateFileW(misc.text_type(source), GENERIC_READ, FILE_SHARE_READ,
                           NULL, OPEN_EXISTING, 0, NULL)
    if source_h == INVALID_HANDLE_VALUE:
        logging.error('Invalid handle.')
        return -1
    num = STORAGE_DEVICE_NUMBER()
    c = ctypes.wintypes.DWORD()
    if not DeviceIoControl(source_h, IOCTL_STORAGE_GET_DEVICE_NUMBER, NULL, 0,
                           ctypes.byref(num), ctypes.sizeof(num),
                           ctypes.byref(c), NULL):
        logging.error('IOCTL_STORAGE_GET_DEVICE_NUMBER failed.')
        return -1
    logging.debug('Device properties for %s: type %d, device %d, partition %d'
                  % (source, num.DeviceType, num.DeviceNumber,
                     num.PartitionNumber))
    ctypes.windll.kernel32.CloseHandle(source_h)
    assert num.DeviceNumber != 0, 'Was going to return the first disk.'
    return num.DeviceNumber

class WindowsBackend(Backend):
    def __init__(self):
        Backend.__init__(self)

    # Device processing.

    def detect_devices(self):
        logical_drives = ctypes.windll.kernel32.GetLogicalDrives()

        for i in range(26):
            if (logical_drives >> i) & 0x01:
                drive = u'%s:\\' % chr(i + 65)
                self._device_added(drive)

    def _device_added(self, drive):
        drive_buf = ctypes.create_unicode_buffer(512)
        fs_buf = ctypes.create_unicode_buffer(512)
        vol_i = ctypes.windll.kernel32.GetVolumeInformationW
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
        if vol_i(drive, drive_buf, 512, None, None, None, fs_buf, 512):
            volume = drive_buf.value
            fs = fs_buf.value
        else:
            logging.error('Could not get volume information for %s' % drive)
            return

        if drive_type > len(DRIVE_TYPES):
               drive_type = 0
        drive_type = DRIVE_TYPES[drive_type]

        if drive_type == 'cdrom':
            if os.path.exists(os.path.join(drive, '.disk/info')):
                self.sources[drive] = {
                    'device' : drive,
                    'size' : misc.fs_size(drive)[0],
                    'label' : volume,
                    'type' : misc.SOURCE_CD,
                }
                if misc.callable(self.source_added_cb):
                    self.source_added_cb(drive)
        elif drive_type == 'removeable': # and fs == u'fat32':
            tot, free = misc.fs_size(drive)
            self.targets[drive] = {
                'capacity' : tot,
                'free' : free,
                'device' : drive,
                # FIXME evand 2009-07-16: How does Windows get the volume name?
                # GetVolumeInformation returns NULL here.
                'label' : '',
                'mountpoint' : drive,
                'status' : misc.CAN_USE,
            }
            if misc.callable(self.target_added_cb):
                self.target_added_cb(drive)
        else:
            tot, free = misc.fs_size(drive)
            logging.debug('Not adding %s (%s %s %s volume, %d total bytes, '
                          '%d bytes free)' %
                          (drive, volume, drive_type, fs, tot, free))

    def format(self, drive):
        assert drive == 'E:\\'
        assert drive in self.targets
        # TODO evand 2009-07-16: Windows does not provide an API for
        # formatting.  It offers a method to bring up the format dialog, but
        # that will not work as there is no way to force it to the FAT32
        # filesystem.
        # One can format a volume using WMI, but that would pull in a
        # dependency on Mark Hammond's pywin32.

    def _is_casper_cd(self, filename):
        '''If this is a casper-based CD, return the CD label.'''
        # XXX evand 2009-07-25: Using 7zip until cdkit gets mingw support.
        cmd = ['7z', 'x', filename, '.disk/info', '-so']
        try:
            output = misc.popen(cmd, stderr=None)
            if output:
                return output
        except misc.USBCreatorProcessException:
            # TODO evand 2009-07-26: Error dialog.
            logging.error('Could not extract .disk/info.')
        return None

    def install(self, source, target, persist):
        target_dev = None
        source_type = self.sources[source]['type']
        if source_type == misc.SOURCE_IMG:
            target_dev = get_device_num_for_letter(target)
            if target_dev < 1:
                logging.error('Could not determine the disk number.  Got %d.' %
                              target_dev)
                # TODO evand 2009-08-28: Fail.
                return
            target_dev = '\\\\?\\Device\\Hardisk%d\\Partition0' % target_dev
        Backend.install(self, source, target, persist, device=target_dev)

#def dd(source, target):
#    import ctypes
#    import ctypes.wintypes
#    GENERIC_READ = (-2147483648)
#    GENERIC_WRITE = (1073741824)
#    FILE_SHARE_READ = 1
#    CREATE_ALWAYS = 2
#    OPEN_EXISTING = 3
#    FILE_ATTRIBUTE_NORMAL = 128
#    INVALID_HANDLE_VALUE = 4294967295L
#    FSCTL_LOCK_VOLUME = 589848
#    NULL = 0
#
#    CreateFileW = ctypes.windll.kernel32.CreateFileW
#    DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
#    if not os.path.isfile(source):
#        source = os.path.join('\\\\.', source)
#    source_h = CreateFileW(misc.text_type(source), GENERIC_READ, FILE_SHARE_READ,
#                           NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL)
#    target = os.path.join('\\\\.', target)
#    target_h = CreateFileW(misc.text_type(source), GENERIC_WRITE, 0,
#                           NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL)
#    if source_h == INVALID_HANDLE_VALUE or target_h == INVALID_HANDLE_VALUE:
#        print('Invalid handle.')
#        return
#    # Lock.
#    bytes_returned = ctypes.wintypes.DWORD()
#    res = DeviceIoControl(target_h, FSCTL_LOCK_VOLUME, NULL, 0, NULL, 0,
#                          byref(bytes_returned), NULL)
#    # Unmount.
#    # ...
#    # Unlock.
