# Shared maintenance and review

Maintenance checks documentation that was already accepted, keeps the results, and prepares proposals. It can keep running when reviewers are missing. Sensitive changes stay pending.

The same text in Spanish is [mantenimiento](https://comunidad-de-inteligencia.github.io/osint-atlas/mantenimiento/).

## What each run does

- **Daily:** contact pages, sources, and critical procedures, plus editorial reviews that are due again.
- **Weekly:** the accepted sources and references, including API documentation pages. API means Application Programming Interface.
- **Monthly:** candidates from six institutional data catalogs, the OSINT Brazuca repository, and the institutional channel of the Instituto Nacional de Ciberseguridad (INCIBE), Spain's national cybersecurity institute. It reads HTML and Markdown links and keeps provenance and the known terms. HTML means HyperText Markup Language. A new link on the same domain can also be a candidate. OSINT means Open Source Intelligence.
- **On a proposal:** validation of data, documents, the index, and tests.

The [latest successful runs, and the incidents](https://github.com/Comunidad-de-Inteligencia/osint-atlas/blob/maintenance-state/README.md), live on the state branch.

## How to read a technical result

- **ok / not-modified:** a usable response, or the same as the previous one.
- **blocked:** access blocked, or a redirect outside the accepted destinations. Do not assume that creating an account is enough.
- **auth-required:** the service asked for authentication.
- **rate-limited:** there is a request limit. The indicated wait is respected, within the time available.
- **temporary-error:** network, certificate, timeout, or server failure. An incident opens after three failed runs in a row.
- **offline:** a removal or absence response. It needs review. It does not delete the source.
- **partial:** the whole document could not be read within the limits. An incomplete fingerprint is not compared as if it were complete.
- **redirected:** the documentation answers at another address on an accepted domain. Someone should see whether the link should change.

Requests are limited per domain, with short retries. Responses are not executed and are not adopted as instructions. Personal notices and case content are not downloaded. Sensitive sources have their own documentation addresses for maintenance.

The report and each entry summarize the latest check with one word and, when it exists, the date. The word comes from the published state. It is not copied into the entry file.

- **disponible:** the page answered (ok, redirected, not-modified, or partial).
- **sin respuesta:** there was no usable answer (offline, temporary-error, blocked, rate-limited, or retired).
- **autenticación:** the service asked for identification (auth-required).
- **sin comprobación:** there is no published run for that page, or the catalog was generated without the state.

## What is kept

The `maintenance-state` branch keeps the technical state and a readable report. It stores the latest run, fingerprints, cache headers, consecutive failures, and incidents. The short history lasts ninety days. Actions artifacts last seven. Full page bodies are not stored.

A change in the visible text can produce an editorial proposal even when the page answers. The proposal links the source and names the previous fingerprint and the observed one. A person has to look at the difference. Automation does not give that change a legal meaning.

## How the work is assigned

The register `data/maintainers.yaml` stores accounts, specialties, primaries, backups, and checked permissions. There is a coordinator. The specialist seats are still empty.

Incidents are grouped by specialty and purpose, with a stable identity. After forty-eight hours for critical work, or seven days for ordinary work, the backup is chosen. If a competent person is missing, the state shows `missing-reviewer`. An assignment is not invented.

For sensitive work, a competent person other than the one who wrote the change has to approve that version. A bot account does not replace a person. An old approval does not count if the proposal changed.

The check uses the register on the base branch and looks up the real permissions on GitHub. The daily run, when it publishes, looks again at open proposals and asks the right person, primary or backup, to review. After a review it can also update from a comment on the proposal or from the manual human-review run. It does not need to interpret the comment text.

## Closing an incident

A recovery closes, by itself, only technical incidents that were explicitly resolved. An editorial proposal needs review.

To record that a content change was looked at, a reviewed proposal adds to `data/resolutions.yaml` the incident key, the checked fingerprint, and the review link. The next check resolves only that fingerprint. If the page changes again, another observation appears on the same grouped proposal.

Candidates stay pending selection and review. They are not added on their own. Closing an editorial incident is a human decision, not a technical check.

## Turning runs on, and spend

The three runs can be started by hand. The `publish` parameter is off by default: a trial leaves artifacts; turning it on publishes the technical state and the proposals. Start the trials one after another. They share a queue so they do not overwrite the history, and GitHub can replace a run that is still waiting.

Before a schedule is enabled, look at the trials, the duration, the quotas, and the spending limit. Missing specialists do not block the technical checks. If spending control is not confirmed, the schedules stay manual.

GitHub refused to protect the private branch because the plan does not include it. The billing lookup did not give enough information. The subscription has not been changed and the schedules have not been enabled. Without that protection, the review state warns, and it does not stop an administrator account from landing a change by hand.

The date of the latest run matters: a GitHub schedule can lag. The MCP marks a daily run as late when it has no success for forty-eight hours, a weekly run after ten days, and a monthly run after forty days. MCP means Model Context Protocol. If no run happens, it cannot create a new warning by itself. The report and the MCP can show that absence.

## Local trials

From the root, with dependencies installed:

~~~console
uv run python tools/check_links.py --scope critical --output reports/daily.json
uv run python tools/check_reviews.py
uv run python tools/check_links.py --scope all --state reports/state.json --output reports/weekly.json
uv run python tools/discover_candidates.py --state reports/state.json
~~~

These operations do not send reports to authorities or to platforms.
