# Languages and parity

[Русская версия](languages.ru.md)

Project Corpus has two first-class user languages: English and Russian.

- `template/en` and `template/ru` contain the same seven authority filenames and
  the same `Tasks/` and `Report/` structure.
- README, access guides, client guides, project instructions, FAQ, security,
  contribution guidance, code of conduct, changelog, and publication checklist
  have English and Russian counterparts.
- Protocol filenames, access-mode constants, status constants, and Task/Report
  field names stay in English so different clients can share one interface.
- When behavior changes, update both language versions together.
- Automated tests verify file-set and invariant parity; they do not replace
  human translation review.

To start, copy the language folder you prefer. No installer is required.
