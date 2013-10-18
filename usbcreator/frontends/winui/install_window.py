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

from usbcreator.frontends.winui.winui import ui

# FIXME evand 2009-07-24: Need to handle the user hitting the close button and
# making the window visible in the pager.
class InstallWindow(ui.MainWindow):
    def __init__(self, main_window):
        self.width = 450
        ui.MainWindow.__init__(self, main_window, 0, 0, self.width, 115,
                               _('Installing'))

    def on_init(self):
        right_edge = self.width - 30
        self.progress_title = ui.Label(self, 10, 5, right_edge, 20,
                                       _('Starting up...'))
        self.progress_bar = ui.ProgressBar(self, 10, 25, right_edge, 25)
        self.progress_subtitle = ui.Label(self, 10, 60, 350, 20, '')
        self.cancel_button = ui.Button(self, right_edge - 50, 60, 60, 20,
                                       _('&Cancel'))
