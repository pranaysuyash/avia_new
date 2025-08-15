# Intent-First UX Design Philosophy
"Design for the Experience, Not the Pixels"

## Core Principle
Before creating, modifying, or removing any design element, investigate the user's actual needs, workflows, and pain points to ensure every design change has measurable user and business impact.

This applies to:

- UI component creation and redesign
- User flow optimization
- Information architecture changes
- Interaction design decisions
- Visual design updates
- Accessibility improvements
- Full UX audits, not just feature-specific work

## Universal Investigation Framework

### Phase 1: Context Discovery
1. **Identify the design challenge** – New feature, usability issue, or aesthetic update.
2. **Research existing user behavior** – Analytics, heatmaps, support tickets, user interviews.
3. **Map current user journeys** – Compare actual usage patterns with intended flows.
4. **Analyze design system context** – Check consistency with existing patterns, components, and accessibility standards.

### Phase 2: User Intent Analysis
**Key questions**:

1. What task is the user trying to accomplish?
2. What's their mental model and expectations?
3. Where do users currently struggle or drop off?
4. What would success look like from their perspective?
5. Does this affect a core or secondary workflow?

### Phase 3: Design Impact Assessment

#### Design Value Factors
- **User Impact** – Improvement in task success, speed, or error rate
- **Business Impact** – Effect on conversion, retention, satisfaction, or compliance
- **Design Effort** – Time to design, validate, and document
- **Technical Complexity** – Development and QA effort, performance implications

#### Quick Filter (skip detailed design work if all are true)
- Purely cosmetic with no measurable usability improvement
- Very low-traffic area with minimal impact
- High implementation complexity for minimal gain
- Recent change with no evidence of user problems
→ **Document as UX debt in ux-debt.md**

## Design Priority Matrix

| User Impact | Business Impact | Implementation Effort | Priority |
|-------------|----------------|----------------------|----------|
| High | High | Low–Medium | Critical – Design immediately |
| High | Medium | Low–Medium | High – Include in next design sprint |
| Medium | High | Low | Medium – Schedule in upcoming iterations |
| High | High | High | Break into MVP + enhancements |
| Low | Low | Any | Defer or log as future consideration |

## MVP UX Rule
For Critical and High priority items, ensure MVP includes:

- **Ability for users to complete the core task without errors**
- **Simplified and intuitive flow**
- **Accessibility compliance for target user groups**
- **Performance within acceptable limits**

Aesthetic refinements, animations, and extended flows can be added in later iterations unless they directly unblock the user.

## Design Strategy Guidelines

### User-Centered Design Process
```markdown
1. Problem Validation
   - User interviews or surveys
   - Analytics & heatmap review
   - Support ticket analysis

2. Solution Exploration
   - Low-fidelity wireframes
   - User flow mapping
   - Multiple design concepts

3. Validation Testing
   - Clickable prototypes
   - A/B or multivariate testing
   - Accessibility evaluation

4. Implementation Planning
   - Design system integration
   - Technical feasibility check
   - Performance considerations
```

### Experience-First Hierarchy
1. **Core Functionality** – Can users complete the task?
2. **Usability** – Is it intuitive and efficient?
3. **Accessibility** – Can all users, including those with disabilities, use it?
4. **Performance** – Is it fast and responsive?
5. **Aesthetics** – Does it look good and match the brand?

## UX Investigation Prompt
(for ChatGPT, Claude, or similar tools)

```markdown
You are to apply the Intent-First UX Design Philosophy to the following design challenge.

### Design Element/Challenge:
[Describe the UI component, flow, or experience needing review]

### Investigation Requirements:
1. **User Context**:
   - Task users are trying to accomplish
   - Current experience & pain points
   - Insights from analytics/feedback

2. **Impact Assessment**:
   - User experience impact (high/medium/low)
   - Business metric impact (conversion, retention, satisfaction)
   - Implementation complexity

3. **Constraints**:
   - Technical limitations
   - Design system consistency requirements
   - Accessibility and performance considerations

4. **Solution Options**:
   - Quick wins (low effort, immediate gain)
   - Medium-term improvements (moderate effort, high value)
   - Long-term vision (high effort, transformational)

5. **Output Format**:
   | Problem | User Impact | Business Impact | Effort | Recommendation | MVP Scope | Metrics |
   |---------|-------------|----------------|--------|----------------|-----------|---------|

### Notes:
- Prioritize completion of tasks over visual polish
- Validate assumptions with real user testing
- Address accessibility and performance from the start
```

## Team Integration Framework

### Design Review Checklist
```markdown
## UX Design Review
- [ ] User problem defined and validated
- [ ] Solution tested with target users
- [ ] Accessibility addressed
- [ ] Design system consistency maintained
- [ ] Performance impact assessed
- [ ] Success metrics defined
- [ ] Technical feasibility confirmed
```

### Cross-Functional Collaboration
```markdown
## Stakeholder Involvement
- **Product Manager**: Validates business impact
- **Developer**: Confirms technical feasibility
- **QA**: Plans testing for new interactions
- **Support**: Provides pain point insights
- **Marketing**: Ensures brand and messaging alignment
```

## Success Metrics

### Quantitative
- **Task Success Rate** – % of users completing intended task
- **Time on Task** – Average time to complete
- **Error Rate** – Frequency of user errors/confusion
- **Abandonment Rate** – Drop-offs in the flow
- **Accessibility Compliance Score** – WCAG adherence

### Qualitative
- **User Feedback** – Direct feedback from usability tests
- **Support Ticket Reduction** – Fewer requests for redesigned flows
- **Developer Velocity** – Ease of implementation via consistent components
- **Team Confidence** – Agreement across stakeholders

## When to Prioritize UX Work

### Prioritize When:
- Clear evidence of user struggle or frustration
- Direct link to key metrics (conversion, retention, CSAT)
- Accessibility gaps preventing usage
- Severe consistency issues

### Deprioritize When:
- Purely aesthetic with no usability gain
- Very low user impact
- Requires major tech change for minimal UX benefit
- Based only on unvalidated assumptions

## UX Debt Log
Maintain `ux-debt.md`:

```markdown
# UX Debt Log

## [YYYY-MM-DD] Checkout Field Grouping
Reason Deferred: Requires backend schema change
User Impact: Medium
Business Impact: Medium
Revisit: Q3 2025
```

## Key Questions to Always Ask
1. What specific user problem does this solve?
2. How will we measure success?
3. Can users with disabilities complete this task?
4. Does it fit our design system, and if not, why?
5. What's the simplest version that improves the experience?
6. Have we validated this with real users?