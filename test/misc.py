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

    def test_keep_file(self):
        f = sample_data.file()

        assert self.utils._keep_file(True, FilterAction.INCLUDE)
        
        assert not self.utils._keep_file(True, FilterAction.EXCLUDE)
        
        assert not self.utils._keep_file(False, FilterAction.INCLUDE)
        
        assert self.utils._keep_file(False, FilterAction.EXCLUDE)

    def test_extract_license(self):
        f = sample_data.file()
        fl = self.utils._extract_license(f)
        expected_l = {'gpl-3.0-or-later', 'gpl-2.0-or-later'}
        assert expected_l == fl

    def test_curate_file_license(self):
        files = sample_data.transformed_files()

        # curate file "bonkey.txt" to be mit
        self.utils._curate_file_license(files, "bonkey.txt", "mit")

        # find the file bonkey.txt
        the_file = None
        for f in files['included']:
            if f['name'] == "bonkey.txt":
                the_file = f
                break

        # compare bonkey's license with expected
        expected_l = 'mit'
        actual_l = the_file['license_key']
        assert expected_l == actual_l
        
        #expected_l = {'gpl-3.0-or-later', 'gpl-2.0-or-later'}
        #assert expected_l == fl

        
if __name__ == '__main__':
    unittest.main()
