# pyfilesync
## A python 3 script that synchronizes multiple folder pairs using a config file.


<p align="middle">
    <img src="doc/img/icon-default.png"/>
</p>

##

## Main features
- mode of operation : one-way mirroring (left to right folder)
- 'Compare' command : finds and prints differences between left and right folders without doing actual synchronization
- 'sync' command for actual synchronization
- option allowing to process a subset of folder pairs
- 'list' command : prints all folder pairs from config file
- comparison criteria : file size and modification date (or file size and file content if requested)
- case sensitivity of filesystem is detected to interpret include/exclude pattern correctly


## Command line
#### Use the following command line to show usage :
```sh
python pyfilesync -h
```

## Config file format
A config file is a JSON file containing folder pairs to synchronize.

> **Environment variables can be used in any field that receives a path, using either `$varname`, `${varname}` or `%varname%` format.**

A minimal example with 1 folder pair is shown below :
```json
{
    "pairs": [
        {
            "left": "$HOME",
            "right": "/mnt/mysavedisk/rightfolder1"
        }
    ]
}
```

An optional `global` section sets parameters that applies to all pairs :
- all parameters in `global` are optional
- include/exclude lists in global are appended to include/exclude in each pair

```json
{
    "global": {
        "include": ["*.txt", "*.mp4"],
        "exclude": ["temp", "*.bak", "*.tmp"],
        "include_regex": [".*/somedir/.*\\.bat"],
        "exclude_regex": [".*test"]
    },
    "pairs": [
        {
            "name": "Personal_Data",
            "left": "~/personalfolder/",
            "right": "/mnt/mysavedisk/rightfolder1",
            "include": ["*/subDir3/*.py"],
            "cmp_files_content": true,
        },
        {
            "name": "Bookmarks",
            "left": "/mnt/data/internet/",
            "right": "${TARGETDIR}"
        }
    ]
}
```

All available parameters are presented here after :
Field name        | default<br>value | global<br>section | Description
---:              | :---:       | :---: | :---
`left`            |             | no  | **-> mandatory**<br>left (source) folder to synchronize from. 
`right`           |             | no  | **-> mandatory**<br>right (target) folder to synchronize to.
`name`            |             | no  | name of the pair. only `_`, `-` and alphanumeric characters are allowed.<br>if not set, a name is automatically generated.
`include`         | **[ '*' ]** | yes | list of **wildcard** expressions that filter the left files to synchronize.
`exclude`         |  **[ ]**    | yes | list of **wildcard** expressions that filter out paths to synchronize.<br>the exclude filters are prioritary over include filters.
`include_regex`   |   **[ ]**   | yes | list of **regular expressions** that filter the left files to synchronize.<br>note: `include_regex` list is appended to `include`, if any.
`exclude_regex`     | **[ ]**   | yes | list of **regular expressions** that filter out paths to synchronize.<br>the exclude filters are prioritary over include filters.<br>note: `include` list is appended to `exclude`, if any.
`cmp_files_content` | **false** | yes | boolean field to force files content instead of modification times as comparison criteria<br>example: ```"cmp_files_content": true```

### About include/exclude patterns
- Config file may contain optional include and/or exclude patterns.
- All files are included by default.
- The priority is given to exclude patterns over includes, in this order :
    - exclude patterns in global section
    - exclude patterns in current pair parameters
    - include patterns in global section
    - include patterns in current pair parameters
- The resulting file filter is used to detect missing files in right folder (left-only files), as well as files to remove (right-only files)
- Each pattern is tested on file path AND filename alone
- **Folder separator** : Always use `/` separator in wildcards and regex expressions, for `\` is replaced by `/` automatically in all file paths before trying to match patterns, so that it will give the same results under Windows and Linux.
- **case sensitivity** : include and exclude are case sensitive or case insensitive depending on left folder filesystem (auto-detected for each pair)
- Be aware that file paths are all made relative to the left/right folders (left/right folders part of any file path is removed before regex matching)
- 2 options are given to indicate include/exclude patterns (NOT mutually exclusive) :
  - Regex expressions : use `"include_regex"` and/or `"exclude_regex"` fields
  - Extended wildcard expressions : use "include" and/or "exclude" fields.

#### Examples of wildcard expressions
Expression        | Description
:---              | :--- |
`'*.cpp'`         | matches path for files (not dir) that have a `.cpp` filename extension
`'book_num??.txt'`| matches paths for files (not dir) like `'book_num03.txt'` or `'book_num29.txt'`
`'*/subDir1/'`      | matches any path that contains a directory named `subDir` anywhere |
`'/rootDir/'`     | matches only paths that start with `rootDir` directory |
`'*/subDir/*.py'`   | matches paths that contain a dir named  `subDir` and whose filename ends with `.py`
`'/subDir1/subDir2/myfile.py'` | matches exact file path (from 'pair' base folder)
`'/subDir1/subDir2/'` | matches exact directory path (from 'pair' base folder), and its content


Example including mp4 and txt files but excluding files in any 'temp' subdir :
```json
{
    "pairs": [
        {
            "left": "~/foldertosave1/",
            "right": "/mnt/mysavedisk/rightfolder1",
            "include": ["*.txt", "*.mp4"],
            "exclude": ["temp/"]
        }
    ]
}
```

