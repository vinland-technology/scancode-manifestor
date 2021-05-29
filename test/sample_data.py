#!/usr/bin/python3

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

def files():
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
