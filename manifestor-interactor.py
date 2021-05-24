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

import readline
readline.parse_and_bind('tab: complete')

class ManifestorCompleter:
    def __init__(self,manifestor):
        self.manifestor = manifestor

    def complete(self,text,state):
        results =  [x for x in self.manifestor if x.startswith(text)] + [None]
        return results[state]

import readline
readline.parse_and_bind('tab: complete')
#readline.parse_and_bind('set editing-mode vi')



#print("delims: " + str(readline.get_completer_delims()))

def _handle_filter_action(action, files, args):
    tokens = action.split(" ")
    command = tokens[0]
    #print("exclude stuff....: " + command)
    tokens.pop(0)
    #for t in tokens:
    #    print("  expr  : " + t)
    if command == COMMAND_EXCLUDE_FILE:
        args['excluded_regexps'].append(tokens)
    elif command == COMMAND_INCLUDE_FILE:
        args['included_regexps'].append(tokens)

    #DEBUG
    for f in files['included']:
        if "convert-utility" in f['path']:
            print("-- filter: " + str(f['path']))

    # TODO: filter on new reg_exp, not all
    _filter(files, args['included_regexps'], args['excluded_regexps'])

    #DEBUG
    for f in files['included']:
        #print("f: " + str(f))
        #print("f: " + str(type(f)))
        print("f: " + str(f['path']))
        if f['path'].find("convert-utility") != -1:
            print("-- filter: " + str(f['path']))
    
    print("inc: " + str(len(files['included'])))
    print("exc: " + str(len(files['excluded'])))
    return 0

def _parse_action(action, files, args):
    print("parse: \"" + action + "\"")
    if action.startswith("bye"):
        unknown_count = _unknown_licenses(files)
        if unknown_count == 0:
            return 1
        else:
            print("Can't leave with unknown licenses (" + str(unknown_count) + " of them now) ")
    elif action.startswith(COMMAND_LIST_INCLUDED):
        print("Included files:")
        _output_filtered_include(files,
                                 args['hide_files']==False,
                                 args['show_directories'],
                                 sys.stdout,
                                None)
    elif action.startswith(COMMAND_LIST_EXCLUDED):
        print("Excluded files:")
        _output_filtered_exclude(files,
                                 args['hide_files']==False,
                                 args['show_directories'],
                                 sys.stdout,
                                 True,
                                 None)
    elif action.startswith(COMMAND_EXCLUDE_FILE) or \
         action.startswith(COMMAND_INCLUDE_FILE):
        return _handle_filter_action(action, files, args)
    else:
        print("miss...")
        return 2


def _interact(files, args):
    words = INTERACTIVE_COMMANDS
    words += _files_to_list(files)
    completer = ManifestorCompleter(words)
    readline.set_completer_delims(' ')
    readline.set_completer(completer.complete)
    #print("words: " + str(words))

    while True:
        file_info = str(_count_files(files['included'])) + " files included"
        license_info = str(_unknown_licenses(files)) + " unknown licenses"
        print("inc: " + str(len(files['included'])))
        print("exc: " + str(len(files['excluded'])))
        print("[ " + file_info + ", " + license_info + " ]")
        action = input("scancode-manfestor$ ")
        print("You typed: " + action)
        action_result = _parse_action(action.strip(), files, args)
        if action_result == 1:
            return 
