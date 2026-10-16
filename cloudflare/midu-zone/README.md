# Shared Cloudflare zone

This stack owns only the existing full `midu.com.au` zone. It does not create DNS records, manage project deployments or change the registrar delegation. Cloudflare-assigned nameservers remain in place; registration stays at VentraIP. Zone deletion/replacement is blocked by lifecycle protection.

## Resource ownership

Each resource has one Terraform state owner:

| Repository | Ownership |
| --- | --- |
| `SongGithub/personal-infra` | Shared `midu.com.au` Cloudflare zone |
| `SongGithub/midu-site` | Public `www` and `blog` CNAME records and this site's publishing workflow |
| Private `SongGithub/midu-learning` | `learn` CNAME, learning Pages project/domain, four Access apps and their policies |

Project stacks take the existing zone ID as an input. They do not read each other's state, create another zone, or manage each other's resources. The blog record remains part of the public website's DNS configuration; its content repository is unchanged. VentraIP registration/nameserver delegation and the existing Google OAuth identity provider remain outside these stacks.

## Credentials and state

Use Terraform 1.16.6 (CI version; minimum 1.7) and the committed provider lockfile, Cloudflare provider 5.28.0. Supply `CLOUDFLARE_API_TOKEN` through your shell environment. Never paste it into a `.tf` file or commit it. Copy `terraform.tfvars.example` to ignored `terraform.tfvars`, replace all placeholders, and restrict the file to your user (`chmod 600 terraform.tfvars`). These examples contain dummy IDs, not working account configuration.

For discovery/adoption, use read-only token permissions. Editing later needs the corresponding Edit/Write permissions, scoped to the owning zone/account. Do not give project stacks permission to change the shared zone.

State is local by default and may contain private values even when Terraform marks them sensitive. `.gitignore` is not encryption: keep state, backups and saved plans on protected storage and back them up privately. Use one operator at a time. Before multiple people or CI apply changes, configure a private encrypted remote backend with locking. No Cloudflare token or state is stored in GitHub Actions; CI only validates mock plans.

## Adopt existing resources first

This is configuration prepared from the verified dashboard setup; a live API import/no-op plan is still required. It is not evidence that the live resources are already under Terraform management.

1. Export DNS and record Access rules privately before adoption. Collect actual resource IDs from Cloudflare using a read-only token.
2. Fill the ignored input file and export your token in the shell. Run these commands from this directory:

```sh
terraform init -input=false -lockfile=readonly
terraform fmt -check -recursive
terraform validate
terraform test -var-file=terraform.tfvars.example
python3 -m unittest discover -s tests -p 'test_*.py'
terraform plan -out=adopt.tfplan
terraform show -json adopt.tfplan | python3 check_adoption.py
```

The guard requires the entire stack and rejects every create, update, replacement and delete, plus incomplete/failed plans. Stop if it refuses. Reconcile configuration against the live API; do not hide differences with `ignore_changes` or use `-target`. Review the human-readable saved plan privately. Only after it shows imports with zero live changes:

```sh
terraform apply adopt.tfplan
terraform plan -detailed-exitcode
```

The second command must exit 0 (no changes), not 2 (changes) or 1 (failure). Import/apply records ownership in state; it must not recreate the live resources. Keep import blocks/IDs for recovery. Do not apply a new plan with an empty state or remove lifecycle protection to force a replacement. `prevent_destroy` is a backstop while the resource block exists, not a substitute for review or a state backup.

## Operate and recover

For subsequent changes, edit the owning stack, run its mock tests, and review a saved real `terraform plan`. The adoption guard intentionally rejects configuration changes; it is for initial adoption/no-op checks. Apply a reviewed saved change plan manually, verify the live endpoint checks in the deployment runbook, and retain a protected state backup. Infrastructure never auto-applies on push.

Reverting Git code alone does not revert infrastructure. Restore the intended configuration, plan again and review before applying. If state is lost, recover its private backup or re-import the same live IDs. During any future ownership move, remove the resource from the old state without destroying it, then import into the new state; never let two states manage it concurrently.

## Sources

- [Pinned Cloudflare provider resource documentation](https://github.com/cloudflare/terraform-provider-cloudflare/tree/v5.28.0/docs/resources)
- [Cloudflare resource adoption](https://developers.cloudflare.com/terraform/advanced-topics/import-cloudflare-resources/) (some examples are v4; this code uses the pinned v5 schema).
- [Terraform import blocks](https://developer.hashicorp.com/terraform/language/import) and [mock provider tests](https://developer.hashicorp.com/terraform/language/tests/mocking).

Token permissions: Zone Read for adoption, Zone Edit for reviewed zone changes. The guard expects exactly one managed zone. Adopt this foundation before project stacks, then pass its actual zone ID as a private input. No account-wide identity settings or paid subscriptions are changed.

## Existing AWS pipeline

This repository also contains a legacy Travis pipeline that deploys AWS infrastructure. Cloudflare-only review commits and the eventual merge commit must include `[skip travis]` so that pipeline is not triggered. This marker is specific to Travis; the new GitHub Actions validation still runs. The AWS pipeline itself is unchanged. See [Travis build skipping](https://docs.travis-ci.com/user/customizing-the-build/#skip-a-build).
