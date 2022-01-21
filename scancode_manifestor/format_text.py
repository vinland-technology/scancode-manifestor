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

class TextFormatter:

    def __init__(self, args, utils):
        self.utils = utils
        self.args = args

    def format(self, report):
        res = "text report not implemented yet, use markdown instead and use pandoc to create text"

        return res

    
