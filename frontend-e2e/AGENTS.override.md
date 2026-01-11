# AGENTS.override.md

## Frontend e2e rules

- Prefer Playwright locators by role/test id, avoid brittle CSS selectors.
- Keep specs focused on user-visible behavior, not internal implementation details.
- Use `npx nx e2e frontend-e2e` to validate when e2e changes are requested.
