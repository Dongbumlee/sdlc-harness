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

## Where files go

| Artifact | Location |
|---|---|
| CDK app | `infra/` |
| Stacks | `infra/lib/*-stack.ts` |
| Container images | ECR repositories (created by CDK) |
| API service code | `src/<Name>API/` |
| Worker service code | `src/<Name>Worker/` |
