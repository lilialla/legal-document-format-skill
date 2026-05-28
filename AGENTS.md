# Agent Instructions

This repository is an open, synthetic-first Agent Skill for legal document formatting. It exists to demonstrate a reusable workflow for DOCX template preservation, content locking, format checks, and visual validation.

## Core Rules

- Do not commit real cases, private templates, client facts, institution-specific rules, or confidential examples.
- Treat formatting as a delivery-control task, not a chance to rewrite legal substance.
- During format work, do not silently change parties, dates, amounts, claims, law citations, reasoning, dispositive text, or signatures.
- If exact template formatting is requested, start from the supplied template or base document. Do not recreate the document from a blank DOCX unless the user expressly chooses ordinary formatting.
- Keep `SKILL.md` short. Put detailed rules in `references/` and load them only when the route requires them.
- Keep scripts deterministic, local-first, and free of hardcoded secrets.

## Verification

Before calling a change ready:

- run shell syntax checks for shell scripts;
- run available script help or smoke checks;
- verify README instructions match the files that exist;
- confirm no private sample material was added;
- if a DOCX is rendered, check that LibreOffice creates a PDF and Poppler creates PNG pages.

## Legal Boundary

This repository supports document formatting and quality control. It does not provide legal advice and does not replace lawyer review.

