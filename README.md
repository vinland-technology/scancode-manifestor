# Scancode Manifestor

Creates package manifest from a Scancode report.

# Manifest

A manifest, as defined by us, for a software package contains information need for license compliance work. The manifest includes information about:

* project information

    * name

    * version

    * sub package

    * home page

* license declaraion

* copyright holders

# Creating the manifest

With Scancode you get a lot of information information about the
scanned source code. In order to create a manifest from a Scancode report we need to:

* curate identified licenses that are incorrect or missing

* filter out files that are not distributed

# Scancode Manifestor workflow


# Terms

* **hide** - when in `filter` mode, you can hide files from being outputed. These files are not excluded form the distributed file. This is useful when resolving problems (which you do in filter mode). If the file is not distributed, use `exclude` instead.

* **exclude* - you typically mark a files as excluded when the files will not end up being distributed. If you just want to not see the file (in filter mode), use `hide` instead. You can use this in combination with `include`.

* **include** - same as `exclude` but rather the opposite. This specifies which files actually are distributed. You can use this in combination with `exclude`.

* **scancode report** - a report as produced by [Scancode](https://github.com/nexB/scancode-toolkit). Make sure to use (at least) the flags `-clipe` to Scancode.

* **manifest** or *conclusion report* - a manifest contains information needed to verify license compliance. See above for what a manifest contains.

* **modes** - the tool works in different modes which reflects a typical workflow for a officer/engineer working with license compliance

    * **filter** - this mode lets you define what files are distributed bu using `include`/`exclude`. While in `filter` mode you can also hide files from output using the `hide` commands

    * **validate** - in this step you can verify that all information is present and the conclusion is OK before creating a report. From this point now `hide` options are allowed.

    * **create** - in this step you create the manifest-



