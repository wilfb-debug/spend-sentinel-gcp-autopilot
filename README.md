# SpendSentinel — GCP FinOps Automation Platform

[![CI](https://github.com/wilfb-debug/spend-sentinel-gcp-autopilot/actions/workflows/ci.yml/badge.svg)](https://github.com/wilfb-debug/spend-sentinel-gcp-autopilot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4?logo=google-cloud)](https://cloud.google.com)
[![tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/wilfb-debug/spend-sentinel-gcp-autopilot/actions)
[![coverage](https://img.shields.io/badge/coverage-80%25+-brightgreen)](https://github.com/wilfb-debug/spend-sentinel-gcp-autopilot/actions)

> Serverless GCP FinOps platform implementing the **Inform** and **Optimize** phases of the FinOps Foundation framework — automated cost allocation, idle resource detection, right-sizing analysis, anomaly surfacing, and stakeholder showback reporting. No manual intervention required.

---

## What It Does

SpendSentinel brings financial accountability to GCP infrastructure. It runs continuously without human oversight, and outputs cost intelligence that engineering leads and finance partners can act on.

Three FinOps capabilities delivered out of the box:

**Inform** — Cloud Asset Inventory API feeds a BigQuery cost allocation layer with always-current resource metadata, tagged by project, type, environment, and location. Engineering teams get visibility into what they own and what it costs.

**Optimize** — Scheduled detection jobs surface right-sizing candidates, idle compute resources, and unallocated assets. Findings are written to BigQuery with quantified estimated monthly savings per resource — not vague recommendations, actionable numbers.

**Operate** — A Looker Studio showback dashboard gives stakeholders a shared view of spend, flagged resources, and savings potential — no BigQuery access or SQL knowledge required.

---

## The Problem

Cloud environments grow quietly. Without automated allocation and detection, engineering teams have no visibility into:

- **Idle resources** consuming budget with zero utilisation
- **Oversized instances** where actual usage is a fraction of provisioned capacity
- **Untagged or unallocated resources** that can't be attributed to teams, products, or environments
- **Cost anomalies** that go undetected until the monthly invoice arrives

The result: cloud spend increases silently. Finance teams see a number. Engineering teams don't know where it came from.

SpendSentinel reduces time-to-action on cloud waste from days to minutes — without manual reviews or spreadsheet reconciliation.

---

## Architecture

![Architecture Diagram](docs/images/architecture-diagram.png)

### Pipeline Flow

```
Cloud Scheduler (daily trigger)
        ↓
Cloud Run Job (inventory service)
        ↓
Cloud Asset Inventory API
        ↓
BigQuery — inventory table (cost allocation layer)
        ↓
FinOps analysis query (right-sizing + idle detection)
        ↓
BigQuery — findings table (quantified savings per resource)
        ↓
BigQuery — daily_savings table (aggregated trend data)
        ↓
Looker Studio — showback dashboard
```

### Component Breakdown

| Component | Role |
|---|---|
| **Cloud Scheduler** | Daily trigger — no always-on compute cost |
| **Cloud Run Job** | Ephemeral container — runs, writes findings, exits |
| **Cloud Asset Inventory API** | Source of truth for all GCP resource metadata |
| **BigQuery (inventory)** | Cost allocation layer — full resource catalogue with labels |
| **BigQuery (findings)** | Structured optimisation findings with savings estimates |
| **BigQuery (daily_savings)** | Aggregated trend data — feeds dashboard savings timeline |
| **Looker Studio** | Stakeholder showback — shareable without BigQuery access |

---

## FinOps Capabilities

| Capability | Implementation | FinOps Phase |
|---|---|---|
| **Cost Allocation** | Cloud Asset Inventory → BigQuery with project, type, location, label attribution | Inform |
| **Idle Resource Detection** | Cloud Run jobs flag resources with no activity signals | Optimize |
| **Right-Sizing Analysis** | Compute instance analysis against utilisation thresholds → findings with savings estimate | Optimize |
| **Showback Reporting** | Looker Studio dashboard — shareable link, no SQL required | Operate |
| **Anomaly Surfacing** | Daily scan delta surfaces new cost risks between runs | Inform |
| **Tagging Compliance** | Label coverage checked per resource — untagged resources flagged as allocation gaps | Inform |

---

## Example Finding

| Resource | Finding Type | Recommendation | Est. Monthly Saving | Est. Annual Saving |
|---|---|---|---|---|
| ss-test-vm | Right-Sizing Candidate | Downsize to n2-standard-1 | $27 | $324 |

At scale across an organisation's full resource catalogue, SpendSentinel surfaces a backlog of optimisation opportunities — ranked by savings impact — that engineering and finance teams can prioritise together.

---

## Data Schema

### `inventory` table
Full resource catalogue for cost allocation and trend analysis.

| Column | Description |
|---|---|
| resource_id | Unique GCP resource identifier |
| resource_name | Human-readable resource name |
| resource_type | GCP resource type (e.g. compute.googleapis.com/Instance) |
| project_id | GCP project — maps to cost allocation unit |
| location | Region / zone |
| labels | Key-value tags for showback attribution |
| collected_at | Scan timestamp — enables trend analysis |

### `findings` table
Structured cost optimisation findings with quantified savings.

| Column | Description |
|---|---|
| resource_id | Resource reference |
| resource_name | Human-readable name |
| finding_type | Idle, Right-Sizing Candidate, Untagged, etc. |
| recommendation | Specific action — downsize, delete, tag |
| estimated_monthly_savings | Quantified saving in USD |
| detected_at | Detection timestamp |

### `daily_savings` table
Aggregated savings potential per day — feeds the Looker Studio trend line for QBR and budget conversations.

---

## Project Walkthrough

### Billing Export Enabled
Cloud billing export activated so actual spend data feeds the BigQuery analytics layer.

![Billing Export](docs/01-billing-export-enabled.png)

---

### BigQuery Dataset Created
SpendSentinel dataset provisioned to store inventory, findings, and savings data.

![BigQuery Dataset](docs/02-bigquery-datasets-created.png)

---

### Findings Table Created
Stores detected cost optimisation opportunities with estimated savings per resource.

![Findings Table](docs/03-table-findings-created.png)

---

### Actions Log Table Created
Tracks optimisation actions taken — audit trail for FinOps governance reporting.

![Actions Log](docs/04-table-actions-log-created.png)

---

### Daily Savings Table
Aggregates potential savings per day — powers the QBR dashboard trend line.

![Daily Savings](docs/05-table-daily-savings-created.png)

---

### BigQuery Tables Overview
Full FinOps data schema provisioned and ready.

![BigQuery Tables](docs/06-spendsentinel-bigquery-tables.png)

---

### Inventory Table Populated
Cloud Run job executes successfully — resource catalogue written to BigQuery.

![Inventory Data](docs/07-inventory-table-created.png)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Compute** | Cloud Run (serverless jobs — no idle cost) |
| **Scheduling** | Cloud Scheduler |
| **Discovery** | Cloud Asset Inventory API |
| **Analytics** | BigQuery |
| **Visualisation** | Looker Studio |
| **Language** | Python 3.12 |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions |

---

## Project Structure

```
spend-sentinel/
│
├── Services-detectors/
│   └── inventory-service/     # Cloud Run job — resource discovery + findings
│
├── Services-enforcer/         # Cleanup policy enforcement
│
├── Infra/                     # Terraform — all infrastructure as code
│
├── sql/
│   ├── create_inventory_table.sql
│   ├── create_findings_table.sql
│   └── cost_analysis_query.sql
│
├── dashboards/                # Looker Studio config
│
├── tests/                     # Unit tests — 80%+ coverage
│
└── docs/                      # Architecture diagrams + walkthrough screenshots
```

---

## Architecture Principles

- **Serverless by default** — no always-on infrastructure, no idle compute cost; SpendSentinel doesn't waste what it's designed to save
- **FinOps-aware design** — cost attribution built in from day one, not retrofitted; every resource is labelled and allocated at discovery time
- **Async stakeholder reporting** — Looker Studio showback dashboard is a shareable link; no live meetings or BigQuery access required for finance partners
- **Tested before shipped** — unit tests, GitHub Actions CI, 80%+ coverage gate on every commit

---

## Roadmap

- Organisation-wide multi-project scanning via folder-level Asset Inventory queries
- Cloud Billing export integration for actual spend data alongside estimated savings
- Committed Use Discount (CUD) and Savings Plan coverage analysis and recommendation engine
- Slack / PagerDuty anomaly alerts for spend spikes above configurable threshold
- Tagging policy enforcement via the enforcer service — auto-apply labels to untagged resources
- FOCUS specification export — multi-cloud billing normalisation for cross-cloud cost comparison

---

## Related Projects

- **[CloudGuard](https://github.com/wilfb-debug/cloudguard-gcp-governance)** — GCP security governance and compliance posture platform
- **[Identity-First Zero-Trust Network](https://github.com/wilfb-debug/gcp-identity-first-network-terraform)** — Zero public IP GCP network architecture with IAP and least-privilege IAM
