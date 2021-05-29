#!/usr/bin/python3


import unittest


import scancode_manifestor.manifestor_utils
from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterAction
from scancode_manifestor.manifestor_utils import FilterModifier
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils

import sample_data

class TestMatchGeneric(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)
        
    
    def test_match_path(self):
        f = sample_data.file()

        assert self.utils._match_file(f,
                                      FilterAttribute.PATH,
                                      "bonkey.txt",
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY)

        assert not self.utils._match_file(f,
                                          FilterAttribute.PATH,
                                          "plonkey.txt",
                                          FilterAction.INCLUDE,
                                          FilterModifier.ANY)
        
        
    def test_match_license(self):
        f = sample_data.file()

        assert self.utils._match_file(f,
                                      FilterAttribute.LICENSE,
                                      "gpl-2.0-or-later",
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY)

        # file has both gpl3 and gpl2, thus false
        assert not self.utils._match_file(f,
                                      FilterAttribute.LICENSE,
                                      "gpl-2.0-or-later",
                                      FilterAction.INCLUDE,
                                      FilterModifier.ONLY)

        assert not self.utils._match_file(f,
                                          FilterAttribute.LICENSE,
                                          "bsd-4-Clause",
                                          FilterAction.INCLUDE,
                                          FilterModifier.ANY)


        
        


if __name__ == '__main__':
    unittest.main()
        
