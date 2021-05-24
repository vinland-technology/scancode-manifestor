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

class ManifestorCommands:
    def __init__(self):
    
        self.COMMAND_EXCLUDE_FILE="exclude-files"
        self.COMMAND_SHORT_EXCLUDE_FILE="ef"
        self.COMMAND_INCLUDE_FILE="include-files"
        self.COMMAND_SHORT_INCLUDE_FILE="if"
        self.COMMAND_LIST_INCLUDED="list-included"
        self.COMMAND_LIST_EXCLUDED="list-excluded"
        self.COMMAND_CURATE_FILE="curate-file"
        self.COMMAND_SHORT_CURATE_FILE="cf"
        self.COMMAND_CURATE_LICENSE="curate-license"
        self.COMMAND_SHORT_CURATE_LICENSE="cl"
        self.COMMAND_CURATE_MISSING_LICENSE="curate-missing-license"
        self.COMMAND_SHORT_CURATE_MISSING_LICENSE="cml"
        self.COMMAND_HIDE_LICENSES="hide-licenses"
        self.COMMAND_SHORT_HIDE_LICENSES="hl"
        self.COMMAND_UNHIDE_LICENSES="unhide-licenses"
        self.COMMAND_SHORT_UNHIDE_LICENSES="ul"
        self.COMMAND_SHOW_LICENSES="show-licenses"
        self.COMMAND_SHORT_SHOW_LICENSES="sl"
        self.COMMAND_HIDE_ONLY_LICENSES="hide-only-licenses"
        self.COMMAND_SHORT_HIDE_ONLY_LICENSES="hol"
        self.COMMAND_SHOW_COMMANDS="commands"


        self.INTERACTIVE_COMMANDS = [ self.COMMAND_EXCLUDE_FILE, self.COMMAND_SHORT_EXCLUDE_FILE, self.COMMAND_INCLUDE_FILE, self.COMMAND_SHORT_INCLUDE_FILE, self.COMMAND_LIST_INCLUDED, self.COMMAND_LIST_EXCLUDED, self.COMMAND_CURATE_FILE, self.COMMAND_SHORT_CURATE_FILE, self.COMMAND_CURATE_LICENSE, self.COMMAND_SHORT_CURATE_LICENSE, self.COMMAND_CURATE_MISSING_LICENSE, self.COMMAND_SHORT_CURATE_MISSING_LICENSE, self.COMMAND_HIDE_LICENSES, self.COMMAND_SHORT_HIDE_LICENSES, self.COMMAND_UNHIDE_LICENSES, self.COMMAND_SHORT_UNHIDE_LICENSES, self.COMMAND_SHOW_LICENSES, self.COMMAND_SHORT_SHOW_LICENSES, self.COMMAND_HIDE_ONLY_LICENSES, self.COMMAND_SHORT_HIDE_ONLY_LICENSES, self.COMMAND_SHOW_COMMANDS ]

