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

## About scancode

ABOUT_SCANCODE_REPORT="About the report"

ABOUT_SCANCODE_REPORT_SCANCODE="Scancode report"

ABOUT_SCANCODE_REPORT_META="Meta information"

ABOUT_SCANCODE_REPORT_SETTINGS="Configuration"

## Conclusion section

CONCLUSION_EXPLANATION="This section lists the conclusion, of the included files, autmatically calculated by the tool."

CONCLUSION_HEADER="Conclusion"

CONCLUSION_COPYRIGHTS_HEADER="Concluded copyrights"

CONCLUSION_COPYRIGHTS_EXPLANATION="Copyright holders, of the included files, as detected by the tool."

CONCLUSION_LICENSES_HEADER="Concluded licenses"

CONCLUSION_LICENSES_EXPLANATION="Licenses as detected by the tool. The different licenses are simply AND:ed together and presented as \"Original\". The \"Original\" license expression is also simpled (boolean algebra) and presented as \"Simpified\"."

CONCLUSION_INCLUDED_LICENSES_HEADER="Licenses for included files"

#CONCLUSION_INCLUDED_LICENSES_EXPLANATION="Licenses ... more info soon"


## Licenses section

LICENSES_EXPLANATION="This section lists the licenses of the included and excluded files"

LICENSES_HEADER = "Licenses"

LICENSES_INCLUDED_FILES_HEADER = "Licenses for included files"

LICENSES_EXCLUDED_FILES_HEADER = "Licenses for excluded files"

LICENSES_ALL_EXPLANATION="This section lists the licenses of the all the files, regardless of whether they are included or excluded"

LICENSES_INCLDUED_EXPLANATION="This section lists all the licenses of the included files. Each license has a list of files licensed under that licenes. Files are linked to the actual files so you can easily check the source code yourself."

LICENSES_EXCLDUED_EXPLANATION="This section lists all the licenses of the excluded files. Each license has a list of files licensed under that licenes. Files are linked to the actual files so you can easily check the source code yourself"


## All files section

LICENSES_ALL_FILES_EXPLANATION="All licenses with files (under that license)."

LICENSES_ALL_FILES_HEADER="Licenses and files"



## Excluded files section

EXCLUDED_FILES_EXPLANATION="This sections lists the files that have been excluded and the filters. Excluding files is used to mark files that are not distributed to end user and thus not needed to consider while verifying compliance. The files have been excluded using either 'file filter' or 'license filter'."

EXCLUDED_FILES_HEADER="Excluded files (by filters)"

EXCLUDED_FILES_FILTERS_HEADER="Exclusion filters"

EXCLUDED_FILES_FILES_HEADER="Excluded files"

EXCLUDED_FILES_FILTERS_EXPLANATION="This sections lists the file exclusion filters. For each filter a list files excluded by this filter is displayed. Files are linked to the actual files so you can easily check the source code yourself."

EXCLUDED_FILES_FILES_EXPLANATION="This sections lists the files excluded by filters. For each file the file type and the filter causing the exclusions is displayed. Files are linked to the actual files so you can easily check the source code yourself. The filter is linked to the filter list in section \"" + EXCLUDED_FILES_FILTERS_HEADER + "\"."

## Included files section

INCLUDED_FILES_EXPLANATION="This sections lists the files that have been included, i.e distributed."

INCLUDED_FILES_HEADER="Included files by filters"

INCLUDED_FILES_FILTERS_HEADER="Inclusion filters"

INCLUDED_FILES_FILES_HEADER="Included files"

INCLUDED_FILES_FILTERS_EXPLANATION="This sections lists the file inclusion filters. For each filter a list files included by this filter is displayed. Files are linked to the actual files so you can easily check the source code yourself."

INCLUDED_FILES_FILES_EXPLANATION="This sections lists the files included by filters. For each file the file type and the filter causing the inclusions is displayed. Files are linked to the actual files so you can easily check the source code yourself. The filter is linked to the filter list in section \"" + INCLUDED_FILES_FILTERS_HEADER + "\"."

## Included files section

CURATED_FILES_EXPLANATION="This sections lists the included (distributed) files that have been curated."

CURATED_FILES_HEADER="Included files by curations"

CURATED_FILES_FILE_HEADER="File name pattern"

CURATED_FILES_MISSING_HEADER="Missing license"

CURATED_FILES_FILE_EXPLANATION="This sections lists the included files that have been curated, ordered by file matching expression. Files are linked to the actual files so you can easily check the source code yourself."

CURATED_FILES_MISSING_EXPLANATION="This sections lists the distributed files originally without license. Files are linked to the actual files so you can easily check the source code yourself."
