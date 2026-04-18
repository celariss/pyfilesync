## 2.1.0 (2026-04-15) :
- added 2 commands to manage history mode :
	- show_history
	- clean_history
- added tests for history mode
- improved filesystem mocking system for testing purpose (FSMock)
- files to be removed on right folder are first saved in history

## v2.0.0 (2026-04-08) :
- added history mode :
	- files are saved in an history mode directory before any update
	- the number of file versions to save are configurable (see `history_mode` parameter in readme)
- change in command line : a json string can replace the config file (for scripting use)
