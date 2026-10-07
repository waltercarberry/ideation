# Bidroom — Comprehensive Build Brief for Claude

## 1. Product definition

Build a polished microsite GUI called **Bidroom**: a pre-submission bid stress-testing dashboard. A user uploads an RFP and their proposal, the system extracts requirements and evaluation criteria, reviews proposal strengths and weaknesses, lets the user curate a simulated client boardroom, and evaluates the bid through several stakeholder agents. The product must produce a transparent competitiveness diagnosis and prioritised fixes.

Core promise:

> See how your proposal could be rejected before the client does.

The product is decision support, not a guaranteed win predictor. Never claim to know the real client’s decision or present a precise probability as fact.

## 2. Hackathon MVP scope

Implement these flows:

1. Load a demo RFP/proposal instantly, with optional upload controls.
2. Show extracted requirements and weighted evaluation criteria.
3. Show proposal coverage, strengths and weaknesses.
4. Let the user curate the boardroom: add/edit roles, priorities, influence and stance.
5. Run a simulated panel using deterministic demo data or an API abstraction.
6. Show evaluator scores, objections, disagreement and decision friction.
7. Show a prioritised action plan; do not automatically rebuild the entire bid.
8. Allow the user to inspect evidence and assumptions.

Do not build for MVP:

- Full automatic proposal/deck rewriting.
- Precise win probabilities.
- 3D avatars or a realistic animated boardroom.
- Long autonomous agent debates.
- User authentication, billing or multi-tenant persistence.
- A production-grade document parser.

## 3. Product language

Use these labels:

- “Simulated competitiveness” rather than “win probability”.
- “Evaluator hypothesis” rather than “the client thinks”.
- “Decision friction” rather than “prediction certainty”.
- “Recommended action” rather than “automatic rewrite”.
- “RFP-grounded”, “user-supplied” and “AI-inferred” badges.

Important disclaimer in the UI:

> This is a structured simulation based on the RFP, proposal and your assumptions. It is not a prediction of the actual client decision.

## 4. Visual direction

Create a premium confidential strategy-room interface.

- Dark navy/charcoal shell: #08111F or similar.
- Warm off-white document surfaces: #F7F5F0.
- Electric blue accent: #45A3FF.
- Amber warning: #F4B740.
- Red risk: #F06A6A.
- Green strength: #52C79A.
- Use a clean sans-serif such as Inter or system sans.
- Use restrained motion: fade, slide, progress, score count-up, node highlighting.
- Avoid generic purple AI gradients, excessive glassmorphism, cartoon avatars and noisy decoration.
- The UI must be responsive, but optimise for a 1440px desktop demo.

Design should feel like procurement intelligence, corporate strategy and an executive workspace.

## 5. App shell and navigation

Use a left rail or top stepper with these stages:

01 Upload
02 RFP map
03 Bid review
04 Build the room
05 Boardroom
06 Action plan

Top bar:

- Bidroom wordmark.
- Demo bid name.
- “Simulation: Draft 01”.
- Small status indicator.
- Reset demo button.

Keep navigation functional. The user should be able to move backwards without losing state.

## 6. Page 1 — Landing/upload

Hero copy:

> Will your proposal survive the client’s boardroom?

Subcopy:

> Upload an RFP and draft bid. Map the evaluation criteria, model competing stakeholder priorities and find the reasons your proposal could lose before submission.

Show two upload cards:

- Upload RFP.
- Upload draft proposal.

Primary CTA:

> Enter the boardroom

Secondary CTA:

> Load demo bid

For reliability, “Load demo bid” must work immediately and populate the full experience. Upload can be a functional-looking control with a simulated parse state if backend support is unavailable.

## 7. Demo dataset

Use a fictional RFP called:

**Northstar Council — Digital Service Transformation Partner**

Client objective:

> Modernise resident-facing digital services while reducing delivery risk, improving accessibility and creating measurable operational savings.

Proposal name:

**Aster Advisory — Northstar Digital Transformation Proposal**

Create six evaluation criteria:

| Criterion | Weight | Coverage | Risk |
|---|---:|---|---|
| Understanding of requirements | 20% | Strong | Low |
| Delivery methodology | 25% | Partial | High |
| Relevant experience | 20% | Strong | Low |
| Team and governance | 15% | Partial | Medium |
| Risk, assurance and accessibility | 10% | Weak | High |
| Price and value | 10% | Partial | Medium |

Use a fictional proposal with believable, polished but imperfect content. The key flaw should be that it is strategically persuasive but operationally under-specified.

Demo facts to surface:

- Strong understanding of the client’s transformation ambition.
- Relevant case study evidence.
- Generic governance language.
- No named mobilisation owner.
- No 90-day transition plan.
- Benefits described qualitatively but not quantified.
- Accessibility mentioned but with limited assurance detail.
- Price is plausible but value-for-money logic is weak.

## 8. Page 2 — RFP intelligence map

Headline:

> What the client will score

Show KPI cards:

- Requirements extracted: 42.
- Mandatory requirements: 9.
- Weighted criteria: 6.
- Partially answered: 7.
- High-risk gaps: 3.

Main component: requirement coverage matrix.

Columns:

- Requirement.
- Weight.
- Coverage.
- Evidence/source.
- Risk.

Rows should be clickable. Clicking a row opens a right-side detail drawer containing:

- Exact requirement text.
- RFP section/page.
- Proposal section mapped to it.
- Evidence found.
- Missing evidence.
- Why it matters.
- Badge showing RFP-grounded.

Use green/amber/red status. Do not make every item red; credible contrast matters.

## 9. Page 3 — Bid review

Headline:

> The proposal answers the brief. It does not yet reassure the room.

Show an overall simulated competitiveness score of **68/100**, labelled “Simulated competitiveness”. Include “Confidence: Medium”.

Three KPI cards:

- Strengths: 5.
- Weaknesses: 6.
- Critical decision risks: 3.

Create two main columns.

### Strengths list

Each strength has a check icon, short title, evidence reference and affected evaluator.

Examples:

- Strong strategic alignment — proposal section 2 — Executive Sponsor.
- Relevant transformation experience — case study 1 — Executive Sponsor and Operations.
- Clear phased approach — section 4 — Procurement.

### Weaknesses list

Each weakness has amber/red status, affected evaluators and a clickable detail drawer.

Examples:

1. Benefits are not quantified.
2. Mobilisation ownership is unclear.
3. Governance language is generic.
4. Accessibility assurance is underdeveloped.
5. Price/value case is not sufficiently connected.
6. Evidence does not show a comparable transition.

Weakness detail format:

- Problem.
- Where detected.
- Why it matters.
- Evaluators affected.
- Suggested action.
- Evidence/status badge.

## 10. Page 4 — Build the room

Headline:

> You know the client. Curate the room.

Subcopy:

> The AI can infer plausible evaluator roles, but you can encode what you know about the client’s priorities, pressures and internal tensions.

Start with six suggested roles:

1. Executive Sponsor.
2. Finance Director.
3. Operations Lead.
4. Procurement Lead.
5. Technical Evaluator.
6. Risk and Assurance Lead.

Show role cards around a central “Your bid” node. The cards should be draggable if practical; otherwise use a responsive grid with connecting lines.

Each role card must show:

- Role name.
- Short priority.
- Influence: High/Medium/Low.
- Stance: Supportive/Neutral/Sceptical.
- Current score.
- Edit button.

Provide an “Add evaluator” button.

### Role editor modal

Fields:

- Role name.
- Primary objective.
- Secondary concerns.
- Likely to reward.
- Likely to challenge.
- Influence.
- Stance.
- Can veto? toggle.
- Notes/context.

Include a free-text field:

> Describe anything you know about how this client makes decisions.

Prepopulate it with:

> The CEO wants a visible transformation win, but the CFO must justify every pound. Procurement is formal and will penalise unsupported claims. Operations is sceptical because a previous supplier overpromised. The technical lead cares about integration, while end users mainly want something simple.

When the user clicks “Interpret context”, show extracted chips:

- Budget pressure.
- Low tolerance for unsupported claims.
- Previous supplier disappointment.
- Integration concern.
- Simplicity valued by end users.

Mark each chip as “User-supplied”.

### Relationship controls

For MVP, include a simple relationship list or lightweight graph:

- Executive Sponsor supports transformation ambition.
- Finance challenges unquantified value.
- Operations challenges delivery certainty.
- Procurement follows the published rubric.
- Risk can block approval.

Allow at least one relationship to be edited or toggled.

## 11. Page 5 — Boardroom simulation

Headline:

> The room is not one mind.

Show a boardroom-style visual with evaluator cards around a central bid card. Avoid human-photo avatars; use abstract role icons and initials.

Default scores:

| Evaluator | Score | Stance | Main concern |
|---|---:|---|---|
| Executive Sponsor | 82 | Supportive | Visible transformation impact |
| Procurement Lead | 74 | Neutral | Evidence and scoring defensibility |
| Risk Lead | 63 | Concerned | Assurance and failure modes |
| Operations Lead | 61 | Cautious | Mobilisation accountability |
| Finance Director | 54 | Sceptical | Quantified value |
| Technical Evaluator | 68 | Neutral | Integration detail |

Make the cards clickable. Clicking one opens a panel containing:

- Priority.
- Score.
- Reaction.
- Two strengths.
- Two concerns.
- Questions they would ask.
- Evidence that could change their score.
- Assumption badges.

Primary button:

> Run boardroom

On click, animate the cards sequentially from “reviewing” to scored. Use a 1.5–2.5 second total animation, not a long wait. Include a small progress indicator.

After scoring, show a compact debate transcript:

EXECUTIVE SPONSOR:
“The proposal understands the transformation ambition.”

FINANCE DIRECTOR:
“The benefits are not measurable enough to justify the investment.”

OPERATIONS LEAD:
“I cannot see who owns mobilisation in the first 90 days.”

PROCUREMENT LEAD:
“The response is relevant, but several claims are unsupported.”

CHAIR:
“Keep in contention. Clarify value, ownership and assurance before submission.”

Use a chat/debate style panel, but make it clear these are simulated viewpoints.

## 12. Decision friction visual

Create a prominent panel called **Decision friction**.

Show a horizontal score comparison or tension chart with all evaluator scores. Highlight the largest gap.

Example diagnosis:

> Strategic enthusiasm is high, but financial confidence is low.

Root cause:

> The bid describes benefits qualitatively without a baseline, target, owner or measurement date.

Secondary friction:

> Operations cannot see who is accountable during mobilisation.

Use an amber or red accent for friction, not a generic sentiment score.

## 13. Page 6 — Action plan

Headline:

> Fix the reasons the room could say no.

Show a prioritised table:

| Priority | Action | Evaluators affected | Impact | Evidence needed |
|---|---|---|---|---|
| 1 | Quantify benefits and measurement method | Finance, Procurement | High | Baseline, target, owner, date |
| 2 | Name mobilisation owner and 90-day milestones | Operations, Risk | High | Delivery plan |
| 3 | Add comparable transition case study | Operations, Sponsor | Medium | Client example |
| 4 | Strengthen accessibility assurance | Risk, Technical | Medium | Standards and testing approach |
| 5 | Connect price to measurable value | Finance, Sponsor | Medium | Benefits table |

Each action should be expandable. Include a “Copy action” button and “Mark reviewed” toggle. Do not automatically rewrite the entire proposal.

At the top, show before/after only as a projected scenario:

```text
Current simulated competitiveness: 68
Potential after addressing top risks: 76
```

Label 76 as “Illustrative impact, not a guarantee”.

## 14. Final report/export view

Provide a clean “Boardroom brief” view with:

- Bid name.
- Simulated competitiveness.
- Status: Competitive but exposed.
- Confidence: Medium.
- Top strengths.
- Top decision risks.
- Evaluator score spread.
- Top five actions.
- Assumptions.
- Disclaimer.

Add buttons:

- Download brief (can be a mocked button or browser print flow).
- Copy executive diagnosis.
- Start another simulation.

## 15. Data model

Use typed frontend state. Suggested TypeScript interfaces:

```ts
interface Criterion {
  id: string;
  title: string;
  weight: number;
  coverage: 'strong' | 'partial' | 'weak' | 'missing';
  evidence: string[];
  source: string;
  risk: 'low' | 'medium' | 'high';
  requirementText: string;
}

interface Evaluator {
  id: string;
  role: string;
  objective: string;
  concerns: string[];
  rewards: string[];
  challenges: string[];
  influence: 'low' | 'medium' | 'high';
  stance: 'supportive' | 'neutral' | 'cautious' | 'sceptical';
  veto: boolean;
  score: number;
  strengths: string[];
  objections: string[];
  questions: string[];
  scoreChangingEvidence: string[];
  sourceType: 'user-supplied' | 'ai-inferred' | 'rfp-grounded';
}

interface Finding {
  id: string;
  type: 'strength' | 'weakness' | 'risk';
  title: string;
  description: string;
  source: string;
  affectedEvaluators: string[];
  severity: 'low' | 'medium' | 'high';
  recommendedAction?: string;
}

interface ActionItem {
  id: string;
  priority: number;
  title: string;
  rationale: string;
  affectedEvaluators: string[];
  impact: 'low' | 'medium' | 'high';
  evidenceNeeded: string[];
  reviewed: boolean;
}
```

## 16. Backend/API abstraction

Build the frontend so it can work with either mocked data or real API responses. Create a service layer rather than embedding mock data inside components.

Suggested functions:

```ts
parseRfp(file): Promise<RfpAnalysis>
reviewBid(rfpAnalysis, proposal): Promise<BidReview>
createEvaluatorPanel(context): Promise<Evaluator[]>
runBoardroom(review, evaluators): Promise<BoardroomResult>
createActionPlan(review, boardroom): Promise<ActionItem[]>
```

For the hackathon default, return deterministic demo data quickly. If an API key is available, keep model calls behind the same functions.

Do not expose API keys in client-side code. If building a purely static HTML demo, clearly separate the mock simulation from any future backend integration.

## 17. Multi-agent prompt contracts

Each evaluator should receive:

- RFP objective.
- Weighted criteria.
- Proposal summary.
- Relevant evidence and gaps.
- Its role definition.
- Instruction to score independently.

Require strict JSON with:

- score from 0–100.
- stance.
- strengths.
- objections.
- questions.
- scoreChangingEvidence.
- rationale.

Evaluator prompt concept:

> You are simulating a procurement stakeholder, not speaking for the real person. Evaluate only from the supplied role, RFP evidence and proposal excerpts. Do not invent confidential facts. Separate evidence from inference. Identify one factor that could change your score.

Chair prompt concept:

> Synthesise independent evaluator reports. Do not average blindly. Identify consensus, disagreement, the highest-impact blocker and the smallest number of actions likely to reduce decision friction. Use only the supplied reports and mark assumptions.

## 18. Scoring logic

Use deterministic scoring wherever possible.

Weighted criterion score:

```text
overallScore = sum(criterion.weight * criterion.normalizedScore)
```

Panel score:

```text
panelScore = weightedMean(evaluator.score, evaluator.influenceWeight)
```

Decision friction:

```text
friction = max(evaluator.score) - min(evaluator.score)
```

Also count repeated objections. If three or more evaluators mention the same issue, promote it to a consensus risk.

Do not convert this into a factual probability of winning. Call the result simulated competitiveness.

## 19. Interaction and motion requirements

- Upload parse: staged progress labels: “Extracting requirements”, “Mapping evidence”, “Preparing boardroom”.
- Requirement row: hover highlight and drawer open.
- Role cards: hover lift and edit modal.
- Run boardroom: sequential card activation and score count-up.
- Score bars: animate from zero to final value.
- Decision friction: draw a connecting line or highlight the score spread.
- Action plan: expand/collapse and mark reviewed.
- Avoid continuous spinners; use clear progress and fast demo timing.

Respect prefers-reduced-motion where practical.

## 20. Quality and trust requirements

Every important output must be explainable.

Show evidence badges:

- RFP-grounded: directly extracted from the RFP.
- User-supplied: entered by the user.
- AI-inferred: generated as a hypothesis.
- Simulated: produced by the evaluator panel.

Add “Why am I seeing this?” tooltips for scores and recommendations.

Do not imply that the agents are real client employees. Do not use identifiable real people by default.

## 21. Accessibility and UX

- Keyboard-accessible controls.
- Strong colour contrast.
- Never use colour alone to communicate risk.
- Visible focus states.
- Descriptive button labels.
- Responsive layout for 1024px and above.
- Use icons plus text for status.
- Keep text readable; do not bury the key diagnosis in tooltips.

## 22. Performance strategy

- Lazy-load heavy visual components.
- Use static demo data immediately.
- Keep analysis animation under three seconds.
- Memoise score charts.
- Avoid repeated model calls.
- Use one request per evaluator or mocked parallel promises.
- Cache the demo result.
- Keep the first meaningful dashboard visible quickly.

## 23. Build order

Implement in this sequence:

1. App shell and routing/state machine.
2. Landing/upload and demo loader.
3. RFP coverage matrix.
4. Bid review findings.
5. Boardroom builder.
6. Boardroom visual and scoring animation.
7. Decision friction and action plan.
8. Evidence drawers and badges.
9. Responsive polish.
10. Final demo reset and export/print view.

## 24. Acceptance criteria

The build is successful when:

- A judge can understand the product within 15 seconds.
- The demo dataset loads with one click.
- The user can move through all six stages.
- At least four evaluator roles are visible and editable.
- The boardroom produces different scores and clear disagreement.
- Every major weakness has a reason and recommended action.
- The interface distinguishes facts, assumptions and simulation.
- The output does not claim certainty about winning.
- The experience feels like a coherent product, not separate prototype screens.
- The complete demo can be shown in under three minutes.

## 25. Three-minute demo script

1. “Bidroom tests whether a proposal can survive the client’s internal decision room.”
2. Load the Northstar demo bid.
3. Show the RFP map: 42 requirements, 7 partial answers and 3 high-risk gaps.
4. Open the bid review: strong strategic fit, weak operational reassurance.
5. Open Build the Room and show the user-supplied CFO pressure and operations scepticism.
6. Run the boardroom.
7. Show executive sponsor at 82 and finance at 54.
8. Show the diagnosis: strategic enthusiasm is not converting into financial confidence.
9. Show the top action: quantify benefits and assign ownership.
10. Close with: “We do not claim to know whether you will win. We show you the reasons the client might say no, before they do.”

## 26. Final instruction to Claude

Build the working frontend, not a written explanation. Make the demo path reliable without external API dependencies. Use realistic mock data behind clean service abstractions. Prioritise visual clarity, interaction quality, trust and the boardroom insight over feature breadth. If a feature conflicts with speed or reliability, choose the simplest polished implementation and leave a clear extension point for a real parser or model backend later.
