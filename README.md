# pyfilesync
## A python 3 script that synchronizes multiple folder pairs using a config file.


<p align="middle">
    <img src="doc/img/icon-default.png"/>
</p>

##


#### Use the following command line to show usage :
```sh
python pyfilesync -h
```

## Config file format
A config file is a JSON file containing folder pairs to synchronize.
> **Note :**
> Environment variables can be used in any field that receives a path, using either `$varname`, `${varname}` or `%varname%` format.

A minimal example with 2 folder pairs is shown below :
```json
{
    "pairs": [
        {
            "left": "~/foldertosave1/",
            "right": "/mnt/mysavedisk/rightfolder1"
        },
        {
            "left": "~/foldertosave2/",
            "right": "${TARGETDIR}"
        }
    ]
}
```

An optional `global` section allows to indicate parameters that applies to all pairs :
- all parameters in `global` are optional
- include/exclude lists are appended to include/exclude in each pair

```json
{
    "global": {
        "include": ["*.txt", "*.mp4"],
        "exclude": ["temp"],
        "include_regex": [".*/somedir/.*\\.bat"],
        "exclude_regex": [".*test"],
        "cmp_files_content": true,
    }
    "pairs": [
        {
            "left": "~/foldertosave1/",
            "right": "/mnt/mysavedisk/rightfolder1",
            "include": ["*/subDir3/*.py"],
        }
    ]
}
```

All available parameters are presented in table below :
Field name | | global<br>section | Description
---: | :---: | :---: | :---
`left` | **mandatory** |  | left (source) folder to synchronize from 
`right` | **mandatory** |  | right (target) folder to synchronize to 
`name` | **optional** |  | name of the pair. If not set, a name is automatically generated
`include` | **optional** | yes | list of **wilcards** expressions that filter the left files to synchronize
`exclude` | **optional** | yes | list of **wildcars** expressions that filter out paths to synchronize.<br>The exclude filters are prioritary over include filters.
`include_regex` | **optional** | yes | list of **regular expressions** that filter the left files to synchronize.<br>note: `include_regex` list is appended to `include`, if any.
`exclude_regex` | **optional** | yes | list of **regular expressions** that filter out paths to synchronize.<br>The exclude filters are prioritary over include filters.<br>note: `include` list is appended to `exclude`, if any.
`cmp_files_content` | **optional** | yes | boolean field to force files content instead of modification times as comparison criteria<br>example: ```"cmp_files_content": true```

## More info on include/exclude
Config file may contain optional include and/or exclude patterns. The priority is given to exclude files. If not given, include pattern target all files by default.
2 options are given to indicate include/exclude patterns :
- Regex expressions : use `"include_regex"` and/or `"exclude_regex"` fields
- Extended wildcard expressions : use "include" and/or "exclude" fields.\
  Examples : `'*.cpp'`, `'*.h'`, `'subDir1'`, `'subDir2*'`, `'*/subDir3/*.py'`\
  -> match paths that contain subDir1 or subDir2* as a folder name (like in `/tmp/subDir1/toto.xml`)
  -> every file whose path match `*/subDir3/*.py` is excluded (even under windows, since `/` is replaced by `\` automatically)

> **Note :**
> - Use `/` as a folder separator in include/exclude expressions\
> - include and exclude are case sensitive or case insensitive depending on filesystem of each left folder (auto-detection)

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

