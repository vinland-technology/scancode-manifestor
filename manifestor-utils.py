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
        needle = regexpr.strip()
        found = re.search(needle, i)
        verbose("re.search('" + needle + "', '" + i + "')")
        #print(single_file['path'] + " regexpr " + str(regexpr))
        verbose(single_file['path'] + " i       " + str(i))
        verbose(" found   " + str(type(found)))
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

def _files_map(included_files, excluded_files):
    files_map = {}
    files_map['included'] = included_files
    files_map['excluded'] = excluded_files
    return files_map

#def _all_files()

def _files_to_list(files):
    file_list=[]
    for f in files['included']:
        #print("f: " + str(f))
        if _isfile(f):
            file_list.append(f['path'])
    return file_list

def _unknown_licenses(files):
    license_summary = _license_summary(files['included'])
    if None in license_summary:
        return license_summary[None]
    else:
        return 0

def _match_file(f, filter, regexpr, include=FilterAction.INCLUDE, only=FilterModifier.ANY):
        if isinstance(regexpr, list):
            verbose("Woops, many items... filter: " + str(f['path']) + str(f['license_expressions']) )
            match = True
            for re in regexpr:
                match = match and _match_generic(f, filter, re, only)
                verbose("   re:" + str(re) + "  ==> " + str(match))
            verbose("   ===================> " + str(match))
        else:
            #print(" match single : " + str(f['name']) + " " + str(f['license_expressions']) + " " + str(filter) + " " + str(regexpr))
            match = _match_generic(f, filter, regexpr, only)
        return match

def _filter_generic(files, filter, regexpr, include=FilterAction.INCLUDE, only=FilterModifier.ANY):
    #print(" * filter: " + str(files))
    included = files['included']
    excluded = files['excluded']

    #print("match file on expr :" + str(regexpr))
    if include == FilterAction.INCLUDE:
        file_list = 'excluded'
        other_list = 'included'
    else:
        file_list = 'included'
        other_list = 'excluded'

    for f in files[file_list]:
        file_path = f['path']
        match = _match_file(f, filter, regexpr)
        #print("-- match file: " + str(f['path'] + "  match: \"" + str(regexpr) + "\" ===> " + str(match)))
        if match == None:
            warn("Can't match: " + regexpr)
        elif match:
            #print("-- match: " + str(filter) + " " + str(f['path']))
            #print(" remove file:     " + str(f['path']) + " " + str(f in file_list) + " " + str(f in other_list))
            #file_list.remove(f)
            files[other_list].append(f)
            files[file_list] = [x for x in files[file_list] if x['path'] != file_path ]
            print(" ----- " + str(len(files[other_list])) + " == " + str(len(files[file_list])))
            #print(" remove file:     " + str(f['path']) + " " + str(f in file_list) + " " + str(f in other_list))
        else:
            #print("no match: " + str(filter) + " " + str(f['path']))
            pass

    
    return _files_map(included, excluded)

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

def _filter(_files, included_regexps, excluded_regexps):
    files = _files
    for regexp_list in included_regexps:
        verbose("Include file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * include file:    " + regexp)
            _filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.INCLUDE)

    for regexp_list in excluded_regexps:
        verbose("Exclude file:    " + str(regexp_list))
        for regexp in regexp_list:
            verbose(" * exclude file:    " + regexp)
            _filter_generic(files, FilterAttribute.PATH, regexp, FilterAction.EXCLUDE)

    if OBSOLETE == False:
        for regexp_list in show_licenses:
            verbose("Include licenses:    " + str(regexp_list))
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
        if _isfile(f):
            cnt += 1
    return cnt

def _license_summary(files):
    licenses={}
    for f in files:
        #print(" path " + str(f['path']))
        verbose(" lice " + str(f['license_expressions']))
        if _isfile(f):
            lic = None
            lic_list = list(_extract_license(f))
            verbose(" list " + str(lic_list))
            lic_list.sort()
            for l in lic_list:
                verbose(" l    " + str(l))
                if lic == None:
                    lic = l
                else:
                    lic += " and " + l

            verbose(" lic  " + str(lic))
            if lic in licenses:
                licenses[lic] += 1
            else:
                licenses[lic] = 1
            verbose (" === " + str(lic) + " ==> " + str(licenses[lic]))

            #licenses.add(_extract_license(f))
    verbose(" ===> " + str(licenses))
    return licenses

def _validate(files, report, outbound_license):
    errors = []
    warnings = []
    included_files = files['included']

    orig_file_count = report['files']['original_files_count']['files']
    report_file_count = report['files']['included_files_count'] + report['files']['excluded_files_count']
    if orig_file_count != report_file_count:
        errors.append("Files in report (" + str(report_file_count) + ") not the same as scancode report (" + str(orig_file_count) + ")")
        
    for f in included_files:
        verbose("validating " + str(f['name']))
        if f['name'] == None or f['name'] == "":
            errors.append("File name can't be None or \"\"")
        if f['license_key'] == None or f['license_key'] == []:
            errors.append("Error for " + f['name'] + ": license can't be None or [].")
        if f['copyright'] == None or f['copyright'] == []:
            warnings.append("Warning for " + f['name'] + ": copyright can't be None or [].")

    
    if outbound_license:
        outbound_ok =_verify_outbound_license(outbound_license, report['conclusion']['license_expression'])
        warning("Chosing license is experimental.  No checks are done")
        
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
    
    #
    # Files
    #
    report['files'] = {}
    report['files']['included'] = _files['included']
    report['files']['excluded'] = _files['excluded']
    report['files']['included_files_count'] = len(_files['included'])
    report['files']['excluded_files_count'] = len(_files['excluded'])
    report['files']['original_files_count'] = _scancode_report_files_count(scancode_report)

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

    #
    # Meta information
    #
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



            
def _output_single_file(f, stream=sys.stdout, hiders=None):
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
        
    licenses  = list(_extract_license(f))
    # empty show license list => show=True
    show_file = show_licenses == []
    #print("show_file: " + str(show_file))
    
    for regexp_list in show_licenses:
        verbose(" * Show licenses:    " + str(regexp_list))
        for regexp in regexp_list:
            match = _match_file(f, FilterAttribute.LICENSE, regexp)
            # any match => show_file becomes True
            show_file = show_file or match
            verbose("    * show license: " + regexp + " ==> " + str(match))

    for regexp_list in hide_licenses:
        verbose(" * Hide licenses:    " + str(regexp_list))
        for regexp in regexp_list:
            match = _match_file(f, FilterAttribute.LICENSE, regexp)
            if match:
                show_file = False
            verbose("    * hide license: " + regexp + " ==> " + str(match))


    if show_file:
        print(" f " + f['path'] + " " + str(licenses), file=stream)
    else:
        print("                     hide " + f['path'] + " " + str(licenses), file=stream)
    
def _output_single(f, show_files=True, show_dirs=False, file_key='included', stream=sys.stdout, hiders=None):

    if show_files and _isfile(f):
        _output_single_file(f, stream, hiders)
    elif show_dirs and _isdir(f):
        licenses = list(_dir_licenses(files, f, file_key))
        print(" d " + f['path'] + " " + str(licenses), file=stream)
        
            
def _output_filtered_helper(files, show_files=True, show_dirs=False, file_key='included', stream=sys.stdout, hiders=None):
    for f in files[file_key]:
        _output_single(f, show_files, show_dirs, file_key, stream, hiders)


def _output_filtered(files, show_files=True, show_dirs=False, stream=sys.stdout, show_excluded=False, hiders=None):
    if show_excluded:
        print("Excluded  " + str(_count_files(files['excluded'])))
        _output_filtered_helper(files, show_files, show_dirs, 'excluded', stream, hiders)

    print("Included  " + str(_count_files(files['included'])))
    _output_filtered_helper(files, show_files, show_dirs, 'included', stream, hiders)

    
def _output_filtered_include(files, show_files=True, show_dirs=False, stream=sys.stdout, hiders=None):
    print("Included  " + str(_count_files(files['included'])))
    _output_filtered_helper(files, show_files, show_dirs, 'included', stream, hiders)

def _output_filtered_exclude(files, show_files=True, show_dirs=False, stream=sys.stdout, hiders=None):
    print("Excluded  " + str(_count_files(files['excluded'])))
    _output_filtered_helper(files, show_files, show_dirs, 'excluded', stream, hiders)

    
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
            if not args['forced_config_mode']:
                warn("File '" + out_file + "' already exists. Remove it, use another name or use forced mode (-f))")
                exit(1)
        sys.stdout = open(out_file, 'w')
        
    print(json.dumps(args))  

def _verify_outbound_license(lic, project_license):
    verbose("verifying license: " + str(lic))
    verbose(" * with: " + str(project_license))
    # TODO: add proper implementation
    return True



