# GitHub Pages enablement

The repository includes a build-only documentation workflow. It intentionally
has no `pages: write` or `id-token: write` permission and cannot deploy a site.

When the owner approves publication, configure **Settings → Pages → Build and
deployment → Source → GitHub Actions**. The proposed public URL is:

```text
https://darksleep1983.github.io/project-corpus/
```

Then review and move the deployment job below into an approved workflow. Keep
the `github-pages` environment protected so only `main` can deploy. GitHub's
Pages workflow requires `pages: write`, `id-token: write`, an environment, and
an uploaded Pages artifact; do not grant those permissions to ordinary test or
pull-request workflows.

```yaml
deploy:
  needs: build
  runs-on: ubuntu-latest
  permissions:
    pages: write
    id-token: write
  environment:
    name: github-pages
    url: ${{ steps.deployment.outputs.page_url }}
  steps:
    - id: deployment
      uses: actions/deploy-pages@v4
```

Owner approval is required because enabling Pages and granting deployment
permissions changes public GitHub behavior.
