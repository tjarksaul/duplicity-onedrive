# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2014 Eduardo Garcia Cebollero <kiwnix@gmail.com>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os.path
import urllib

import duplicity.backend
from duplicity import globals
from duplicity import log
from duplicity import tempdir

class OneDriveBackend(duplicity.backend.Backend):
    """Connect to remote store using File Transfer Protocol"""
    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        # we expect an error return, so go low-level and ignore it
        try:
            p = os.popen("mkdir -p /tmp/dupli-onedrive/")
            fout = p.read()
            ret = p.close()
        except Exception:
            pass
        # the expected error is 8 in the high-byte and some output
        self.parsed_url = parsed_url

        self.url_string = duplicity.backend.strip_auth_from_url(self.parsed_url)

        # This squelches the "file not found" result from ncftpls when
        # the ftp backend looks for a collection that does not exist.
        # version 3.2.2 has error code 5, 1280 is some legacy value
        # self.popen_breaks[ 'ncftpls' ] = [ 5, 1280 ]

        # Use an explicit directory name.
        if self.url_string[-1] != '/':
            self.url_string += '/'

        #self.password = self.get_password()

        # if globals.ftp_connection == 'regular':
        #    self.conn_opt = '-E'
        # else:
        #    self.conn_opt = '-F'
        self.tempname = "/tmp/dupli-onedrive"

    def _put(self, source_path, remote_filename):
        remote_path = os.path.join(urllib.unquote(self.parsed_url.path.lstrip('/'))).rstrip()
        commandline = "ln -s %s /tmp/dupli-onedrive/%s && onedrive-cli put '%s/%s' '%s'" % \
            (source_path.name, remote_filename, self.tempname, remote_filename, remote_path)
        try:
            self.subprocess_popen(commandline)
        except Exception as exc:
            commandline = "[ -f /tmp/dupli-onedrive/%s ] && rm /tmp/dupli-onedrive/%s" % \
            (remote_filename, remote_filename)
            self.subprocess_popen(commandline)
            raise exc

    def _get(self, remote_filename, local_path):
        remote_path = os.path.join(urllib.unquote(self.parsed_url.path), remote_filename).rstrip()
        commandline = "onedrive-cli get '%s' '%s'" % \
            (remote_path.lstrip('/'), local_path.name)
        self.subprocess_popen(commandline)

    def _list(self):
        # Do a long listing to avoid connection reset
        remote_path = os.path.join(urllib.unquote(self.parsed_url.path.lstrip('/'))).rstrip()
        commandline = "onedrive-cli ls '%s'" % (remote_path)
        _, l, _ = self.subprocess_popen(commandline)
        # Look for our files as the last element of a long list line
        return [x.split()[-1] for x in l.split('\n') if x and not x.startswith("total ")]

    def _delete(self, filename):
        remote_file_path = os.path.join(urllib.unquote(self.parsed_url.path.lstrip('/')), filename)
        commandline = "onedrive-cli rm '%s'" % \
            (remote_file_path)
        self.subprocess_popen(commandline)

    def __del__(self):
        try:
            p = os.popen("rm -rf /tmp/dupli-onedrive/")
            fout = p.read()
            ret = p.close()
        except Exception:
            pass


duplicity.backend.register_backend("onedrive", OneDriveBackend)
