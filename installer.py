#!/usr/bin/env python3
"""Ledgerbook setup — custom, fully styled two-panel Qt installer."""
import os
import shlex
import shutil
import subprocess
import sys
import venv
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QWidget, QFrame, QProgressBar,
    QCheckBox, QStackedWidget, QSizePolicy,
)

BASE = Path(__file__).resolve().parent
HOME = Path.home()
DATA = Path(os.environ.get('XDG_DATA_HOME', str(HOME / '.local/share')))
DEFAULT = DATA / 'ledgerbook' / 'app'
CONFIG = DATA / 'ledgerbook' / 'installation.txt'
VERSION = '1.0.0'


def install(destination, progress=lambda message, percent: None, desktop_shortcut=False):
    dest = Path(destination).expanduser().resolve()
    if dest in (HOME, Path('/'), BASE) or dest.is_relative_to(BASE):
        raise ValueError('Choose a dedicated installation folder outside the setup files.')
    if not (BASE / 'ledgerbook' / 'app.py').is_file():
        raise FileNotFoundError('Application files are missing from the setup archive.')
    progress('Preparing installation folder…', 8)
    dest.mkdir(parents=True, exist_ok=True)
    env = dest / '.venv'
    if not (env / 'bin/python').exists():
        progress('Creating isolated Python environment…', 18)
        venv.EnvBuilder(with_pip=True, symlinks=True).create(env)
    progress('Installing Qt 6 runtime (internet required on first installation)…', 35)
    result = subprocess.run(
        [str(env / 'bin/python'), '-m', 'pip', 'install', '--disable-pip-version-check',
         'PySide6-Essentials>=6.7,<7'], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise RuntimeError('Could not install Qt dependencies.\n\n' + result.stdout[-3000:])
    progress('Copying Ledgerbook application files…', 70)
    shutil.copytree(BASE / 'ledgerbook', dest / 'ledgerbook', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(BASE / 'LICENSE', dest / 'LICENSE')
    progress('Creating application launcher…', 84)
    binpath = HOME / '.local/bin' / 'ledgerbook'
    binpath.parent.mkdir(parents=True, exist_ok=True)
    binpath.write_text('#!/bin/sh\ncd ' + shlex.quote(str(dest)) + '\nexec ' +
                       shlex.quote(str(env / 'bin/python')) + ' -m ledgerbook "$@"\n')
    binpath.chmod(0o755)
    icon = DATA / 'icons/hicolor/256x256/apps/ledgerbook.png'
    icon.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BASE / 'assets/ledgerbook.png', icon)
    desktop = DATA / 'applications/ledgerbook.desktop'
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop_entry = ('[Desktop Entry]\nType=Application\nName=Ledgerbook\n'
                     'Comment=Offline logbook manager\nExec=' + str(binpath) +
                     '\nIcon=' + str(icon) +
                     '\nTerminal=false\nCategories=Office;Utility;\n')
    desktop.write_text(desktop_entry)
    if desktop_shortcut:
        desktop_dir = HOME / 'Desktop'
        if desktop_dir.is_dir():
            shortcut = desktop_dir / 'Ledgerbook.desktop'
            shortcut.write_text(desktop_entry)
            shortcut.chmod(0o755)
    progress('Finishing installation…', 96)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(str(dest))
    progress('Installation complete', 100)
    return dest



class InstallWorker(QObject):
    update = Signal(str, int)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, destination, shortcut):
        super().__init__()
        self.destination, self.shortcut = destination, shortcut

    def run(self):
        try:
            self.completed.emit(str(install(self.destination, self.update.emit, self.shortcut)))
        except Exception as exc:
            self.failed.emit(str(exc))


def label(text, kind=None, wrap=False):
    w = QLabel(text)
    if kind:
        w.setObjectName(kind)
    w.setWordWrap(wrap)
    return w


def page(title, description):
    w = QWidget()
    w.setObjectName('contentPage')
    layout = QVBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)
    layout.addWidget(label(title, 'pageTitle'))
    layout.addWidget(label(description, 'description', True))
    layout.addSpacing(8)
    return w, layout


class Setup(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'Ledgerbook {VERSION} — Setup')
        self.setFixedSize(900, 550)
        self.setObjectName('setupWindow')
        self.index = 0
        self.busy = False
        self.completed = False
        self.thread = None
        self.worker = None
        self._build()
        self._apply_style()
        self._show_step(0)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        outer.addLayout(body, 1)

        # The sidebar is a real, fixed-width panel, not a QWizard side-widget.
        self.sidebar = QFrame()
        self.sidebar.setObjectName('sidebar')
        self.sidebar.setFixedWidth(240)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(27, 33, 24, 26)
        side.setSpacing(0)
        logo = label('▤', 'logo')
        side.addWidget(logo)
        side.addSpacing(8)
        side.addWidget(label('LEDGERBOOK', 'brand'))
        side.addSpacing(3)
        side.addWidget(label('S E T U P   W I Z A R D', 'eyebrow'))
        side.addSpacing(39)
        self.steps = []
        for i, title in enumerate(('Welcome', 'Location', 'Ready to install', 'Installation', 'Finish')):
            step = label(f'{i + 1:02d}  {title}', 'step')
            step.setMinimumHeight(40)
            side.addWidget(step)
            side.addSpacing(3)
            self.steps.append(step)
        side.addStretch(1)
        side.addWidget(label('VERSION 1.0.0\nOFFLINE · OPEN SOURCE', 'sideFooter'))
        body.addWidget(self.sidebar)

        self.content = QFrame()
        self.content.setObjectName('content')
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(48, 48, 42, 30)
        content_layout.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.setObjectName('pages')
        content_layout.addWidget(self.stack)
        body.addWidget(self.content, 1)

        welcome, v = page('Welcome to Ledgerbook Setup', 'Install Ledgerbook on your Linux computer.')
        v.addSpacing(15)
        v.addWidget(label('A better place for your records', 'sectionTitle'))
        v.addWidget(label('Ledgerbook is a customizable, fully offline logbook manager. '
                          'This setup wizard will install the application, create its launcher, '
                          'and configure the Qt 6 runtime.', 'bodyText', True))
        v.addWidget(label('• Your existing logbooks and database will be preserved.\n'
                          '• No account or cloud connection is required.\n'
                          '• Internet is needed only to download Qt dependencies.', 'muted', True))
        v.addStretch(1)
        v.addWidget(label('Copyright © 2026 Nate Robertson  ·  GNU GPL-3.0-only', 'copyright'))
        self.stack.addWidget(welcome)

        location, v = page('Choose Installation Location', 'The recommended folder is already selected.')
        v.addSpacing(14)
        v.addWidget(label('Install Ledgerbook to:', 'sectionTitle'))
        row = QHBoxLayout()
        saved = CONFIG.read_text().strip() if CONFIG.exists() else str(DEFAULT)
        self.path = QLineEdit(saved)
        self.path.setMinimumHeight(42)
        row.addWidget(self.path, 1)
        browse = QPushButton('Browse…')
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        v.addLayout(row)
        v.addWidget(label('Ledgerbook will appear in your application menu. Your personal '
                          'logbook database is stored separately.', 'muted', True))
        self.shortcut = QCheckBox('Create a desktop shortcut (if a Desktop folder exists)')
        v.addWidget(self.shortcut)
        v.addStretch(1)
        self.stack.addWidget(location)

        ready, v = page('Ready to Install', 'Review your selections before installing Ledgerbook.')
        v.addSpacing(15)
        v.addWidget(label('Setup is ready to begin', 'sectionTitle'))
        self.summary = label('', 'summary', True)
        self.summary.setMinimumHeight(122)
        v.addWidget(self.summary)
        v.addStretch(1)
        v.addWidget(label('The first installation may take a few minutes.', 'muted'))
        self.stack.addWidget(ready)

        installing, v = page('Installing Ledgerbook', 'Please wait while setup completes.')
        v.addSpacing(15)
        v.addWidget(label('Installing components', 'sectionTitle'))
        self.status = label('Preparing installation…', 'bodyText', True)
        v.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setMinimumHeight(24)
        v.addWidget(self.progress)
        self.detail = label('Do not close the installer while files are being copied.', 'muted', True)
        v.addWidget(self.detail)
        v.addStretch(1)
        self.stack.addWidget(installing)

        done, v = page('Installation Complete', 'Ledgerbook has been installed successfully.')
        v.addSpacing(15)
        v.addWidget(label('Ledgerbook is ready to use', 'sectionTitle'))
        v.addWidget(label('Open Ledgerbook from your application menu or run '
                          '“ledgerbook” in a terminal. Your existing logbooks are preserved.', 'bodyText', True))
        v.addStretch(1)
        v.addWidget(label('Click Finish to close Setup.', 'muted'))
        self.stack.addWidget(done)

        footer = QFrame()
        footer.setObjectName('footer')
        footer.setFixedHeight(69)
        actions = QHBoxLayout(footer)
        actions.setContentsMargins(24, 11, 24, 11)
        actions.addStretch(1)
        self.back = QPushButton('‹  Back')
        self.back.clicked.connect(self._back)
        self.next = QPushButton('Next  ›')
        self.next.setObjectName('primaryButton')
        self.next.clicked.connect(self._next)
        self.cancel = QPushButton('Cancel')
        self.cancel.clicked.connect(self.reject)
        actions.addWidget(self.back)
        actions.addWidget(self.next)
        actions.addWidget(self.cancel)
        outer.addWidget(footer)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog#setupWindow { background: #f8fafc; }
            QFrame#sidebar { background-color: #172b49; border: 0; }
            QFrame#sidebar QLabel { background: transparent; color: #b8cbe5; }
            QLabel#logo { color: #ffffff; font-size: 42px; font-weight: 700; }
            QLabel#brand { color: #ffffff; font-size: 18px; font-weight: 800; }
            QLabel#eyebrow { color: #91b5e1; font-size: 10px; }
            QLabel#step { color: #b8cbe5; font-size: 12px; padding: 0px 10px; border-radius: 6px; }
            QLabel#step[active="true"] { background: #2e527e; color: #ffffff; font-weight: 700; }
            QLabel#sideFooter { color: #91a9c6; font-size: 10px; }
            QFrame#content, QWidget#contentPage, QStackedWidget#pages { background: #f8fafc; }
            QFrame#content QLabel { background: transparent; color: #263448; font-size: 12px; }
            QLabel#pageTitle { color: #1a2941; font-size: 22px; font-weight: 700; }
            QLabel#description { color: #64748b; font-size: 12px; }
            QLabel#sectionTitle { color: #1a2941; font-size: 17px; font-weight: 700; }
            QLabel#bodyText { color: #34465f; font-size: 13px; }
            QLabel#muted { color: #61748d; font-size: 12px; }
            QLabel#copyright { color: #61748d; font-size: 11px; }
            QLabel#summary { background: #edf2f8; color: #263448; border: 1px solid #d7e0ed;
                             border-radius: 8px; padding: 16px; font-size: 13px; }
            QLineEdit { background: #ffffff; color: #1c2d42; border: 1px solid #b9c8d9;
                        border-radius: 6px; padding: 8px; selection-background-color: #386fbd; }
            QLineEdit:focus { border: 2px solid #386fbd; }
            QCheckBox { color: #34465f; spacing: 8px; }
            QFrame#footer { background: #f8fafc; border-top: 1px solid #d7e0ed; }
            QPushButton { background: #edf2f8; color: #243650; border: 1px solid #c5d2e2;
                          border-radius: 6px; padding: 9px 19px; min-height: 19px; font-weight: 600; }
            QPushButton:hover { background: #dae7f6; }
            QPushButton:disabled { background: #f1f3f6; color: #9ca8b6; border-color: #dce2e9; }
            QPushButton#primaryButton { background: #3479ca; color: #ffffff; border: 1px solid #3479ca; }
            QPushButton#primaryButton:hover { background: #2468b8; }
            QPushButton#primaryButton:disabled { background: #adc9e7; color: #f5f8fc; }
            QProgressBar { background: #e6edf6; border: 0; border-radius: 8px;
                           text-align: center; color: #1b304b; }
            QProgressBar::chunk { background: #3479ca; border-radius: 8px; }
        """)
        # Explicit sidebar palette avoids inheriting Linux Mint's dark/light system theme.
        self.sidebar.setAutoFillBackground(True)

    def _browse(self):
        selected = QFileDialog.getExistingDirectory(self, 'Choose installation folder',
                                                    str(Path(self.path.text()).expanduser().parent))
        if selected:
            self.path.setText(selected)

    def _show_step(self, index):
        self.index = index
        self.stack.setCurrentIndex(index)
        for i, step in enumerate(self.steps):
            step.setProperty('active', i == index)
            step.style().unpolish(step)
            step.style().polish(step)
            step.update()
        self.back.setVisible(index in (1, 2))
        self.next.setText(('Next  ›', 'Next  ›', 'Install', 'Next  ›', 'Finish')[index])
        self.next.setEnabled(index != 3 or self.completed)
        self.cancel.setVisible(index != 4)
        if index == 2:
            self.summary.setText('Installation folder\n' + self.path.text().strip() +
                                 '\n\nComponents\nLedgerbook application · Qt 6 runtime · Application launcher')
        if index == 3 and not self.completed and not self.busy:
            self._start_install()

    def _back(self):
        if not self.busy and self.index in (1, 2):
            self._show_step(self.index - 1)

    def _next(self):
        if self.index == 4:
            self.accept()
        elif self.index == 1:
            if not self.path.text().strip():
                QMessageBox.warning(self, 'Installation location', 'Choose an installation folder.')
                return
            self._show_step(2)
        elif self.index == 2:
            self._show_step(3)
        elif self.index == 3:
            if self.completed:
                self._show_step(4)
        else:
            self._show_step(1)

    def _start_install(self):
        self.busy = True
        self.cancel.setEnabled(False)
        self.thread = QThread(self)
        self.worker = InstallWorker(self.path.text().strip(), self.shortcut.isChecked())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.update.connect(self._progress)
        self.worker.completed.connect(self._complete)
        self.worker.failed.connect(self._error)
        self.worker.completed.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def _progress(self, message, percent):
        self.status.setText(message)
        self.progress.setValue(percent)

    def _complete(self, path):
        self.busy = False
        self.completed = True
        self.status.setText('Ledgerbook installed successfully.')
        self.progress.setValue(100)
        self.detail.setText('Installed to ' + path)
        self.cancel.setEnabled(True)
        self.next.setEnabled(True)

    def _error(self, message):
        self.busy = False
        self.status.setText('Installation could not be completed.')
        self.detail.setText('Close setup and retry after resolving the error.')
        self.cancel.setEnabled(True)
        QMessageBox.critical(self, 'Installation failed', message)

    def reject(self):
        if self.busy:
            QMessageBox.information(self, 'Installation in progress',
                                    'Wait for installation to finish before closing setup.')
            return
        super().reject()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = Setup()
    window.show()
    sys.exit(app.exec())
