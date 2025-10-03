Cloud: AWS (MVP)
Runtime: Python 3.11
Infra baseline: Serverless-first
Data: DynamoDB (high-write KV), Aurora Serverless v2 (relational), S3 (events/logs)
Messaging: EventBridge (async), SQS (work queues)
APIs: API Gateway (REST)
Security: IAM, Secrets Manager, KMS
Observability: CloudWatch + OTEL; structured logs + traces
Cost: managed serverless, cap idle costs
IaC: Terraform
