# Contributing

[Русская версия](CONTRIBUTING.ru.md)

Keep changes small, reviewable, and compatible with the security boundary.

Before opening a pull request:

1. run `python -m unittest discover -s tests -v`;
2. do not add secrets, machine-specific paths, generated Corpus data, backups, or audit logs;
3. update both English and Russian user documentation when behavior changes;
4. explain any change to the write allowlist, path validation, backup logic, or client connection model.
