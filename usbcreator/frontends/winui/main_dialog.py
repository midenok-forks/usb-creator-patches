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

class MainDialog(ui.Page):
    '''Main window of usb-creator.'''
    def on_init(self):
        self.heading = ui.Label(self.parent, 10, 4, 365, 25,
            _('To try or install Ubuntu from a removable disk, '
              'it needs to be set up as a startup disk.'))
        self.source_heading = ui.Label(self.parent, 10, 30, 365, 25,
                                       _('Source disc image (.iso) or CD:'))
        listview_width = 350
        self.sources = ui.ListView(self.parent, 10, 50, listview_width, 100)
        self.sources.insert_column(_('Image'), listview_width / 3, idx=0)
        self.sources.insert_column(_('OS Version'), listview_width / 3, idx=1)
        self.sources.insert_column(_('Size'), listview_width / 3, idx=2)
        
        self.other_button = ui.Button(self.parent, 310, 155, 50, 25,
                                      _('Other...'))
        self.target_heading = ui.Label(self.parent, 10, 170, 365, 25,
                                       _('Removable disk to use:'))
        self.targets = ui.ListView(self.parent, 10, 185, listview_width, 100)
        self.targets.insert_column(_('Device'), listview_width / 4, idx=0)
        self.targets.insert_column(_('Label'), listview_width / 4, idx=1)
        self.targets.insert_column(_('Capacity'), listview_width / 4, idx=2)
        self.targets.insert_column(_('Free Space'), listview_width / 4, idx=3)
        
        self.persistent_heading = ui.Label(self.parent, 10, 285, 365, 25,
                                           _('When starting up from this disk, '
                                             'documents and settings will be:'))
        self.persist_radio = ui.RadioButton(self.parent, 10, 295, 365, 25,
                                            _('Stored in reserved space'))
        self.how_much = ui.Label(self.parent, 30, 320, 75, 25, _('How much:'))
        self.persist_label = ui.Label(self.parent, 0, 0, 50, 25, '')
        self.persist_slider = ui.Trackbar(self.parent, 90, 315, 225, 25)
        self.persist_slider.set_buddy(self.persist_label._hwnd, left=False)
        self.persist_radio.set_check(True)
        self.no_persist_radio = ui.RadioButton(self.parent, 10, 335, 365, 25,
                                               _('Discarded on shutdown, unless'
                                                 ' you save them elsewhere'))

        self.quit_button = ui.DefaultButton(self.parent, 200, 365, 50, 25,
                                            _('Quit'))
        self.make_button = ui.Button(self.parent, 255, 365, 100, 25,
                                     _('Make startup disk'))
