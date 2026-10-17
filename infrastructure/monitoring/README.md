# Cloud monitoring as code

Log-based metrics and alert policies for the hosted API (ADR 024, telemetry contract section 5). The v2.3.0 release records seven policies applied to staging on 14 October 2026. This is historical deployment evidence, not a fresh cloud-state check; see the [hosting tracker](../../docs/plans/hosting-execution-tracker.md).

| Path | What it is |
|---|---|
| `metrics/*.yaml` | One Cloud Logging log-based metric per file, in the format `gcloud logging metrics create --config-from-file` reads. Each counts or measures one telemetry event from the `football-api` and `football-api-staging` Cloud Run services. |
| `alerts/*.json` | One Cloud Monitoring alert policy per file. Each has a documentation block saying what it means and what to check first. |
| `apply.sh` | Creates or updates metrics and recreates matching policies. `--dry-run` prints the commands instead. |
| `remove.sh` | Deletes exactly what `apply.sh` creates. `--dry-run` prints the commands instead. |

## Apply

You need `gcloud` signed in to the project with the alpha component (`gcloud components install alpha`), and an email notification channel (Monitoring > Alerting > Edit notification channels). Its full name looks like `projects/<project>/notificationChannels/<id>`; keep it out of Git.

```sh
export PROJECT_ID=<your project id>
export NOTIFICATION_CHANNEL=<channel full name>
infrastructure/monitoring/apply.sh --dry-run   # check the commands first
infrastructure/monitoring/apply.sh
```

Running it again updates the metrics in place and recreates each policy, so there is always exactly one of each. Metrics only count log lines written after they exist.

After the first apply, send a few requests and check in Metrics Explorer that `api_requests` has a `status_class` label (it is extracted from the numeric `status` field) and that the PromQL alerts show data, since those two parts cannot be checked without a project.

## Remove

```sh
PROJECT_ID=<your project id> infrastructure/monitoring/remove.sh
```

## Cost

At this project's volume, log-based metrics and alert policies are expected to stay within Google Cloud's free allowances. Confirm that on Google's current Cloud Logging and Cloud Monitoring pricing pages before applying; this repository does not guarantee it.

## No uptime checks

There are no uptime checks on purpose: a probe every minute keeps the scale-to-zero API warm, which costs money and hides the cold-start behaviour the hosting plan measures (phase 6, point 11).
