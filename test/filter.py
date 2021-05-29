#!/usr/bin/python3


import unittest


import scancode_manifestor.manifestor_utils
from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterAction
from scancode_manifestor.manifestor_utils import FilterModifier
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils

class TestFilterGeneric(unittest.TestCase):

    def setUp(self):
        self.logger = ManifestLogger(False)
        self.utils = ManifestUtils(self.logger)
        
    
    def test_include_path(self):

        files = sample_data()

        assert len(files['included']) == 5
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 3
        assert len(files['excluded']) == 2

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 3
        assert len(files['excluded']) == 2


    def test_exclude_path(self):

        files = sample_data()

        assert len(files['included']) == 5
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 2
        assert len(files['excluded']) == 3

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "onkey",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 2
        assert len(files['excluded']) == 3


    def test_exclude_license(self):

        files = sample_data()

        assert len(files['included']) == 5
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "mit",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)


        assert len(files['included']) == 4
        assert len(files['excluded']) == 1

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.PATH,
                                   "mit",
                                   FilterAction.EXCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 4
        assert len(files['excluded']) == 1


    def test_include_license(self):

        files = sample_data()

        assert len(files['included']) == 5
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "mit",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)


        assert len(files['included']) == 1
        assert len(files['excluded']) == 4

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "mit",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)

        assert len(files['included']) == 1
        assert len(files['excluded']) == 4


    def test_include_only_license(self):

        files = sample_data()

        assert len(files['included']) == 5
        assert len(files['excluded']) == 0

        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "gpl-2.0-or-later",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ANY)


        assert len(files['included']) == 2
        assert len(files['excluded']) == 3

        files = sample_data()

        # try include same files, no change
        self.utils._filter_generic(files,
                                   FilterAttribute.LICENSE,
                                   "gpl-2.0-or-later",
                                   FilterAction.INCLUDE,
                                   FilterModifier.ONLY)

        assert len(files['included']) == 1
        assert len(files['excluded']) == 4


        
    
def sample_file(name, path, licenses):
    file = {}
    file['name'] = name
    file['path'] = path + "/" + name
    file['licenses'] = []
    for l in licenses:
        lic = {}
        lic['key'] = l
        file['licenses'].append(lic)

    return file

def sample_data():
    ifiles = []
    ifiles.append(sample_file("bonkey.txt", "git/dit/", ["gpl-2.0-or-later", "gpl-3.0-or-later"]))
    ifiles.append(sample_file("monkey.txt", "git/dit/", ["gpl-2.0-or-later"]))
    ifiles.append(sample_file("donkey.txt", "git/dit/", ["bsd-new"]))
    ifiles.append(sample_file("flunkey.txt", "git/dit/", ["mit"]))
    ifiles.append(sample_file("splungy.txt", "git/dit/", ["gpl-3.0-only"]))

    efiles= []

    files = {}
    files['included'] = ifiles
    files['excluded'] = efiles
    
    return files

if __name__ == '__main__':
    unittest.main()
