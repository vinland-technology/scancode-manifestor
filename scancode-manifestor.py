#!/usr/bin/python3

###################################################################
#
# Scancode report -> manifest creator
#
# SPDX-FileCopyrightText: 2020 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
###################################################################

from argparse import RawTextHelpFormatter
import argparse

import json
import os
import re
import sys
import subprocess
from enum import Enum
from license_expression import Licensing


#
# The scancode reports goes through parts of the pipe below:
#
# report (JSON) ----> filter --> transform --> curate --> validate --> output
#
# * filter:     discards files not distributed (makefile, docs, ...) or with a license
# * transform:  transform to list of files (name, license, (c))
# * curate:     set license if faulty, missing or unclear
# * validate:   check if all files have proper information
# * output:     output result in correct format
#
# Modes:
# -----------------------
# * analyzer (default): prints information about the files remaing (i.e distributed)
#     * only filter is used
# * settings:           creates a settings file (for easier use in CI)
#     * only filter is used
# * manifest:           creates a manifest in requested format
#     * whole pipe is used



PROGRAM_NAME = "scancode-analyser.py"
PROGRAM_DESCRIPTION = "A tool to create package manifests from a Scancode report"
PROGRAM_AUTHOR = "Henrik Sandklef"
COMPLIANCE_UTILS_VERSION="__COMPLIANCE_UTILS_VERSION__"
PROGRAM_URL="https://github.com/vinland-technology/compliance-utils"
PROGRAM_COPYRIGHT="(c) 2021 Henrik Sandklef<hesa@sandklef.com>"
PROGRAM_LICENSE="GPL-3.0-or-later"
PROGRAM_SEE_ALSO=""

UNKNOWN_LICENSE = "unknown"

if COMPLIANCE_UTILS_VERSION == "__COMPLIANCE_UTILS_VERSION__":
    GIT_DIR=os.path.dirname(os.path.realpath(__file__))
    command = "cd " + GIT_DIR + " && git rev-parse --short HEAD"
    try:
        res = subprocess.check_output(command, shell=True)
        COMPLIANCE_UTILS_VERSION=str(res.decode("utf-8"))
    except Exception as e:
        COMPLIANCE_UTILS_VERSION="unknown"

VERBOSE=False

class FilterAttribute(Enum):
    PATH      = 1
    LICENSE   = 2
    COPYRIGHT = 3

class FilterAction(Enum):
    INCLUDE       = 1
    EXCLUDE       = 2

class FilterModifier(Enum):
    ANY   = 1
    ONLY  = 2

def error(msg):
    sys.stderr.write(msg + "\n")

def verbose(msg):
    if VERBOSE:
        sys.stderr.write(msg)
        sys.stderr.write("\n")
        sys.stderr.flush()


def parse():

    description = "NAME\n  " + PROGRAM_NAME + "\n\n"
    description = description + "DESCRIPTION\n  " + PROGRAM_DESCRIPTION + "\n\n"
    
    epilog = ""
    epilog = epilog + "AUTHOR\n  " + PROGRAM_AUTHOR + "\n\n"
    epilog = epilog + "REPORTING BUGS\n  File a ticket at " + PROGRAM_URL + "\n\n"
    epilog = epilog + "COPYRIGHT\n  Copyright " + PROGRAM_COPYRIGHT + ".\n  License " + PROGRAM_LICENSE + "\n\n"
    epilog = epilog + "SEE ALSO\n  " + PROGRAM_SEE_ALSO + "\n\n"
    
    
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument('file',
                        type=str,
                        help='scancode report file')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='output verbose information to stderr',
                        default=False)
    
    parser.add_argument('-d', '--directory',
                        dest='dir',
                        help='',
                        default=False)

    # ?
    parser.add_argument('-tl', '--top-level',
                        dest='top_level',
                        action='store_true',
                        help='print only top level directory(ies) in text format',
                        default=False)

    # ?
    parser.add_argument('-f', '--files',
                        dest='files',
                        action='store_true',
                        help='output license information per file instead of per dir',
                        default=False)

    # ?
    parser.add_argument('-ic', '--include-copyrights',
                        dest='include_copyrights',
                        action='store_true',
                        help='output copyright information',
                        default=False)

    # ?
    parser.add_argument('-j', '--json',
                        dest='json_format',
                        action='store_true',
                        help='output in JSON',
                        default=False)

    parser.add_argument('-el', '--exclude-licenses',
                        dest='excluded_licenses',
                        type=str,
                        nargs="+",
                        help="excluded licenses (if set, remove file/dir from printout)",
                        default=[])

    parser.add_argument('-il', '--include-licenses',
                        dest='included_licenses',
                        type=str,
                        nargs="+",
                        help="included licenses (if set, remove file/dir from printout)",
                        default=[])

    # ?
    parser.add_argument('-exl', '--exact-exclude-licenses',
                        dest='exact_excluded_licenses',
                        type=str,
                        nargs="+",
                        help="excluded licenses (if they appear as only license) (if set, remove file/dir from printout)",
                        default=None)

    # ?
    parser.add_argument('-exu', '--exact-exclude-unknown',
                        dest='exact_excluded_unknown_licenses',
                        action='store_true',
                        help="exclude exact unknown licenses (if they appear as only license) (if set, remove file/dir from printout)",
                        default=None)

    parser.add_argument('-e', '--exclude',
                        dest='excluded_regexps',
                        type=str,
                        nargs="+",
                        help="exclude files and dirs matching the supplied patterns",
                        default=[])

    parser.add_argument('-i', '--include',
                        dest='included_regexps',
                        type=str,
                        nargs="+",
                        help="include files and dirs matching the supplied patterns",
                        default=[])

    parser.add_argument('-c', '--curate',
                        dest='curations',
                        type=str,
                        action='append',
                        nargs="+",
                        help="curations ....",
                        default=[])

    parser.add_argument('-V', '--version',
                        action='version',
                        version=COMPLIANCE_UTILS_VERSION,
                        default=False)

    args = parser.parse_args()

    global VERBOSE
    VERBOSE=args.verbose
    
    return args


def __match_generic(single_file, field_path, field, needle, only):
    print("   * 0 -> match " + str(needle) + " " + str(field_path) + " " + str(field))
    haystack = single_file
    if field_path != None:
        for f in field_path:
            print("      * match \"" + str(f) + "\"  " + str(haystack), end="")
            haystack = haystack[f]
            print("  => " + str(haystack))
            
    print("   * 1 -> match    " + str(field))
    print("   * 1 -> field    " + str(type(field)))
    print("   * 1 -> haystack " + str(type(haystack)))
    print("   * 1 -> haystack " + str(haystack))

    if haystack == None or haystack == []:
        print("NONONEONEOENEON  None or []")
        found = None
    else:
        print("   * 2 -> match needle   " + str(needle))
        print("   * 2 -> match haystack " + str(haystack))
        if field == None:
            print("field can't be None")
            return None
        else:
            if isinstance(haystack, list):
                all_match = True
                one_match = False
                for h in haystack:
                    found = re.search(needle, h)
                    all_match = all_match and found
                    one_match = one_match or  found
                if only:
                    return all_match
                else:
                    return one_match
            else:
                haystack = haystack[field]
                found = re.search(needle, haystack)
                return found
    print("   * matched:  " + str(found))
    return found

def _fetch_license(single_file):
    return single_file['license_expressions']

def _fetch_copyright(single_file):
    copyright_list = single_file['copyrights']
    #print("single_file:    " + str(single_file['path']))
    c_list = []
    for c in copyright_list:
        c_list.append(c['value'])
        #print(" (c)  " + str(c['value']))
    return c_list

def _match_generic(single_file, filter, regexpr, only):
    # fetch list of items to search in
    items = None
    if filter == FilterAttribute.PATH:
        path = single_file['path']
        items = [ path ]
    elif filter == FilterAttribute.COPYRIGHT:
        items = _fetch_copyright(single_file)
    elif filter == FilterAttribute.LICENSE:
        items = _fetch_license(single_file)
    else:
        return None
        
    #print(single_file['path'] + "  items: " + str(items))
    if items == []:
        return False
    
    # for each item, search for regexpr
    all_match = True
    one_match = False
    for i in items:
        found = re.search(regexpr, i)
        #print(single_file['path'] + " regexpr " + str(regexpr))
        #print(single_file['path'] + " i       " + str(i))
        #print(" found   " + str(type(found)))
        #print(" found   " + str(found))
        #print(" found   " + str(found==True))
        all_match = all_match and (found!=None)
        one_match = one_match or  (found!=None)

    #print(" " + str(all_match) + " " + str(one_match))
    if FilterModifier.ONLY:
        #print("return ONLY")
        return all_match
    else:
        #print("return ONE")
        return one_match
    
def _filter_generic(files, filter, regexpr, include=FilterAction.INCLUDE, only=FilterModifier.ANY):
    #print(" * filter: " + str(files))
    filtered = []
    for f in files:
        #_match_generic(f, None,           'path', regexpr, only)
        #_match_generic(f, ["license_expressions"], '', regexpr, only)
        #_match_generic(f, ["copyrights"], ['key'],     regexpr, only)
        match = _match_generic(f, filter, regexpr, only)

        # store in list if either:
        #   match and include 
        # or 
        #   not match and exclude
        if match == None:
            print("uh oh")
        elif match and include == FilterAction.INCLUDE:
            verbose("filter include, keeping : " + str(f['name']))
            filtered.append(f)
            
        elif not match and include==FilterAction.EXCLUDE:
            verbose("filter exclude, keeping : " + str(f['name']))
            filtered.append(f)
            
    return filtered

def _isfile(f):
    return f['type'] == "file"

def _isdir(f):
    return f['type'] == "directory"

def _out(files, show_files=True, show_dirs=False):
    for f in files:
        if show_files and _isfile(f):
            print(" f " + f['path'] + " " + str(f['license_expressions']), file=sys.stderr)
        elif show_dirs and _isdir(f):
            print(" d " + f['path'] + " " + str(f['license_expressions']), file=sys.stderr)

def summarize(files):
    summary = {}
    licenses   = set()
    copyrights = set()
    for f in files:
        for l in f['license_expressions']:
            licenses.add(l)
        for c in f['copyrights']:
            copyrights.add(c['value'])

    license_list = list(licenses)
    license_list.sort()
    
    copyrights_list = list(copyrights)
    copyrights_list.sort()
    
    summary['license'] = license_list
    summary['copyright'] = copyrights_list
    return summary

def _transform_files(files):
    file_list = []
    for f in files:
        file_map = {}
        file_map['name'] = f['path']

        lic_expr = None
        for lic in list(set(f['license_expressions'])):
            if lic_expr == None:
                lic_expr = ""
            else:
                lic_expr += " and "
            lic_expr += lic
            
        file_map['license'] = lic_expr

        copyrights = set()
        for c in f['copyrights']:
            copyrights.add(c['value'])
        file_map['copyright'] = list(copyrights)
        file_list.append(file_map)
    return file_list

def _curate_file_license(files, regexpr, lic):
    new_list = []
    for f in files:
        #print("\nf: " + str(f))
        if re.search(regexpr, f['name']):
            #verbose(f['name'] + " " + str(f['license']) + " => " + lic)
            verbose(f['name'] + " " + str(f['license']) + " => " + lic)
            f['license'] = lic
        new_list.append(f)
    return new_list

def _validate(files):
    for f in files:
        verbose("validating " + str(f['name']))
        if f['name'] == None or f['name'] == "":
            error("File name can't be None or \"\"")
            exit(10)
        if f['license'] == None or f['license'] == []:
            error("Error for " + f['name'] + ": license name can't be None or [].")
            exit(10)
        if f['copyright'] == None or f['copyright'] == []:
            verbose("Warning for " + f['name'] + ": copyright name None or [].")
            
def _output_files(files):
    copyrights = set()
    licenses = set()
    for f in files:
        verbose("collecting info " + str(f['name']) + " " + f['license'])
        for c in f['copyright']:
            copyrights.add(c)
        licenses.add(f['license'])

    lic_expr = None
    for lic in licenses:
        if lic_expr == None:
            lic_expr = ""
        else:
            lic_expr += " and "
        
        lic_expr += lic
    print("Licenses:")
    print(lic_expr)
    print("Copyright:")
    c_list = list(copyrights)
    c_list.sort()
    for c in c_list:
        print(c)

def main():
    args = parse()

    with open(args.file) as fp:
        report = json.load(fp)

    files = report['files']

    #
    # filter files
    #
    for regexp in args.included_regexps:
        verbose("Include file:    " + regexp)
        files = _filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.INCLUDE)

    for regexp in args.excluded_regexps:
        verbose("Exclude file:    " + regexp)
        files = _filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.EXCLUDE)

    for regexp in args.included_licenses:
        verbose("Include license: " + regexp)
        files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.INCLUDE)

    for regexp in args.excluded_licenses:
        verbose("Exclude license: " + regexp)
        files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.EXCLUDE)


    
    #    files = _filter_generic(files, Filters.PATH, "ondemand", False)
    #    files = _filter_generic(files, Filters.PATH, "tests", False)
    files = _filter_generic(files, FilterAttribute.LICENSE, "mit", FilterAction.INCLUDE, FilterModifier.ONLY)
    #   files = _filter_generic(files, FilterAttribute.PATH, "extras", FilterAction.EXCLUDE)
    #_out(files, True, True)
    #print("\n")

    #
    # transform to intermediate format
    #
    transformed = _transform_files(files)
    #print(json.dumps((transformed)))

    #
    # add curations
    #
    curated = transformed
    verbose("curations: " + str(args.curations))
    for curation in args.curations:
        verbose("  * " + str(curation))
        length = len(curation)
        if length < 2:
            error("      * uh oh")
            exit(2)
        else:
            lic = curation[length-1]
            for i in range(0,length-1):
                verbose("      * " + curation[i] + ": " + lic)
                curated = _curate_file_license(curated, curation[i], lic)
    #curated = _curate_file_license(transformed, "types.hpp", "bsd-3-clause")
    #curated = _curate_file_license(curated, "rapidfuzz-cpp/rapidfuzz/details/SplittedSentenceView.hpp", "mit")
    #curated = _curate_file_license(curated, "unicode.hpp", "mit")
#print(json.dumps((transformed)))

    _output_files(curated)
    exit(0)

    #
    # validate
    #
    _validate(curated)
    
    _output_files(curated)
    
    #print(json.dumps(summarize(files)))
    exit(0)

        
    if args.dir:
        files_info = {}
        dirs_info = {}
        result = collect_license_dir(report, args.dir, args, dirs_info, files_info)
    else:
        result = output_license_per_dir(report, args)

    if result != None:
        if args.json_format:
            print(json.dumps(result))
        else:
            for k,v in result.items():

                # If dir and top-level
                if not args.files and args.top_level:
                    if "/" in k:
                        continue
                    
                l_fmt = "%-40s: %s %s"
                lic = list(v['licenses'])
                if lic == [] and args.files:
                    continue
                if args.include_copyrights:
                    cop = v['copyrights']
                else:
                    cop=""
                res_str = str(l_fmt) % ( k, lic, cop)
                print(res_str)
    else:
        print("")
        
#                l_fmt = "%-40s: %s %s"
#                lic_c_str = str(l_fmt) % ( dir, set_str, c_set_str)

    
if __name__ == '__main__':
    main()
    
