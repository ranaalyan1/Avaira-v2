# Record architecture decisions

* Status: accepted
* Deciders: Jules
* Date: 2025-05-18

## Context and Problem Statement

We are upgrading Avaira to v3. To ensure that the rationale behind architecturally significant decisions is captured and shared, we need a systematic way to record them.

## Decision Drivers

* Need for traceability of architectural changes.
* Desire for a consistent format for decision records.
* Better communication of architectural choices to current and future team members.

## Considered Options

* ADRs (Architecture Decision Records)
* Wiki pages
* Email threads
* Comments in code

## Decision Outcome

Chosen option: ADRs, because they are versioned alongside the code, easy to review, and provide a clear history of why decisions were made.

### Positive Consequences

* Better documentation of "why" things are done a certain way.
* Easier onboarding for new researchers/engineers.
* Systematic review process for architectural shifts.

### Negative Consequences

* Slight overhead in documenting decisions.

## Links

* [MADR template](https://github.com/adr/madr)
