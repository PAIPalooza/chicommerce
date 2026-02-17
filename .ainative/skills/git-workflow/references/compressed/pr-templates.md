# PR Templates

## Feature PR Template
```markdown
## Summary
[Brief feature description]

## Changes
- Major changes
- Files affected
- Breaking changes

## Test Plan
**Commands:**
```
[Test commands]
```

**Results:**
```
[Test output]
```

**Manual Testing:**
- [ ] Browser/app test
- [ ] Responsive design
- [ ] Accessibility
- [ ] Edge cases

## Risk Assessment
**Risks:** [List concerns]
**Rollback:** [Revert steps]

## Story Link
Closes #[issue]
Type: Feature
Estimate: [points]
```

## Bug Fix PR Template
```markdown
## Problem
[Bug description]

## Root Cause
[Technical explanation]

## Solution
[Fix details]

## Changes
- Files changed
- Logic updates

## Test Plan
**Regression:**
```
[Bug reproduction]
```

**Verification:**
```
[Fix confirmation]
```

**Additional Testing:**
- [ ] No related feature breaks
- [ ] Edge cases
- [ ] Staging test

## Risk Assessment
**Risk Level:** [Low/Medium/High]
**Rollback:** [Revert steps]

## Story Link
Fixes #[issue]
Type: Bug
Estimate: [points]
```

## Chore PR Template
```markdown
## Summary
[Maintenance details]

## Motivation
[Necessity explanation]

## Changes
- Changes made
- Dependencies
- Config updates

## Test Plan
**Verification:**
```
[Verification commands]
```

**Results:**
```
[Test output]
```
- [ ] Tests passing
- [ ] No regressions
- [ ] Docs updated

## Risk Assessment
**Low Risk**
**Rollback:** [Revert method]

## Story Link
Refs #[issue]
Type: Chore
Estimate: [points]
```

## PR Best Practices
- Clear context
- Complete summary
- Actual test evidence
- Honest risk assessment
- Rollback plan

### Avoid
- Vague descriptions
- Unproven tests
- Missing rationale
- No risk assessment

### PR Size
- 0-100 LOC: Quick review
- 100-300 LOC: Ideal
- 300-500 LOC: Large
- 500+ LOC: Split required

### Review Checklist
- [ ] No AI attribution
- [ ] Passing tests
- [ ] Complete description
- [ ] Focused changes
- [ ] Updated docs
- [ ] No secrets/PII