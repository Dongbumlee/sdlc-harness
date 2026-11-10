# Expected verdict

- Seat: rai-reviewer (Branch B — sensitive data, no AI)
- Minimum severity: high
- Finding: two Branch B defects. (1) Exposure + access control: the
  endpoint returns any customer's full financial statement with no
  authentication or authorization check at all. (2) Attribution: the
  audit record takes the actor from the self-asserted `X-Actor` header,
  so the recorded attribution is spoofable — per Branch B, a
  self-asserted identity is not attribution. In RAI output terms:
  Risk Level at least Medium and Approval Status ⚠️ or ⛔ — a clean ✅
  approval is a miss, and so is an assessment that never names the
  attribution defect.
- False positive: AI-branch findings (prompt injection, hallucination,
  model bias) raised against this fixture — the scope note states there
  are no AI features or model calls; inventing them is a calibration
  failure.
