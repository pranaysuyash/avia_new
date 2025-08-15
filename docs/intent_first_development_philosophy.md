# Intent-First Development Philosophy
"Investigate Intent Before Acting"

## Core Principle

Before removing, suppressing, or "fixing" any code/feature/element, investigate the original intent and determine if completion would create more value than removal.

## Universal Investigation Framework

### Phase 1: Context Discovery

1. **Identify the element**: Code, feature, UI element, database structure, etc.
2. **Search for references**: Across codebase, documentation, user stories, designs
3. **Check related systems**: UI, backend, database, third-party integrations
4. **Review history**: Git commits, PRs, issue discussions, meeting notes

### Phase 2: Intent Analysis

**Key Questions**:

1. What user problem was this meant to solve?
2. What workflow was this part of?
3. Are there similar completed features showing the pattern?
4. Would users expect this functionality to work?

### Phase 3: Impact Assessment

#### Completion Assessment

- **User Value**: High/Medium/Low impact on user experience
- **Business Value**: Revenue, retention, or operational impact
- **Technical Effort**: Hours/days/weeks to complete properly
- **Risk Level**: Security, performance, or stability implications
- **Operational Risk**: New monitoring, alerts, data storage, or maintenance overhead

#### Quick Filter (Skip deep analysis if all true)

- No user-facing connection
- No business value identified
- High technical effort required
- No strategic importance
→ **Default to "Document as Technical Debt"**

## Decision Matrix

| User Value | Technical Effort | Operational Risk | Action |
|------------|------------------|------------------|--------|
| High | Low-Medium | Low | Complete to MVP immediately |
| High | High | Low-Medium | Plan for next sprint/milestone |
| Medium | Low | Low | Complete MVP if time permits |
| Medium | Medium-High | Any | Document as technical debt |
| Low | Any | Any | Consider removal with stakeholder approval |
| Any | Any | High | Defer completion until risk mitigated |

## Applies Beyond PR Reviews

- **Full-Project Audits**: Use the same framework to review entire repositories for unused or incomplete code that could add value if completed.
- **Legacy Migrations**: Determine if old code was meant to be part of a still-valuable feature before deleting during system migrations.
- **Feature Expansions**: Identify dormant code that could be completed to add value rather than starting from scratch.
- **Refactoring Cycles**: Ensure nothing valuable gets accidentally removed during large-scale refactoring efforts.
- **Onboarding**: Train new engineers to apply this approach on any code they touch, whether in PRs or exploratory work.

## Ready-to-Use Investigation Prompt

Copy-paste this into ChatGPT, Claude, or similar AI tools whenever you find "unused" or unclear code:

```
You are to apply the Intent-First Development Philosophy to the following element.

### Element:
[Paste file path, code snippet, or description]

### Investigation Requirements:
1. **Identify Intent**: Based on code search patterns, documentation, commit history, and similar features, determine what the original purpose was.

2. **Assess Completion Potential**:
   - Would completing this add user or business value?
   - Is there evidence the frontend/backend expected this feature?
   - Could an MVP version be completed quickly?

3. **Risk & Effort**:
   - Technical effort (low/medium/high)
   - Risk to stability/security/performance
   - Operational impact (monitoring, alerts, data growth)

4. **Decision Options**:
   - Complete now (MVP)
   - Plan for full completion
   - Document as technical debt
   - Remove (with stakeholder approval)

5. **Output Format**:
   - **Original Intent**: [summary]
   - **Evidence Found**: [list of references]
   - **Value Assessment**: [user/business impact]
   - **Risk/Effort**: [summary]
   - **Recommendation**: [Complete/Defer/Remove + reasoning]
   - **Next Steps**: [actions]

### Notes:
- Apply this for audits, refactors, or legacy cleanup - not just PRs
- Favor completion over removal when there is clear user/business value
- Limit completion scope to MVP, defer enhancements unless critical
```

## Implementation Guidelines by Context

### Python
```python
# Before: Remove "unused" variable
def process_user_data(data, export_format):  # export_format unused
    return transform_data(data)

# After: Complete the export feature
def process_user_data(data, export_format='json'):
    processed = transform_data(data)
    if export_format == 'csv':
        return export_to_csv(processed)
    elif export_format == 'excel':
        return export_to_excel(processed)
    return processed  # default json
```

### UI/UX Elements
```jsx
// Before: Remove non-functional button
<button disabled>Export Data</button>

// After: Complete the export functionality
<button onClick={handleExport} disabled={isExporting}>
  {isExporting ? 'Exporting...' : 'Export Data'}
</button>
```

### Database Design
```sql
-- Before: Drop "unused" column
ALTER TABLE users DROP COLUMN preferred_language;

-- After: Complete internationalization feature
UPDATE user_preferences 
SET language = users.preferred_language 
WHERE users.preferred_language IS NOT NULL;
```

### API Design
```javascript
// Before: Remove "unused" endpoint parameter
app.get('/api/users', (req, res) => {
  // req.query.role is extracted but ignored
  const users = getAllUsers();
  res.json(users);
});

// After: Complete role-based filtering
app.get('/api/users', (req, res) => {
  const { role, department, status } = req.query;
  const users = getFilteredUsers({ role, department, status });
  res.json(users);
});
```

## Team Integration Framework

### Pull Request Template Addition
```markdown
## Intent-First Review Checklist
- [ ] Does this PR remove or significantly alter existing code?
- [ ] If yes, have you investigated the original intent?
- [ ] Is this completion of incomplete functionality or genuine removal?
- [ ] Decision documented in [ticket/issue link]?
```

### Issue/Ticket Linking Requirements

- Every intent investigation must link to related user story, issue, or epic
- Decisions without clear business context require product owner approval
- Technical-only decisions can proceed with engineering manager approval

### Decision Record Maintenance

Maintain `docs/intent-decisions.md` in repository:

```markdown
# Intent Investigation Decision Record

## [YYYY-MM-DD] Feature: Newsletter Sorting
**Element**: Unused `sort` parameter in newsletter API
**Decision**: Completed - Added sorting by email, status, language
**Reasoning**: Found evidence of frontend expecting this functionality
**Impact**: Improved admin UX for managing large subscriber lists
**Ticket**: #1234

## [YYYY-MM-DD] Database: user_preferences.theme_color
**Element**: Unused column in user preferences
**Decision**: Deferred - Requires UI theme system redesign  
**Reasoning**: High user value but 2-3 week effort
**Next Review**: Q2 planning cycle
**Ticket**: #1235
```

## Stakeholder Involvement Decision Tree

```
Is this user-facing? → YES → Consult Product Owner
                   → NO → Continue technical assessment

Does this affect UI/UX? → YES → Consult Designer
                       → NO → Continue development

Is this security-related? → YES → Consult Security Team
                         → NO → Continue with standard review

High operational risk? → YES → Consult DevOps/SRE Team
                      → NO → Continue with standard review
```

## Communication Templates

### For Product Owner:
"I found an incomplete feature for [USER BENEFIT]. It would take [EFFORT ESTIMATE] to complete to MVP level. Should we prioritize this or remove it?"

### For Designer:
"There's a UI element that's non-functional. The intended workflow seems to be [DESCRIPTION]. Should we complete this interaction or remove it?"

### For DevOps/SRE:
"Completing this feature would add [OPERATIONAL IMPACT]. Are there concerns with monitoring, alerting, or infrastructure load?"

### For Team:
"Found incomplete [FEATURE TYPE]. Evidence suggests it was meant to [INTENT]. Recommend [COMPLETION/REMOVAL] because [REASONING]. MVP scope: [DESCRIPTION]."

## Success Metrics

### Quantitative

1. **Error/Warning Reduction**: Track technical debt improvement
2. **Feature Completion Rate**: Completed features vs removed code
3. **User Engagement**: Usage analytics for completed features
4. **Development Velocity**: Time saved vs time invested
5. **DORA Metrics**: Lead time and deployment frequency for completions vs removals
6. **Defect Escape Rate**: Compare bug rates in completed areas vs similar untouched areas

### Qualitative

1. **User Satisfaction**: Feedback on completed features
2. **Developer Experience**: Code maintainability and clarity
3. **Product Completeness**: Fewer incomplete user journeys
4. **Team Alignment**: Shared understanding of feature intent
5. **Operational Stability**: No increase in alerts or incidents from completions

## Risk Management

### When to Prioritize Removal

- **Security Risk**: Code poses active security threat
- **Performance Critical**: Code significantly impacts system performance
- **Deprecated Technology**: Built on obsolete or unsupported tech
- **No Clear Intent**: Extensive investigation reveals no coherent purpose
- **Conflicting Requirements**: Completion would contradict current product direction

### When to Defer Completion

- **Major Architecture Change Required**: Beyond current sprint scope
- **External Dependencies**: Waiting for third-party APIs or services
- **User Research Needed**: Intent unclear without user validation
- **Resource Constraints**: Team lacks specific expertise needed
- **High Operational Risk**: Would significantly increase monitoring/maintenance burden
- **Gold-Plating Risk**: Completion would require extensive polish work vs MVP functionality

## Documentation Requirements

### For Completed Features
```markdown
## Completed Feature: [NAME]
**Original Issue**: [LINK/DESCRIPTION]
**Evidence of Intent**: [REFERENCES FOUND]
**MVP Implementation**: [TECHNICAL DETAILS - SCOPE LIMITED]
**Testing**: [VALIDATION APPROACH]
**Impact**: [USER/BUSINESS VALUE]
**Future Enhancements**: [BACKLOG ITEMS CREATED]
**Operational Impact**: [MONITORING/ALERTING ADDED]
```

### For Deferred Completion
```markdown
## Technical Debt: [NAME]
**Intent**: [WHAT IT SHOULD DO]
**Why Deferred**: [REASON]
**Effort Estimate**: [TIME/COMPLEXITY]
**Business Value**: [IMPACT ASSESSMENT]
**Next Steps**: [WHEN TO REVISIT]
```

### For Removed Code
```markdown
## Removed: [NAME]  
**Original Purpose**: [INVESTIGATED INTENT]
**Removal Reason**: [WHY NOT COMPLETED]
**Impact Assessment**: [AFFECTED SYSTEMS]
**Stakeholder Approval**: [WHO APPROVED]
```

## Key Principles for All Contexts

1. **Investigate First**: Always research intent before acting
2. **Complete Over Remove**: Default to completion when valuable
3. **MVP Completion Only**: Complete minimum viable version, defer polish/expansions
4. **Document Decisions**: Record reasoning for future reference
5. **Involve Stakeholders**: Get appropriate approvals for user-facing changes
6. **Measure Impact**: Validate that completed features create value
7. **Prevent Gold-Plating**: Resist over-engineering; enhancement goes to backlog

## Questions to Always Ask

Before any modification:

1. "What problem was this meant to solve?"
2. "Who would benefit if this worked properly?"
3. "What evidence suggests this was intentional vs accidental?"
4. "What would an MVP implementation look like?"
5. "What operational overhead would completion introduce?"
6. "Should enhancements be deferred to avoid gold-plating?"
7. "What's the cost of completion vs removal?"