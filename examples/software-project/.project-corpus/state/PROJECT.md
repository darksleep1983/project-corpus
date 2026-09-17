# Project

Protocol-Version: 2.0
Project-ID: software-status-filter
Logical-Name: Status Filter

## Objective

Add a status filter that lets users focus the issue list on unresolved work.

## Invariants

- Filter behavior must preserve the existing default list when no filter is chosen.
- A completed change needs an executable test and a report with its result.

## Durable Scope Boundaries

- This Corpus covers the status-filter feature and its tests, not deployment or account administration.

## Non-Goals

- Redesigning the issue-list interface.
- Changing remote service configuration.
