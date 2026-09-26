# Contributing

[Русская версия](CONTRIBUTING.ru.md)

Keep changes small, reviewable, and compatible with the Markdown Protocol and
optional Runtime.

Before opening a pull request:

1. run `python -m unittest discover -s tests -v` if Python 3.11+ is available;
2. do not add secrets, machine-specific paths, generated user Corpus data, or
   backups;
3. update English and Russian user documentation together;
4. keep V1's seven authority filenames and protected-file rules consistent
   where V1 behavior is documented;
5. explain any change to access modes, synchronization, or safety boundaries;
6. do not add a bundled server or required user runtime without an explicit
   architecture decision.

The Markdown Protocol does not require Python. Python 3.11+ is required only for
the optional local Runtime and repository tests.
