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

import logging

from usbcreator.frontends.base import Frontend
from usbcreator.frontends.winui.winui import ui
from usbcreator.frontends.winui.main_dialog import MainDialog
from usbcreator.frontends.winui.install_window import InstallWindow
from usbcreator import misc

class WinuiFrontend(Frontend, ui.Frontend):
    _main_window_class_ = ui.MainWindow

    def __init__(self, backend):
        #Frontend.__init__(self)
        ui.Frontend.__init__(self)
        self.current_page = None

        self.maindialog = MainDialog(self.main_window)
        self.installwindow = InstallWindow(self.main_window)

        # Connect signals.
        self.maindialog.quit_button.on_click = self.quit
        self.maindialog.sources.on_selection_changed = \
            self.selection_changed_source
        self.maindialog.targets.on_selection_changed = \
            self.selection_changed_target
        self.maindialog.no_persist_radio.on_click = \
            self.maindialog.persist_slider.disable
        self.maindialog.persist_radio.on_click = \
            self.maindialog.persist_slider.enable
        self.maindialog.persist_slider.on_wm_hscroll = \
            self.persist_value_changed
        self.maindialog.make_button.on_click = \
            self.install
        self.maindialog.other_button.on_click = \
            self.other
        # TODO evand 2009-07-24: This really needs a confirmation MessageBox.
        self.installwindow.cancel_button.on_click = \
            self.quit

        # Set initial state.
        self.maindialog.make_button.disable()

        # Connect to backend signals.
        self.backend = backend
        self.backend.source_added_cb = self.add_source
        self.backend.target_added_cb = self.add_target
        self.backend.failure_cb = self.failure
        self.backend.success_cb = self.success
        self.backend.install_progress_cb = self.progress
        self.backend.install_progress_message_cb = self.progress_message
        self.backend.retry_cb = self.retry

        # Scan for devices and bring up the window.
        self.backend.detect_devices()
        self.show_page(self.maindialog)

    def success(self):
        self.installwindow.hide()
        self.show_info_message(_('The installation is complete.  You may now '
                                 'reboot your computer with this device '
                                 'inserted to try or install Ubuntu.'),
                               _('Installation complete'))
        ui.Frontend.stop(self)

    def failure(self, message=None):
        logging.critical('Installation failed.')
        self.installwindow.hide()
        fail_title = _('Installation failed')
        if message:
            self.show_error_message(message, fail_title)
        else:
            # TODO evand 2009-07-28: Better error message.
            self.show_error_message(_('Installation failed.'), fail_title)
        ui.Frontend.stop(self)

    def retry(self, message):
        return self.ask_to_retry(message)

    # Frontend functions.
    def add_source(self, source):
        # FIXME evand 2009-07-21: Don't expose backend data structures like
        # this.
        source = self.backend.sources[source]
        i = self.maindialog.sources.insert_item(source['device'], -1)
        self.maindialog.sources.set_item(i, 1, source['label'])
        self.maindialog.sources.set_item(
            i, 2, misc.format_size(source['size']))

    def add_target(self, target):
        t = self.maindialog.targets
        t.clear()
        target = self.backend.targets[target]
        i = t.insert_item(target['device'], -1)
        t.set_item(i, 1, target['label'])
        t.set_item(i, 2, misc.format_size(target['capacity']))
        t.set_item(i, 3, misc.format_size(target['free']))

    # Callback functions.
    def selection_changed_target(self, item):
        sel = self.maindialog.targets.get_selection()
        target = self.backend.targets[sel]
        maximum = target['free'] / 1024 / 1024
        if maximum < misc.MIN_PERSISTENCE:
            # disable persistence.
            self.maindialog.persist_slider.disable()
        else:
            self.maindialog.persist_slider.enable()
            self.maindialog.persist_slider.set_range(
                misc.MIN_PERSISTENCE, maximum)
        self.selection_changed(item)

    def selection_changed_source(self, item):
        self.backend.set_current_source(self.maindialog.sources.get_selection())
        self.selection_changed(item)

    def selection_changed(self, item):
        # TODO evand 2009-07-29: Doesn't belong here.  Should go in the
        # target_changed callback.
        s = self.maindialog.sources
        t = self.maindialog.targets
        if s.get_selection() and t.get_selection():
            self.maindialog.make_button.enable()
        else:
            self.maindialog.make_button.disable()

    def persist_value_changed(self, event):
        pos = self.maindialog.persist_slider.get_pos()
        self.maindialog.persist_label.set_text('%d MB' % pos)

    def quit(self):
        self.backend.cancel_install()
        ui.Frontend.quit(self)

    def progress(self, complete, remaining, speed):
        self.installwindow.progress_bar.set_position(complete)
        if remaining and speed:
            # TODO evand 2009-07-24: Could use a time formatting function like
            # our human size function.
            mins = int(remaining / 60)
            secs = int(remaining % 60)
            text = _('%d%% complete (%dm%ss remaining)') % \
                    (complete, mins, secs)
            self.installwindow.progress_subtitle.set_text(text)
        else:
            self.installwindow.progress_subtitle.set_text(_('%d%% complete') %
                                                          complete)

    def progress_message(self, message):
        self.installwindow.progress_title.set_text(message)

    def install(self):
        source = misc.text_type(self.maindialog.sources.get_selection())
        target = misc.text_type(self.maindialog.targets.get_selection())
        if self.maindialog.persist_radio.is_checked():
            persist = self.maindialog.persist_slider.get_pos()
        else:
            persist = 0
        if source and target:
            self.installwindow.show()
            self.main_window.hide()
            self.backend.install(source, target, persist)

    def other(self):
        # TODO evand 2009-07-28: The list itself needs to be moved into the
        # base frontend.
        # To be displayed as a list of file type filters.
        filters = [ _('CD Images'), '*.ISO',
                    _('Disk Images'), '*.IMG',
                    _('All'), '*.*'
                  ]
        f = '\0'.join(filters) + '\0'
        filename = ui.open_dialog(self.main_window._hwnd, file_filter=f)
        if filename != '':
            self.backend.add_image(filename)

    # Everything else.

    def on_init(self):
        self.main_window.set_text(_('Make Startup Disk'))
        self.main_window.resize(375,425)

    def show_page(self, page):
        if self.current_page is page:
            self.current_page.show()
            return
        if self.current_page:
            self.current_page.hide()
        self.current_page = page
        page.show()
        self.main_window.show()
        self.run()
