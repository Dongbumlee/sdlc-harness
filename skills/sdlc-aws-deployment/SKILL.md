---
name: sdlc-aws-deployment
description: >-
  Create AWS infrastructure with CDK (TypeScript) using L2/L3 constructs, deploy
  containerized APIs to Lambda (container image + Function URL) and long-running
  workers to ECS Fargate Spot, and manage deployment lifecycle. Use when writing
  CDK stacks, configuring Lambda container functions, setting up Fargate
  services, or preparing deployments. Triggers on CDK, Lambda, Function URL,
  Fargate, ECS, infrastructure, or deployment requests. Never use raw
  CloudFormation or L1 (Cfn*) constructs — always use L2/L3 CDK constructs.
  Never use App Runner for new work — it is closed to new customers since
  2026-04-30.
version: "1.1"
author: sdlc-harness
user-invocable: false
---

# SDLC AWS Deployment — CDK + Lambda + Fargate

## When to use

- Creating or updating CDK stacks (TypeScript)
- Deploying containerized HTTP APIs to Lambda (container image + Function URL)
- Running background workers on ECS Fargate
- Wiring SQS queues, Secrets Manager, ECR, IAM roles
- Reviewing infrastructure-as-code for compliance
- Preparing environment promotion (dev → staging → production)

## Paved-road architecture

One CDK app, two compute targets — this is the pack's core opinion:

```
             ┌──────────────────────┐
             │ Lambda (container    │  HTTP API — same Docker image,
             │ image) + Function URL│  $0 at test scale (always-free tier)
             └──────────┬───────────┘
                        │ enqueue job
             ┌──────────▼───────────┐      ┌──────────────┐
             │ SQS queue            ├─────►│ DLQ          │  poison messages, retryable
             │ (jobs)               │      └──────────────┘
             └──────────┬───────────┘
                        │ long-poll
          ┌─────────────▼──────────────┐
          │ ECS Fargate service        │  background worker (long-running,
          │ (Spot)                     │  up to 25 min per deep-research job —
          └─────────────┬──────────────┘  exceeds Lambda's 15-min limit)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   DynamoDB        S3 buckets      Secrets Manager
   (single table)  (private only)  (LLM + search API keys)
```

**Why this split:** the API is request-driven and short-lived — a container
image on Lambda with a Function URL keeps the Docker story (same image as the
worker) at $0 idle via the always-free tier (1M requests + 400k GB-seconds/mo),
with HTTPS and no ALB/API Gateway bill. The worker (planner → researchers →
critic → writer pipeline, up to 25 min/job) exceeds Lambda's 15-minute limit,
so it runs on Fargate — where the SQS + DLQ retry contract also unlocks
Fargate Spot pricing (~70% cheaper, interruption-safe).

**⛔ App Runner is dead for new work.** AWS closed it to new customers on
2026-04-30 (maintenance mode, no new features). Never recommend it; if you
find it in existing code, flag migration to the road below.

**Scale-up path:** when the API outgrows Lambda (sustained high traffic,
connections beyond response streaming, VPC subtleties), move it to an ECS
Fargate service + ALB (or ECS Express Mode) — same container image, same SQS
contract, no API redesign.

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
table.grantReadWriteData(apiFn);      // Lambda execution role, created by the L2
table.grantReadWriteData(workerTaskRole);
bucket.grantPut(workerTaskRole);
bucket.grantRead(apiFn);
secret.grantRead(workerTaskRole);
secret.grantRead(apiFn);
```

Rules:
- One IAM role per compute target (API role, worker role) — never a shared
  god-role.
- Task/execution roles (not access keys) for AWS API access. If you see
  `AWS_ACCESS_KEY_ID` in code or env files, that is a critical finding.
- Trust policies: only the service principal that needs it
  (`ecs-tasks.amazonaws.com`, `lambda.amazonaws.com`).

## Step 4: Secrets — Secrets Manager, never plaintext

All secrets (LLM API key, search API key) live in Secrets Manager — never
plaintext env vars, never baked into the image:

```typescript
// ✅ CORRECT: Fargate — secret injected by the platform
const apiKey = secretsmanager.Secret.fromSecretNameV2(this, 'LlmKey', 'prod/llm-api-key');

workerTaskDefinition.addContainer('worker', {
  image: ecs.ContainerImage.fromEcrRepository(repo),
  secrets: {
    LLM_API_KEY: ecs.Secret.fromSecretsManager(apiKey),
  },
});

// ✅ CORRECT: Lambda — grant read, fetch at runtime with in-memory cache
const apiFn = new lambda.DockerImageFunction(this, 'Api', {
  code: lambda.DockerImageCode.fromEcr(repo, { tag: gitSha }),
  memorySize: 1024,
  timeout: Duration.seconds(30),
});
apiKey.grantRead(apiFn);
// handler fetches once per execution environment and caches —
// never put the secret value in `environment`
```

## Step 5: Cost guardrails (enforced, not advisory)

- **Lambda always-free tier covers the API** at dev/test scale (1M req +
  400k GB-s/mo). **Function URL, not API Gateway** — HTTPS with no per-hour
  charge. API Gateway only when you need its features (usage plans, WAF,
  custom authorizers at scale).
- **Fargate Spot** for the worker: the job queue + DLQ makes work retryable, so
  Spot interruption is safe and ~70% cheaper.
- **NAT Gateway is guilty until proven innocent.** S3 and DynamoDB have **free
  gateway VPC endpoints** — use them instead of routing through NAT. A NAT
  Gateway with no justification is a compliance finding.
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
│   ├── compute-stack.ts        # Lambda API (container + Function URL),
│   │                           # Fargate worker service, ECR, roles
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

- **Lambda 15-minute timeout.** Long-running background jobs go on Fargate.
  Putting the agent pipeline on Lambda will hit the timeout wall.
- **Function URL auth**: `authType: NONE` + application-level auth for v1;
  `AWS_IAM` only when callers can sign requests.
- **Container image architecture**: the ECR image arch (arm64/x86_64) must match
  the Lambda architecture setting — mismatches fail at invoke time, not deploy.
- **Lambda container images** need the Lambda runtime interface — use AWS base
  images or the Lambda Web Adapter; a plain web-server image will not boot.
- **Cold starts**: measure before adding provisioned concurrency — at test scale
  you will not need it.
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
