# Image releases

The manual `release images` workflow builds API, web and backup images from the selected workflow commit, tags them with the full commit SHA, and publishes to GHCR. Deployment consumes immutable registry digests rather than tags. No workflow was dispatched and no image or public deployment was published during implementation.

The build job alone has `packages: write`; other jobs have `contents: read`. Authentication uses the repository `GITHUB_TOKEN` and `docker login --password-stdin`, following [GitHub's package publishing guidance](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions). Existing packages must grant this repository Actions access. Images carry repository/revision labels. These are Linux images for the single-VM stack, not desktop-game releases.

`deploy` defaults to false. Enabling it selects the `production` GitHub environment, whose deployment protections should be configured before first use. The workflow does not substitute for green CI: select a commit with successful backend, browser, Godot, production-smoke and budget checks.

## Host prerequisites

Prepare a Linux host with Docker, Compose 2.24.4 or later (`!reset` support), SSH and a deploy user allowed to manage Docker. The domain's DNS must point to it, and inbound 80/443 must be reachable. Preserve SSH host identity through a trusted independent channel; never blindly accept `ssh-keyscan` output.

Configure environment secrets `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY` and `DEPLOY_KNOWN_HOSTS`. `DEPLOY_HOST` is a DNS name or IPv4 address, SSH uses port 22. Set environment variable `DEPLOY_ROOT`, an existing absolute directory such as `/srv/fundforge`, owned by the deploy user. Paths are restricted to letters, numbers, slash, underscore and hyphen. Put the production settings from `deploy/.env.example` in `DEPLOY_ROOT/.env`; the workflow never transfers database secrets.

Authenticate the host to GHCR ahead of time if packages are private, with an independently provisioned read-packages credential. The workflow's short-lived publishing token is not copied to the host. For public packages the host can pull anonymously. Retain off-host backup storage and recovery credentials separately; the workflow does not create them.

## Local validation

Use placeholder environment values and placeholder digests to render configuration without contacting a host:

```bash
digest=sha256:$(printf '0%.0s' {1..64})
bash deploy/release.sh deploy/.env.example \
  "ghcr.io/example/fundforge-api@$digest" \
  "ghcr.io/example/fundforge-web@$digest" \
  "ghcr.io/example/fundforge-backup@$digest" --dry-run
```

Dry-run validates image syntax, the environment file and Compose rendering only. It does not build, pull, connect to a database or start containers. The existing `deploy/smoke.sh` exercises the built stack separately. Do not print full rendered Compose configuration with production credentials.

## Upgrade behavior

Each deployment receives its own `releases/SHA-RUN-ATTEMPT/deploy` directory. It does not reset a checkout, replace local source edits, delete volumes or prune earlier releases. All releases use the existing `fundforge` Compose project and named database/backup volumes.

The script pulls all three images before interrupting service. For an existing API it stops web/API ingress and the authoritative clock, dumps through the running old backup image, and restores/verifies the archive through old and candidate code. A failure before replacement restarts the old API/web containers. A populated database without its running old API/backup refuses the upgrade; restore the prior stack first. A genuinely empty database is treated as first install.

Candidate verification rejects incompatible pinned rooms by default. Different rules versions are never silently upgraded. `allow_incompatible` is an explicit operational acknowledgment, not proof of replay: affected rooms retain stored heads but cannot be played/reverified with candidate rules. Preserve the prior image/backup for those rooms. Use a separate old-rules stack/database if ongoing access is required; this script does not route rooms across versions.

The replacement starts with `--no-build --wait`, checks API readiness and the web root inside the Docker network, then records the three deployed digests. Public TLS, DNS and WebSocket routing still need external checks. A post-replacement failure does not automatically roll back: migrations can make an old binary incompatible with the live database. Keep the pre-upgrade archive and manifest, inspect logs, and test an isolated restore before a deliberate recovery. No database down/volume deletion command is part of this release path.

Remaining external prerequisites are actual host/domain access, verified host keys, registry read access, environment protection, off-host backups and public endpoint verification. This automation does not claim any of them have been supplied.
