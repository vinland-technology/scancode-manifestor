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
import subprocess
import sys

import scancode_manifestor.manifestor_utils

class ManifestorCompleter:
    def __init__(self,manifestor):
        self.manifestor = manifestor

    def complete(self,text,state):
        results =  [x for x in self.manifestor if x.startswith(text)] + [None]
        return results[state]


class ManifestorInteractor:
    def __init__(self, commands, utils, logger):
        self.commands = commands
        self.utils = utils
        self.logger = logger

    def _curate_missing_license(self, action, files, args):
        self.logger.verbose("--------- CURATE LICENSE -----")
        arguments = self._action_arguments(action)
        if len(arguments) < 1:
            self.logger.error("You must supply a license to curate with")
            return 2

        lic = None
        for curation in arguments:
            if lic == None:
                lic = curation
            else:
                lic += " and " + curation
        args['missing_license_curation']=lic

    def _curated_info(self, files, args):
        transformed = self.utils._transform_files(files)
        self.utils._curate(transformed, args['file_curations'], args['license_curations'], args['missing_license_curation'])

        curated = {}
        curated['files'] = transformed
        curated['included_count'] = self.utils._count_files_transformed(transformed['included'])
        curated['excluded_count'] = self.utils._count_files_transformed(transformed['excluded'])
        curated['unknown_count'] = self.utils._unknown_license_count_transformed(transformed['included'])
        curated['licenses'] = self.utils._licenses_in_transformed(transformed['included'])
        return curated
        
    def _prompt(self, files, args):
        curated = self._curated_info(files, args)
        
        inc_file_info    = str(curated['included_count']) + " files included" 
        exc_file_info    = " (" + str(curated['excluded_count']) + " excluded)" 
        known_license_info = str(len(curated['licenses']))  + " licenses"
        unknown_license_info = " (" + str(curated['unknown_count'])  + " files with unknown)"
        license_info = known_license_info + unknown_license_info
        prompt = "[ " + inc_file_info + exc_file_info + " | " + license_info + " ]"
        prompt += "\n" + " -- scancode-manfestor-interactive-shell$ "
        return prompt
        
    def _handle_filter_action(self, action, files, args):
        tokens = action.split(" ")
        command = tokens[0]
        #print("exclude stuff....: " + command)
        tokens.pop(0)
        #for t in tokens:
        #    print("  expr  : " + t)
        if command == self.commands.COMMAND_EXCLUDE_FILE:
            args['excluded_regexps'].append(tokens)
        elif command == self.commands.COMMAND_INCLUDE_FILE:
            args['included_regexps'].append(tokens)

        # TODO: filter on new reg_exp, not all
        self.utils._filter(files, args['included_regexps'], args['excluded_regexps'])

        #print("inc: " + str(len(files['included'])))
        #print("exc: " + str(len(files['excluded'])))
        return 0

    def _parse_action(self, action, files, args):
        self.logger.verbose("parse: \"" + action + "\"")
        if action.startswith("bye"):
            curated = self._curated_info(files, args)
            unknown_count = curated['unknown_count']
            if unknown_count == 0:
                return 1
            else:
                print("Can't leave with unknown licenses (" + str(unknown_count) + " of them now) ")
            exit (0)
                
        elif action.startswith(self.commands.COMMAND_LIST_INCLUDED):
            print("Included files:")
            self.utils._output_filtered_include(files,
                                                args['hide_files']==False,
                                                args['show_directories'],
                                                sys.stdout,
                                                self.utils._hiders(args))
        elif action.startswith(self.commands.COMMAND_LIST_EXCLUDED):
            print("Excluded files:")
            self.utils._output_filtered_exclude(files,
                                                args['hide_files']==False,
                                                args['show_directories'],
                                                sys.stdout,
                                                self.utils._hiders(args))
        elif action.startswith(self.commands.COMMAND_EXCLUDE_FILE) or \
             action.startswith(self.commands.COMMAND_INCLUDE_FILE):
            return self._handle_filter_action(action, files, args)
        elif action.startswith(self.commands.COMMAND_CURATE_MISSING_LICENSE) or \
             action.startswith(self.commands.COMMAND_SHORT_CURATE_MISSING_LICENSE):
            return self._curate_missing_license(action, files, args)
        elif action.startswith(self.commands.COMMAND_HIDE_LICENSES) or \
             action.startswith(self.commands.COMMAND_SHORT_HIDE_LICENSES):
            return self._add_hide(args, self._action_arguments(action))
        elif action.startswith(self.commands.COMMAND_UNHIDE_LICENSES) or \
             action.startswith(self.commands.COMMAND_SHORT_UNHIDE_LICENSES):
            return self._unhide(args, self._action_arguments(action))
        elif action.startswith(self.commands.COMMAND_SHOW_LICENSES) or \
             action.startswith(self.commands.COMMAND_SHORT_SHOW_LICENSES):
            return self._add_show(args, self._action_arguments(action))
        elif action.startswith(self.commands.COMMAND_OPEN_FILE):
            print("OPEN FILE...." + str(action))
            for f in self._action_arguments(action):
                res = subprocess.run(["less " + f], shell=True)
        elif action.startswith(self.commands.COMMAND_SHOW_COMMANDS):
            print("Commands:")
            for command in self.commands.INTERACTIVE_COMMANDS:
                print(" " + str(command))
        else:
            self.logger.error("\"" + action.split(" ")[0] + "\" is not a command..... ignoring it")
            return 2

    def _add_hide(self, args, licenses):
        for arg in licenses:
            args['hide_licenses'].append([arg])
            if arg in args['show_licenses']:
                args['show_licenses'].remove(arg)
            if [arg] in args['show_licenses']:
                args['show_licenses'].remove([arg])
            
        self.logger.verbose("args['show_licenses']:" + str(args['show_licenses']))
        self.logger.verbose("args['hide_licenses']:" + str(args['hide_licenses']))
        
    def _unhide(self, args, licenses):
        for arg in licenses:
            if arg in args['hide_licenses']:
                args['hide_licenses'].remove(arg)
            if [arg] in args['hide_licenses']:
                args['hide_licenses'].remove([arg])
            
        self.logger.verbose("args['show_licenses']:" + str(args['show_licenses']))
        self.logger.verbose("args['hide_licenses']:" + str(args['hide_licenses']))
        
    def _add_show(self, args, licenses):
        for arg in licenses:
            args['show_licenses'].append([arg])
            if arg in args['hide_licenses']:
                args['hide_licenses'].remove(arg)
            if [arg] in args['hide_licenses']:
                args['hide_licenses'].remove([arg])
            
        self.logger.verbose("args['show_licenses']:" + str(args['show_licenses']))
        self.logger.verbose("args['hide_licenses']:" + str(args['hide_licenses']))
        
    def _action_arguments(self, action):
        tokens = action.split(" ")
        tokens.pop(0)
        return tokens
        
    def _action_command(self, action):
        tokens = action.split(" ")
        return tokens[0]
        
    def _interact(self, files, args):
        words = self.commands.INTERACTIVE_COMMANDS.copy()
        words += self.utils._files_to_list(files)
        completer = ManifestorCompleter(words)
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(' ')
        readline.set_completer(completer.complete)
        #print("words: " + str(words))

        while True:
            prompt = self._prompt(files, args)
            action = input(prompt)
            self.logger.verbose("You typed: " + action)
            action_result = self._parse_action(action.strip(), files, args)
            if action_result == 1:
                return 
