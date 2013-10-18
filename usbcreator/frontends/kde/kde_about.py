#############################################################################
##
## Copyright 2009 Roderick B. Greening <roderick.greening@gmail.com>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of
## the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

#############################################################################
# Name: kde_about.py
#
# Description: The class which builds the about information for the app
#############################################################################

from PyQt4 import uic
from usbcreator.frontends.kde.translate import translate
uic.properties.Properties._string = translate
from usbcreator.misc import setup_gettext
setup_gettext()

from PyKDE4.kdecore import KAboutData, KLocalizedString, ki18n

#############################################################################

class AboutData(KAboutData):
    """Add KDE specific data for About"""

    def __init__(self):

        appName     = "usb-creator-kde"
        catalogue   = "usbcreator"
        programName = ki18n("Startup Disk Creator")
        version     = "0.2.23"
        description = ki18n("Create a startup disk using a CD or disc image")
        license     = KAboutData.License_GPL_V3
        copyright   = ki18n("Copyright 2009 Roderick B. Greening")
        text        = KLocalizedString()
        homePage    = "http://launchpad.net/usb-creator"
        bugEmail    = "ubuntu-installer@lists.ubuntu.com"

        KAboutData.__init__(self,
                            appName,
                            catalogue,
                            programName,
                            version,
                            description,
                            license,
                            copyright,
                            text,
                            homePage,
                            bugEmail)

        # Add any authors below
        self.addAuthor(ki18n("Roderick B. Greening"),
                       ki18n("Author/Maintainer"),
                       "roderick.greening@gmail.com")

