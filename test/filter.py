#!/usr/bin/python3


import unittest


import scancode_manifestor.manifestor_utils
from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterAction
from scancode_manifestor.manifestor_utils import FilterModifier
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils

import sample_data

class TestFilterGeneric(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)
        
    def test_include_bad_indata(self):
        files = sample_data.files()

        # None as list
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(None,
                                                            FilterAttribute.PATH,
                                                            "onkey",
                                                            FilterAction.INCLUDE,
                                                            FilterModifier.ANY))

        # Existing but faulty list
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic([],
                                                            FilterAttribute.PATH,
                                                            "onkey",
                                                            FilterAction.INCLUDE,
                                                            FilterModifier.ANY))
        # No filter 
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(files,
                                                            None,
                                                            "onkey",
                                                            FilterAction.INCLUDE,
                                                            FilterModifier.ANY))
        
        # Incorrect filter 
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(files,
                                                            "incrorect indata",
                                                            "onkey",
                                                            FilterAction.INCLUDE,
                                                            FilterModifier.ANY))
        
        # Incorrect filter action
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(files,
                                                            FilterAttribute.PATH,
                                                            "onkey",
                                                            None,
                                                            FilterModifier.ANY))
        
        # Incorrect filter action
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(files,
                                                            FilterAttribute.PATH,
                                                            "onkey",
                                                            "incorrect data",
                                                            FilterModifier.ANY))
        # None as modifier
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(files,
                                                            FilterAttribute.PATH,
                                                            "onkey",
                                                            FilterAction.INCLUDE,
                                                            None))
        # Incorrect modifier
        self.assertRaises(Exception,
                          lambda:self.utils._filter_generic(files,
                                                            FilterAttribute.PATH,
                                                            "onkey",
                                                            FilterAction.INCLUDE,
                                                            "incorrect data"))
        
    def test_include_path(self):

        files = sample_data.files()

        assert len(files['included']) == 6
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 3
        assert len(files['excluded']) == 3

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 3
        assert len(files['excluded']) == 3


    def test_exclude_path(self):

        files = sample_data.files()

        assert len(files['included']) == 6
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 3
        assert len(files['excluded']) == 3

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 3
        assert len(files['excluded']) == 3


    def test_exclude_license(self):

        files = sample_data.files()

        assert len(files['included']) == 6
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "mit",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)


        assert len(files['included']) == 5
        assert len(files['excluded']) == 1

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "mit",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 5
        assert len(files['excluded']) == 1


    def test_include_license(self):

        files = sample_data.files()

        assert len(files['included']) == 6
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "mit",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)


        assert len(files['included']) == 1
        assert len(files['excluded']) == 5

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "mit",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 1
        assert len(files['excluded']) == 5


    def test_include_only_license(self):

        files = sample_data.files()

        assert len(files['included']) == 6
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "gpl-2.0-or-later",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)


        assert len(files['included']) == 2
        assert len(files['excluded']) == 4

        files = sample_data.files()

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "gpl-2.0-or-later",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ONLY)

        assert len(files['included']) == 1
        assert len(files['excluded']) == 5


        
    

if __name__ == '__main__':
    unittest.main()
