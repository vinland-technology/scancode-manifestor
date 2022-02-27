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

from argparse import RawTextHelpFormatter
import argparse

import json
import os
import re
import sys
import subprocess

from scancode_manifestor.manifestor_commands import ManifestorCommands
from scancode_manifestor.manifestor_interactor import ManifestorInteractor
import scancode_manifestor.manifestor_utils
from scancode_manifestor.manifestor_utils import ManifestLogger
from scancode_manifestor.manifestor_utils import ManifestUtils
from scancode_manifestor.manifestor_utils import FilterAction
from scancode_manifestor.manifestor_utils import FilterAttribute
from scancode_manifestor.manifestor_utils import FilterModifier

from scancode_manifestor.format_markdown import MarkdownFormatter
from scancode_manifestor.format_text import TextFormatter
from scancode_manifestor.format_json import JSONFormatter
from scancode_manifestor.format_yaml import YamlFormatter

from scancode_manifestor.scancode_manifestor_config import scancode_manifestor_version



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
PROGRAM_URL="https://github.com/vinland-technology/scancode-manifestor"
PROGRAM_COPYRIGHT="(c) 2021 Henrik Sandklef<hesa@sandklef.com>"
PROGRAM_LICENSE="GPL-3.0-or-later"
PROGRAM_SEE_ALSO=""

UNKNOWN_LICENSE = "unknown"


MODE_FILTER      = "filter"
MODE_VALIDATE    = "validate"
MODE_CREATE      = "create"
MODE_CONFIG      = "config"
MODE_INTERACTIVE = "interactive"
MODE_COPYRIGHT = "copyright"
MODE_LICENSE = "license"

ALL_MODES = [ MODE_FILTER, MODE_VALIDATE, MODE_CREATE, MODE_CONFIG, MODE_INTERACTIVE, MODE_COPYRIGHT , MODE_LICENSE]
DEFAULT_MODE=MODE_FILTER

OUTPUT_FORMAT_TEXT="text"
OUTPUT_FORMAT_JSON="json"
OUTPUT_FORMAT_MARKDOWN="markdown"
OUTPUT_FORMAT_YAML="yaml"
DEFAULT_OUTPUT_FORMAT=OUTPUT_FORMAT_TEXT

def parse(commands):
    
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
                        type=str,
                        default=MODE_FILTER)

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='output verbose information to stderr',
                        default=False)
    
    parser.add_argument('-of', '--output-format',
                        dest='format',
                        help='format of output',
                        default=DEFAULT_OUTPUT_FORMAT)
    
    parser.add_argument('-fc', '--force-config',
                        action='store_true',
                        dest='forced_config_mode',
                        help='force save config file',
                        default=False)
    
    parser.add_argument('-o', '--output',
                        dest='output',
                        help='output to file',
                        default=None)
    
    parser.add_argument('--output-filters',
                        action='store_true',
                        dest='output_filters',
                        help='output filter to stdout',
                        default=False)
    
    parser.add_argument('-nc', '--no-conclusion',
                        dest='no_conclusion',
                        help='leave out conclusions from report',
                        default=False)
    
    parser.add_argument('-ae', '--add-explanations',
                        action='store_true',
                        dest='add_explanations',
                        help='add explanations about scetions to report',
                        default=False)
    
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

    parser.add_argument('-psu', '--project-source-url',
                        dest='project_source_url',
                        help="specify url to the source code of the projet",
                        default=None)

    parser.add_argument('-piu', '--project-issue-url',
                        dest='project_issue_url',
                        help="url to the issue tracker of the projet",
                        default=None)

    parser.add_argument('-pdu', '--project-download-url',
                        dest='project_download_url',
                        help="specify url to the source code of the scanned version of the projet",
                        default=None)

    # ?
    parser.add_argument('-ic', '--include-copyrights',
                        dest='include_copyrights',
                        action='store_true',
                        help='output copyright information',
                        default=False)

    parser.add_argument('-' + commands.COMMAND_SHORT_HIDE_LICENSES, '--' + commands.COMMAND_HIDE_LICENSES,
                        dest='hide_licenses',
                        type=str,
                        action='append',
                        nargs="+",
                        help="excluded licenses (if set, remove file/dir from printout)",
                        default=[])

    parser.add_argument('-' + commands.COMMAND_SHORT_SHOW_LICENSES, '--' + commands.COMMAND_SHOW_LICENSES,
                        dest='show_licenses',
                        type=str,
                        action='append',
                        nargs="+",
                        help="included licenses (if set, remove file/dir from printout)",
                        default=[])

    parser.add_argument('-' + commands.COMMAND_SHORT_HIDE_ONLY_LICENSES, '--' + commands.COMMAND_HIDE_ONLY_LICENSES,
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

    parser.add_argument('-' + commands.COMMAND_SHORT_EXCLUDE_FILE, '--' + commands.COMMAND_EXCLUDE_FILE,
                        dest='excluded_regexps',
                        type=str,
                        action='append',
                        nargs="+",
                        help="exclude files and dirs matching the supplied patterns",
                        default=[])

    parser.add_argument('-eff', '--exclude-file-file',
                        dest='excluded_file_file',
                        type=str,
                        action='append',
                        nargs="+",
                        help="file with exclude file expressions to be read an used",
                        default=[])
    
    parser.add_argument('-iff', '--include-file-file',
                        dest='included_file_file',
                        type=str,
                        action='append',
                        nargs="+",
                        help="file with include file expressions to be read an used",
                        default=[])

    parser.add_argument('-ede', '--enable-default-excludes',
                        dest='enable_default_excludes',
                        action='store_true',
                        help="use built-in files with exclude file expressions to be read an used",
                        default=False)

    parser.add_argument('-' + commands.COMMAND_SHORT_INCLUDE_FILE, '--' + commands.COMMAND_INCLUDE_FILE,
                        dest='included_regexps',
                        type=str,
                        action='append',
                        nargs="+",
                        help="include files and dirs matching the supplied patterns",
                        default=[])

    parser.add_argument('-' + commands.COMMAND_SHORT_CURATE_FILE, '--' + commands.COMMAND_CURATE_FILE,
                        dest='file_curations',
                        type=str,
                        action='append',
                        nargs="+",
                        help="curations ....",
                        default=[])

    parser.add_argument('-' + commands.COMMAND_SHORT_CURATE_LICENSE, '--' + commands.COMMAND_CURATE_LICENSE,
                        dest='license_curations',
                        type=str,
                        action='append',
                        nargs="+",
                        help="curations ....",
                        default=[])

    parser.add_argument('-' + commands.COMMAND_SHORT_CURATE_MISSING_LICENSE, '--' + commands.COMMAND_CURATE_MISSING_LICENSE,
                        dest='missing_license_curation',
                        type=str,
                        help="missing license curation",
                        default=None)

    parser.add_argument('-ol', '--outbound-license',
                        dest='outbound_license',
                        type=str,
                        help="chose outbound license (must be a valid choice)",
                        default=None)

    parser.add_argument('-V', '--version',
                        action='version',
                        version=scancode_manifestor_version,
                        default=False)

    args = parser.parse_args()

    return args


class ScancodeManifestor:
    def __init__(self, commands, logger, utils):
        self.commands = commands
        self.logger = logger
        self.utils = utils

    def _setup_files(self, files):
        return self.utils._files_map(files, [])

    def _output_filters(self, args):
        print("#################################################")
        print("# Excluded file expressions")
        print("#  - generated from scancode-manifestory.py")
        print("#################################################")
        print("#")
        print("")
        for el in args['excluded_regexps']:
            for e in el:
                print(e + "\n")
            
        
    def _read_merge_args(self, args):
        new_args = {}
        self.logger.verbose("read config: " + str(args['config']))
        with open(args['config']) as fp:
            config_args = json.load(fp)
        self.logger.verbose("read config: " + str(json.dumps(config_args)))
        self.logger.verbose("")
        self.logger.verbose("args       : " + str(json.dumps(args)))
        self.logger.verbose("")
        for k,v in config_args.items():
            #print("k : " + str(k))
            self.logger.verbose(" * " + str(k))
            self.logger.verbose("   * " + str(v))
            #self.logger.verbose("   * " + str(args[k]))
            v_type = type(config_args[k])
            self.logger.verbose("    * " + str(v_type))
            new_args[k] = config_args[k]
            if k not in args or args[k] == None or args[k] == [] :
                pass
            else:
                if isinstance(config_args[k],list):
                    self.logger.verbose("       merge ")
                    new_args[k] = config_args[k] + args[k] 
                else:
                    reuse_options = [ 'enable_default_excludes', 'include_copyrights']
                    if k in reuse_options:
                        new_args[k] = v
                    else:
                        new_args[k] = args[k] 
                    self.logger.verbose("       replace")

        self.logger.verbose(" -- merged arguments ---")
        new_args['mode'] = args['mode']
        for k,v in new_args.items():
            self.logger.verbose(" * " + str(k) + ": " + str(new_args[k]))
        return new_args

    def _using_hide_args(self, args):
        keys = set()
        HIDE_OPTIONS = ['hide_licenses', 'hide_only_licenses', ]
        #for k,v in args.items():
        for k in HIDE_OPTIONS:
            v = args[k]
            if "hide" in k and not (v == None or v == []):
                print("key: " + str(k) + " value: " + str(v))
                keys.add(k)
        return keys
    
    def _merge_include_files(self, args):
        new_reg_exp = []
        for file_name_list in args['included_file_file']:
            for file_name in file_name_list:
                #print("INCLUDE FILE: " + str(file_name))
                f = open(file_name, 'r')
                for line in f.readlines():
                    stripped_line = line.strip().replace("\n","")
                    if not stripped_line.startswith("#") and len(stripped_line) > 0:
                        reg_exp = stripped_line
                        if not stripped_line.endswith("/"):
                            reg_exp = stripped_line + "$"
                        new_reg_exp.append(reg_exp)
                        #print("    expr: " + str(reg_exp))
 
        if not new_reg_exp is []:
            args['included_regexps'].append(new_reg_exp)

    
    def _merge_exclude_files(self, args):
        if args['enable_default_excludes']:
            SCRIPT_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
            VAR_DIR = os.path.join(SCRIPT_DIR, "var")
            files = [ 'armijn_file_filter.txt' , 'default.txt']
            file_names = []
            for f in files:
                file_name = os.path.join(VAR_DIR, f)
                file_names.append(file_name)
                #print("SCR: " + SCRIPT_DIR)
                #print("VAR: " + VAR_DIR)
                #print("ADD: " + file_name)
                #print(" ---> " + str(file_names))
            args['excluded_file_file'].append(file_names)
                
        new_reg_exp = []
        #print(" me " + str(args['excluded_file_file']))
        for file_name_list in args['excluded_file_file']:
            for file_name in file_name_list:
                #print(" * " + str(file_name))
                f = open(file_name, 'r')
                for line in f.readlines():
                    stripped_line = line.strip().replace("\n","")
                    #print(" ==| " +  str(len(line)) + " |==" + str(line) , end="")
                    if not stripped_line.startswith("#") and len(stripped_line) > 0:
                        reg_exp = stripped_line
                        if not stripped_line.endswith("/"):
                            reg_exp = stripped_line + "$"
                        #print("-----> " + reg_exp)
                        new_reg_exp.append(reg_exp)
        if not new_reg_exp is []:
            args['excluded_regexps'].append(new_reg_exp)



            
def get_formatter(args, utils):
    if args['format'].lower() == OUTPUT_FORMAT_TEXT:
        return TextFormatter(args, utils)
    elif args['format'].lower() == OUTPUT_FORMAT_JSON:
        return JSONFormatter(args, utils)
    elif args['format'].lower() == OUTPUT_FORMAT_MARKDOWN:
        return MarkdownFormatter(args, utils)
    elif args['format'].lower() == OUTPUT_FORMAT_YAML:
        return YamlFormatter(args, utils)
    return None

def main():

    commands = ManifestorCommands()
    parsed_args = parse(commands)

    args = parsed_args.__dict__
    
    #print("command line: " + str(sys.argv))
    #print("command line: " + str(parsed_args.mode))
    #exit(0)

    logger = ManifestLogger(args['verbose'])
    utils = ManifestUtils(logger)
    manifestor = ScancodeManifestor(commands, logger, utils)
    formatter = get_formatter(args, utils)
    manifestor._merge_exclude_files(args)
    manifestor._merge_include_files(args)
    
    #
    # if config file supplied - read up args and merge with those
    # supplied on command line
    #
    if args['config'] != None:
        args = manifestor._read_merge_args(args)

    #
    # if config mode - dump args and leave
    #
    if args['mode'] == MODE_CONFIG:
        keys = manifestor._using_hide_args(args)
        if keys != set():
            logger.error("Can't save config file if hide options are used. Remove the following options from your command line and try again: " + str(keys))
            exit(2)
            
        utils._output_args_to_file(args)
        exit(0)

    #
    # if outputfilters mode - dump filters and leave
    #
    if args['output_filters']:
        manifestor._output_filters(args)
        exit(0)

    # check inconsistent arguments
    if args['mode'] == MODE_INTERACTIVE and args['output'] == None:
        logger.error("When in acteractive mode you must specify a file name for the manifest")
        exit(3)
        

    #
    # SETUP 
    #
    hiders = utils._hiders(args)
    
    # Open scancode report
    with open(args['input_file']) as fp:
        scancode_report = json.load(fp)

    # Setup files map
    files = manifestor._setup_files(scancode_report['files'])

    
    #
    # filter files
    #
    #print("reading file file: " + str(args['excluded_file_file']))
    files = utils._filter(files, args['included_regexps'], args['excluded_regexps'])
    filtered = files
        
    if args['mode'] == MODE_INTERACTIVE:
        #print("excluded: " + str(args['excluded_regexps']))
        interactor = ManifestorInteractor(commands, utils, logger)
        interactor._interact(filtered, args)
        #print("excluded: " + str(args['excluded_regexps']))

    if args['mode'] == MODE_FILTER:
        #
        # if filter mode - this is the final step in the pipe
        #
        if args['verbose_file']:
            utils._output_verbose_file(files, args['verbose_file'])
        else:
            utils._output_filtered(filtered, args['hide_files']==False, args['show_directories'], sys.stdout, args['show_excluded_files'], hiders)
        exit(0)

    keys = manifestor._using_hide_args(args)
    if keys != set():
        logger.error("Hide options are only allowed in filter mode. Remove the following options from your command line and try again: " + str(keys))
        exit(2)

    #
    # Continue with pipe, but first verbose files
    #
    if args['verbose']:
        logger.verbose("---- filtered files -----")
        utils._output_filtered(filtered, sys.stderr, hiders)

    #
    # transform to intermediate format
    #
    utils._transform_files(filtered)
    transformed = filtered
    if args['verbose']:
        logger.verbose("---- transformed files -----")
        utils._output_filtered(transformed, sys.stderr, hiders)
    #print(json.dumps((transformed)))


    #
    # add curations
    #
    curations = utils._curate(transformed, args['file_curations'], args['license_curations'], args['missing_license_curation'])
    curated = transformed
    
    #
    # Copyright output mode
    #
    if args['mode'] == MODE_COPYRIGHT:
        copyrights = utils.copyrights(curated)
        copyrights_formatted = formatter.format_copyrights(copyrights)
        print(copyrights_formatted)
        exit(0)
    
    #
    # License output mode
    #
    if args['mode'] == MODE_LICENSE:
        licenses = utils.licenses(curated['included'])
        print(licenses)
        exit(0)
    
    #
    # validate
    #
    report = utils._report(args, scancode_report, transformed)
    validation = utils._validate(curated, report, args['outbound_license'])
    if validation['errors'] != []:
        for err in validation['errors']:
            logger.error(err)
        exit(9)
    #
    # if validate mode - this is the final step in the pipe
    #
    if args['mode'] == MODE_VALIDATE:
        print("Curated and validated files:")
        utils._output_files(curated)
        print("")
        print("Excluded files: ")
        print("  " + str(len(curated['excluded'])))
        print("Included files:")
        print("  " + str(len(curated['included'])))
        print("Copyright:")
        for c in report['conclusion']['copyright']:
            print("  " + str(c))
        print("License (original):")
        print("  " + str(report['conclusion']['license_expression_original']))
        print("License (simplified):")
        print("  " + str(report['conclusion']['license_expression']))
        exit(0)

    if args['mode'] == MODE_CREATE:
        format_report = formatter.format(report)

        if args['output'] != None:
            with open(args['output'], "w") as manifest_file:
                manifest_file.write(format_report) 
        else:
            print(format_report)
        

    
if __name__ == '__main__':
    main()
    
