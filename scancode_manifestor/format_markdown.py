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
from scancode_manifestor.manifestor_utils import FilterAttribute

class MarkdownFormatter:

    def __init__(self, utils):
        self.utils = utils
        self.incl_lic_file = None
        self.excl_lic_file = None

    def _file_url(self, f):
        return "[" + f['path'] + "](" + f['path'] + ")"


    def _excluded_file(self, f):
        res = " * " + self._file_url(f)
        res += "\n\n"
        res += "    * ***file type***:" + str(f['file_type']).strip()
        manifestor_map = f['scancode_manifestor']
        if 'filter_type' in manifestor_map:
            res += "\n\n"
            res += "    * ***exclusion cause***:" 
            f_type = manifestor_map['filter_type']
            f_expr = manifestor_map['filter_expr']
            if f_type == FilterAttribute.PATH:
                res += "file name matches \"" +  f_expr + "\""
            elif f_type == FilterAttribute.LICENSE:
                res += "license matches \"" +  f_expr + "\""
            elif f_type == FilterAttribute.COPYRIGHT:
                res += "copyright matches \"" +  f_expr + "\""
            else:
                res += " ERROR - unknown filter type " + str(f_type)
        res += "\n\n"
        return res
    
    def _excluded_files(self, header_cnt, report):
        files = report['files']['excluded']
        h = str(header_cnt)
        res = "# " + h + " Excluded files"
        res += "\n\n"
        res += "### " + h + ".1 Filters"
        res += "\n\n"
        for re_list in report["meta"]["arguments"]["excluded_regexps"]:
            for re in re_list:
                res += str(" * '" + re + "'\n\n")
        res += "\n\n"
        res += "### " + h + ".2 Files"
        res += "\n\n"
        for f in files:
            if f['type'] == 'file':
                res += " * " + self._excluded_file(f) + "\n\n"
        return res

    def _included_file(self, f):
        res = " * " + self._file_url(f)
        res += "\n\n"
        res += "    * ***file type***: " + str(f['file_type']).strip()
        manifestor_map = f['scancode_manifestor']
        c_license = manifestor_map['curated_license']
        res += "\n\n"
        res += "    * ***original license***: " + manifestor_map['license_key']
        res += "\n\n"
        res += "    * ***curated license***: " + c_license 
        res += "\n\n"
        res += "    * ***curation cause***:" 
        if 'curation_type' in manifestor_map:
            c_type = manifestor_map['curation_type']
            c_expr = manifestor_map['curation_expr']
            
            if c_type == 'file':
                res += " file name matches \"" +  c_expr + "\"" 
            else:
                res += " ERROR: missing regexpr unknown curation type " + str(c_type)
        else:
            res += " ERROR: missing c_type in curation"
        return res 

    def _included_files(self, header_cnt, report):
        files = report['files']['included']
        h = str(header_cnt)
        res = "# " + h + " Included files"
        res += "\n\n"
        res += "### " + h + ".1 Files"
        res += "\n\n"
        for f in files:
            if f['type'] == 'file':
                res += self._included_file(f)+ "\n\n"
        return res

    def _add_to_lic_file_map(self, lic, f):
        if self.incl_lic_file == None:
            self.incl_lic_file = {}
        if lic not in self.incl_lic_file:
            self.incl_lic_file[lic] = []
        self.incl_lic_file[lic].append(f)

    def _add_to_excl_lic_file_map(self, lic, f):
        if self.excl_lic_file == None:
            self.excl_lic_file = {}
        if lic not in self.excl_lic_file:
            self.excl_lic_file[lic] = []
        self.excl_lic_file[lic].append(f)


        
    def _license_summary(self, header_cnt, report):
        h = str(header_cnt)
        res = "# " + h + " Licenses"
        res += "\n\n"
        res += "## " + h + ".1 Licenses for included files"
        res += "\n\n"
        for f in report['files']['included']:
            self._add_to_lic_file_map(f['scancode_manifestor']['license_key'], f )
        for k,v in self.incl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        
        res += "## " + h + ".2 Licenses for excluded files"
        res += "\n\n"
        for f in report['files']['excluded']:
            if 'scancode_manifestor' in f and 'license_key' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['license_key']
            else:
                lic_key = "unknown"
            self._add_to_excl_lic_file_map(str(lic_key), f)
        for k,v in self.excl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        return res
    
    def _conclusion_summary(self, header_cnt,report):
        h = str(header_cnt)
        res = "# " + h + " Conclusion"
        res += "\n\n"
        res += "## " + h + ".1 Copyrights"
        res += "\n\n"
        for c in report['conclusion']['copyright']:
            res += " * " + str(c)
            res += "\n\n"
        res += "## " + h + ".2 Licenses"
        res += "\n\n"
        res += " * ***Original***: " + report['conclusion']['license_expression_original']
        res += "\n\n"
        res += " * ***Simplified***: " + report['conclusion']['license_expression']

        return res
    
    def format(self, report):
        res = "# Report from ..."

        res += "\n\n"

        res += self._conclusion_summary(1, report)
        
        res += "\n\n"

        res += self._license_summary(2, report)
        
        res += "\n\n"

        res += self._excluded_files(3, report)

        res += "\n\n"

        res += self._included_files(4, report)

        return res
