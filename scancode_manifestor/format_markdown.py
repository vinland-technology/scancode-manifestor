#!/usr/bin/env python3

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

    def _file_name_url(self, fn):
        return "[" + fn + "](" + fn + ")"

    def _file_url(self, f):
        return self._file_name_url(f['path'])


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
        
        res = "<a name=\"" + scancode_manifestor.explanations.EXCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "# 5 " + scancode_manifestor.explanations.EXCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.EXCLUDED_FILES_EXPLANATION + "*"
            res += "\n\n"
            
        res += "<a name=\"" + scancode_manifestor.explanations.EXCLUDED_FILES_FILTERS_HEADER + "\"></a>\n\n"
        res += "### 5.1 " + scancode_manifestor.explanations.EXCLUDED_FILES_FILTERS_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.EXCLUDED_FILES_FILTERS_EXPLANATION + "*"
            res += "\n\n"
        for re_list in report["meta"]["arguments"]["excluded_regexps"]:
            for re in re_list:
                res += str(" * <a name=\"" + re + "\"></a>" + re + "\n\n" )
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
        res += "<a name=\"" + scancode_manifestor.explanations.EXCLUDED_FILES_FILES_HEADER + "\"></a>\n\n"
        res += "### 5.2 " + scancode_manifestor.explanations.EXCLUDED_FILES_FILES_HEADER
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

        res = "<a name=\"" + scancode_manifestor.explanations.INCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "# 6 " + scancode_manifestor.explanations.INCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.INCLUDED_FILES_EXPLANATION + "*"
            res += "\n\n"
        res += "<a name=\"" + scancode_manifestor.explanations.INCLUDED_FILES_FILES_HEADER + "\"></a>\n\n"
        res += "### 6.1 " + scancode_manifestor.explanations.INCLUDED_FILES_FILES_HEADER
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


    def _add_lic_file_map(self, lic_map, lic, f):
        if lic not in lic_map:
            lic_map[lic] = []
        lic_map[lic].append(f)


        
    def _license_summary(self, report):
        # List files per  license (regardless whether included or excluded)
        combined_license_files = {}
        
        res  = "<a name=\"" + scancode_manifestor.explanations.LICENSES_HEADER + "\"></a>\n\n"
        res += "# 4 " + scancode_manifestor.explanations.LICENSES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSES_EXPLANATION + "*"
            res += "\n\n"

        # find included files' license
        for f in report['files']['included']:
            self._add_to_lic_file_map(f['scancode_manifestor']['license_key'], f )
            self._add_lic_file_map(combined_license_files, f['scancode_manifestor']['license_key'], f['path'])
        # find excluded files' license
        for f in report['files']['excluded']:
            if 'scancode_manifestor' in f and 'license_key' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['license_key']
            else:
                lic_key = "unknown"
            self._add_to_excl_lic_file_map(str(lic_key), f)
            self._add_lic_file_map(combined_license_files, lic_key, f['path'])

        
            
        # all licenses with and files
        res += "<a name=\"" + scancode_manifestor.explanations.LICENSES_ALL_FILES_HEADER + "\"></a>\n\n"
        res += "## 4.1 " + scancode_manifestor.explanations.LICENSES_ALL_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSES_ALL_FILES_EXPLANATION + "*"
            res += "\n\n"
        for k,v in combined_license_files.items():
            res += " * " + str(k)
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_name_url(f)
                res += "\n\n"
            
        # included files
        res += "<a name=\"" + scancode_manifestor.explanations.LICENSES_INCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "## 4.2 " + scancode_manifestor.explanations.LICENSES_INCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSES_INCLDUED_EXPLANATION + "*"
            res += "\n\n"
        for k,v in self.incl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        
        # excluded files
        res += "<a name=\"" + scancode_manifestor.explanations.LICENSES_EXCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "## 4.3 " + scancode_manifestor.explanations.LICENSES_EXCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSES_EXCLDUED_EXPLANATION + "*"
            res += "\n\n"
        for k,v in self.excl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        return res

    def _conclusion_summary(self, report):
        if self.args['no_conclusion']:
            return ""
        
        res = "# 3 Conclusion"
        res += "\n\n"
        res += "## 3.1 Copyrights"
        res += "\n\n"
        for c in report['conclusion']['copyright']:
            res += " * " + str(c)
            res += "\n\n"
        res += "## 3.2 Licenses"
        res += "\n\n"
        res += " * ***Original***: " + report['conclusion']['license_expression_original']
        res += "\n\n"
        res += " * ***Simplified***: " + report['conclusion']['license_expression']

        return res

    def _key_to_str(self, data, key):
        if key in data:
            return str(data[key])
        else:
            return " missing "

    def _header_link(self, header):
        return "[" + header + "](#" + header + ")\n\n"
        
    def format(self, report):
        uname=os.uname()
        res = "# 1 Scancode manifestor report"
        res += "\n\n"
        res += "## 1.1 Table of content"
        res += "\n\n"
        res += " 1 Scancode manifestor report"
        res += "\n\n"
        res += " 2 " + self._header_link(scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT)
        res += " 3 Conclusions\n\n"
        res += " 4 " +   self._header_link(scancode_manifestor.explanations.LICENSES_HEADER)
        res += " 4.1 " + self._header_link(scancode_manifestor.explanations.LICENSES_ALL_FILES_HEADER)
        res += " 4.2 " + self._header_link(scancode_manifestor.explanations.LICENSES_INCLUDED_FILES_HEADER)
        res += " 4.3 " + self._header_link(scancode_manifestor.explanations.LICENSES_EXCLUDED_FILES_HEADER)
        res += " 5 " +   self._header_link(scancode_manifestor.explanations.EXCLUDED_FILES_HEADER)
        res += " 5.1 " +   self._header_link(scancode_manifestor.explanations.EXCLUDED_FILES_FILTERS_HEADER)
        res += " 5.2 " +   self._header_link(scancode_manifestor.explanations.EXCLUDED_FILES_FILES_HEADER)
        res += " 6 " +   self._header_link(scancode_manifestor.explanations.INCLUDED_FILES_HEADER)
        res += " 6.1 " +   self._header_link(scancode_manifestor.explanations.INCLUDED_FILES_FILES_HEADER)
        res += "\n\n"
        res += "# 2 " + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT
        res += "\n\n"
        scan_str = None
        if 'meta' in report:
            meta=report['meta']
            scan_str = " * ***Scancode report file***: " + self._file_name_url(self._key_to_str(meta, 'scancode_report_file'))
            scan_str += "\n\n"
            scan_str += " * ***Tool***: " + self._key_to_str(meta, 'scancode_name')
            scan_str += "\n\n"
            scan_str += " * ***Version***: " + self._key_to_str(meta, 'scancode_version')
            scan_str += "\n\n"
        if scan_str == None:
            scan_str = "*no header section found in Scancode report*"
            scan_str += "\n\n"

        res += scan_str
        
        res += "## Meta information report"
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
        res += "\n\n"

        res += self._conclusion_summary(report)
        
        res += "\n\n"

        res += self._license_summary(report)
        
        res += "\n\n"

        res += self._excluded_files(report)

        res += "\n\n"

        res += self._included_files(report)

        return res
