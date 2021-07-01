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
import sys

from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterAttribute_to_string
from scancode_manifestor.manifestor_utils import FilterAction_to_string
import scancode_manifestor.explanations


class MarkdownFormatter:

    def __init__(self, args, utils):
        self.utils = utils
        self.args = args
        self.incl_lic_file = None
        self.excl_lic_file = None

    def _collapse_begin(self, open=False, message="Click to expand"):
        open_string = ""
        
        if open:
            open_string = " open"
            
        return "<details" + open_string +  ">\n<summary>" + message + "</summary>\n\n"
        
    def _collapse_begin_open(self, message="Click to collapse"):
        return self._collapse_begin(True, message)
        
    def _collapse_end(self):
        return "</details>\n"
        
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
            #print("5.2  " + str(f['path']) + " " + str(manifestor_map['filter_expr']), file=sys.stderr)
            res += "\n\n"
            f_action_s = FilterAction_to_string(manifestor_map['filter_action'])
            f_type_s = FilterAttribute_to_string(manifestor_map['filter_type'])
            f_type = manifestor_map['filter_type']
            f_expr = "[" + manifestor_map['filter_expr'] + "](#" + manifestor_map['filter_expr'] + ")"

            #res += "    * ***filter type***: " + str(manifestor_map['filter_type']) + "\n\n"
            #res += "    * ***filter type***: " + f_type_s + "\n\n"
            #res += "    * ***filter action***: " + f_action_s + "\n\n"
            #res += "    * ***filter expr***: " + f_expr + "\n\n"

            exclusion_string = " matches "
            if f_action_s == "include":
                exclusion_string = " does not match "
            res += "    * ***filter information***: " + f_type_s + " excluded since it " + exclusion_string + f_expr
            
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
        res += self._collapse_begin()        
        for re_list in report["meta"]["arguments"]["excluded_regexps"]:
            for re in re_list:
                res += str(" * <a name=\"" + re + "\">" + re + "</a>\n\n" )
                for f in files:
                    if f['type'] == "file":
                        #print("--------")
                        manifestor_map = f['scancode_manifestor']
                        #print("f: " + str(f['path']) + " " + str(f['type']) + " " + str(manifestor_map['filter_type']) + " " + str(manifestor_map['filter_expr']) + "== " + str(re) + "<br>")
                        if f['type'] == 'file':
                            #res += " file"
                            if manifestor_map['filter_type'] == FilterAttribute.PATH:
                                #res+=" filter"
                                if re == manifestor_map['filter_expr']:
                                    res += "    * " + self._file_url(f) +  "\n\n"
                res += "\n\n"
        res += self._collapse_end()        
                
        res += "\n\n"
        res += "<a name=\"" + scancode_manifestor.explanations.EXCLUDED_FILES_FILES_HEADER + "\"></a>\n\n"
        res += "### 5.2 " + scancode_manifestor.explanations.EXCLUDED_FILES_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.EXCLUDED_FILES_FILES_EXPLANATION + "*"
            res += "\n\n"
        res += self._collapse_begin()        
        for f in files:
            if f['type'] == 'file':
                res += self._excluded_file(f) + "\n\n"
        res += self._collapse_end()        

        return res

    def _included_file(self, f, indent=""):
        res = indent + " * " + self._file_url(f)
        res += "\n\n"
        res += indent + "    * ***file type***: " + str(f['file_type']).strip()
        manifestor_map = f['scancode_manifestor']
        res += "\n\n"
        res += indent + "    * ***original license***: " + str(manifestor_map['license_key'])
        res += "\n\n"

        # filter information
        if 'filter_type' in manifestor_map:
            #print("6.2  " + str(f['path']) + " " + str(manifestor_map['filter_expr']), file=sys.stderr)
            res += "\n\n"
            f_action_s = FilterAction_to_string(manifestor_map['filter_action'])
            f_type_s = FilterAttribute_to_string(manifestor_map['filter_type'])
            f_type = manifestor_map['filter_type']
            f_expr = "[" + manifestor_map['filter_expr'] + "](#" + manifestor_map['filter_expr'] + ")"

            #res += "    * ***filter type***: " + str(manifestor_map['filter_type']) + "\n\n"
            #res += "    * ***filter type***: " + f_type_s + "\n\n"
            #res += "    * ***filter action***: " + f_action_s + "\n\n"
            #res += "    * ***filter expr***: " + f_expr + "\n\n"

            inclusion_string = " matches "
            if f_action_s == "exclude":
                inclusion_string = " does not match "
            res += indent + "    * ***filter information***: " + f_type_s + " included since it " + inclusion_string + f_expr
            res += "\n\n"
        else:
            res += indent + "    * ***filter information***: included by default\n\n"
            
        # curation information
        if 'curated_license' in manifestor_map:
            c_license = manifestor_map['curated_license']
            res += indent + "    * ***curated license***: " + c_license 
            res += "\n\n"
            res += indent + "    * ***curation reason***:" 
            if 'curation_type' in manifestor_map:
                #print(str(manifestor_map))
                c_type = manifestor_map['curation_type']
                c_expr = manifestor_map['curation_expr']

                if c_type == 'file':
                    res += " file name matches \"" +  c_expr + "\"" 
                elif c_type == 'license':
                    if c_expr == "[]":
                        res += " missing license curation"
                    else:
                        res += " license name matches \"" +  c_expr + "\"" 
                else:
                    res += " ERROR: missing regexpr unknown curation type " + str(c_type)
            else:
                res += " ERROR: missing c_type in curation"
        else:
            pass
        return res 

    def _curated_files(self, report):
        files = report['files']['included']
        res = "<a name=\"" + scancode_manifestor.explanations.CURATED_FILES_HEADER + "\"></a>\n\n"
        res += "# 7 " + scancode_manifestor.explanations.CURATED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.CURATED_FILES_EXPLANATION + "*"
            res += "\n\n"
        res += "<a name=\"" + scancode_manifestor.explanations.CURATED_FILES_FILE_HEADER + "\"></a>\n\n"
        res += "### 7.1 " + scancode_manifestor.explanations.CURATED_FILES_FILE_HEADER
        res += "\n\n"
        
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.CURATED_FILES_FILE_EXPLANATION + "*"
            res += "\n\n"
        res += "\n\n"
        res += self._collapse_begin()

        for curation in report['meta']['arguments']['file_curations']:
            curation_expr = curation[:-1]
            curation_license = curation[-1]
            res += " * " + str(curation_expr) + "\n\n"
            for f in files:
                if f['type'] == 'file':
                    assert 'scancode_manifestor' in f
                    manifestor_map = f['scancode_manifestor']
                    if 'curated_license' in manifestor_map:
                        if manifestor_map['curated_license'] == curation_license:
                            c_license = manifestor_map['curated_license']
                            o_license = manifestor_map['license_key']
                            c_type = manifestor_map['curation_type']
                            c_expr = manifestor_map['curation_expr']
                            if c_type == 'file':
                                res += "    * " + self._file_name_url(f['path']) + "\n\n"
                                res += "        * ***original license:*** " + o_license + "\n\n" 
                                res += "        * ***curated license:*** \"" +  curation_license + "\n\n" 
                    
        res += self._collapse_end()        

        res += "<a name=\"" + scancode_manifestor.explanations.CURATED_FILES_MISSING_HEADER + "\"></a>\n\n"
        res += "### 7.2 " + scancode_manifestor.explanations.CURATED_FILES_MISSING_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.CURATED_FILES_MISSING_EXPLANATION + "*"
            res += "\n\n"
        res += self._collapse_begin()        
        curation_license = report['meta']['arguments']['missing_license_curation']
        for f in files:
            if f['type'] == 'file':
                assert 'scancode_manifestor' in f
                manifestor_map = f['scancode_manifestor']
                if 'curated_license' in manifestor_map:
                    license_key = manifestor_map['license_key']
                    if license_key == "None" or license_key == None:
                        #print("f: " + f['path'] + " ==> \"" + str(license_key) + "\"", file=sys.stderr)
                        c_license = manifestor_map['curated_license']
                        o_license = manifestor_map['license_key']
                        c_type = manifestor_map['curation_type']
                        c_expr = manifestor_map['curation_expr']
                        #print("   \"" + c_type + "\"", file=sys.stderr)
                        #print("   \"" + c_expr + "\"", file=sys.stderr)
                        if c_type == 'license' and c_expr == "[]":
                            res += " * " + self._file_name_url(f['path']) + "\n\n"
                            res += "     * ***curated license:*** \"" +  curation_license + "\"\n\n" 
        res += self._collapse_end()        

        return res
        

    def _included_files(self, report):
        files = report['files']['included']

        res = "<a name=\"" + scancode_manifestor.explanations.INCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "# 6 " + scancode_manifestor.explanations.INCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.INCLUDED_FILES_EXPLANATION + "*"
            res += "\n\n"
            
        res += "<a name=\"" + scancode_manifestor.explanations.INCLUDED_FILES_FILTERS_HEADER + "\"></a>\n\n"
        res += "### 6.1 " + scancode_manifestor.explanations.INCLUDED_FILES_FILTERS_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.INCLUDED_FILES_FILTERS_EXPLANATION + "*"
            res += "\n\n"
        res += self._collapse_begin()

        # Iterate through all included regexpes
        for re_list in report["meta"]["arguments"]["included_regexps"]:
            for re in re_list:
                res += str(" * <a name=\"" + re + "\"></a>" + re + "\n\n" )
                for f in files:
                    if f['type'] == "file":
                        #print("--------")
                        manifestor_map = f['scancode_manifestor']
                        if f['type'] == 'file':
                            #res += " file"
                            if 'filter_type' in manifestor_map and  manifestor_map['filter_type'] == FilterAttribute.PATH:
                                #res+=" filter"
                                if re == manifestor_map['filter_expr']:
                                    res += "    * " + self._file_url(f) +  "\n\n"
                res += "\n\n"
        # Find all files neither included or excluded
        res += str(" * Included by default (not excluded)\n\n" )
        for f in files:
            if f['type'] == "file":
                #print("--------")
                manifestor_map = f['scancode_manifestor']
                if f['type'] == 'file':
                    #res += " file"
                    if 'filter_type' not in manifestor_map:
                        #res += "    * " + self._file_url(f) +  "\n\n"
                        res += self._included_file(f, "    ") +  "\n\n"
        
        res += self._collapse_end()        

        res += "<a name=\"" + scancode_manifestor.explanations.INCLUDED_FILES_FILES_HEADER + "\"></a>\n\n"
        res += "### 6.2 " + scancode_manifestor.explanations.INCLUDED_FILES_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.INCLUDED_FILES_FILES_EXPLANATION + "*"
            res += "\n\n"
        res += self._collapse_begin()        
        for f in files:
            if f['type'] == 'file':
                res += self._included_file(f)+ "\n\n"
        res += self._collapse_end()        

        return res

    def _add_to_lic_file_map(self, f):
        lic = f['scancode_manifestor']['license_key']
        #print("Add lic for: " + str(f['path']) + "  => " + str(lic))
        if lic == None:
            lic = f['scancode_manifestor']['curated_license']
        if lic == None:
            print("still lic == None")
            exit(0)
            
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
            self._add_to_lic_file_map(f )
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
        res += self._collapse_begin()
        for k,v in combined_license_files.items():
            res += " * " + str(k)
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_name_url(f)
                res += "\n\n"
        res += self._collapse_end()
            
        # included files
        res += "<a name=\"" + scancode_manifestor.explanations.LICENSES_INCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "## 4.2 " + scancode_manifestor.explanations.LICENSES_INCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSES_INCLDUED_EXPLANATION + "*"
            res += "\n\n"
        res += self._collapse_begin_open()
        for k,v in self.incl_lic_file.items():
            res += " * " + str(k)
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        res += self._collapse_end()
        
        # excluded files
        res += "<a name=\"" + scancode_manifestor.explanations.LICENSES_EXCLUDED_FILES_HEADER + "\"></a>\n\n"
        res += "## 4.3 " + scancode_manifestor.explanations.LICENSES_EXCLUDED_FILES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.LICENSES_EXCLDUED_EXPLANATION + "*"
            res += "\n\n"
        res += self._collapse_begin()
        for k,v in self.excl_lic_file.items():
            res += " * " + k
            res += "\n\n"
            for f in v:
                res += "    * " + self._file_url(f)
                res += "\n\n"
        res += self._collapse_end()
        return res
    
    def _conclusion_summary(self, report):
        if self.args['no_conclusion']:
            return ""
        
        res = "<a name=\"" + scancode_manifestor.explanations.CONCLUSION_HEADER + "\"></a>\n\n"
        res += "# 3 " + scancode_manifestor.explanations.CONCLUSION_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.CONCLUSION_EXPLANATION + "*"
            res += "\n\n"
            
        res += "<a name=\"" + scancode_manifestor.explanations.CONCLUSION_COPYRIGHTS_HEADER + "\"></a>\n\n"
        res += "## 3.1 "  + scancode_manifestor.explanations.CONCLUSION_COPYRIGHTS_HEADER
        res += "\n\n"
        res += self._collapse_begin(False, "Click to expand list of copyright holders")
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.CONCLUSION_COPYRIGHTS_EXPLANATION + "*"
            res += "\n\n"
        for c in report['conclusion']['copyright']:
            res += " * " + str(c)
            res += "\n\n"
        res += self._collapse_end()
        res += "*Note: the copyright holders listed here may not be complete*"
        res += "\n\n"

        res += "<a name=\"" + scancode_manifestor.explanations.CONCLUSION_LICENSES_HEADER + "\"></a>\n\n"
        res += "## 3.2 "  + scancode_manifestor.explanations.CONCLUSION_LICENSES_HEADER
        res += "\n\n"
        if self.args['add_explanations']:
            res += "*" + scancode_manifestor.explanations.CONCLUSION_LICENSES_EXPLANATION + "*"
            res += "\n\n"
        res += " * ***Original***: " + str(report['conclusion']['license_expression_original'])
        res += "\n\n"
        res += " * ***Simplified***: " + str(report['conclusion']['license_expression'])
        res += "\n\n"

        #res += "## 7.3 "  + scancode_manifestor.explanations.CONCLUSION_INCLUDED_LICENSES_HEADER
        #res += "\n\n"
        #if self.args['add_explanations']:
        #    res += "*" + scancode_manifestor.explanations.CONCLUSION_INCLUDED_LICENSES_EXPLANATION + "*"
        #    res += "\n\n"
        #for k,v in self.incl_lic_file.items():
        #    res += " * " + str(k)
        #    res += "\n\n"

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
        res += " 2.1 " + self._header_link(scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_SCANCODE)
        res += " 2.2 " + self._header_link(scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_META)
        res += " 2.3 " + self._header_link(scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_SETTINGS)
        res += " 3 " +   self._header_link(scancode_manifestor.explanations.CONCLUSION_HEADER)
        res += " 3.1 " +   self._header_link(scancode_manifestor.explanations.CONCLUSION_COPYRIGHTS_HEADER)
        res += " 3.2 " +   self._header_link(scancode_manifestor.explanations.CONCLUSION_LICENSES_HEADER)
        #res += " 7.3 " +   self._header_link(scancode_manifestor.explanations.CONCLUSION_INCLUDED_LICENSES_HEADER)
        res += " 4 " +   self._header_link(scancode_manifestor.explanations.LICENSES_HEADER)
        res += " 4.1 " + self._header_link(scancode_manifestor.explanations.LICENSES_ALL_FILES_HEADER)
        res += " 4.2 " + self._header_link(scancode_manifestor.explanations.LICENSES_INCLUDED_FILES_HEADER)
        res += " 4.3 " + self._header_link(scancode_manifestor.explanations.LICENSES_EXCLUDED_FILES_HEADER)
        res += " 5 " +   self._header_link(scancode_manifestor.explanations.EXCLUDED_FILES_HEADER)
        res += " 5.1 " +   self._header_link(scancode_manifestor.explanations.EXCLUDED_FILES_FILTERS_HEADER)
        res += " 5.2 " +   self._header_link(scancode_manifestor.explanations.EXCLUDED_FILES_FILES_HEADER)
        res += " 6 " +   self._header_link(scancode_manifestor.explanations.INCLUDED_FILES_HEADER)
        res += " 6.1 " +   self._header_link(scancode_manifestor.explanations.INCLUDED_FILES_FILTERS_HEADER)
        res += " 6.2 " +   self._header_link(scancode_manifestor.explanations.INCLUDED_FILES_FILES_HEADER)
        res += " 7 " +   self._header_link(scancode_manifestor.explanations.CURATED_FILES_HEADER)
        res += " 7.1 " +   self._header_link(scancode_manifestor.explanations.CURATED_FILES_FILE_HEADER)
        res += " 7.1 " +   self._header_link(scancode_manifestor.explanations.CURATED_FILES_MISSING_HEADER)
        res += "\n\n"
        res += "<a name=\"" + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT + "\"></a>\n\n"
        res += "# 2 " + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT
        res += "\n\n"
        res += "<a name=\"" + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_SCANCODE + "\"></a>\n\n"
        res += "## 2.1 " + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_SCANCODE
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
        
        res += "<a name=\"" + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_META + "\"></a>\n\n"
        res += "## 2.2 " + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_META
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

        res += "<a name=\"" + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_SETTINGS + "\"></a>\n\n"
        res += "## 2.3 " + scancode_manifestor.explanations.ABOUT_SCANCODE_REPORT_SETTINGS
        res += "\n\n"
        res += self._collapse_begin()
        res += "\n" + str(json.dumps(report['meta'], indent=4)).replace("\n","\n\n") + "\n"
        res += self._collapse_end()        
        
        res += "\n\n"

        res += self._conclusion_summary(report)
        
        res += "\n\n"

        res += self._license_summary(report)
        
        res += "\n\n"

        res += self._excluded_files(report)

        res += "\n\n"

        res += self._included_files(report)

        res += "\n\n"

        res += self._curated_files(report)

        res += "\n\n"


        return res
