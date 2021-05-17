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
MODE_CREATE      = "create"
MODE_CONFIG      = "config"

ALL_MODES = [ MODE_FILTER, MODE_VALIDATE, MODE_CREATE, MODE_CONFIG ]
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
    
    parser.add_argument('-f', '--force',
                        action='store_true',
                        dest='forced_mode',
                        help='used forced mode',
                        default=False)
    
    parser.add_argument('-o', '--output',
                        help='output to file',
                        default=None)
    
    parser.add_argument('-c', '--config',
                        help='read config file',
                        default=None)
    
    parser.add_argument('-gon', '--generate-output-name',
                        action='store_true',
                        dest='generate_output_name',
                        help='generate output file name from project',
                        default=None)
    
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
    
    parser.add_argument('-sef', '--show-excluded-files',
                        action='store_true',
                        dest='show_excluded_files',
                        help='show excluded files when in filter mode',
                        default=False)
    
    parser.add_argument('-i', '--input-file',
                        dest='input_file',
                        help='read input from file',
                        default=None)

    parser.add_argument('-vf', '--verbose-file',
                        dest='verbose_file',
                        help='outpur all scancode information about file',
                        default=None)

    parser.add_argument('-pn', '--project-name',
                        dest='project_name',
                        help='specify name of project',
                        default=None)

    parser.add_argument('-spn', '--package-name',
                        dest='sub_package_name',
                        help='specify name of sub package in project',
                        default=None)

    parser.add_argument('-pv', '--project-version',
                        dest='project_version',
                        help='specify version of project',
                        default=None)

    parser.add_argument('-pu', '--project-url',
                        dest='project_url',
                        help='specify url to the project',
                        default=None)

    # ?
    parser.add_argument('-ic', '--include-copyrights',
                        dest='include_copyrights',
                        action='store_true',
                        help='output copyright information',
                        default=False)

    parser.add_argument('-hl', '--hide-licenses',
                        dest='hide_licenses',
                        type=str,
                        action='append',
                        nargs="+",
                        help="excluded licenses (if set, remove file/dir from printout)",
                        default=[])

    parser.add_argument('-sl', '--show-licenses',
                        dest='show_licenses',
                        type=str,
                        action='append',
                        nargs="+",
                        help="included licenses (if set, remove file/dir from printout)",
                        default=[])

    parser.add_argument('-hol', '--hide-only-licenses',
                        dest='hide_only_licenses',
                        type=str,
                        action='append',
                        nargs="+",
                        help="hide licenses (if they appear as only license) in filter mode",
                        default=[])

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
        return False

    #print(single_file['path'] + "  items: " + str(items))
    if regexpr == "[]":
        #print("REGEXPR []")
        # If regexpr is []
        #   and items (the files's selected attributes) are empty => True
        #   and items (the files's selected attributes) are not empty => False
        # Typically this occurs when matching empty license (i.e. []) with "[]"
        #print("ITEMS " + str(items) + " ==>" + str(items == set()))
        #if items == set():
        #    print("ITEMS " + str(single_file['path']) + " " + str(single_file['license_expressions']))
            
        return items == set()
    

    # for each item, search for regexpr
    all_match = None
    one_match = False
    for i in items:
        found = re.search(regexpr, i)
        #print(single_file['path'] + " regexpr " + str(regexpr))
        #print(single_file['path'] + " i       " + str(i))
        #print(" found   " + str(type(found)))
        #print(" found   " + str(found))
        #print(" found   " + str(found==True))
        if all_match == None:
            all_match = (found!=None)
        else:
            all_match = all_match and (found!=None)
        one_match = one_match or  (found!=None)

    if all_match == None:
        all_match = False
        
    if only == FilterModifier.ONLY:
        #print("return ONLY " + str(all_match))
        return all_match
    elif only == FilterModifier.ANY:
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
        if isinstance(regexpr, list):
            verbose("Woops, many items... filter: " + str(f['path']) + str(f['license_expressions']) )
            match = True
            for re in regexpr:
                match = match and _match_generic(f, filter, re, only)
                verbose("   re:" + str(re) + "  ==> " + str(match))
            verbose("   ===================> " + str(match))
        else:
            match = _match_generic(f, filter, regexpr, only)
            
        #print("match " + str(f['path'] + " " + str(f['license_expressions']) + " " + str(regexpr) + ": " + str(match)))
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

def _extract_license_spdx(f):
    licenses = set()
    for lic in f['licenses']:
        #print("Add license key: " + f['path'] + " " + lic['key'])
        licenses.add(lic['spdx_license_key'])
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

def _dir_licenses(_files, dir, key):
    licenses = set()
    dir_name = dir['path']
    files = _files[key]
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
    
    summary['license_key'] = license_list
    summary['copyright'] = copyrights_list
    return summary

def _filter(files, included_regexps, excluded_regexps, show_licenses, hide_licenses, hide_only_licenses):
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
    
    for regexp_list in show_licenses:
        verbose("Include file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * include license: " + regexp)
            files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.INCLUDE)
            
    for regexp_list in hide_licenses:
        verbose("Exclude file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * exclude license: " + regexp)
            files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.EXCLUDE)

    for regexp_list in hide_only_licenses:
        verbose("Exclude only license: " + str(regexp_list))
        files = _filter_generic(files, FilterAttribute.LICENSE, regexp_list, FilterAction.EXCLUDE, FilterModifier.ANY)

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

        spdx_expr = None
        for lic in list(_extract_license_spdx(f)):
            if spdx_expr == None:
                spdx_expr = ""
            else:
                spdx_expr += " and "
            spdx_expr += lic


        #print("lic: " + str(lic_expr))
        file_map['license_key'] = lic_expr
        file_map['license_spdx'] = spdx_expr

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
            verbose(f['name'] + " " + str(f['license_key']) + " => " + lic)
            f['license_key'] = lic
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
            if f['license_key'] == None or f['license_key'] == []:
                verbose(f['name'] + " " + str(f['license_key']) + " => " + lic)
                f['license_key'] = lic
        elif f['license_key'] == None:
            pass
        elif re.search(regexpr, f['license_key']):
            verbose(f['name'] + " " + str(f['license_key']) + " => " + lic)
            f['license_key'] = lic
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

def _count_files(files):
    cnt = 0 
    for f in files:
        if f['type'] == "file":
            cnt += 1
    return cnt

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
        if f['license_key'] == None or f['license_key'] == []:
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
    spdx = set()
    files = _files['included']
    
    for f in files:
        verbose("collecting info " + str(f['name']) + " " + str(f['license_key']))
        for c in f['copyright']:
            copyrights.add(c)
        licenses.add(f['license_key'])
        spdx.add(f['license_spdx'])
        
    lic_expr = None
    #print("licenses: " + str(licenses))
    for lic in licenses:
        if lic_expr == None:
            lic_expr = ""
        else:
            lic_expr += " and "
        
        lic_expr += str(lic)

    spdx_expr = None
    for lic in spdx:
        if spdx_expr == None:
            spdx_expr = ""
        else:
            spdx_expr += " and "
        
        spdx_expr += str(lic)

    c_list = list(copyrights)
    c_list.sort()

    #print("\nlicenses: " + str(lic_expr))
    licensing = Licensing()
    parsed = licensing._parse_and_simplify(lic_expr)
    json_compat_lic = str(parsed).replace("AND", " & ")
    #print("\nlicenses: " + str(parsed))
    #exit(0)
    
          
    
    report = {}
    report['files'] = {}
    report['files']['included'] = _files['included']
    report['files']['excluded'] = _files['excluded']
    report['conclusion'] = {}
    report['conclusion']['project_name'] = args['project_name']
    report['conclusion']['project_version'] = args['project_version']
    report['conclusion']['project_url'] = args['project_url']
    report['conclusion']['copyright'] = c_list
    report['conclusion']['license_expression'] = json_compat_lic
    #report['conclusion']['license_expression_spdx'] = spdx_expr
    report['conclusion']['included_files_count'] = len(_files['included'])
    report['conclusion']['excluded_files_count'] = len(_files['excluded'])
    report['conclusion']['original_files_count'] = _scancode_report_files_count(scancode_report)
    report['meta']={}
    report['meta']['arguments'] = args #.__dict__
    report['meta']['report_date'] = str(datetime.datetime.now())
    report['meta']['scancode_report'] = args['input_file']

    return report

def _output_args(args):
    print(json.dumps(report))


def _output_files(files):
    # TODO: also output command line arg
    # TODO: output excluded files as well
    with_copyright = False
    for f in files['included']:
        if with_copyright:
            print(str(f['name']) + " [" + f['license_key'] + "] [", end="" )
            for c in f['copyright']:
                print(str(c), end="" )
            print("]")
        else:
            print("f: " + str(f['name']))
            print(str(f['name']) + " [" + f['license_key'] + "]")


def _output_verbose_file(files, verbose_file):
    for key in [ 'included', 'excluded']:
        for f in files[key]:
            if verbose_file == f['path']:
                print(json.dumps(f, indent=2))
                return

def _output_filtered_helper(files, show_files=True, show_dirs=False, file_key='included', stream=sys.stdout):
    for f in files[file_key]:
        if show_files and _isfile(f):
            licenses = list(_extract_license(f))
            print(" f " + f['path'] + " " + str(licenses), file=stream)
        elif show_dirs and _isdir(f):
            licenses = list(_dir_licenses(files, f, file_key))
            print(" d " + f['path'] + " " + str(licenses), file=stream)


def _output_filtered(files, show_files=True, show_dirs=False, stream=sys.stdout, show_excluded=False):
    if show_excluded:
        print("Excluded  " + str(_count_files(files['excluded'])))
        _output_filtered_helper(files, show_files, show_dirs, 'excluded', stream)

    print("Included  " + str(_count_files(files['included'])))
    _output_filtered_helper(files, show_files, show_dirs, 'included', stream)

    
def _get_config_file_name(args):
    if args['output'] != None:
        return args['output']
    if args['generate_output_name'] != None:
        if args['project_name'] != None and args['project_version'] != None:
            name = args['project_name'] + "-"
            sub_pkg =args['sub_package_name'] + "-"
            if sub_pkg == None:
                sub_pkg = ""
            version = args['project_version'] + "-"
            return name + sub_pkg + version + "-conclusion.json"
        else:
            warn("Missing project information. Can't generate output file name")
            # TODO: throw exception instead of exit
            exit (2)
    
    
    
def output_args_to_file(args):
    verbose("Storing config..")
    out_file = _get_config_file_name(args)
    verbose("Storing config to: \"" + str(out_file) + "\"")
    if out_file != None:
        if os.path.isfile(out_file):
            if not args['forced_mode']:
                warn("File '" + out_file + "' already exists. Remove it, use another name or use forced mode (-f))")
                exit(1)
        sys.stdout = open(out_file, 'w')
        
    print(json.dumps(args))  

    
def _setup_files(files):
    return _files_map(files, [])

def _read_merge_args(args):
    new_args = {}
    verbose("read config: " + str(args['config']))
    with open(args['config']) as fp:
        config_args = json.load(fp)
    verbose("read config: " + str(json.dumps(config_args)))
    verbose("")
    verbose("args       : " + str(json.dumps(args)))
    verbose("")
    for k,v in config_args.items():
        verbose(" * " + str(k))
        verbose("   * " + str(v))
        verbose("   * " + str(args[k]))
        v_type = type(config_args[k])
        verbose("    * " + str(v_type))
        new_args[k] = config_args[k]
        if args[k] == None or args[k] == [] :
            pass
        else:
            if isinstance(config_args[k],list):
                verbose("       merge ")
                new_args[k] = config_args[k] + args[k] 
            else:
                new_args[k] = args[k] 
                verbose("       replace")
    
    verbose(" -- merged arguments ---")
    new_args['mode'] = args['mode']
    for k,v in new_args.items():
        verbose(" * " + str(k) + ": " + str(new_args[k]))
    return new_args

def _using_hide_args(args):
    keys = set()
    HIDE_OPTIONS = ['hide_licenses', 'hide_only_licenses', ]
    #for k,v in args.items():
    for k in HIDE_OPTIONS:
        v = args[k]
        if "hide" in k and not (v == None or v == []):
            print("key: " + str(k) + " value: " + str(v))
            keys.add(k)
    return keys

def main():
    parsed_args = parse()

    args = parsed_args.__dict__

    #print("command line: " + str(sys.argv))
    #print("command line: " + str(parsed_args.mode))
    #exit(0)
    
    #
    # if config file supplied - read up args and merge with those
    # supplied on command line
    #
    if args['config'] != None:
        args = _read_merge_args(args)
    
    #
    # if config mode - dump args and leave
    #
    if args['mode'] == MODE_CONFIG:
        keys = _using_hide_args(args)
        if keys != set():
            error("Can't save config file if hide options are used. Remove the following options from your command line and try again: " + str(keys))
            exit(2)
            
        output_args_to_file(args)
        exit(0)


    #
    # SETUP 
    #
    
    # Open scancode report
    with open(args['input_file']) as fp:
        scancode_report = json.load(fp)

    # Setup files map
    files = _setup_files(scancode_report['files'])

    #
    # filter files
    #
    filtered = _filter(files, args['included_regexps'], args['excluded_regexps'], args['show_licenses'], args['hide_licenses'], args['hide_only_licenses'])

    #
    # if filter mode - this is the final step in the pipe
    #
    if args['mode'] == MODE_FILTER:
        if args['verbose_file']:
            _output_verbose_file(files, args['verbose_file'])
        else:
            _output_filtered(filtered, args['hide_files']==False, args['show_directories'], sys.stdout, args['show_excluded_files'])
        exit(0)

    keys = _using_hide_args(args)
    if keys != set():
        error("Hide options are only allowed in filter mode. Remove the following options from your command line and try again: " + str(keys))
        exit(2)

    #
    # Continue with pipe, but first verbose files
    #
    if args['verbose']:
        verbose("---- filtered files -----")
        _output_filtered(filtered, sys.stderr)

    #
    # transform to intermediate format
    #
    transformed = _transform_files(filtered)
    if args['verbose']:
        verbose("---- transformed files -----")
        _output_filtered(transformed, sys.stderr)
    #print(json.dumps((transformed)))

    #
    # add curations
    #
    curated = _curate(transformed, args['file_curations'], args['license_curations'], args['missing_license_curation'])
    
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
    if args['mode'] == MODE_VALIDATE:
        print("Curated and validated files:")
        _output_files(curated)
        print("License and copyright:")
        print("license:   " + str(report['conclusion']['license_expression']))
        print("copyright: " + str(report['conclusion']['copyright']))
        exit(0)

    print(json.dumps(report, indent=2))
        

    
if __name__ == '__main__':
    main()
    
