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
version: "1.2"
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
             │ Lambda (container    │  HTTP API — same ECR repo as the worker
             │ image) + Function URL│  ($0 at test scale: always-free tier);
             └──────────┬───────────┘  two tagged images, api-<tag>/worker-<tag>
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
image on Lambda with a Function URL keeps the Docker story (same ECR repo as the
worker, two tagged images) at $0 idle via the always-free tier (1M requests + 400k GB-seconds/mo),
with HTTPS and no ALB/API Gateway bill. The worker (planner → researchers →
critic → writer pipeline, up to 25 min/job) exceeds Lambda's 15-minute limit,
so it runs on Fargate — where the SQS + DLQ retry contract also unlocks
Fargate Spot pricing (~70% cheaper, interruption-safe).

**Single-table key design.** DynamoDB uses one table per the pack's reference
key design: list access patterns first, then model them as `PK`/`SK` with a
sparse `GSI1` (`STATUS#<status>`). The canonical reference layout lives in the
`sdlc-dynamodb-repository` skill (Step 1) — every table design in this pack
starts there.

**⛔ App Runner is dead for new work.** AWS closed it to new customers on
2026-04-30 (maintenance mode, no new features). Never recommend it; if you
find it in existing code, flag migration to the road below.

**Scale-up path:** when the API outgrows Lambda (sustained high traffic,
connections beyond response streaming, VPC subtleties), move it to an ECS
Fargate service + ALB (or ECS Express Mode) — same image contract (one ECR repo,
`api-`/`worker-` tags), same SQS contract, no API redesign.

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

**Offline fallback:** if the MCP servers are unavailable in the environment,
do not block the build — proceed from CDK API knowledge plus this skill, and
note the limitation in the build log. The pack's guidance must stand on its
own; MCP servers are accelerators, not prerequisites.

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

### Creating secrets in CDK

The examples above import existing secrets. To create them in the stack:

```typescript
const apiKeys = new secretsmanager.Secret(this, 'ApiKeys', {
  secretName: 'deep-research/api-keys',
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ keys: [] }),
    generateStringKey: 'placeholder', // replaced post-deploy, see below
  },
});
```

Post-deploy, set the real values out of band — never commit them:

```bash
aws secretsmanager put-secret-value \
  --secret-id deep-research/api-keys \
  --secret-string '{"keys":["<key>"]}'
```

Secret rotation needs a custom rotation Lambda — out of v1 scope. Document
the rotation plan instead of pretending rotation exists.

### Application-level auth for Function URL (`authType: NONE`)

v1 uses `authType: NONE` + application-level auth. The paved pattern:

- API keys live in Secrets Manager as JSON: `{"keys": ["<key>", ...]}`.
- The Lambda handler fetches the secret **at runtime** (never in
  `environment`) and caches it in memory with a ~60s TTL, so key rotation
  takes effect without a redeploy and Secrets Manager calls stay cheap.
- Per-key rate limits (spec: 10 jobs/hour) are DynamoDB counter items with
  TTL: `RATE#<key>#<hour>` → `{count, expires_at}`; a conditional write
  fails the request with 429 when the count exceeds the limit.

```python
# handler sketch: cached key fetch
_api_keys, _keys_fetched_at = None, 0.0

def _valid_key(provided: str) -> bool:
    global _api_keys, _keys_fetched_at
    if time.time() - _keys_fetched_at > 60:  # 60s in-memory cache
        resp = secrets_client.get_secret_value(SecretId=API_KEYS_SECRET_NAME)
        _api_keys = set(json.loads(resp["SecretString"])["keys"])
        _keys_fetched_at = time.time()
    return provided in _api_keys
```

## Step 5: Cost guardrails (enforced, not advisory)

- **Lambda always-free tier covers the API** at dev/test scale (1M req +
  400k GB-s/mo). **Function URL, not API Gateway** — HTTPS with no per-hour
  charge. API Gateway only when you need its features (usage plans, WAF,
  custom authorizers at scale).
- **Fargate Spot** for the worker: the job queue + DLQ makes work retryable, so
  Spot interruption is safe and ~70% cheaper.
- **The "$0 at test scale" story covers the API, not the worker.** Lambda's
  always-free tier makes the API free at dev scale; the Fargate worker at
  `desiredCount: 1` (0.25 vCPU / 0.5 GB on Spot) still costs ~$15/mo idle.
  For dev: scale the service to zero when idle, add SQS-driven autoscaling
  (scale on `ApproximateNumberOfMessagesVisible`), or destroy the stack after
  testing — a forgotten `desiredCount: 1` is the actual money leak.
- **NAT Gateway is guilty until proven innocent.** S3 and DynamoDB have **free
  gateway VPC endpoints** — use them instead of routing through NAT. A NAT
  Gateway with no justification is a compliance finding.
- **CloudWatch Logs**: always set a retention period (e.g. 30 days). Forgotten
  log groups with infinite retention are a classic money leak.
- Run `cdk-nag` on every stack; suppressions require a written justification.
  Starter triage for the findings every L2-based app hits:

  | Finding | Triage |
  |---|---|
  | IAM4/IAM5 on L2 default roles | Suppress with justification: CDK-managed roles need the wildcarded actions. `ecr:GetAuthorizationToken` *requires* `Resource: "*"` — AWS mandates it, there is no narrower form. |
  | IAM5 on DynamoDB GSI ARNs | Resource-level `appliesTo` cannot match synth-time logical IDs (e.g. `<Table.Arn>/index/*`); suppress at stack level and document the exact scope in prose instead. |
  | S3 server access logging | Needs a *second* bucket as the log target; for v1, suppress with justification or add the logging bucket. |
  | VPC flow logs | Recurring CloudWatch Logs cost; document the decision (on for prod, off with justification for dev). |
  | Secret rotation | Needs a custom rotation Lambda — out of v1 scope; suppress with justification and a rotation plan. |
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

## Fargate network design (no-NAT)

The no-NAT rule is only half the story: gateway VPC endpoints cover S3 and
DynamoDB for free, but the Fargate worker must also reach **SQS, Secrets
Manager, ECR, and CloudWatch Logs** — none of which have gateway endpoints.
Pick one of these two compliant designs and document the choice:

**Option A — dev/test default: public subnets + public IP ($0 extra).**
The task gets a public IP and reaches AWS services over the internet; no NAT
Gateway, no interface endpoints. Lock it down with an egress-only security
group (no ingress rules — the worker only long-polls SQS):

```typescript
new ecs.FargateService(this, 'Worker', {
  // ...
  vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
  assignPublicIp: true,
  securityGroups: [egressOnlySg], // allowAllOutbound: true, no ingress
});
```

Acceptable when the spec says private networking is not required for v1.

**Option B — production: private subnets + interface VPC endpoints.**
No public IPs on tasks; add interface endpoints for SQS, Secrets Manager,
ECR (api + dkr), and CloudWatch Logs — roughly $7.50/mo each (~$35+/mo idle
for the full set). Choose this when compliance requires no public IPs.

**Rule:** the network design must be written down (which option and why).
"No NAT" without one of these two designs is an incomplete design, not a
cost saving — the compliance reviewer checks for it.
=======
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
>>>>>>> feat/pack-gaps-scenarios-234

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
- `cdk.context.json` carries per-environment, **non-secret** context:
  `environment`, `region`, `imageTag` (plus CDK feature flags). Secrets never
  go there (see Gotchas).
- **ECR image tag wiring:** the tag comes from the `imageTag` CDK context
  parameter (default `"dev"`). CI sets it from the git SHA:
  `npx cdk deploy -c imageTag=$GITHUB_SHA`. Images are tagged
  `api-<imageTag>` and `worker-<imageTag>` (see "ECR image pipeline" below).

## ECR image pipeline (who builds what, in which order)

Lambda's `DockerImageCode.fromEcr` resolves the image URI **at deploy time**,
so the repository and the images must exist *before* `cdk deploy` runs.
Creating the repo inside the compute stack does not work — the image is not
there yet when the Lambda function is created.

Order of operations:

1. Create the ECR repo **outside** the compute stack (one CLI step, or a
   bootstrap stack):
   `aws ecr create-repository --repository-name <name>`.
2. Build (matching arch — see Gotchas) and push both images:
   `api-<imageTag>` and `worker-<imageTag>`.
3. Deploy with the repo imported, not created:
   `ecr.Repository.fromRepositoryName(this, 'Images', '<name>')`.
4. `npx cdk deploy -c imageTag=$GITHUB_SHA`.

**One repo, two images** — this is the pack's answer to "one image or two":
`api-<tag>` carries the Lambda runtime interface (AWS base image or the
Lambda Web Adapter); `worker-<tag>` does not need it. Both live in the same
ECR repository.

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

- **Lambda 15-minute timeout.** Long-running background jobs go on Fargate.
  Putting the agent pipeline on Lambda will hit the timeout wall.
- **Function URL auth**: `authType: NONE` + application-level auth for v1;
  `AWS_IAM` only when callers can sign requests.
- **Container image architecture**: the ECR image arch (arm64/x86_64) must match
  the Lambda architecture setting — mismatches fail at invoke time, not deploy.
  Pin `--platform=linux/amd64` at build time when targeting `X86_64`, and add
  a CI check: `docker inspect --format '{{.Architecture}}' <image>` must agree
  with the CDK `Architecture` / `CpuArchitecture` setting.
- **Lambda container images** need the Lambda runtime interface — use AWS base
  images or the Lambda Web Adapter; a plain web-server image will not boot.
- **Lambda runs containers as non-root**: source files in the image must be
  world-readable. Docker `COPY` preserves host file modes — `660` files (e.g.
  from a restrictive umask) cause an init-time `PermissionError` and every
  invocation returns HTTP 502 with no application logs. Fix modes at the
  source (`chmod -R a+rX`) and add a defensive `RUN chmod -R a+r /var/task`
  to the Lambda Dockerfile.
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
  of the worker, or messages return to the queue mid-processing. Formula:
  `visibility timeout ≥ long-poll (20s) + max processing time + clock skew`.
  Worked example: stub worker → 10 min; a real 25-min job → ≥30 min, or keep
  the timeout shorter and extend it with `ChangeMessageVisibility` heartbeats
  while the job runs.
- **CDK CLI behind an egress proxy** — set `no_proxy` to bypass the proxy
  for AWS endpoints, or synth/deploy calls hang or fail (agent-VM finding
  2026-10-03).

## Troubleshooting

- **`cdk bootstrap` / `cdk deploy` dies with `ECONNRESET` mid-call.**
  The CLI sometimes creates the CloudFormation change set and then dies before
  executing it, leaving the stack in `REVIEW_IN_PROGRESS` with no visible
  error. Recover with the AWS CLI — first list stuck stacks, then execute the
  pending change set manually:

  ```bash
  aws cloudformation list-stacks \
    --stack-status-filter REVIEW_IN_PROGRESS
  aws cloudformation execute-change-set \
    --stack-name <stack-name> --change-set-name <pending-change-set-name>
  ```

  Then re-run the CDK command.

- **Raw CloudFormation recovery skips asset publishing.** If you deploy from
  synthesized `cdk.out/` templates with `aws cloudformation create-stack`
  (passing `BootstrapVersion=/cdk-bootstrap/<hash>/version`), `cdk deploy`'s
  asset-publishing step does not run: any template referencing an S3 asset
  (e.g. the log-retention provider's code zip) fails with `NoSuchKey` until
  you manually upload `cdk.out/asset.<hash>` to the bootstrap staging bucket
  under the key the template expects.

## Where files go

| Artifact | Location |
|---|---|
| CDK app | `infra/` |
| Stacks | `infra/lib/*-stack.ts` |
| Container images | ECR repository — one repo, `api-<tag>`/`worker-<tag>` images; repo created outside the compute stack (see "ECR image pipeline") |
| API service code | `src/<Name>API/` |
| Worker service code | `src/<Name>Worker/` |
