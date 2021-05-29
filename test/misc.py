#!/usr/bin/python3


import unittest


import scancode_manifestor.manifestor_utils
from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterAction
from scancode_manifestor.manifestor_utils import FilterModifier
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils

import sample_data
 
class TestMiscIs(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)
        
    
    def test_isfile(self):
        assert self.utils._isfile(sample_data.file())
        assert not self.utils._isfile(sample_data.dir())

    def test_isdir(self):
        assert not self.utils._isdir(sample_data.file())
        assert self.utils._isdir(sample_data.dir())

    def test_extract_license(self):
        lic = self.utils._extract_license(sample_data.file())
        assert  lic == \
            {"gpl-2.0-or-later", "gpl-3.0-or-later"} or \
            {"gpl-3.0-or-later", "gpl-2.0-or-later"}

    def test_dir_licenses(self):
        files = sample_data.files()
        dir = sample_data.sample_dir("git/dit")
        lic_list = list(self.utils._dir_licenses(files, dir, "included"))
        lic_list.sort()
        right_list = ['bsd-new', 'gpl-2.0-or-later', 'gpl-3.0-only', 'gpl-3.0-or-later', 'mit']
        assert right_list == lic_list

if __name__ == '__main__':
    unittest.main()
