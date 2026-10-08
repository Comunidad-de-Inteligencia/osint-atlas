# How to contribute

You can improve an explanation, correct an entry, or fill a gap. Another person must be able to check the change. This is the English door. The [Spanish contributing guide](https://github.com/Comunidad-de-Inteligencia/osint-atlas/blob/main/CONTRIBUTING.md) is the same procedure.

Catalog entries and procedures are not translated here. A translation is not an editorial review.

## Prepare a change

1. Find the entry and the scenario. Do not duplicate a source that already exists.
2. Edit its YAML file in `data/resources/`. Keep the identifier, even if the service name changes.
3. Cite the responsible page for each correction. If you cannot check language, cost, or access, leave that state unknown.
4. Explain the input, the steps, the expected result, how to read it, and the limits.
5. Use fictional examples, with no identifiable person and no sensitive material.
6. Open a proposal with the problem, the observed change, and how to check it.

Original procedures live in `content/procedimientos/`. The pages under `docs/procedimientos/` are generated. Contact references use `{{contact:identifier}}`. The values stay in `data/contacts.yaml`.

An entry belongs in `data/resources/`. A procedure belongs in `content/procedimientos/`. A guide or a list that does not fit in one entry belongs in `docs/referencias/`. A new entry with `maintenance_urls` joins the weekly link check on its own.

Questions, translation ideas, and methods go to Discussions. A change to an entry or a procedure is an issue, using the Spanish or English form. Do not paste cases, personal data, or text from a paid manual.

## Check before you open the proposal

~~~console
uv sync --locked
uv run python tools/build_catalog.py
uv run python tools/validate_docs.py
uv run python -m unittest discover -s tests -v
~~~

Do not hand-edit generated entries, indexes, or exports. Generation does not invent explanations. It uses the original content.

To preview the public guide: `uv sync --locked --group docs` and `uv run mkdocs serve`.

## What approval means

An assistant's observation is not a human review. The `verified` state needs a reference, a date, and a registered person. The creation date stays separate.

Sensitive changes need approval by another competent person on the current version of the proposal. Until that person exists, the proposal stays pending. A bot can prepare issues. It cannot approve or merge those changes.

## Adding maintainers

Add the real user, account type, specialties, and a checked permission to the maintainer register. Assigning reviews requires write access and a recent permission check. Record a primary and a backup per specialty. Do not fill a vacancy with a fictional name.

Adding reviewers and policy changes also need review. The first addition needs an explicit decision by the owner naming the competent person. A proposal cannot grant itself the power to approve itself.

## Accessibility and privacy

Use plain language, ordered headings, and descriptive links. Avoid large tables and explain any diagram in text. See the [accessibility checks](https://comunidad-de-inteligencia.github.io/osint-atlas/ACCESIBILIDAD/), in Spanish.

Do not add real investigations, victim data, sensitive captures, or case URLs. For a catalog issue, the organization's or platform's documentation page is enough.

Sponsorship does not buy a catalog entry or a review.
