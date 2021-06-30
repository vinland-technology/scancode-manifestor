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
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils
import json

from test import sample_data
 
class TestMatchGeneric(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)

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
        actual_l = the_file['scancode_manifestor']['curated_license']
        self.assertTrue(expected_l == actual_l)
        
        #expected_l = {'gpl-3.0-or-later', 'gpl-2.0-or-later'}
        #assert expected_l == fl

    def test_curate_license(self):
        files = sample_data.files()

        # Make sure, no curations
        for f in files['included']:
            # No curation yet, so no 'scancode_manifestor'
            self.assertFalse('scancode_manifestor' in f)
            #print(f['path'] + ": " + str(f['license_expressions']) )

        self.utils._curate_license(files, "x11", "mit")

        for f in files['included']:
            if f['name'] == "readme.txt":
                # find the file readme.txt, which is licensed under x11 but curated to mit

                # curation, so 'scancode_manifestor' and 'curated_license' in there
                self.assertTrue('scancode_manifestor' in f)
                self.assertTrue('curated_license' in f['scancode_manifestor'])

                # only one original license
                self.assertTrue(len(f['license_expressions']) == 1)

                # original license should be "x11"
                self.assertTrue(f['license_expressions'][0] == "x11")

                # curated license should be "mit"
                self.assertTrue(f['scancode_manifestor']['curated_license'] == "mit")

            else:
                # No curation, so no 'scancode_manifestor'
                #print(json.dumps(f, indent=4))
                self.assertFalse('scancode_manifestor' in f)

        
        
        #print(":: " + str(json.dumps(f, indent=4)))
        
        
if __name__ == '__main__':
    unittest.main()
        
    
