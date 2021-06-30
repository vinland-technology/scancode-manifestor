#!/usr/bin/python3

###################################################################
#
# Scancode report -> manifest creator
#
# SPDX-FileCopyrightText: 2021 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
###################################################################

import unittest


import scancode_manifestor.manifestor_utils
from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterAction
from scancode_manifestor.manifestor_utils import FilterModifier
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils

from test import sample_data
 
class TestMiscIs(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)
        
    
    def test_isfile(self):
        self.assertTrue(self.utils._isfile(sample_data.file()))
        self.assertFalse(self.utils._isfile(sample_data.dir()))

    def test_isdir(self):
        self.assertFalse(self.utils._isdir(sample_data.file()))
        self.assertTrue(self.utils._isdir(sample_data.dir()))

    def test_extract_license(self):
        lic = self.utils._extract_license(sample_data.file())
        self.assertTrue(  lic == \
            {"gpl-2.0-or-later", "gpl-3.0-or-later"} or \
            {"gpl-3.0-or-later", "gpl-2.0-or-later"})

    def test_dir_licenses(self):
        files = sample_data.files()
        dir = sample_data.sample_dir("git/dit")
        lic_list = list(self.utils._dir_licenses(files, dir, "included"))
        lic_list.sort()
        right_list = ['bsd-new', 'gpl-2.0-or-later', 'gpl-3.0-only', 'gpl-3.0-or-later', 'mit']
        self.assertTrue(right_list == lic_list)

    def test_keep_file(self):
        f = sample_data.file()

        self.assertTrue(self.utils._keep_file(True, FilterAction.INCLUDE))
        
        self.assertFalse(self.utils._keep_file(True, FilterAction.EXCLUDE))
        
        self.assertFalse(self.utils._keep_file(False, FilterAction.INCLUDE))
        
        self.assertTrue(self.utils._keep_file(False, FilterAction.EXCLUDE))

    def test_extract_license(self):
        f = sample_data.file()
        fl = self.utils._extract_license(f)
        expected_l = {'gpl-3.0-or-later', 'gpl-2.0-or-later'}
        self.assertTrue(expected_l == fl)


        
if __name__ == '__main__':
    unittest.main()
