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
Field name | default<br>value | global<br>section | Description
---: | :---: | :---: | :---
`left`            |             | no  | **-> mandatory**<br>left (source) folder to synchronize from. 
`right`           |             | no  | **-> mandatory**<br>right (target) folder to synchronize to.
`name`            |             | no  | name of the pair. only `_`, `-` and alphanumeric characters are allowed.<br>if not set, a name is automatically generated.
`include`         | **[ '*' ]** | yes | list of **wildcard** expressions that filter the left files to synchronize.
`exclude`         |  **[ ]**    | yes | list of **wildcard** expressions that filter out paths to synchronize.<br>the exclude filters are prioritary over include filters.
`include_regex`   |   **[ ]**   | yes | list of **regular expressions** that filter the left files to synchronize.<br>note: `include_regex` list is appended to `include`, if any.
`exclude_regex`     | **[ ]**   | yes | list of **regular expressions** that filter out paths to synchronize.<br>the exclude filters are prioritary over include filters.<br>note: `include` list is appended to `exclude`, if any.
`cmp_files_content` | **false** | yes | boolean field to force files content instead of modification times as comparison criteria<br>example: ```"cmp_files_content": true```

### More info on include/exclude
- Config file may contain optional include and/or exclude patterns. If not given, include pattern target all files by default.
- The priority is given to exclude patterns over include.
- The resulting file filter is used to detect missing files in right folder (left-only files), as well as files to remove (right-only files)
- 2 options are given to indicate include/exclude patterns :
  - Regex expressions : use `"include_regex"` and/or `"exclude_regex"` fields
  - Extended wildcard expressions : use "include" and/or "exclude" fields.\
  Examples : `'*.cpp'`, `'*.h'`, `'subDir1'`, `'subDir2*'`, `'*/subDir3/*.py'`\
  -> match paths that contain subDir1 or subDir2* as a folder name (like in `/tmp/subDir1/toto.xml`)
  -> every file whose path match `*/subDir3/*.py` is excluded (even under windows, since `/` is replaced by `\` automatically)
- **Folder separator** : Always Use `/` as folder separator in any include/exclude expressions
- **case sensitivity** : include and exclude are case sensitive or case insensitive depending on left folder filesystem (auto-detected for each pair)

Example including mp4 and txt files but excluding files in any 'temp' subdir :
```json
{
    "pairs": [
        {
            "left": "~/foldertosave1/",
            "right": "/mnt/mysavedisk/rightfolder1",
            "include": ["*.txt", "*.mp4"],
            "exclude": ["temp"]
        }
    ]
}
```

