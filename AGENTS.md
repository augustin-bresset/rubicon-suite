# Agent Instructions for Rubicon Suite

Welcome to the Rubicon Suite repository. Please follow these guidelines when making changes:

## Scope and Documentation
- This file applies to the entire repository unless a more specific `AGENTS.md` is added in a subdirectory.
- Review `README.md`, `roadmap.md`, and `meta/` docs for context before making significant changes or assumptions about the data pipeline.

## Development Practices
- Favor small, focused commits with clear messages describing *what* changed and *why*.
- Keep code style consistent with existing files; do not introduce new formatting conventions without consensus.
- Avoid adding try/except blocks around imports.

## Testing and Verification
- When altering Odoo modules or data pipelines, prioritize the relevant `make` targets (e.g., `make init-data-modules`, `make raw_to_data_all`, `make import_all`) and module-level test commands described in `README.md`.
- For quick checks, prefer targeted tests over full suite runs to keep feedback fast. Document any skipped or unavailable tests in your notes and final summary.

## Data and Configuration Safety
- Never commit secrets or environment-specific configuration. `.env` should remain local.
- Be cautious with large data files; avoid adding raw datasets to version control.

## Communication
- Summaries should clearly state user-visible effects and reference important files.
- If you create additional `AGENTS.md` files in subdirectories, ensure their instructions refine (not contradict) the guidance here.