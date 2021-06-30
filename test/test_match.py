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
 
class TestMatchGeneric(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)
        
    def test_match_path_bad_indata(self):
        f = sample_data.file()

        self.assertRaises(Exception,
                          lambda:self.utils._match_file(None,
                                      FilterAttribute.PATH,
                                      "bonkey.txt",
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                      None,
                                      "bonkey.txt",
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                      "incorrect",
                                      "bonkey.txt",
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                      FilterAttribute.PATH,
                                      None,
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                      FilterAttribute.PATH,
                                      set(),
                                      FilterAction.INCLUDE,
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                      FilterAttribute.PATH,
                                      "bonkey.txt",
                                      None,
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                      FilterAttribute.PATH,
                                      "bonkey.txt",
                                      "incorrect",
                                      FilterModifier.ANY))
    
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                                        FilterAttribute.PATH,
                                                        "bonkey.txt",
                                                        FilterAction.INCLUDE,
                                                        None))
        self.assertRaises(Exception,
                          lambda:self.utils._match_file(f,
                                                        FilterAttribute.PATH,
                                                        "bonkey.txt",
                                                        FilterAction.INCLUDE,
                                                        "incorrect"))
    
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
        
