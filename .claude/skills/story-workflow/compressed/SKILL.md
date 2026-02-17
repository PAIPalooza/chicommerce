# Story Workflow & Estimation

## Backlog Rules
* Top unstarted story; clarify acceptance criteria
* Branch: `{type}/{shortcut-id}-{slug}`

## TDD Workflow
* **Red:** Failing tests (`WIP: red tests for {story}`)
* **Green:** Minimal passing code
* **Refactor:** Improve design

## Story Flow
* Finished → PR → CI → Review → Merge → Delivered → PM Accept/Reject

## Story Types
* Feature: New capability
* Bug: Fix behavior
* Chore: Maintenance/infrastructure

## Fibonacci Points
* 0: Trivial changes
* 1: Clear, contained work
* 2: Moderate complexity
* 3/5/8: Large - **SPLIT** first

## Story Splitting
1. Break into ≤2 point sub-stories
2. Deliver incremental value
3. Document split in parent story

## References
* `references/estimation-guide.md`
* `references/story-templates.md`
* `references/shortcut-integration.md`