# Business Requirements Summary (BRD)

## 1) Context & Goals
We are modernizing a small set of backend capabilities into a serverless footprint on AWS. The system should be simple, cost-efficient, and easily deployable with CI. We’ll prioritize: correctness, idempotency for critical operations, and basic observability.

## 2) Capabilities (derived from current behaviors)
### A. Orders
- Accept new orders and persist them in a key-value store.
- Retrieve an order by ID.
- Emit an event after a successful order creation to trigger downstream work (e.g., building a receipt).

### B. Receipts
- React to the “order created” event and perform a follow-up task (e.g., generate/log a receipt).
- Initial implementation can be a no-op worker (no external calls) while we validate the event flow.

### C. CRM Ingestion
- Nightly/as-needed CSV files are dropped to object storage.
- On each file, parse rows and emit a canonical “customer upserted” event for each valid record.

### D. Inventory Reservations
- Accept a reservation request that decrements inventory if sufficient stock exists.
- Enforce **idempotency** for reservation requests using a client-supplied `request_id` with a 24-hour TTL.
- Publish an “inventory reserved” event upon success; reject with a conflict if insufficient stock.

## 3) Non-Functional Requirements
- **Cloud**: AWS.
- **Architecture**: Prefer simple serverless (HTTP API + Lambdas + DynamoDB + EventBridge + S3 for ingestion).
- **Security**: No plaintext secrets in source control. Use SSM Parameter Store / GitHub Secrets and OIDC for CI.
- **IAM**: Least-privilege; scope to specific resources (tables, buckets, buses, functions).
- **Observability**: JSON logs; minimal CloudWatch alarms (errors/throttles). X-Ray optional.
- **Environments**: PR “preview” (plan only) and a **staging** environment for apply.
- **Idempotency & Concurrency**: Where applicable (e.g., inventory), enforce exactly-once semantics using conditional writes.

## 4) Suggested Logical Model (informative, not prescriptive)
- **Orders Service**
  - Ingress: HTTP (create/get).
  - Storage: Orders table (partition key: `order_id`).
  - Egress: Event “ReceiptGenerated”.
- **Receipts Worker**
  - Ingress: Event “ReceiptGenerated”.
  - Behavior: Minimal processing/logging.
- **CRM Ingestor**
  - Ingress: S3 object created (CSV).
  - Egress: Event “CustomerUpserted”.
- **Inventory Service**
  - Ingress: HTTP (reserve).
  - Storage: Inventory table (`sku`) + idempotency marker items (`idem#{request_id}` with TTL).
  - Egress: Event “InventoryReserved”.

## 5) Constraints & Guardrails
- Prefer HTTP API (API Gateway v2), Lambda (Python 3.11), DynamoDB (on-demand), EventBridge.
- Resource names should be parameterized as `project-env-*`.
- All routing, triggers, and env var wiring should be defined in IaC (Terraform).
- CI must lint, test, package, and run Terraform plan; auto-apply only to staging on main branch with OIDC.

## 6) Acceptance (high-level)
- The system deploys via CI to staging.
- Basic unit tests exist per discovered handler.
- Terraform validates/plans cleanly; IAM policies are scoped.
- Event flows function (orders→receipt, CSV→customer upsert, inventory→reserved).
