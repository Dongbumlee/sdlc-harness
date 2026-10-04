---
name: sdlc-aws-deployment
description: >-
  Create AWS infrastructure with CDK (TypeScript) using L2/L3 constructs, deploy
  containerized services to App Runner (API) and ECS Fargate (workers), and manage
  deployment lifecycle. Use when writing CDK stacks, configuring App Runner,
  setting up Fargate services, or preparing deployments. Triggers on CDK, App
  Runner, Fargate, ECS, infrastructure, or deployment requests. Never use raw
  CloudFormation or L1 (Cfn*) constructs — always use L2/L3 CDK constructs.
version: "1.0"
author: sdlc-harness
user-invocable: false
---

# SDLC AWS Deployment — CDK + App Runner + Fargate

## When to use

- Creating or updating CDK stacks (TypeScript)
- Deploying HTTP APIs to App Runner
- Running background workers on ECS Fargate
- Wiring SQS queues, Secrets Manager, ECR, IAM roles
- Reviewing infrastructure-as-code for compliance
- Preparing environment promotion (dev → staging → production)

## Paved-road architecture

One CDK app, two compute targets — this is the pack's core opinion:

```
                 ┌─────────────┐
                 │  App Runner │  HTTP API (request-driven, auto-scaling)
                 └──────┬──────┘
                        │ enqueue job
                 ┌──────▼──────┐      ┌──────────────┐
                 │ SQS queue   ├─────►│ DLQ          │  poison messages, retryable
                 │ (jobs)      │      └──────────────┘
                 └──────┬──────┘
                        │ long-poll
          ┌─────────────▼──────────────┐
          │ ECS Fargate service        │  background worker (long-running,
          │ (worker, Spot eligible)    │  up to 25 min per deep-research job)
          └─────────────┬──────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   DynamoDB        S3 buckets      Secrets Manager
   (single table)  (private only)  (LLM + search API keys)
```

**Why this split:** App Runner is request-driven and cannot host long-running
background work. The worker (planner → researchers → critic → writer pipeline)
runs on Fargate, which also unlocks Fargate Spot pricing for retryable,
DLQ-backed work.

## Step 0: Probe the target region before anything else (SCP-aware)

An organization Service Control Policy can deny **every** AWS API call
outside an allow-listed region. The scenario-2 "different region" variant
died on this: the org SCP explicitly denied ECR, Lambda, EC2, and DynamoDB
calls in every probed region except `us-east-2` — discovered only at
deploy time (2026-10-03).

**Probe effective permissions before synth, not after deploy:**

```bash
# Lightweight, read-only, per service — fail fast with a clear message
for svc in "ec2 describe-availability-zones" \
           "ecr describe-repositories" \
           "lambda list-functions" \
           "dynamodb list-tables"; do
  aws $svc --region <target-region> || echo "BLOCKED: $svc in <target-region>"
done
```

`AccessDeniedException ... explicit deny in a service control policy`
means the region is unreachable — no synthesis or deploy will fix it.
Do not let the builder discover this mid-deploy.

## Step 1: Load CDK best practices

Use the CDK MCP server for construct selection and patterns:

```
# via packs/aws/mcp-servers.json -> aws-cdk (uvx awslabs.cdk-mcp-server@latest)
```

For authoritative service docs, use the AWS documentation MCP server
(`awslabs.aws-documentation-mcp-server`). For cost checks on the chosen
architecture, use the pricing MCP server (`awslabs.aws-pricing-mcp-server`).

## Step 2: L2/L3 constructs — MANDATORY

**⛔ NEVER write raw CloudFormation or L1 (`Cfn*`) constructs.**
**✅ ALWAYS use L2/L3 CDK constructs.** L2 constructs encode security defaults,
sane naming, and grant helpers — the same role AVM modules play on Azure.

**WRONG — L1 construct:**
```typescript
// ⛔ WRONG: raw CloudFormation escape hatch
const bucket = new s3.CfnBucket(this, 'Bucket', {
  bucketName: 'my-bucket',
  // no Block Public Access, no encryption, no lifecycle — all manual
});
```

**CORRECT — L2 construct:**
```typescript
// ✅ CORRECT: L2 construct with secure defaults
const bucket = new s3.Bucket(this, 'Artifacts', {
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  encryption: s3.BucketEncryption.S3_MANAGED,
  enforceSSL: true,
  lifecycleRules: [{ expiration: Duration.days(30) }],
});
```

**If no L2 construct exists** for a resource, only then use L1 — and add a comment:
`// No L2 construct available — using L1 escape hatch`.

## Step 3: IAM — grant methods, never inline policy JSON

**⛔ NEVER hand-write IAM policy JSON.**
**✅ ALWAYS use `grant*()` methods** on the construct that owns the resource.

```typescript
// ✅ CORRECT: least-privilege grants, no policy JSON
table.grantReadWriteData(workerTaskRole);
bucket.grantPut(workerTaskRole);
bucket.grantRead(apiTaskRole);
secret.grantRead(workerTaskRole);
```

Rules:
- One IAM role per compute target (API role, worker role) — never a shared
  god-role.
- Task roles (not access keys) for AWS API access from containers. If you see
  `AWS_ACCESS_KEY_ID` in code or env files, that is a critical finding.
- Trust policies: only the service principal that needs it
  (`ecs-tasks.amazonaws.com`, `tasks.apprunner.amazonaws.com`).

## Step 4: Secrets — Secrets Manager, injected at runtime

All secrets (LLM API key, search API key) live in Secrets Manager and are
injected as secure environment variables — never plaintext, never baked into
the image:

```typescript
// ✅ CORRECT: secret injected by the platform
const apiKey = secretsmanager.Secret.fromSecretNameV2(this, 'LlmKey', 'prod/llm-api-key');

new apprunner.Service(this, 'Api', {
  source: apprunner.Source.fromEcr({ imageConfiguration: { port: 8000 } }),
  // secrets referenced, not embedded
});
workerTaskDefinition.addContainer('worker', {
  image: ecs.ContainerImage.fromEcrRepository(repo),
  secrets: {
    LLM_API_KEY: ecs.Secret.fromSecretsManager(apiKey),
  },
});
```

## Step 5: Cost guardrails (enforced, not advisory)

- **NAT Gateway is guilty until proven innocent.** S3 and DynamoDB have **free
  gateway VPC endpoints** — use them instead of routing through NAT. A NAT
  Gateway with no justification is a compliance finding.
- **Fargate Spot** for the worker: the job queue + DLQ makes work retryable, so
  Spot interruption is safe and ~70% cheaper.
- **App Runner**: provisioned instances only when cold starts hurt; default to
  auto-scaling from zero.
- **CloudWatch Logs**: always set a retention period (e.g. 30 days). Forgotten
  log groups with infinite retention are a classic money leak.
- Run `cdk-nag` on every stack; suppressions require a written justification.
- **cdk-nag `AwsSolutions-EC23` false positive on VPC CIDR intrinsics.**
  The rule ("security groups should not allow ingress from 0.0.0.0/0")
  cannot resolve `Fn::GetAtt` VPC CIDR references — it reports a validation
  *error* (not a finding) on SG rules allowing 443 from the VPC CIDR via
  intrinsic. Verify the synthesized template manually for this pattern; do
  not treat nag output as a pure pass/fail gate here (found 2026-10-03).
- **The "no NAT" rule has a sharp edge for synchronous endpoints.** A Lambda
  in isolated subnets has **no internet access**. If a synchronous endpoint
  must reach a public dependency (Pulse `/admin/collect` → public feed,
  2026-10-03), it fails outright — the scheduled path (EventBridge →
  Fargate) worked, the sync admin path did not. Default to (a): the endpoint
  only *triggers* async work and never calls the public dependency itself.
  If the endpoint itself needs egress, justify a NAT gateway for the API
  subnets or move the endpoint to a target with egress — and document it.

## Step 6: CDK app layout

```
infra/
├── bin/app.ts                  # CDK app entry point
├── lib/
│   ├── network-stack.ts        # VPC, gateway endpoints (no NAT by default)
│   ├── data-stack.ts           # DynamoDB table, S3 buckets
│   ├── queue-stack.ts          # SQS queue + DLQ
│   ├── compute-stack.ts        # App Runner API, Fargate worker, ECR, roles
│   └── secrets-stack.ts        # Secrets Manager secrets
├── cdk.json
└── cdk.context.json            # per-environment context (dev/staging/prod)
```

Conventions:
- TypeScript CDK only (v1 paved road).
- One stack per concern above; cross-stack references via exported values.
- Default region `us-west-2` (v1); make it a context parameter, not hardcoded.
- Standard tags on all stacks: `Project`, `Environment`, `ManagedBy=cdk`.

## Container image contracts (deploy-verified 2026-10-03)

- **Region comes from the stack, never from code.** `AWS_REGION` (and
  `AWS_DEFAULT_REGION`) are required container env vars, sourced from the
  stack region. The worker once hardcoded a `us-west-2` default while
  deployed in `us-east-2` — botocore performs **no** SQS QueueUrl region
  redirection (the request goes to the client's region endpoint), so this
  was a latent multi-region bug that "worked anyway" for unexplained
  reasons.

  ```typescript
  // ✅ CORRECT
  workerTaskDefinition.addContainer('worker', {
    image: ...,
    environment: {
      AWS_REGION: this.region,
      AWS_DEFAULT_REGION: this.region,
    },
  });
  ```

  ```python
  # ⛔ WRONG: region default baked into application code
  AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
  ```

- **Reusing a Lambda base image on Fargate: override the entrypoint.**
  Lambda base images set `ENTRYPOINT` to the Lambda runtime interface
  client, which demands a handler argument — on Fargate the task exits
  immediately (exit 142, Pulse deploy 2026-10-03). Override it:

  ```typescript
  entryPoint: ['/var/lang/bin/python3'],
  command: ['-m', 'collector.collect'],
  ```

- **Image tag prefixes must match between build and deploy.** If the CDK
  app prefixes tags (e.g. `pulse-<tag>`), CI must push with the same
  prefix — otherwise the deploy references an image that was never pushed
  (Pulse deploy 2026-10-03: build pushed `<tag>`, CDK expected
  `pulse-<tag>`, recovered with an ECR retag). One convention, enforced in
  CI.

## ElastiCache Serverless notes (deploy-verified 2026-10-03)

No L2 construct exists — use the L1 escape hatch (`CfnServerlessCache`)
with the comment from Step 2.

- **TLS is mandatory.** ElastiCache Serverless requires TLS; connecting
  without `ssl=True` hangs the read forever — surfaced as a Lambda timeout
  with no error at all. Always:

  ```python
  redis.Redis(host=..., port=..., ssl=True, socket_timeout=5,
              decode_responses=True)
  ```

## Gotchas

- **App Runner ≠ worker host.** Long-running background jobs go on Fargate.
  Putting the agent pipeline on App Runner will hit request timeouts.
- **L1 constructs are the #1 mistake** — the same way raw `resource`
  declarations are on Azure. Always check for an L2 construct first.
- **Secrets in `cdk.context.json`** — context files get committed; secrets never
  go there. Secrets Manager only.
- **`cdk deploy --require-approval never`** in CI is convenient and dangerous —
  keep manual approval for IAM-changing deployments.
- **ECR image immutability** — tag images by git SHA, never redeploy `:latest`
  and assume it moved.
- **SQS visibility timeout** must exceed the longest single poll-process cycle
  of the worker, or messages return to the queue mid-processing.
- **CDK CLI behind an egress proxy** — set `no_proxy` to bypass the proxy
  for AWS endpoints, or synth/deploy calls hang or fail (agent-VM finding
  2026-10-03).

## Where files go

| Artifact | Location |
|---|---|
| CDK app | `infra/` |
| Stacks | `infra/lib/*-stack.ts` |
| Container images | ECR repositories (created by CDK) |
| API service code | `src/<Name>API/` |
| Worker service code | `src/<Name>Worker/` |
