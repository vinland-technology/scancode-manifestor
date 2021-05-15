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
import datetime
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
PROGRAM_URL="https://github.com/vinland-technology/scancode-manifestor"
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

MODE_FILTER      = "filter"
MODE_VALIDATE    = "validate"
MODE_REPORT      = "report"
MODE_CONFIG      = "config"

ALL_MODES = [ MODE_FILTER, MODE_VALIDATE, MODE_REPORT, MODE_CONFIG ]
DEFAULT_MODE=MODE_FILTER

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

def warn(msg):
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
    epilog = epilog + "PROJECT PAGE\n  " + PROGRAM_URL + "\n\n"
    epilog = epilog + "AUTHORS\n  " + PROGRAM_AUTHOR + "\n\n"
    epilog = epilog + "REPORTING BUGS\n  File a ticket at " + PROGRAM_URL + "\n\n"
    epilog = epilog + "COPYRIGHT\n  Copyright " + PROGRAM_COPYRIGHT + ".\n  License " + PROGRAM_LICENSE + "\n\n"
    epilog = epilog + "SEE ALSO\n  " + PROGRAM_SEE_ALSO + "\n\n"
    
    
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument('mode',
                        help='Specify execution mode (' + str(ALL_MODES) + '). Default mode: ' + DEFAULT_MODE ,
                        nargs='?',
                        default=DEFAULT_MODE)

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='output verbose information to stderr',
                        default=False)
    
    parser.add_argument('-sd', '--show-directories',
                        action='store_true',
                        dest='show_directories',
                        help='show directories from output when in filtered mode' ,
                        default=False)
    
    parser.add_argument('-hf', '--hide-files',
                        action='store_true',
                        dest='hide_files',
                        help='hide files from output when in filtered mode',
                        default=False)
    
    parser.add_argument('-i', '--input-file',
                        dest='file',
                        help='read input from file',
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

    parser.add_argument('-ef', '--exclude-files',
                        dest='excluded_regexps',
                        type=str,
                        action='append',
                        nargs="+",
                        help="exclude files and dirs matching the supplied patterns",
                        default=[])

    parser.add_argument('-if', '--include-files',
                        dest='included_regexps',
                        type=str,
                        action='append',
                        nargs="+",
                        help="include files and dirs matching the supplied patterns",
                        default=[])

    parser.add_argument('-cf', '--curate-file',
                        dest='file_curations',
                        type=str,
                        action='append',
                        nargs="+",
                        help="curations ....",
                        default=[])

    parser.add_argument('-cl', '--curate-license',
                        dest='license_curations',
                        type=str,
                        action='append',
                        nargs="+",
                        help="curations ....",
                        default=[])

    parser.add_argument('-cml', '--curate-missing-license',
                        dest='missing_license_curation',
                        type=str,
                        help="missing license curation",
                        default=None)

    parser.add_argument('-V', '--version',
                        action='version',
                        version=COMPLIANCE_UTILS_VERSION,
                        default=False)

    args = parser.parse_args()

    global VERBOSE
    VERBOSE=args.verbose
    
    return args


def _fetch_license(single_file):
    return _extract_license(single_file)
#    return single_file['license_expressions']

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

def _files_map(included_files, excluded_files):
    files_map = {}
    files_map['included'] = included_files
    files_map['excluded'] = excluded_files
    return files_map

    
def _filter_generic(files, filter, regexpr, include=FilterAction.INCLUDE, only=FilterModifier.ANY):
    #print(" * filter: " + str(files))
    filtered = []
    ignored = files['excluded']

    for f in files['included']:
        #_match_generic(f, None,           'path', regexpr, only)
        #_match_generic(f, ["license_expressions"], '', regexpr, only)
        #_match_generic(f, ["copyrights"], ['key'],     regexpr, only)
        match = _match_generic(f, filter, regexpr, only)

        # store in list if either:
        #   match and include 
        # or 
        #   not match and exclude
        if match == None:
            warn("Can't match: " + regexpr)
        elif match:
            if include == FilterAction.INCLUDE:
                verbose("filter include, keeping:  " + str(f['name']))
                filtered.append(f)
            else:
                verbose("filter include, ignoring: " + str(f['name']))
                ignored.append(f)
                
        elif not match:
            if include==FilterAction.EXCLUDE:
                verbose("filter exclude, keeping:  " + str(f['name']))
                filtered.append(f)
            else:
                verbose("filter exclude, ignoring: " + str(f['name']))
                ignored.append(f)

    return _files_map(filtered, ignored)

def _isfile(f):
    return f['type'] == "file"

def _isdir(f):
    return f['type'] == "directory"

def _extract_license(f):
    licenses = set()
    for lic in f['licenses']:
        licenses.add(lic['key'])
    return licenses

def _obsolete_extract_license(f):
    # use set - to automatically remove duplicates
    licenses = set()
    #print("file: " + str(f['licenses']))
    for lic in f['licenses']:
        # Try to find SPDX license
        # if not possible to find SPDX, choose scancode key
        spdx = lic['spdx_license_key']
        if spdx:
            licenses.add(spdx)
        else:
            licenses.add(lic['key'])
    return licenses

def _dir_licenses(files, dir):
    licenses = set()
    dir_name = dir['path']
    verbose("_dir_licenses: " + dir_name)
    for f in files:
        file_name = f['path']
        if file_name.startswith(dir_name):
            licenses.update(_extract_license(f))
            verbose(" * include: " + file_name + "   " + str(licenses) + " " + str(_extract_license(f)))
        else:
            verbose(" * ignore:  " + file_name)
    return licenses
        
def _obsoleted_summarize(_files):
    summary = {}
    licenses   = set()
    copyrights = set()
    files = _files['included']
    
    for f in files:
        licenses = _extract_license(f)
        #for l in f['license_expressions']:
            #licenses.add(l)
        for c in f['copyrights']:
            copyrights.add(c['value'])

    license_list = list(licenses)
    license_list.sort()
    
    copyrights_list = list(copyrights)
    copyrights_list.sort()
    
    summary['license'] = license_list
    summary['copyright'] = copyrights_list
    return summary

def _filter(files, included_regexps, excluded_regexps, included_licenses, excluded_licenses):
    for regexp_list in included_regexps:
        verbose("Include file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * include file:    " + regexp)
            files = _filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.INCLUDE)

    for regexp_list in excluded_regexps:
        verbose("Exclude file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * exclude file:    " + regexp)
            files = _filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.EXCLUDE)
    
    for regexp_list in included_licenses:
        verbose("Include file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * include license: " + regexp)
            files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.INCLUDE)

    for regexp_list in excluded_licenses:
        verbose("Exclude file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * exclude license: " + regexp)
            files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.EXCLUDE)

    return files

def _transform_files_helper(files):
    file_list = []
    for f in files:
        if not _isfile(f):
            continue
        file_map = {}
        file_map['name'] = f['path']
        file_map['sha1'] = f['sha1']
        file_map['sha256'] = f['sha256']
        file_map['md5'] = f['md5']

        lic_expr = None
        for lic in list(_extract_license(f)):
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

def _transform_files(files):
    return _files_map(_transform_files_helper(files['included']), _transform_files_helper(files['excluded']))
    
def _curate_file_license(files, regexpr, lic):
    new_list = []
    included_files = files['included']
    for f in included_files:
        #print("\nf: " + str(f))
        if re.search(regexpr, f['name']):
            #verbose(f['name'] + " " + str(f['license']) + " => " + lic)
            verbose(f['name'] + " " + str(f['license']) + " => " + lic)
            f['license'] = lic
        new_list.append(f)
    return _files_map(new_list, files['excluded'])

def _curate_license(files, regexpr, lic):
    new_list = []
    #print("files: " + str(files))
    included_files = files['included']
    for f in included_files:
        # Passing "[]" as regexp should be interpreted as
        # matches license=[]
        if regexpr == "[]":
            if f['license'] == None or f['license'] == []:
                verbose(f['name'] + " " + str(f['license']) + " => " + lic)
                f['license'] = lic
        elif f['license'] == None:
            pass
        elif re.search(regexpr, f['license']):
            verbose(f['name'] + " " + str(f['license']) + " => " + lic)
            f['license'] = lic
        new_list.append(f)
    return _files_map(new_list, files['excluded'])

def _curate(files, file_curations, license_curations, missing_license_curation):
    curated = files
    verbose("curations: " + str(file_curations))

    for curation in file_curations:
        verbose("  * " + str(curation))
        length = len(curation)
        if length < 2:
            error("Bad curation: " + str(curation))
            exit(2)
        else:
            lic = curation[length-1]
            # TODO: make sure lic is a valid license
            for i in range(0,length-1):
                verbose("      * " + curation[i] + " => " + lic)
                curated = _curate_file_license(curated, curation[i], lic)

    for curation in license_curations:
        verbose("  * " + str(curation))
        length = len(curation)
        if length < 2:
            error("Bad curation: " + str(curation))
            exit(2)
        else:
            lic = curation[length-1]
            # TODO: make sure lic is a valid license
            for i in range(0,length-1):
                verbose("      * " + curation[i] + " => " + lic)
                curated = _curate_license(curated, curation[i], lic)

    if missing_license_curation:
        #print("curated: " + str(curated))
        curated = _curate_license(curated, "[]", missing_license_curation)

    return curated

def _validate(files, report):
    errors = []
    warnings = []
    included_files = files['included']

    orig_file_count = report['conclusion']['original_files_count']['files']
    report_file_count = report['conclusion']['included_files_count'] + report['conclusion']['excluded_files_count']
    if orig_file_count != report_file_count:
        errors.append("Files in report (" + report_file_count + ") not the same as scancode report (" + orig_file_count + ")")
        
    
    
    for f in included_files:
        verbose("validating " + str(f['name']))
        if f['name'] == None or f['name'] == "":
            errors.append("File name can't be None or \"\"")
        if f['license'] == None or f['license'] == []:
            errors.append("Error for " + f['name'] + ": license can't be None or [].")
        if f['copyright'] == None or f['copyright'] == []:
            warnings.append("Warning for " + f['name'] + ": copyright can't be None or [].")

    ret = {}
    ret['errors'] = errors
    ret['warnings'] = warnings
    return ret

def _scancode_report_files_count(scancode_report):
    dirs = 0
    files = 0 
    for f in scancode_report['files']:
        if f['type'] == "directory":
            dirs += 1
        elif f['type'] == "file":
            files += 1

    return { 'dirs': dirs, 'files': files}
    
def _report(args, scancode_report, _files):
    copyrights = set()
    licenses = set()
    files = _files['included']
    
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

    c_list = list(copyrights)
    c_list.sort()

    report = {}
    report['files'] = {}
    report['files']['included'] = _files['included']
    report['files']['excluded'] = _files['excluded']
    report['conclusion'] = {}
    report['conclusion']['license'] = lic_expr
    report['conclusion']['copyright'] = c_list
    report['conclusion']['included_files_count'] = len(_files['included'])
    report['conclusion']['excluded_files_count'] = len(_files['excluded'])
    report['conclusion']['original_files_count'] = _scancode_report_files_count(scancode_report)
    report['meta']={}
    report['meta']['arguments'] = args.__dict__
    report['meta']['report_date'] = str(datetime.datetime.now())
    report['meta']['scancode_report'] = args.file

    return report

def _output_args(args):
    print(json.dumps(report))


def _output_files(files):
    # TODO: also output command line arg
    # TODO: output excluded files as well
    with_copyright = False
    for f in files['included']:
        if with_copyright:
            print(str(f['name']) + " [" + f['license'] + "] [", end="" )
            for c in f['copyright']:
                print(str(c), end="" )
            print("]")
        else:
            print(str(f['name']) + " [" + f['license'] + "]")

def _output_filtered_helper(files, show_files=True, show_dirs=False, file_key='included', stream=sys.stdout):
    for f in files[file_key]:
        if show_files and _isfile(f):
            licenses = list(_extract_license(f))
            print(" f " + f['path'] + " " + str(licenses), file=stream)
        elif show_dirs and _isdir(f):
            licenses = list(_dir_licenses(files, f))
            print(" d " + f['path'] + " " + str(licenses), file=stream)


def _output_filtered(files, stream=sys.stdout):
    print("Excluded " + str(len(files['excluded'])))
    _output_filtered_helper(files, True, False, 'excluded', stream)
    print("Included " + str(len(files['included'])))
    _output_filtered_helper(files, True, False, 'included', stream)
    
            
def _setup_files(files):
    return _files_map(files, [])
            
def main():
    args = parse()

    # dumps args (to save cli, later on)
    # print(json.dumps(args.__dict__))

    #
    # SETUP 
    #
    
    # Open scancode report
    with open(args.file) as fp:
        scancode_report = json.load(fp)

    # Setup files map
    files = _setup_files(scancode_report['files'])

    #
    # filter files
    #
    filtered =_filter(files, args.included_regexps, args.excluded_regexps, args.included_licenses, args.excluded_licenses)

    #
    # if filter mode - this is the final step in the pipe
    #
    if args.mode == MODE_FILTER:
        _output_filtered(filtered, sys.stdout)
        exit(0)


    #
    # Continue with pipe, but first verbose files
    #
    if args.verbose:
        verbose("---- filtered files -----")
        _output_filtered(filtered, sys.stderr)

    #
    # transform to intermediate format
    #
    transformed = _transform_files(filtered)
    if args.verbose:
        verbose("---- transformed files -----")
        _output_filtered(transformed, sys.stderr)
    #print(json.dumps((transformed)))

    #
    # add curations
    #
    curated = _curate(transformed, args.file_curations, args.license_curations, args.missing_license_curation)
    
    #
    # validate
    #
    report = _report(args, scancode_report, curated)
    validation =_validate(curated, report)
    if validation['errors'] != []:
        for err in validation['errors']:
            error(err)
        exit(9)
    #
    # if validate mode - this is the final step in the pipe
    #
    if args.mode == MODE_VALIDATE:
        print("Curated and validated files:")
        _output_files(curated)
        print("License and copyright:")
        print("license:   " + str(report['conclusion']['license']))
        print("copyright: " + str(report['conclusion']['copyright']))
        exit(0)

    print(json.dumps(report))
        

    
if __name__ == '__main__':
    main()
    
