# Using the catalog with an assistant

## What the connector can do

The local Model Context Protocol (MCP) can search entries, territories, procedures, documentation, and official assistance routes. It returns references, coverage, and review state. It does not visit the sources while answering, it does not watch channels, and it does not send reports.

## Install

You need Python 3.12, Git, and uv. Clone the repository with your usual permissions. From the root:

~~~console
uv sync --locked
uv run python tools/build_catalog.py --check
uv run osint-atlas-mcp
~~~

Configure the MCP client to run `uv` with the arguments `--directory`, the absolute path of the repository, `run`, `--locked`, and `osint-atlas-mcp`. Transport is stdio, standard input and output. Diagnostic messages use the error stream.

## Sync a dedicated copy

Sync is off by default. To turn it on in a copy that only runs the connector, set `OSINT_ATLAS_DEDICATED` to `1` in the client.

The launcher syncs before it loads the server. It only accepts the remote of this repository, including an older address that still points at the same project, and only updates that fit `main`. It prepares a separate snapshot, installs the locked dependencies, and validates the data before starting another process. It does not merge conflicts and it does not overwrite your changes.

If Git, the network, a permission, a dependency, or validation is missing, it keeps the last snapshot that worked. Age comes from the commit, not from the time the files were copied. If that cannot be known, the value is null.

## Tools

- `search_resources`: text, territory, category, scenario, access, `input_type`, `output_type`, and `platform`.
- `get_resource`: the entry, references, review, and coverage.
- `get_jurisdiction`: territory notes, the entry count, and one page of results.
- `search_playbooks` and `get_playbook`: search and read procedures.
- `search_docs` and `get_doc`: search and read the reference documentation.
- `list_scenarios`: coverage and gaps, for one territory or for the whole matrix.
- `get_reporting_routes`: routes filtered by scenario, territory, platform, and kind of action.

Searches use `limit` and `offset`. They return `count`, `total`, and `next_offset`. Filters apply before paging. An empty query lists items. A query made only of punctuation returns `invalid_query`. An unknown territory or filter returns `unknown_filter`.

Catalog identifiers and names are accepted, without regard to case or accents. Scenario and type names follow the project taxonomy.

## Examples

~~~json
{"query":"","jurisdiction":"España","scenario":"procurement","limit":5,"offset":0}
~~~

The result offers up to five entries and the total that matches the filters. If `next_offset` is a number, use it for the next page.

~~~json
{"scenario":"platform-report","jurisdiction":"ES","platform":"telegram","kind":"platform-report"}
~~~

This query describes the platform channel. It sends nothing and it is not a complaint.

`get_doc` accepts identifiers such as `empezar`, `mantenimiento`, `ia`, `business`, and `es/empresas/de-handelsregister`. `search_docs` returns the identifiers that exist.

## How an assistant should answer

Cite the responsible source and keep the limits. Say which review is missing and separate evidence, observation, and inference. In sensitive scenarios, keep wording such as “possible” or “not confirmed”.

Results separate the catalog version, the index state, the age of the commit, and maintenance. An old index is rebuilt atomically. If the new content is invalid, `last-valid-snapshot` names the previous copy.

Local technical measurements are read from `.cache/maintenance-state/state.json`. The dedicated copy tries to fetch that file from the `maintenance-state` branch. Without a copy of the state, the answer is unknown, never a run that did not happen.

The same text in Spanish is [usar el catálogo con un asistente](https://comunidad-de-inteligencia.github.io/osint-atlas/ia/).
