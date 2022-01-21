#!/usr/bin/env python3

# /usr/bin/python3

###################################################################
#
# Scancode report -> manifest creator
#
# SPDX-FileCopyrightText: 2021 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
###################################################################

import json

class JSONFormatter:

    def __init__(self, args, utils):
        self.utils = utils
        self.args = args

    def format(self, report):
        return str(json.dumps(report))

    def format_copyrights(self, copyrights):
        value = []
        key = "copyrightText"
        for c_line in copyrights:
            value.append(c_line + "\n")
        return json.dumps({ key:"".join(value) })
