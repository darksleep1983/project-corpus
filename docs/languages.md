# Languages and parity

Project Corpus has two first-class user languages: English and Russian.

- The README, client guides, project-instruction template, core Corpus template,
  FAQ, security guidance, contribution guidance, code of conduct, changelog, and
  publishing checklist have an English and Russian counterpart.
- The installer creates either an English or Russian Corpus with --language en or
  --language ru.
- Protocol filenames, tool names, JSON keys, command-line arguments, status
  constants, and authorization values stay in English so every client uses the
  same interface.
- When a user-visible behavior changes, update both language versions in the same
  pull request.
- Automated tests verify that both Corpus templates contain the same authority
  files and protocol invariants. They do not replace human translation review.

Use README.md for English and README.ru.md for Russian.

