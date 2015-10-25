#!/usr/bin/env python

#  ======================================================================
#  Copyright (C) 2007-2016 Giampaolo Rodola' <g.rodola@gmail.com>
#
#                         All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#  ======================================================================

import os
import tempfile

from pyftpdlib._compat import getcwdu
from pyftpdlib._compat import u
from pyftpdlib.filesystems import AbstractedFS
from testutils import HOME
from testutils import safe_remove
from testutils import TESTFN
from testutils import touch
from testutils import unittest
from testutils import VERBOSITY

if os.name == 'posix':
    from pyftpdlib.filesystems import UnixFilesystem


class TestAbstractedFS(unittest.TestCase):
    """Test for conversion utility methods of AbstractedFS class."""

    def setUp(self):
        safe_remove(TESTFN)

    tearDown = setUp

    def test_ftpnorm(self):
        # Tests for ftpnorm method.
        ae = self.assertEqual
        fs = AbstractedFS(u('/'), None)

        fs._cwd = u('/')
        ae(fs.ftpnorm(u('')), u('/'))
        ae(fs.ftpnorm(u('/')), u('/'))
        ae(fs.ftpnorm(u('.')), u('/'))
        ae(fs.ftpnorm(u('..')), u('/'))
        ae(fs.ftpnorm(u('a')), u('/a'))
        ae(fs.ftpnorm(u('/a')), u('/a'))
        ae(fs.ftpnorm(u('/a/')), u('/a'))
        ae(fs.ftpnorm(u('a/..')), u('/'))
        ae(fs.ftpnorm(u('a/b')), '/a/b')
        ae(fs.ftpnorm(u('a/b/..')), u('/a'))
        ae(fs.ftpnorm(u('a/b/../..')), u('/'))
        fs._cwd = u('/sub')
        ae(fs.ftpnorm(u('')), u('/sub'))
        ae(fs.ftpnorm(u('/')), u('/'))
        ae(fs.ftpnorm(u('.')), u('/sub'))
        ae(fs.ftpnorm(u('..')), u('/'))
        ae(fs.ftpnorm(u('a')), u('/sub/a'))
        ae(fs.ftpnorm(u('a/')), u('/sub/a'))
        ae(fs.ftpnorm(u('a/..')), u('/sub'))
        ae(fs.ftpnorm(u('a/b')), u('/sub/a/b'))
        ae(fs.ftpnorm(u('a/b/')), u('/sub/a/b'))
        ae(fs.ftpnorm(u('a/b/..')), u('/sub/a'))
        ae(fs.ftpnorm(u('a/b/../..')), u('/sub'))
        ae(fs.ftpnorm(u('a/b/../../..')), u('/'))
        ae(fs.ftpnorm(u('//')), u('/'))  # UNC paths must be collapsed

    def test_ftp2fs(self):
        # Tests for ftp2fs method.
        def join(x, y):
            return os.path.join(x, y.replace('/', os.sep))

        ae = self.assertEqual
        fs = AbstractedFS(u('/'), None)

        def goforit(root):
            fs._root = root
            fs._cwd = u('/')
            ae(fs.ftp2fs(u('')), root)
            ae(fs.ftp2fs(u('/')), root)
            ae(fs.ftp2fs(u('.')), root)
            ae(fs.ftp2fs(u('..')), root)
            ae(fs.ftp2fs(u('a')), join(root, u('a')))
            ae(fs.ftp2fs(u('/a')), join(root, u('a')))
            ae(fs.ftp2fs(u('/a/')), join(root, u('a')))
            ae(fs.ftp2fs(u('a/..')), root)
            ae(fs.ftp2fs(u('a/b')), join(root, u(r'a/b')))
            ae(fs.ftp2fs(u('/a/b')), join(root, u(r'a/b')))
            ae(fs.ftp2fs(u('/a/b/..')), join(root, u('a')))
            ae(fs.ftp2fs(u('/a/b/../..')), root)
            fs._cwd = u('/sub')
            ae(fs.ftp2fs(u('')), join(root, u('sub')))
            ae(fs.ftp2fs(u('/')), root)
            ae(fs.ftp2fs(u('.')), join(root, u('sub')))
            ae(fs.ftp2fs(u('..')), root)
            ae(fs.ftp2fs(u('a')), join(root, u('sub/a')))
            ae(fs.ftp2fs(u('a/')), join(root, u('sub/a')))
            ae(fs.ftp2fs(u('a/..')), join(root, u('sub')))
            ae(fs.ftp2fs(u('a/b')), join(root, 'sub/a/b'))
            ae(fs.ftp2fs(u('a/b/..')), join(root, u('sub/a')))
            ae(fs.ftp2fs(u('a/b/../..')), join(root, u('sub')))
            ae(fs.ftp2fs(u('a/b/../../..')), root)
            # UNC paths must be collapsed
            ae(fs.ftp2fs(u('//a')), join(root, u('a')))

        if os.sep == '\\':
            goforit(u(r'C:\dir'))
            goforit(u('C:\\'))
            # on DOS-derived filesystems (e.g. Windows) this is the same
            # as specifying the current drive directory (e.g. 'C:\\')
            goforit(u('\\'))
        elif os.sep == '/':
            goforit(u('/home/user'))
            goforit(u('/'))
        else:
            # os.sep == ':'? Don't know... let's try it anyway
            goforit(getcwdu())

    def test_fs2ftp(self):
        # Tests for fs2ftp method.
        def join(x, y):
            return os.path.join(x, y.replace('/', os.sep))

        ae = self.assertEqual
        fs = AbstractedFS(u('/'), None)

        def goforit(root):
            fs._root = root
            ae(fs.fs2ftp(root), u('/'))
            ae(fs.fs2ftp(join(root, u('/'))), u('/'))
            ae(fs.fs2ftp(join(root, u('.'))), u('/'))
            # can't escape from root
            ae(fs.fs2ftp(join(root, u('..'))), u('/'))
            ae(fs.fs2ftp(join(root, u('a'))), u('/a'))
            ae(fs.fs2ftp(join(root, u('a/'))), u('/a'))
            ae(fs.fs2ftp(join(root, u('a/..'))), u('/'))
            ae(fs.fs2ftp(join(root, u('a/b'))), u('/a/b'))
            ae(fs.fs2ftp(join(root, u('a/b'))), u('/a/b'))
            ae(fs.fs2ftp(join(root, u('a/b/..'))), u('/a'))
            ae(fs.fs2ftp(join(root, u('/a/b/../..'))), u('/'))
            fs._cwd = u('/sub')
            ae(fs.fs2ftp(join(root, 'a/')), u('/a'))

        if os.sep == '\\':
            goforit(u(r'C:\dir'))
            goforit(u('C:\\'))
            # on DOS-derived filesystems (e.g. Windows) this is the same
            # as specifying the current drive directory (e.g. 'C:\\')
            goforit(u('\\'))
            fs._root = u(r'C:\dir')
            ae(fs.fs2ftp(u('C:\\')), u('/'))
            ae(fs.fs2ftp(u('D:\\')), u('/'))
            ae(fs.fs2ftp(u('D:\\dir')), u('/'))
        elif os.sep == '/':
            goforit(u('/'))
            if os.path.realpath('/__home/user') != '/__home/user':
                self.fail('Test skipped (symlinks not allowed).')
            goforit(u('/__home/user'))
            fs._root = u('/__home/user')
            ae(fs.fs2ftp(u('/__home')), u('/'))
            ae(fs.fs2ftp(u('/')), u('/'))
            ae(fs.fs2ftp(u('/__home/userx')), u('/'))
        else:
            # os.sep == ':'? Don't know... let's try it anyway
            goforit(getcwdu())

    def test_validpath(self):
        # Tests for validpath method.
        fs = AbstractedFS(u('/'), None)
        fs._root = HOME
        self.assertTrue(fs.validpath(HOME))
        self.assertTrue(fs.validpath(HOME + '/'))
        self.assertFalse(fs.validpath(HOME + 'bar'))

    if hasattr(os, 'symlink'):

        def test_validpath_validlink(self):
            # Test validpath by issuing a symlink pointing to a path
            # inside the root directory.
            fs = AbstractedFS(u('/'), None)
            fs._root = HOME
            TESTFN2 = TESTFN + '1'
            try:
                touch(TESTFN)
                os.symlink(TESTFN, TESTFN2)
                self.assertTrue(fs.validpath(u(TESTFN)))
            finally:
                safe_remove(TESTFN, TESTFN2)

        def test_validpath_external_symlink(self):
            # Test validpath by issuing a symlink pointing to a path
            # outside the root directory.
            fs = AbstractedFS(u('/'), None)
            fs._root = HOME
            # tempfile should create our file in /tmp directory
            # which should be outside the user root.  If it is
            # not we just skip the test.
            with tempfile.NamedTemporaryFile() as file:
                try:
                    if HOME == os.path.dirname(file.name):
                        return
                    os.symlink(file.name, TESTFN)
                    self.assertFalse(fs.validpath(u(TESTFN)))
                finally:
                    safe_remove(TESTFN)


@unittest.skipUnless(os.name == 'posix', "UNIX only")
class TestUnixFilesystem(unittest.TestCase):

    def test_case(self):
        root = getcwdu()
        fs = UnixFilesystem(root, None)
        self.assertEqual(fs.root, root)
        self.assertEqual(fs.cwd, root)
        cdup = os.path.dirname(root)
        self.assertEqual(fs.ftp2fs(u('..')), cdup)
        self.assertEqual(fs.fs2ftp(root), root)


if __name__ == '__main__':
    unittest.main(verbosity=VERBOSITY)