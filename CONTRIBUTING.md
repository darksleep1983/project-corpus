# Contributing

[Русская версия](CONTRIBUTING.ru.md)

Keep changes small, reviewable, and compatible with all three access modes.

Before opening a pull request:

1. run `python -m unittest discover -s tests -v` if Python 3.11+ is available;
2. do not add secrets, machine-specific paths, generated user Corpus data, or
   backups;
3. update English and Russian user documentation together;
4. keep the seven authority filenames and protected-file rules consistent;
5. explain any change to access modes, synchronization, or safety boundaries;
6. do not add a bundled server or required user runtime without an explicit
   architecture decision.

Python is used only for repository tests; Project Corpus users do not need it.
