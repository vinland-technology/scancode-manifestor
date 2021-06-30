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

def sample_file(name, path, licenses):
    file = {}
    file['name'] = name
    file['type'] = "file"
    file['path'] = path + "/" + name
    file['license_expressions'] = []
    for l in licenses:
        file['license_expressions'].append(l)

    return file

def sample_transformed_file(name, path, licenses):
    file = {}
    file['name'] = name
    file['type'] = "file"
    file['path'] = path + "/" + name
    file['license_key'] = licenses

    return file

def sample_dir(name):
    file = {}
    file['name'] = name
    file['path'] = name
    file['type'] = "directory"
    return file

def files():
    ifiles = []
    ifiles.append(sample_file("bonkey.txt", "git/dit/", ["gpl-2.0-or-later", "gpl-3.0-or-later"]))
    ifiles.append(sample_file("monkey.txt", "git/dit/", ["gpl-2.0-or-later"]))
    ifiles.append(sample_file("donkey.txt", "git/dit/", ["bsd-new"]))
    ifiles.append(sample_file("flunkey.txt", "git/dit/", ["mit"]))
    ifiles.append(sample_file("splungy.txt", "git/dit/", ["gpl-3.0-only"]))
    ifiles.append(sample_file("readme.txt", "otherdir", ["x11"]))

    efiles= []

    files = {}
    files['included'] = ifiles
    files['excluded'] = efiles
    
    return files

def transformed_files():
    ifiles = []
    ifiles.append(sample_transformed_file("bonkey.txt", "git/dit/", "gpl-2.0-or-later and gpl-3.0-or-later"))
    ifiles.append(sample_transformed_file("monkey.txt", "git/dit/", "gpl-2.0-or-later"))
    ifiles.append(sample_transformed_file("donkey.txt", "git/dit/", "bsd-new"))
    ifiles.append(sample_transformed_file("flunkey.txt", "git/dit/", "mit"))
    ifiles.append(sample_transformed_file("splungy.txt", "git/dit/", "gpl-3.0-only"))
    ifiles.append(sample_transformed_file("readme.txt", "otherdir", "x11"))

    efiles= []

    files = {}
    files['included'] = ifiles
    files['excluded'] = efiles
    
    return files

def file():
    return sample_file("bonkey.txt", "git/dit/", ["gpl-2.0-or-later", "gpl-3.0-or-later"])

def dir():
    return sample_dir("git/dit")

