
# Business Requirements Document (BRD)
**Application Modernization & Migration to AWS (Terraform + Python)**

---

## 1. Executive Summary
This BRD defines the requirements for modernizing and migrating the identified application to **AWS Cloud**. The migration will be achieved using **Terraform** for Infrastructure-as-Code (IaC) and **Python** for automation and orchestration. The goal is to ensure the application meets business, compliance, and performance objectives while aligning with **Minimum Entry Criteria (MEC)**.

---

## 2. General Application Details
Based on the discovery template provided (`app-cloud-analysis.md`).  
- Application Name: *To be confirmed with client team*  
- Business Area: *Captured in discovery workshop*  
- Dependencies: Listed in discovery template, must migrate in lockstep.  
- Data Classification: As per MEC, sensitive workloads must have encryption and IAM guardrails.  

---

## 3. Current State Architecture (CSA)
Per discovery document:  
- **Server Architecture**: On-prem x86 servers, legacy OS.  
- **Database**: SQL-based DBs noted in discovery template.  
- **Interfaces**: Mix of internal and external APIs, batch file transfers.  
- **Monitoring**: Limited automation, requires migration to AWS-native observability.  
- **Licensing**: Vendor support tied to on-prem; cloud licensing considerations required.  

---

## 4. Target State Architecture (TSA) on AWS
- **Compute**: AWS EC2 for lift-and-shift workloads; ECS/EKS for containerized future state.  
- **Storage**: Amazon S3 for objects; Amazon RDS for relational DB; backup to S3 Glacier.  
- **Networking**: VPC with private/public subnets; ALB/NLB load balancing.  
- **Authentication & IAM**: IAM roles, AWS SSO integration, KMS encryption.  
- **Observability**: CloudWatch logs/metrics, X-Ray tracing, OpenSearch for log analytics.  
- **IaC**: All infra via **Terraform** modules; application automation in **Python** (Lambdas, Glue jobs, Step Functions).  

---

## 5. Minimum Entry Criteria (MEC)
From the provided Excel (`ZNA DCE x86 Minimum Entry Criteria - 240216`):  
**MEC**: 32 rows × 10 cols | Columns: Unnamed: 0, Unnamed: 1, Unnamed: 2, Unnamed: 3, Unnamed: 4, Unnamed: 5, Unnamed: 6, Unnamed: 7...
**Other**: 36 rows × 4 cols | Columns: Software, Recommended, Minimum, Additional Notes...

Applications must remediate any MEC gaps before migration. Common MEC checks include:  
- Supported OS and database versions.  
- Patching and vulnerability compliance.  
- Backup and DR readiness.  
- Monitoring and logging in place.  

---

## 6. Functional Requirements
1. Provision infrastructure using **Terraform** (modular, reusable code).  
2. Implement application automation using **Python**.  
3. Enforce encryption at rest and in transit.  
4. Integrate monitoring and logging into CloudWatch/OpenSearch.  
5. Establish CI/CD pipelines for Terraform and Python automation.  
6. Provide backup, restore, and disaster recovery within RPO/RTO limits.  

---

## 7. Non-Functional Requirements
- **Security**: IAM least privilege, encryption, MEC alignment.  
- **Performance**: Meet/exceed baseline throughput/latency.  
- **Scalability**: Elastic scaling with Auto Scaling Groups/EKS.  
- **Auditability**: CloudTrail and GuardDuty enabled.  
- **Reliability**: HA via multi-AZ, DR strategy documented.  
- **Cost Efficiency**: Right-sized compute, S3 lifecycle management, tagging.  

---

## 8. Migration & Cutover Plan
- **Pre-Migration**: Validate MEC, finalize IaC design, test Terraform.  
- **Migration Execution**:  
  - Lift-and-shift phase: migrate VMs to EC2.  
  - Refactor phase: containerization in ECS/EKS.  
  - Data migration via AWS DMS.  
- **Cutover**: Weekend maintenance window; DNS switch; failback option on-prem.  
- **Post Go-Live**: Hypercare, monitoring validation, MEC compliance sign-off.  

---

## 9. Risks & Mitigation
- **Schema drift**: Validate with AWS DMS pre-cutover.  
- **Performance degradation**: Enable auto-scaling, monitor via CloudWatch.  
- **Security gaps**: Enforce MEC and AWS Security Hub baselines.  
- **Cost overruns**: Apply budgets, tagging, lifecycle rules.  

---

## 10. Acceptance Criteria
- All infrastructure deployed via Terraform.  
- Python automation operational for workflows.  
- MEC compliance validated.  
- Application functional in AWS with no critical issues post-cutover.  
- Business sign-off received.  

---

