# V1 to V2 migration contract

Migration is inspectable, explicit, and non-destructive by default.

## Required behavior

1. Read all seven V1 current files completely.
2. Detect duplicates, missing files, and conflicting project identity or status.
3. Produce a migration plan without modifying V1.
4. Map stable identity to PROJECT and operational state to STATUS.
5. Preserve Tasks, Reports, and provenance.
6. Treat loaders and handoffs as source material, not independent V2 authority.
7. Require an explicit apply operation to create a separate V2 destination.
8. Preserve the V1 source until the owner separately authorizes cleanup.

Migration must not convert an absolute V1 project path into portable PROJECT
authority. Runtime may offer it as an untrusted suggestion for the external
trust grant.

