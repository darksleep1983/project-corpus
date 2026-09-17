# Task

Protocol-Version: 2.0
Project-ID: software-status-filter
Task-ID: task-status-filter
Task-Status: OPEN
Created-At: 2026-09-17T00:00:00Z

## Objective

Add a status selector that filters the issue list to open or completed items.

## Scope

- Add the filter behavior and focused automated tests.
- Preserve the current unfiltered default.

## Constraints

- Do not change storage format or deployment configuration.
- Do not claim completion without test evidence.

## Acceptance Criteria

- Selecting each status returns only matching items.
- No selection preserves the existing list.
- Focused tests pass and are cited in a Report.
