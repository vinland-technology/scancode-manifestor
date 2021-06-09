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

EXCLUDED_FILES_EXPLANATION="This sections lists the files that have been excluded and the filters. Excluding files is used to mark files that are not distributed to end user and thus not needed to consider while verifying compliance. The files have been excluded using either 'file filter' or 'license filter'. Each file is listed with the type of filter and the matching string causing the exclusion."

EXCLUDED_FILES_FILTER_EXPLANATION="This sections lists the file exclusion filters. For each filter a list files excluded by this filter is displayed "

EXCLUDED_FILES_FILES_EXPLANATION="This sections lists the files excluded by filters. For each file the file type and the filter causing the exclusions is displayed"

LICENSE_EXPLANATION="This section lists the licenses of the included and excluded files"

LICENSE_ALL_EXPLANATION="This section lists the licenses of the all the files, regardless of whether they are included or excluded"

LICENSE_INCLDUED_EXPLANATION="This section lists all the licenses of the included files. Each license has a list of files licensed under that licenes"

LICENSE_EXCLDUED_EXPLANATION="This section lists all the licenses of the excluded files. Each license has a list of files licensed under that licenes"

