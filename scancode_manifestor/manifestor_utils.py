#!/usr/bin/python3

###################################################################
#
# Scancode report -> manifest creator
#
# SPDX-FileCopyrightText: 2021 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
###################################################################

from enum import Enum
import datetime
import json
import re
import sys
from license_expression import Licensing

OBSOLETE = True

VERBOSE=False

#
# manifestor_data {
#   filter_type
#   filter_expr
#   filter_action
#   license_key
#   license_spdx
#   copyright
#   curation_type
#   curation_expr
#   curated_license
# }

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

class ManifestLogger:
    def __init__(self,debug):
        self.debug = debug

    def error(self, msg):
        sys.stderr.write(msg + "\n")

    def warn(self, msg):
        sys.stderr.write(msg + "\n")

    def verbose(self, msg):
        if self.debug:
            sys.stderr.write(msg)
            sys.stderr.write("\n")
            sys.stderr.flush()

    def mode(self, debug):
        self.debug = debug

class ManifestUtils:
    def __init__(self,logger):
        self.logger = logger

    def _fetch_license(self, single_file):
        return self._extract_license(single_file)
    #    return single_file['license_expressions']

    def _fetch_copyright(self, single_file):
        copyright_list = single_file['copyrights']
        #print("single_file:    " + str(single_file['path']))
        c_list = []
        for c in copyright_list:
            c_list.append(c['value'])
            #print(" (c)  " + str(c['value']))
        return c_list

    def _match_generic(self, single_file, filter, regexpr, only):
        # fetch list of items to search in
        items = None
        if filter == FilterAttribute.PATH:
            path = single_file['path']
            items = [ path ]
        elif filter == FilterAttribute.COPYRIGHT:
            items = self._fetch_copyright(single_file)
        elif filter == FilterAttribute.LICENSE:
            items = self._fetch_license(single_file)
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
            needle = regexpr.strip()
            found = re.search(needle, i)
            self.logger.verbose("re.search('" + needle + "', '" + i + "')")
            #print(single_file['path'] + " regexpr " + str(regexpr))
            self.logger.verbose(single_file['path'] + " i       " + str(i))
            self.logger.verbose(" found   " + str(type(found)))
            #print(" found   " + str(found))
            #print(" found   " + str(found==True))
            if all_match == None:
                all_match = (found!=None)
            else:
                all_match = all_match and (found!=None)
            one_match = one_match or  (found!=None)

        if all_match == None:
            all_match = False

        #print("matcher " + single_file['path'] + " all: " + str(all_match) + "    one_match: " + str(one_match))
        if only == FilterModifier.ONLY:
            #print("return ONLY " + str(all_match))
            return all_match
        elif only == FilterModifier.ANY:
            #print("return ONE")
            return one_match

    def _files_map(self, included_files, excluded_files):
        files_map = {}
        files_map['included'] = included_files
        files_map['excluded'] = excluded_files
        return files_map

    #def _all_files(self, )

    def _files_to_list(self, files):
        file_list=[]
        for f in files['included']:
            #print("f: " + str(f))
            if self._isfile(f):
                file_list.append(f['path'])
        return file_list

    def _unknown_licenses(self, files):
        license_summary = self._license_summary(files['included'])
        if None in license_summary:
            return license_summary[None]
        else:
            return 0

    # return count of license from a transformed file list
    def _licenses_in_transformed(self, files):
        licenses = set() 
        for f in files:
            assert 'scancode_manifestor' in f
            if 'curated_license' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['curated_license']
                #print(" curated ", end="")
            elif 'license_key' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['license_key']
                #print(" originial ", end="")                    
            else:
                # If we get here, it means the transormation has failed.
                # Better go out with a bang
                print("000000000000000000000000000000000000000000000000000000")
                assert False
            licenses.add(lic_key)
                
        return licenses
    
    # return count of license from a transformed file list
    def _license_count_transformed(self, lic, files):
        count = 0 
        for f in files:
            if 'license_key' in f and f['license_key'] == lic:
                count += 1
            
        return count
    
    # return count of unknown licenses from a transformed file list
    def _unknown_license_count_transformed(self, files):
        count = 0 
        for f in files:
            if 'license_key' not in f or f['license_key'] == None or f['license_key'] == []:
                count += 1
            
        return count
    
    def _match_file(self, f, filter, regexpr, include=FilterAction.INCLUDE, only=FilterModifier.ANY):
        if f == None:
            raise ValueError("No files argument supplied")
        if filter == None or type(filter) != FilterAttribute:
            raise ValueError("No filter, or incorrect type, argument supplied")
        if include == None or type(include) != FilterAction:
            raise ValueError("No filter action, or incorrect type, argument supplied")
        if regexpr == None or type(regexpr) != str:
            raise ValueError("No filter modifier, or incorrect type, argument supplied")
        if only == None or type(only) != FilterModifier:
            raise ValueError("No filter modifier, or incorrect type, argument supplied")

        if isinstance(regexpr, list):
            self.logger.self.logger.verbose("Woops, many items... filter: " + str(f['path']) + str(f['license_expressions']) )
            match = True
            for re in regexpr:
                match = match and self._match_generic(f, filter, re, only)
                self.logger.verbose("   re:" + str(re) + "  ==> " + str(match))
            self.logger.verbose("   ===================> " + str(match))
        else:
            #print(" match single : " + str(f['name']) + " " + str(f['license_expressions']) + " " + str(filter) + " " + str(regexpr))
            match = self._match_generic(f, filter, regexpr, only)
        return match

    def _keep_file(self, match, filter):
        if match:
            return filter == FilterAction.INCLUDE
        else:
            return filter == FilterAction.EXCLUDE
        
    def _filter_generic(self, files, filter, regexpr, include=FilterAction.INCLUDE, only=FilterModifier.ANY):
        if files == None:
            raise ValueError("No files argument supplied")
        if filter == None or type(filter) != FilterAttribute:
            raise ValueError("No filter, or incorrect type, argument supplied")
        if include == None or type(include) != FilterAction:
            raise ValueError("No filter action, or incorrect type, argument supplied")
        if only == None or type(only) != FilterModifier:
            raise ValueError("No filter modifier, or incorrect type, argument supplied")

        try:
            #print(" * filter: " + str(files))
            included = files['included']
            excluded = files['excluded']
        except:
            raise ValueError("Incorrect list of files")
            

        for f in files['included']:
            file_path = f['path']
            match = self._match_file(f, filter, regexpr, include, only)
            #print("-- match file: " + str(f['path'] + "  match: \"" + str(regexpr) + "\" ===> " + str(match)), file=sys.stderr)
            if match == None:
                warn("Can't match: " + regexpr)
            else:

                
                keep = self._keep_file(match, include)

                #print("-- match file: " + str(f['path'] + "  match: \"" + str(regexpr) + "\" ===> " + str(match)) + "  ==> " + str(keep), file=sys.stderr)
                if not keep:
                    #print("remove   i:" + str(len(files['included'])) + "   e:" + str(len(excluded)) + " " + str(f) )

                    self._add_scancode_manifestor_data(f, 'filter_type', filter)
                    self._add_scancode_manifestor_data(f, 'filter_action', include)
                    self._add_scancode_manifestor_data(f, 'filter_expr', str(regexpr))
                    excluded.append(f)

                    #print("woops: " + str(f['name']))
                    #print("woops: " + str(f['scancode_manifestor']))
                    files['included'] = [x for x in files['included'].copy() if x['path'] != file_path ]
                    #print("remove   i:" + str(len(files['included'])) + "   e:" + str(len(excluded)))

                else:
                    # OK, we should keep it

                    # if we explcitly included it, mark it as such
                    if include == FilterAction.INCLUDE:
                        self._add_scancode_manifestor_data(f, 'filter_type', filter)
                        self._add_scancode_manifestor_data(f, 'filter_action', include)
                        self._add_scancode_manifestor_data(f, 'filter_expr', str(regexpr))


        return self._files_map(included, excluded)

    def _isfile(self, f):
        return f['type'] == "file"

    def _isdir(self, f):
        return f['type'] == "directory"

    def _extract_license(self, f):
        licenses = set()
        for lic in f['license_expressions']:
            licenses.add(lic)
            #licenses.add(lic['key'])
        return licenses

    def _extract_license_spdx(self, f):
        licenses = set()
        for lic in f['licenses']:
            #print("Add license key: " + f['path'] + " " + lic['key'])
            licenses.add(lic['spdx_license_key'])
        return licenses


    def _dir_licenses(self, _files, dir, key):
        licenses = set()
        dir_name = dir['path']
        files = _files[key]
        self.logger.verbose("_dir_licenses: " + dir_name)
        for f in files:
            file_name = f['path']
            if file_name.startswith(dir_name):
                licenses.update(self._extract_license(f))
                self.logger.verbose(" * include: " + file_name + "   " + str(licenses) + " " + str(self._extract_license(f)))
            else:
                self.logger.verbose(" * ignore:  " + file_name)
        return licenses


    def _filter(self, _files, included_regexps, excluded_regexps):
        files = _files
        for regexp_list in included_regexps:
            self.logger.verbose("Include file:    " + str(regexp_list))
            for regexp in regexp_list:
                self.logger.verbose(" * include file:    " + regexp)
                self._filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.INCLUDE)

        for regexp_list in excluded_regexps:
            self.logger.verbose("Exclude file:    " + str(regexp_list))
            for regexp in regexp_list:
                self.logger.verbose(" * exclude file:    " + regexp)
                self._filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.EXCLUDE)

        if OBSOLETE == False:
            for regexp_list in show_licenses:
                self.logger.verbose("Include licenses:    " + str(regexp_list))
                for regexp in regexp_list:
                    self.logger.verbose(" * include license: " + regexp)
                    files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.INCLUDE)

            for regexp_list in hide_licenses:
                self.logger.verbose("Exclude file:    " + str(regexp_list))
                for regexp in regexp_list:
                    self.logger.verbose(" * exclude license: " + regexp)
                    files = _filter_generic(files, FilterAttribute.LICENSE, regexp, FilterAction.EXCLUDE)

            for regexp_list in hide_only_licenses:
                self.logger.verbose("Exclude only license: " + str(regexp_list))
                files = _filter_generic(files, FilterAttribute.LICENSE, regexp_list, FilterAction.EXCLUDE, FilterModifier.ANY)

        return files

    def _add_scancode_manifestor_data(self, f, key, data):
        if 'scancode_manifestor' not in f:
            f['scancode_manifestor'] = {}
        f['scancode_manifestor'][key] = data


        
    def _transform_files_helper(self, files):
        #file_list = []
        for f in files:
            if not self._isfile(f):
                continue
            

            lic_expr = None
            for lic in list(self._extract_license(f)):
                if lic_expr == None:
                    lic_expr = ""
                else:
                    lic_expr += " and "

                if "or" in lic.lower() or "|" in lic:
                    lic_expr += " ( " + lic + " ) "
                else:
                    lic_expr += lic

            spdx_expr = None
            for lic in list(self._extract_license_spdx(f)):
                if spdx_expr == None:
                    spdx_expr = ""
                else:
                    spdx_expr += " and "
                spdx_expr += str(lic)


            #print("lic: " + str(lic_expr))
            self._add_scancode_manifestor_data(f, 'license_key', lic_expr)
            self._add_scancode_manifestor_data(f, 'license_spdx', spdx_expr)

            copyrights = set()
            for c in f['copyrights']:
                copyrights.add(c['value'])
            self._add_scancode_manifestor_data(f, 'copyright', list(copyrights))
            #file_list.append(file_map)
        #return file_list

    def _hiders(self, args):
        hiders = {}
        hiders['hide_licenses']      = args['hide_licenses']
        hiders['hide_only_licenses'] = args['hide_only_licenses']
        hiders['show_licenses']      = args['show_licenses']
        return hiders
    
    def _transform_files(self, files):
        #return self._files_map(self._transform_files_helper(files['included']), self._transform_files_helper(files['excluded']))
        self._transform_files_helper(files['included'])
        self._transform_files_helper(files['excluded'])
        #print("sizes=" + str(len(files['included'])) + " " + str(len(files['excluded'])))
        for f in files['included']:
            if f['type'] != "file":
                if f not in files['excluded']:
                    files['excluded'].append(f)
                    #print("Adding " + str(f['path']) + " " + str(f['type']))
        files['included'] = [x for x in files['included'].copy() if x['type'] == "file" ]
        #print("sizes=" + str(len(files['included'])) + " " + str(len(files['excluded'])))
        

    def _curate_file_license(self, files, regexpr, lic):
        for f in files['included']:
            if re.search(regexpr, f['path']):
                self.logger.verbose(f['name'] + " => " + lic)
                self._add_scancode_manifestor_data(f, 'curation_type', 'file')
                self._add_scancode_manifestor_data(f, 'curation_expr', regexpr)
                self._add_scancode_manifestor_data(f, 'curated_license', lic)

    def _do_curate_license(self, f, lic):
        if ('scancode_manifestor' not in f) or (f['scancode_manifestor']['license_key']==None):
            #print(" * " + str(f['name']))
            self.logger.verbose(f['name'] + " missing license_key => " + lic)
            #if "dumps" in f['path']:
                #print(" *** FILE: " + str(f['path']))
                #print(" *** FILE: " + str(json.dumps(f, indent=4)))
                #print(" *** FILE: " + str(f))
                #print(" *** FILE: " + str(f['license_key']))
            self._add_scancode_manifestor_data(f, 'curation_type', 'license')
            self._add_scancode_manifestor_data(f, 'curated_license', lic)
            self._add_scancode_manifestor_data(f, 'curation_expr', "[]")
            #                    f['license_key'] = lic
            return 1
                    
        else:
            self.logger.warn("File " + str(f['path']))
            self.logger.warn(" - previously curated to: " + f['scancode_manifestor']['curated_license'])
            self.logger.warn(" - ignoring curation to:  " + lic)
            self.logger.warn(" - scancode_manifestor:   " + str(json.dumps(f['scancode_manifestor'], indent=4)))
        return 0
                
    def _curate_license(self, files, regexpr, lic):
        curations = 0 
        new_list = []
        #print("files: " + str(files))
        included_files = files['included']
        for f in included_files:

            # Passing "[]" as regexp should be interpreted as
            # matches license=[]
            if regexpr == "[]":
                #if "dumps" in f['path']:
                    #print("----HERE I AM " + str(f['path'] + " " + str(f)))

                if f['licenses'] == []:
                    curation_cnt = self._do_curate_license(f, lic)
                    curations += curation_cnt
            else:
                if len(f['license_expressions']) == 1:
                    if f['license_expressions'][0] == regexpr:
                        curation_cnt = self._do_curate_license(f, lic)
                        curations += curation_cnt
        return curations

    def _curate(self, files, file_curations, license_curations, missing_license_curation):
        #print("curate cml: " + str(missing_license_curation))
        self.logger.verbose("curations: " + str(file_curations))
                
        for curation in file_curations:
            self.logger.verbose("  * " + str(curation))
            length = len(curation)
            if length < 2:
                error("Bad curation: " + str(curation))
                # TODO: throw exception instead of exit
                exit(2)
            else:
                lic = curation[length-1]
                # TODO: make sure lic is a valid license
                for i in range(0,length-1):
                    self.logger.verbose("      * " + curation[i] + " => " + lic)
                    self._curate_file_license(files, curation[i], lic)

        for curation in license_curations:
            self.logger.verbose("  * " + str(curation))
            length = len(curation)
            if length < 2:
                self.logger.error("Bad curation: " + str(curation))
                # TODO: throw exception instead of exit
                exit(2)
            else:
                lic = curation[length-1]
                # TODO: make sure lic is a valid license
                for i in range(0,length-1):
                    self.logger.verbose("      * " + curation[i] + " => " + lic)
                    self._curate_license(files, curation[i], lic)

        if missing_license_curation:
            self._curate_license(files, "[]", missing_license_curation)

        return files

    def _count_files(self, files):
        cnt = 0 
        for f in files:
            if self._isfile(f):
                cnt += 1
        return cnt

    def _count_files_transformed(self, files):
        cnt = 0 
        for f in files:
            cnt += 1
        return cnt

    def _license_summary(self, files):
        licenses={}
        for f in files:
            #print(" path " + str(f['path']))
            self.logger.verbose(" lice " + str(f['license_expressions']))
            if self._isfile(f):
                lic = None
                lic_list = list(self._extract_license(f))
                self.logger.verbose(" list " + str(lic_list))
                lic_list.sort()
                for l in lic_list:
                    self.logger.verbose(" l    " + str(l))
                    if lic == None:
                        lic = l
                    else:
                        if "or" in lic.lower() or "|" in lic.lower():
                            lic += " and ( " + l + " )"
                        else:
                            lic += " and " + l
                            

                self.logger.verbose(" lic  " + str(lic))
                if lic in licenses:
                    licenses[lic] += 1
                else:
                    licenses[lic] = 1
                self.logger.verbose (" === " + str(lic) + " ==> " + str(licenses[lic]))

                #licenses.add(self._extract_license(f))
        self.logger.verbose(" ===> " + str(licenses))
        return licenses

    def _validate(self, files, report, outbound_license):
        errors = []
        warnings = []
        included_files = files['included']

        orig_file_count = report['files']['original_files_count']['files']
        report_file_count = report['files']['included_files_count'] + report['files']['excluded_files_count']
        if orig_file_count != report_file_count:
            errors.append("Files in report (" + str(report_file_count) + ") not the same as scancode report (" + str(orig_file_count) + ")")
            

            
        for f in included_files:
            #print("----> " + json.dumps(f, indent=6))
            #print("----> " + str(f['type']))
            manifest_map = f['scancode_manifestor']
            self.logger.verbose("validating " + str(f['name']))
            if f['name'] == None or f['name'] == "":
                errors.append("File name can't be None or \"\"")
            if manifest_map['license_key'] == None or manifest_map['license_key'] == []:
                curated = False
                if 'curation_type' in manifest_map and 'curated_license' in manifest_map:
                    if manifest_map['curation_type']  == 'license' and manifest_map['curated_license'] != None:
                        curated = True
                    elif manifest_map['curation_type']  == 'file' and manifest_map['curated_license'] != None:
                        curated = True
                if not curated:
                    errors.append("Error for " + f['path'] + ": license can't be None or [].")
                #else:
                    #print("Curated... " + str(f['path']))
            if manifest_map['copyright'] == None or manifest_map['copyright'] == []:
                warnings.append("Warning for " + f['path'] + ": copyright can't be None or [].")


        if outbound_license:
            outbound_ok =_verify_outbound_license(outbound_license, report['conclusion']['license_expression'])
            warning("Chosing license is experimental.  No checks are done")

        ret = {}
        ret['errors'] = errors
        ret['warnings'] = warnings
        return ret

    def _scancode_report_files_count(self, scancode_report):
        dirs = 0
        files = 0 
        for f in scancode_report['files']:
            if f['type'] == "directory":
                dirs += 1
            elif f['type'] == "file":
                files += 1

        return { 'dirs': dirs, 'files': files}

    def _report(self, args, scancode_report, _files):
        copyrights = set()
        licenses = set()
        spdx = set()
        files = _files['included']

        for f in files:
            if self._isdir(f):
                continue
            manifest_map = f['scancode_manifestor']
            #print("collecting info " + str(f))
            self.logger.verbose("collecting info " + str(f['name']) + " " + str(manifest_map['license_key']))
            for c in manifest_map['copyright']:
                copyrights.add(c)

            assert 'scancode_manifestor' in f
            #print("---------------- CHECKING------")
            #print(json.dumps(f['scancode_manifestor'], indent=4))
            #print("Adding license for file : " + str(f['path']) + ": ", end="")
            if 'curated_license' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['curated_license']
                #print(" curated ", end="")
            elif 'license_key' in f['scancode_manifestor']:
                lic_key = f['scancode_manifestor']['license_key']
                #print(" originial ", end="")                    
            else:
                # If we get here, it means the transormation has failed.
                # Better go out with a bang
                print("000000000000000000000000000000000000000000000000000000")
                assert False
            #print(lic_key)                    
                
            #lic_key = manifest_map['license_key']
            #if lic_key == None:
            #    if 'scancode_manifestor' in f['scancode_manifestor']:
            #        lic_key = f['scancode_manifestor']['curated_license']
            #        #print("wooops.... : " + str(f['path']) + " has " + f['scancode_manifestor']['curated_license'])
            #    else:
            #        lic_key = " none "
                
            #else:
            licenses.add(lic_key)
            spdx.add(manifest_map['license_spdx'])

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

        #
        # Files
        #
        report['files'] = {}
        report['files']['included'] = _files['included']
        report['files']['excluded'] = _files['excluded']
        report['files']['included_files_count'] = self._count_files(_files['included'])
        report['files']['excluded_files_count'] = self._count_files(_files['excluded'])
        report['files']['original_files_count'] = self._scancode_report_files_count(scancode_report)

        #
        # Project
        #
        project = {}
        project['name'] = args['project_name']
        project['sub_package'] = args['sub_package_name']
        project['version'] = args['project_version']
        project['url'] = args['project_url']
        project['source_url'] = args['project_source_url']
        project['issue_url'] = args['project_issue_url']
        project['download_url'] = args['project_download_url']
        report['project'] = project

        #
        # Conclusion
        #
        report['conclusion'] = {}
        report['conclusion']['copyright'] = c_list
        report['conclusion']['license_expression'] = json_compat_lic
        report['conclusion']['license_expression_original'] = lic_expr


        #
        # Meta information
        #
        report['meta']={}
        #report['meta']['curations'] = curations
        report['meta']['arguments'] = args #.__dict__
        report['meta']['report_date'] = str(datetime.datetime.now())
        report['meta']['scancode_report_file'] = args['input_file']
        report['meta']['scancode_name'] = scancode_report['headers'][0]['tool_name']
        report['meta']['scancode_version'] = scancode_report['headers'][0]['tool_version']
        #report['meta']['scancode_report'] = scancode_report

        return report

    def _output_args(self, args):
        print(json.dumps(report))

    def _curated_license(self, f):
        manifestor_map = f['scancode_manifestor']
        if 'curated_license' in manifestor_map:
            return manifestor_map['curated_license']
        else:
            return ""

    def _curation_type(self, f):
        manifestor_map = f['scancode_manifestor']
        if 'curation_type' in manifestor_map:
            return manifestor_map['curation_type']
        else:
            return ""

    def _output_files(self, files):
        # TODO: also output command line arg
        # TODO: output excluded files as well
        with_copyright = False
        for f in files['included']:
            manifestor_map = f['scancode_manifestor']
            #print("mm: " + str(manifestor_map))
            lk = manifestor_map['license_key']
            if lk == None:
                lk = " none "
            license_info = "[ " + lk + " : " + self._curated_license(f)  + " : " + self._curation_type(f) + " ]"
            if with_copyright:
                print(str(f['name']) + " [" + license_info + "] [", end="" )
                for c in f['copyright']:
                    print(str(c), end="" )
                print("]")
            else:
                #print("f: " + str(f['name']))
                #print("f: " + str(f['type']))
                print("  " + str(f['name']) + " " + license_info)


    def _output_verbose_file(self, files, verbose_file):
        for key in [ 'included', 'excluded']:
            for f in files[key]:
                if verbose_file == f['path']:
                    print(json.dumps(f, indent=2))
                    return




    def _output_single_file(self, f, stream=sys.stdout, hiders=None):
        hide_licenses     = None
        hide_only_license = None

        #print("")
        #print("_output_single_file: " + str(hiders))
        #print("info: " + str(f['name']) + " "  + str(f['license_expressions']))

        if hiders != None:
            hide_licenses = hiders['hide_licenses']
            hide_only_licenses = hiders['hide_only_licenses']
            show_licenses = hiders['show_licenses']
        else:
            hide_licenses = []
            hide_only_licenses = []
            show_licenses = []

        licenses  = list(self._extract_license(f))
        # empty show license list => show=True
        show_file = show_licenses == []
        #print("show_file: " + str(show_file))

        for regexp_list in show_licenses:
            self.logger.verbose(" * Show licenses:    " + str(regexp_list))
            for regexp in regexp_list:
                match = self._match_file(f, FilterAttribute.LICENSE, regexp)
                # any match => show_file becomes True
                show_file = show_file or match
                self.logger.verbose("    * show license: " + regexp + " ==> " + str(match))

        for regexp_list in hide_licenses:
            self.logger.verbose(" * Hide licenses:    " + str(regexp_list))
            for regexp in regexp_list:
                match = self._match_file(f, FilterAttribute.LICENSE, regexp)
                if match:
                    show_file = False
                self.logger.verbose("    * hide license: " + regexp + " ==> " + str(match))

        for regexp_list in hide_only_licenses:
            self.logger.verbose(" * Hide only licenses:    " + str(regexp_list))
            for regexp in regexp_list:
                match = self._match_file(f, FilterAttribute.LICENSE, regexp, FilterAction.INCLUDE, FilterModifier.ONLY)
                if match:
                    show_file = False
                self.logger.verbose("    * hide license: " + regexp + " ==> " + str(match))


        if show_file:
            print(" f " + f['path'] + " " + str(licenses), file=stream)
        else:
            self.logger.verbose("                     hide " + f['path'] + " " + str(licenses))

    def _output_single(self, files, f, show_files=True, show_dirs=False, file_key='included', stream=sys.stdout, hiders=None):

        if show_files and self._isfile(f):
            self._output_single_file(f, stream, hiders)
        elif show_dirs and self._isdir(f):
            licenses = list(self._dir_licenses(files, f, file_key))
            print(" d " + f['path'] + " " + str(licenses), file=stream)

    def _output_filtered_helper(self, files, show_files=True, show_dirs=False, file_key='included', stream=sys.stdout, hiders=None):
        for f in files[file_key]:
            self._output_single(files, f, show_files, show_dirs, file_key, stream, hiders)


    def _output_filtered(self, files, show_files=True, show_dirs=False, stream=sys.stdout, show_excluded=False, hiders=None):
        if show_excluded:
            #TODO: output to stream
            print("Excluded  " + str(self._count_files(files['excluded'])))
            self._output_filtered_helper(files, show_files, show_dirs, 'excluded', stream, hiders)

        #TODO: output to stream
        print("Included  " + str(self._count_files(files['included'])))
        self._output_filtered_helper(files, show_files, show_dirs, 'included', stream, hiders)


    def _output_filtered_include(self, files, show_files=True, show_dirs=False, stream=sys.stdout, hiders=None):
        #TODO: output to stream
        print("Included  " + str(self._count_files(files['included'])))
        self._output_filtered_helper(files, show_files, show_dirs, 'included', stream, hiders)

    def _output_filtered_exclude(self, files, show_files=True, show_dirs=False, stream=sys.stdout, hiders=None):
        #TODO: output to stream
        print("Excluded  " + str(self._count_files(files['excluded'])))
        self._output_filtered_helper(files, show_files, show_dirs, 'excluded', stream, hiders)


    def _get_config_file_name(self, args):
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



    def _output_args_to_file(self, args):
        self.logger.verbose("Storing config..")
        out_file = self._get_config_file_name(args)
        self.logger.verbose("Storing config to: \"" + str(out_file) + "\"")
        if out_file != None:
            if os.path.isfile(out_file):
                if not args['forced_config_mode']:
                    self.logger.warn("File '" + out_file + "' already exists. Remove it, use another name or use forced mode (-f))")
                    # TODO: throw exception instead of exit
                    exit(1)
            sys.stdout = open(out_file, 'w')

        print(json.dumps(args))  

    def _verify_outbound_license(self, lic, project_license):
        self.logger.verbose("verifying license: " + str(lic))
        self.logger.verbose(" * with: " + str(project_license))
        # TODO: add proper implementation
        return True


def FilterAttribute_to_string(filter):
    if filter == FilterAttribute.PATH:
        return "file"
    elif filter == FilterAttribute.COPYRIGHT:
        return "copyright"
    elif filter == FilterAttribute.LICENSE:
        return "license"
    else:
        return "unknown"

def FilterAction_to_string(action):
    if action == FilterAction.INCLUDE:
        return "include"
    elif action == FilterAction.EXCLUDE:
        return "exclude"
    else:
        return "unknown"
    
