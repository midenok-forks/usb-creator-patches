from distutils.core import setup
from DistUtilsExtra.command import *
import os

class usb_creator_build_i18n(build_i18n.build_i18n):
    def run(self):
         build_i18n.build_i18n.run(self)
         print("extracting strings for KDE frontend")
         os.system("./Messages.sh")

setup(name='usb-creator',
    version='0.2.23',
    description='Ubuntu startup disk creator',
    author='Evan Dandrea',
    author_email='evand@ubuntu.com',
    packages=['usbcreator',
              'usbcreator.frontends',
              'usbcreator.frontends.gtk',
              'usbcreator.frontends.kde',
              'usbcreator.frontends.base',
              'usbcreator.backends',
              'usbcreator.backends.base',
              'usbcreator.backends.fastboot',
              'usbcreator.backends.udisks',
             ],
    scripts=['bin/usb-creator-gtk','bin/usb-creator-kde'],
    data_files=[('share/usb-creator', ['gui/usbcreator-gtk.ui']),
                ('share/usb-creator', ['bin/usb-creator-helper']),
                ('share/usb-creator', ['gui/ubuntu-nexus7-USAGE-NOTICE-en.txt']),
                ('share/icons/hicolor/scalable/apps', ['desktop/usb-creator-gtk.svg', 'desktop/usb-creator-kde.svg']),
                ('share/kde4/apps/usb-creator-kde', ['gui/usbcreator-kde.ui']),
                ('/etc/dbus-1/system.d', ['dbus/com.ubuntu.USBCreator.conf']),
                ('share/dbus-1/system-services', ['dbus/com.ubuntu.USBCreator.service']),
                ('share/apport/package-hooks', ['debian/source_usb-creator.py'])],
    cmdclass = { "build" : build_extra.build_extra,
        "build_i18n" :  usb_creator_build_i18n,
        "build_help" :  build_help.build_help,
        "build_icons" :  build_icons.build_icons,
        "clean": clean_i18n.clean_i18n,
        }
    )

