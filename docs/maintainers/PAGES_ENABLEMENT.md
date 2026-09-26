# GitHub Pages deployment

The documentation site is published at:

```text
https://darksleep1983.github.io/project-corpus/
```

The active [documentation workflow](https://github.com/darksleep1983/project-corpus/blob/main/.github/workflows/docs.yml) builds
the site with `mkdocs build --strict` and deploys the Pages artifact from
`main`. Pull requests build and validate the site without deploying it. The
workflow grants Pages deployment permissions only to its deploy job.

Any future change to Pages settings or deployment permissions remains an
owner-controlled repository action.
