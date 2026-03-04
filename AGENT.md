# Agent Instructions for Rubicon Suite

Welcome to the Rubicon Suite repository. Please follow these guidelines when making changes:

## Critical Scope & Structure
- **Frontend Architecture**: The frontend is built **entirely within Odoo** (Views, Actions, OWL).
- **Deprecated Code**: The directory `pdp-frontend` (React/Vite) is **DEPRECATED and UNUSED**. **DO NOT** edit or use files in this directory.
- **Backend**: Odoo modules are located in `rubicon_addons`.

## Development Practices
- **Frontend Implementation**: All UI changes must be made in `rubicon_addons/pdp_frontend` (or related Odoo modules) using XML Views (QWeb) and Odoo Actions.
- **Git**: Favor small, focused commits with clear messages.
- **Code Style**: Keep consistency; avoid try/except blocks around imports.
- **Debug Scripts** : Always keep the temporary script in a ***temporary*** folder. 
- **Clean Up** : Clean up regularly the source folder and the temporary folder.

## Odoo 18.0 Specifics
### Migration Notes
- **Views & Actions**: The `tree` view type is deprecated/removed in favor of `list`.
    - In `ir.actions.act_window`, use `view_mode="list,form"`, not `tree,form`.
    - In XML view definitions, use `<list>` tag instead of `<tree>`.

## Testing and Verification
- Prioritize relevant `make` targets (e.g., `make init-data-modules`, `make raw_to_data_all`, `make import_all`).
- Prefer targeted tests for fast feedback.

## Data and Configuration Safety
- Never commit secrets or environment-specific configuration (`.env`).
- Be cautious with large data files; avoid adding raw datasets to version control.

## Communication
- Summaries should clearly state user-visible effects and reference important files.
