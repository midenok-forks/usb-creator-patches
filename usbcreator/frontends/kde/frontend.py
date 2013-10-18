#!/usr/bin/python

# Copyright (C) 2009 Roderick B. Greening <roderick.greening@gmail.com>
# 
# Based in part on work by:
#  David Edmundson <kde@davidedmundson.co.uk>
#  Canonical Ltd. USB Creator Team
# 
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

import sys
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.kdeui import KIcon, KMessageBox, KGlobalSettings
from PyKDE4.kdecore import KProcess, KStandardDirs, KUrl, i18n
from PyKDE4.kio import KFileDialog

from usbcreator.frontends.kde.translate import translate
uic.properties.Properties._string = translate
import gettext
import logging

from usbcreator.frontends.base import Frontend
from usbcreator import misc
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

queue = Queue()
def thread_wrap(func):
    '''Decorator for functions that will be called by another thread.'''
    def wrap(*args):
        queue.put(lambda: func(*args))
    return wrap

class KdeFrontend(Frontend, QObject):
    @classmethod
    def startup_failure(cls, message):
        KMessageBox.sorry(None, message, "", KMessageBox.Notify)

    @classmethod
    def DBusMainLoop(cls):
        from dbus.mainloop.qt import DBusQtMainLoop
        DBusQtMainLoop(set_as_default=True)

    def __init__(self, backend, img=None, persistent=True,
                 allow_system_internal=False):
        QObject.__init__(self)

        #our passed vars - keep them private
        self.__persistent = persistent
        self.__img = img
        self.__allow_system_internal = allow_system_internal

        # Perform some initialization
        self.__initPrivateVars()
        self.__initUI()

        #enable the backend
        self.__backend = backend

        # Connect to backend signals.
        self.__backend.source_added_cb = self.add_source
        self.__backend.target_added_cb = self.add_target
        self.__backend.source_removed_cb = self.remove_source
        self.__backend.target_removed_cb = self.remove_target
        self.__backend.failure_cb = self.failure
        self.__backend.success_cb = self.success
        self.__backend.install_progress_cb = self.progress
        self.__backend.install_progress_message_cb = self.progress_message
        self.__backend.retry_cb = self.retry
        self.__backend.target_changed_cb = self.update_target
        self.__backend.format_ended_cb = self.format_ended
        self.__backend.format_failed_cb = self.format_failed

        #add any file sources passed
        if self.__img is not None:
            self.__backend.add_image(misc.text_type(self.__img))

        downloadsDir = QDir(KGlobalSettings.self().downloadPath())
        isoFilter = []
        isoFilter.append("*.iso")
        for iso in downloadsDir.entryList(isoFilter, QDir.Files):
            self.__backend.add_image(misc.text_type(downloadsDir.absoluteFilePath(iso)))

        def test_func(*a):
            if not queue.empty():
                func = queue.get_nowait()
                func()
                queue.task_done()
            return True
        self.queue_processor = self.add_timeout(500, test_func, None)

        self.__backend.detect_devices()

        self.update_loop = self.add_timeout(2000, self.__backend.update_free)

    def __initPrivateVars(self):
        """Initialize Private Variables"""

        # main window
        self.__mainWindow = QDialog()

        # ui file
        self.__mainWindow_ui = "usbcreator-kde.ui"

        # init Backend to None - easier to debug...
        self.__backend = None

    def __initUI(self):
        """Initialize the interface"""

        # Locate the ui for the main window and load it.
        if 'USBCREATOR_LOCAL' in os.environ:
            appdir = os.path.join(os.getcwd(), 'gui')
        else:
            file = KStandardDirs.locate("appdata", self.__mainWindow_ui)
            appdir = file[:file.rfind("/")]
        uic.loadUi(misc.text_type(appdir + "/" + self.__mainWindow_ui), self.__mainWindow)

        #set default persist size
        self.__mainWindow.ui_persist_label.setText(misc.format_mb_size(128))

        #set persistent ui elements state
        if self.__persistent:
            self.__mainWindow.ui_persist_enabled.setChecked(True)
            self.__mainWindow.ui_persist_text.setEnabled(True)
            self.__mainWindow.ui_persist_slider.setEnabled(True)
            self.__mainWindow.ui_persist_label.setEnabled(True)
        else:
            self.__mainWindow.ui_persist_disabled.setChecked(True)
            self.__mainWindow.ui_persist_frame.hide()

        #hide sources if an argument was provided
        if self.__img is not None:
            self.__mainWindow.ui_source_list.hide()
            self.__mainWindow.ui_add_source.hide()
            self.__mainWindow.insert_label.hide()
            self.__mainWindow.source_label.hide()

        #disable the start button and persist frame by default
        self.__mainWindow.ui_persist_frame.setEnabled(False)
        self.__mainWindow.ui_start_button.setEnabled(False)

        #add some buttons
        self.__mainWindow.ui_quit_button.setIcon(KIcon("application-exit"))
        self.__mainWindow.ui_start_button.setIcon(KIcon("dialog-ok-apply"))
        self.__mainWindow.ui_add_source.setIcon(KIcon("media-optical"))
        self.__mainWindow.ui_format_dest.setIcon(KIcon("drive-removable-media-usb-pendrive"))

        #set up signals
        self.connect(self.__mainWindow.ui_add_source,SIGNAL('clicked()'),
            self.add_file_source_dialog)
        self.connect(self.__mainWindow.ui_persist_slider,SIGNAL('valueChanged(int)'),
            lambda value: self.__mainWindow.ui_persist_label.setText(misc.format_mb_size(value)))
        self.connect(self.__mainWindow.ui_quit_button,SIGNAL('clicked()'),
            self.quit)
        self.connect(self.__mainWindow.ui_start_button,SIGNAL('clicked()'),
            self.install)
        self.connect(self.__mainWindow.ui_dest_list,SIGNAL(
            'currentItemChanged(QTreeWidgetItem*,QTreeWidgetItem*)'),
            self.dest_selection_changed)
        self.connect(self.__mainWindow.ui_source_list,SIGNAL(
            'currentItemChanged(QTreeWidgetItem*,QTreeWidgetItem*)'),
            self.source_selection_changed)
        self.connect(self.__mainWindow.ui_format_dest,SIGNAL('clicked()'),
            self.format_dest_clicked)

        self.__mainWindow.ui_source_list.setSortingEnabled(True)
        self.__mainWindow.ui_source_list.sortByColumn(0, Qt.AscendingOrder)
        self.__mainWindow.ui_dest_list.setSortingEnabled(True)
        self.__mainWindow.ui_dest_list.sortByColumn(0, Qt.AscendingOrder)
        self.progress_bar = QProgressDialog("",i18n('Cancel'),0,100,self.__mainWindow)
        #set title of progress window (same as gtk frontend)
        self.progress_bar.setWindowTitle(_('Installing'))
        #prevent progress bar from emitting reset on reaching max value (and auto closing)
        self.progress_bar.setAutoReset(False)
        #force immediate showing, rather than waiting...
        self.progress_bar.setMinimumDuration(0)
        #must disconnect the canceled() SIGNAL, otherwise the progress bar is actually destroyed
        self.disconnect(self.progress_bar,SIGNAL('canceled()'),self.progress_bar.cancel)
        #now we connect our own signal to display a warning dialog instead
        self.connect(self.progress_bar,SIGNAL('canceled()'),self.warning_dialog)

        #show the window
        self.__mainWindow.show()

    def __timeout_callback(self, func, *args):
        '''Private callback wrapper used by add_timeout'''

        timer = self.sender()
        active = func(*args)
        if not active:
            timer.stop()

    def __fail(self, message=None):
        '''Handle Failed Install Gracefully'''

        logging.exception('Installation failed.')
        self.__backend.unmount()
        self.progress_bar.hide()
        if not message:
            message = _('Installation failed.')
        KMessageBox.error(self.__mainWindow, message)
        sys.exit(1)

    def add_timeout(self, interval, func, *args):
        '''Add a new timer for function 'func' with optional arguments. Mirrors a
        similar gobject call timeout_add.'''

        # FIXME: now that we are part of a Qt object, we may be able to alter for builtin timers
        timer = QTimer()
        QObject.connect(timer,
            SIGNAL('timeout()'),
            lambda: self.__timeout_callback(func, *args))
        timer.start(interval)

        return timer

    def delete_timeout(self, timer):
        '''Remove the specified timer'''

        if timer.isActive():
            return False
        timer.stop()
        return True

    def add_target(self, target):
        logging.debug('add_target: %s' % misc.text_type(target))
        new_item = QTreeWidgetItem(self.__mainWindow.ui_dest_list)
        new_item.setData(0,Qt.UserRole,target)
        # FIXME:
        # the new_item lines should be auto triggered onChange to the
        # TreeWidget when new_item is appended.
        new_item.setText(0,target)
        new_item.setIcon(0,KIcon("drive-removable-media-usb-pendrive"))

        item = self.__mainWindow.ui_dest_list.currentItem()
        if not item:
            item = self.__mainWindow.ui_dest_list.topLevelItem(0)
            if item:
                self.__mainWindow.ui_dest_list.setCurrentItem(item,True)

        # populate from device data
        if self.__backend is not None:
            dev = self.__backend.targets[target]
            pretty_name = "%s %s (%s)" % (dev['vendor'], dev['model'], dev['device'])
            new_item.setText(0,pretty_name)
            new_item.setText(1,dev['label'])
            new_item.setText(2,misc.format_size(dev['capacity']))
            free = dev['free']
            if free >= 0:
                new_item.setText(3,misc.format_size(free))
            else:
                new_item.setText(3,'')

    def remove_target(self, target):
        for i in range(0,self.__mainWindow.ui_dest_list.topLevelItemCount()):
            item = self.__mainWindow.ui_dest_list.topLevelItem(i)
            if item.data(0,Qt.UserRole) == target:
                self.__mainWindow.ui_dest_list.takeTopLevelItem(i)
                break

        if not self.__mainWindow.ui_dest_list.currentItem():
            item = self.__mainWindow.ui_dest_list.topLevelItem(0)
            if item:
                self.__mainWindow.ui_dest_list.setCurrentItem(item,True)

    def add_source(self, source):
        logging.debug('add_source: %s' % misc.text_type(source))
        new_item = QTreeWidgetItem(self.__mainWindow.ui_source_list)
        new_item.setData(0,Qt.UserRole,source)
        # FIXME:
        # the new_item lines should be auto triggered onChange to the TreeWidget
        # when new_item is appended.
        new_item.setText(0,source)
        new_item.setIcon(0,KIcon("media-optical"))

        item = self.__mainWindow.ui_source_list.currentItem()
        if not item:
            item = self.__mainWindow.ui_source_list.topLevelItem(0)
            if item:
                self.__mainWindow.ui_source_list.setCurrentItem(item,True)

        # how does this all get added? here or elsewhere...
        # populate from device data
        if self.__backend is not None:
            new_item.setText(0,self.__backend.sources[source]['device'])
            # Strip as some derivates like to have whitespaces/newlines (e.g. netrunner)
            new_item.setText(1,self.__backend.sources[source]['label'].strip())
            new_item.setText(2,misc.format_size(self.__backend.sources[source]['size']))

    def remove_source(self, source):
        for i in range(0,self.__mainWindow.ui_source_list.topLevelItemCount()):
            item = self.__mainWindow.ui_source_list.topLevelItem(i)
            if item.data(0,Qt.UserRole) == source:
                self.__mainWindow.ui_source_list.removeItemWidget(item,0)
                break

        if not self.__mainWindow.ui_source_list.currentItem():
            item = self.__mainWindow.ui_source_list.topLevelItem(0)
            if item:
                self.__mainWindow.ui_source_list.setCurrentItem(item,True)

    def get_source(self):
        '''Returns the UDI of the selected source image.'''
        item = self.__mainWindow.ui_source_list.currentItem()
        if item:
            # Must deal in unicode and not QString for backend
            source = misc.text_type(item.data(0,Qt.UserRole))
            return source
        else:
            logging.debug('No source selected.')
            return ''

    def get_target(self):
        '''Returns the UDI of the selected target disk or partition.'''
        item = self.__mainWindow.ui_dest_list.currentItem()
        if item:
            # Must deal in unicode and not QString for backend
            dest = misc.text_type(item.data(0,Qt.UserRole))
            return dest
        else:
            logging.debug('No target selected.')
            return ''

    def get_persistence(self):
        if (self.__mainWindow.ui_persist_enabled.isChecked() and
            self.__mainWindow.ui_persist_frame.isEnabled()):
            val = self.__mainWindow.ui_persist_slider.value()
            return int(val)
        else:
            return 0

    def update_target(self, udi):
        for i in range(0,self.__mainWindow.ui_dest_list.topLevelItemCount()):
            item = self.__mainWindow.ui_dest_list.topLevelItem(i)
            if misc.text_type(item.data(0,Qt.UserRole)) == udi:
                self.__mainWindow.ui_dest_list.emit(
                    SIGNAL('itemChanged(item,0)'))
                break
        # Update persistence maximum value.
        self.__mainWindow.ui_persist_frame.setEnabled(False)
        self.__mainWindow.ui_start_button.setEnabled(False)
        target = self.__backend.targets[udi]
        persist_mb = target['persist'] / 1024 / 1024
        if persist_mb > misc.MIN_PERSISTENCE:
            self.__mainWindow.ui_persist_frame.setEnabled(True)
            self.__mainWindow.ui_persist_slider.setRange(
                misc.MIN_PERSISTENCE, persist_mb)
        # Update install button state.
        status = target['status']
        source = self.__backend.get_current_source()
        if not source:
            return
        stype = self.__backend.sources[source]['type']
        if (status == misc.CAN_USE or
         (self.__mainWindow.ui_start_button.isEnabled() and stype == misc.SOURCE_IMG)):
            self.__mainWindow.ui_start_button.setEnabled(True)
        else:
            self.__mainWindow.ui_start_button.setEnabled(False)
            status = misc.NEED_FORMAT
        # Update the destination status message.
        if status == misc.CANNOT_USE:
            msg = _('The device is not large enough to hold this image.')
        elif status == misc.NEED_SPACE:
            msg = _('There is not enough free space for this image.')
            # FIXME RBG: 04/01/10 - Need Open button for folder to device for removing files
        elif status == misc.NEED_FORMAT:
            msg = _('The device needs to be formatted for use.')
        else:
            msg = ''
        self.__mainWindow.ui_dest_status.setText(msg)

    def source_selection_changed(self, current_item, prev_item):
        '''The selected image has changed we need to refresh targets'''
        if not self.__backend:
            return
        if current_item is not None:
            udi = misc.text_type(current_item.data(0,Qt.UserRole))
        else:
            udi = None
        self.__backend.set_current_source(udi)
        item = self.__mainWindow.ui_dest_list.currentItem()
        self.dest_selection_changed(item, None)

    def dest_selection_changed(self, current_item, prev_item):
        '''The selected partition has changed and the bounds on the persistence
        slider need to be changed, or the slider needs to be disabled, to
        reflect the amount of free space on the partition.'''

        if not self.__backend:
            return

        if current_item is None:
            return

        udi = misc.text_type(current_item.data(0,Qt.UserRole))
        self.update_target(udi)

    def add_file_source_dialog(self):
        filename = ''
        filter = '*.iso|' + _('CD Images') + '\n*.img|' + _('Disk Images')
        # FIXME: should set the default path KUrl to users home dir...
        # This is all screwy as its run as root under kdesudo... Home = root and not user.. blarg!
        # Need to convert to plain string for backend to work
        filename = misc.text_type(KFileDialog.getOpenFileName(KUrl(),filter))
        if not filename:
          return
        self.__backend.add_image(filename)

    def install(self):
        source = self.get_source()
        target = self.get_target()
        persist = self.get_persistence()
        if (source and target):
            self.__mainWindow.hide()
            self.delete_timeout(self.update_loop)
            starting_up = _('Starting up')
            self.progress_bar.setLabelText(starting_up)
            self.progress_bar.show()
            try:
                self.__backend.install(source, target, persist,
                                       allow_system_internal=self.__allow_system_internal)
            except:
                self.__fail()
        else:
            message = _('You must select both source image and target device first.')
            self.notify(message)

    @thread_wrap
    def progress(self, complete, remaining, speed):
        # Updating value cause dialog to re-appear from hidden (dunno why)
        if not self.progress_bar.isHidden():
            self.progress_bar.setValue(int(complete))

    @thread_wrap
    def progress_message(self, message):
        self.progress_bar.setLabelText(message)

    def quit(self, *args):
        self.__backend.cancel_install()
        sys.exit(0)

    @thread_wrap
    def failure(self, message=None):
        '''Install failed'''
        self.__fail(message)

    @thread_wrap
    def success(self):
        '''Install completed'''
        self.__backend.unmount()
        self.progress_bar.hide()
        text = _('The installation is complete.  You may now reboot your '
                 'computer with this device inserted to try or install '
                 'Ubuntu.')

        KMessageBox.information(self.__mainWindow, text)
        sys.exit(0)

    @thread_wrap
    def retry(self, message):
        '''A retry dialog'''

        caption = _('Retry?')

        res = KMessageBox.warningYesNo(self.__mainWindow,message,caption)

        return res == KMessageBox.Yes

    def notify(self,title):
        KMessageBox.sorry(self.__mainWindow,title)

    def warning_dialog(self):
        '''A warning dialog to show when progress dialog cancel is pressed'''

        caption = _('Quit the installation?')
        text = _('Do you really want to quit the installation now?')

        #hide the progress bar - install will still continue in bg
        self.progress_bar.hide()

        res = KMessageBox.warningYesNo(self.__mainWindow,text,caption)

        if res == KMessageBox.Yes:
            self.quit()

        #user chose not to quit, so re-show progress bar
        self.progress_bar.show()

    def format_ended(self):
        self.__mainWindow.unsetCursor()
        self.__mainWindow.ui_format_dest.setEnabled(True)

    @thread_wrap
    def format_failed(self, message):
        self.__mainWindow.unsetCursor()
        self.__mainWindow.ui_format_dest.setEnabled(True)
        # TODO sort through error types (message.get_dbus_name()) in backend,
        # individual functions in frontend for each error type.
        KMessageBox.error(self.__mainWindow, str(message))

    def format_dest_clicked(self):
        item = self.__mainWindow.ui_dest_list.currentItem()
        if not item:
            return
        udi = misc.text_type(item.data(0,Qt.UserRole))

        text = _('Are you sure you want to erase the entire disk?')

        res = KMessageBox.warningYesNo(self.__mainWindow,text)

        if res == KMessageBox.Yes:
            self.__mainWindow.setCursor(Qt.BusyCursor)
            # Disable simultaneous format attempts.. let current finish first
            self.__mainWindow.ui_format_dest.setEnabled(False)
            self.__backend.format(udi)

