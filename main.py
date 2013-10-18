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

# USB Creator for Windows.
import sys
import os

import locale
import logging

root_dir = os.path.abspath(os.path.dirname(__file__))
lib_dir = os.path.join(root_dir, 'lib')
sys.path.insert(0, lib_dir)

from usbcreator.frontends.winui import WinuiFrontend
from usbcreator.backends.windows import WindowsBackend
from usbcreator.misc import setup_gettext, setup_logging, text_type

setup_logging()

import ctypes
MB_ICONSTOP = 16
try:
    if not ctypes.windll.advpack.IsNTAdmin(0, 0):
        ctypes.windll.user32.MessageBoxW(0,
            _(u'Please run this program as an administrator to continue.'),
            _(u'Administrator privileges required'), MB_ICONSTOP)
        logging.error('Please run this program as an administrator.')
        sys.exit(1)
except Exception:
    pass

# TODO evand 2009-07-27: Options!

translations_dir = os.path.join(root_dir, 'translations')
setup_gettext(localedir=translations_dir)

try:
    b = WindowsBackend()
    WinuiFrontend(b)
except Exception as e:
    # TODO evand 2009-07-28: Thread cleanup?
    ctypes.windll.user32.MessageBoxW(0,
        _(u'An unhandled exception occurred:\n%s' % text_type(e)),
        _(u'Error'), MB_ICONSTOP)
    logging.exception('Unhandled exception:')
    sys.exit(1)
