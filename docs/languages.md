# Languages and parity

[Русская версия](languages.ru.md)

Project Corpus has two first-class user languages: English and Russian.

- The original V1 templates in `template/en` and `template/ru` contain the same
  seven authority filenames and the same `Tasks/` and `Report/` structure.
- New projects use the V2 minimal template; see the [Quick Start](quickstart.md).
- README, access guides, client guides, project instructions, FAQ, security,
  contribution guidance, code of conduct, changelog, and publication checklist
  have English and Russian counterparts.
- Protocol filenames, access-mode constants, status constants, and Task/Report
  field names stay in English so different clients can share one interface.
- When behavior changes, update both language versions together.
- Automated tests verify file-set and invariant parity; they do not replace
  human translation review.

For an existing V1 project, copy its chosen language folder. For V2, follow the
Quick Start. The Markdown Protocol requires no installer; only the optional
local Runtime needs Python.
