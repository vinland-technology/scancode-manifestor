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

import datetime
import getpass
import json
import os

from scancode_manifestor.manifestor_utils import FilterAttribute
import scancode_manifestor.explanations

class MarkdownFormatter:

    def __init__(self, args, utils):
        self.utils = utils
        self.args = args
        self.incl_lic_file = None
        self.excl_lic_file = None
        self.header_cnt = 1

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
            f_expr = "[" + manifestor_map['filter_expr'] + "](#" + manifestor_map['filter_expr'] + ")"
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
    
    def _excluded_files(self, report):
        files = report['files']['excluded']
        h = self._get_header()
        
        res = "# " + h + " Excluded files"
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.EXCLUDED_FILES_EXPLANATION + "*"
            res += "\n\n"
            
        res += "### " + h + ".1 Exclusion filters"
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.EXCLUDED_FILES_FILTER_EXPLANATION + "*"
            res += "\n\n"
        for re_list in report["meta"]["arguments"]["excluded_regexps"]:
            for re in re_list:
                res += str(" * <a name=\"" + re + "\"></a>'" + re + "\n\n" )
                for f in files:
                    if f['type'] == "file":
                        #print("--------")
                        manifestor_map = f['scancode_manifestor']
                        #print("f: " + str(f['path']) + " " + str(f['type']) + " " + str(manifestor_map['filter_type']) + " " + str(manifestor_map['filter_expr']) + "== " + str(re) + "<br>")
                        if f['type'] == 'file':
                            #res+=" file"
                            if manifestor_map['filter_type'] == FilterAttribute.PATH:
                                #res+=" filter"
                                if re == manifestor_map['filter_expr']:
                                    res += "    * " + self._file_url(f) +  "\n\n"
                res += "\n\n"
                
        res += "\n\n"
        res += "### " + h + ".2 Excluded files"
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.EXCLUDED_FILES_FILES_EXPLANATION + "*"
            res += "\n\n"
        for f in files:
            if f['type'] == 'file':
                res += self._excluded_file(f) + "\n\n"
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

    def _included_files(self, report):
        files = report['files']['included']

        h = self._get_header()
        
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


        
    def _license_summary(self, report):
        h = self._get_header()
        res = "# " + h + " Licenses"
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSE_EXPLANATION + "*"
            res += "\n\n"

        # find included files' license
        for f in report['files']['included']:
            self._add_to_lic_file_map(f['scancode_manifestor']['license_key'], f )
        # find excluded files' license
        for f in report['files']['excluded']:
            if 'scancode_manifestor' in f and 'license_key' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['license_key']
            else:
                lic_key = "unknown"
            self._add_to_excl_lic_file_map(str(lic_key), f)
        
            
        # included files
        res += "## " + h + ".1 Licenses for included files"
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSE_INCLDUED_EXPLANATION + "*"
            res += "\n\n"
        for k,v in self.incl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        
        # excluded files
        res += "## " + h + ".2 Licenses for excluded files"
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSE_EXCLDUED_EXPLANATION + "*"
            res += "\n\n"
        for k,v in self.excl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        return res

    def _get_header(self):
        keep = self.header_cnt
        self.header_cnt += 1
        return str(keep)
    
    def _conclusion_summary(self, report):
        if self.args['no_conclusion']:
            return ""
        
        h = self._get_header()
        
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
        uname=os.uname()
        res = "# Scancode manifestor report"
        res += "\n\n"
        res += "## Meta information"
        res += "\n\n"
        res += " * ***date***: " + str(datetime.datetime.now())
        res += "\n\n"
        res += " * ***user***: " + getpass.getuser()
        res += "\n\n"
        res += " * ***os***: " + uname.sysname + " / " + uname.release + " / " + uname.version
        res += "\n\n"
        res += " * ***machine***: " + uname.machine
        res += "\n\n"
        res += " * ***node***: " + uname.nodename
        res += "\n\n"

        res += self._conclusion_summary(report)
        
        res += "\n\n"

        res += self._license_summary(report)
        
        res += "\n\n"

        res += self._excluded_files(report)

        res += "\n\n"

        res += self._included_files(report)

        return res
