# pyfilesync
## A python 3 script that synchronizes multiple folder pairs using a config file.


<p align="middle">
    <img src="doc/img/icon-default.png"/>
</p>

##

#### This script uses dirsync python project. To install dirsync, use the following command :
```sh
pip install dirsync
```

#### Then use the following command line to show usage :
```sh
python pyfilesync -h
```

## Config file format
A config file is a JSON file containing folder pairs to synchronize.
> **Note :**
> Environment variables can be used in source and target values, using either `$varname`, `${varname}` or `%varname%` format.

A minimal example with 2 folder pairs is shown below :
```json
{
    "pairs": [
        {
            "source": "~/foldertosave1/",
            "target": "/mnt/mysavedisk/targetfolder1"
        },
        {
            "source": "~/foldertosave2/",
            "target": "/mnt/mysavedisk/targetfolder2"
        }
    ]
}
```



Config file may contain optional include and/or exclude patterns. The priority is given to exclude files. If not given, include pattern target all files by default.
2 options are given to indicate include/exclude patterns :
- Regex expressions : use `"include_regex"` and/or `"exclude_regex"` fields
- Extended wildcard expressions : use "include" and/or "exclude" fields.\
  Examples : `'*.cpp'`, `'*.h'`, `'subDir1'`, `'subDir2*'`, `'*/subDir3/*.py'`\
  -> match paths that contain subDir1 or subDir2* as a folder name (like in `/tmp/subDir1/toto.xml`)
  -> every file whose path match `*/subDir3/*.py` is excluded (even under windows, since `/` is replaced by `\` automatically)

> **Note :**
> - Use `/` as a folder separator in include/exclude expressions\
> - include and exclude are case sensitive or case insensitive depending on filesystem of each source folder (auto-detection)

Example including mp4 and txt files but excluding files in any 'temp' subdir :
```json
{
    "pairs": [
        {
            "source": "~/foldertosave1/",
            "target": "/mnt/mysavedisk/targetfolder1",
            "include": ["*.txt", "*.mp4"],
            "exclude": ["temp"]
        }
    ]
}
```
Config files may also contain optional `cmp_files_content` boolean field to force comparison of files content instead of modification times :
```json
{
    "pairs": [
        {
            "source": "~/foldertosave1/",
            "target": "/mnt/mysavedisk/targetfolder1",
            "cmp_files_content": true,
        }
    ]
}
```
Last but not least, an optional `global` section allows to indicate parameters that applies to all pairs :
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
            "source": "~/foldertosave1/",
            "target": "/mnt/mysavedisk/targetfolder1",
            "include": ["*/subDir3/*.py"],
        }
    ]
}
```