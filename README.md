# AWS FinOps & Infrastructure Intelligence Agent

An autonomous multi-region cloud discovery, FinOps governance, and architectural reasoning engine built on **Amazon Bedrock AgentCore Runtime**, **Anthropic Claude Sonnet**, and the **Model Context Protocol (MCP)**.

---

## Architecture Overview

The platform decouples live infrastructure state discovery from generative reasoning through a three-stage pipeline:

* **Discovery Orchestrator**: Executes concurrent multi-region API sweeps across 15+ AWS resource types alongside Cost Explorer trend extraction.
* **Deterministic Compression Engine**: Sanitizes, tallies, and condenses raw infrastructure state into a high-density, context-optimized schema.
* **AgentCore & MCP Gateway**: Evaluates aggregated telemetry via Claude Sonnet to generate an enterprise cloud audit spanning cost leakages, security boundaries, and modernization opportunities.

---

## Architectural Comparison

| Strategic Dimension | AWS Native Cost Optimization Hub | Custom AgentCore + MCP FinOps Platform |
| --- | --- | --- |
| **Telemetry Ingestion** | Asynchronous batch processing of billing logs (CUR, Cost Explorer, CloudWatch) | Real-time, synchronous multi-region discovery via parallel execution threads |
| **Waste Detection Latency** | 24 to 48 hour processing window for metric aggregation | Instant runtime detection for unattached storage, unassociated IPs, and idle gateways |
| **LLM Context Management** | Managed internal routing | Deterministic JSON compression preventing context window saturation and excess token spend |
| **Evaluation Scope** | Focused primarily on cost, instance sizing, and utilization metrics | Unified audit covering FinOps waste, exposure boundaries (0.0.0.0/0 on admin ports), and modernization vectors |
| **Interoperability Standard** | Proprietary AWS Management Console integrations | Open **Model Context Protocol (MCP)** standard compatible with Bedrock MCP Gateway, Claude Desktop, and developer IDEs |
| **Deployment Footprint** | AWS-managed SaaS control plane | Flexible deployment on **Bedrock AgentCore Runtime**, ECS/Fargate container, or secure local execution |
| **Operational Overhead** | Fixed service/tier pricing and potential licensing overhead | Zero SaaS markup; standard AWS API consumption and direct Bedrock foundation model token billing |

---

## Core Capabilities & Discovery Surface

* **Compute Topology**: EC2 operational states, Auto Scaling Group boundaries, Lambda deployments, and ECS/EKS container cluster footprints.
* **Network & Perimeter Security**: VPC routing, NAT Gateway base cost baselines, unassociated Elastic IPs, security group rule exposure (`0.0.0.0/0` on ports `22` and `3389`), and WAFv2 WebACL allocations.
* **Database & Persistence**: RDS instance engine distribution (differentiating legacy vs. open-source/serverless), DynamoDB tables, and S3 storage footprints.
* **Application Integration**: API Gateway endpoints, SQS queuing backlogs, SNS notification topographies, and EventBridge routing rules.
* **Financial Waste Attribution**: Automated cost run-rate calculations for unattached EBS storage volumes, unassociated Elastic IPs, and underutilized network transitions.

---

## Deployment & Runtime Configuration

### Bedrock AgentCore Runtime

The platform integrates natively with `bedrock-agentcore` to execute as a serverless agent runtime.

**Deployment Package Structure**

```text
agent-deployment-bundle/
├── main.py                     # AgentCore entrypoint and discovery engine
├── requirements.txt            # System dependencies
└── iam/
    └── execution_policy.json   # Least-privilege IAM policy

```

**Packaging & Deployment Steps**

1. Package the deployment bundle into an archive artifact:
```bash
zip -r finops-agentcore-runtime.zip main.py requirements.txt
aws s3 cp finops-agentcore-runtime.zip s3://<deployment-artifacts-bucket>/

```


2. Provision the agent inside the Amazon Bedrock console or via AWS CLI targeting the `anthropic.claude-sonnet-4-6` foundation model.

---

## Bedrock MCP Gateway & Client Integration

The platform functions as a standardized Model Context Protocol (MCP) server, allowing autonomous agent workflows, enterprise LLM platforms, and developer tooling to query cloud telemetry on demand.

### Bedrock AgentCore Gateway Target Definition

Register the FinOps agent as an active MCP endpoint in your Bedrock AgentCore Gateway:

```json
{
  "TargetName": "AWSFinOpsDiscoveryGateway",
  "TargetType": "MCP_SERVER",
  "Configuration": {
    "McpServer": {
      "Endpoint": "https://<agentcore-runtime-endpoint>/mcp",
      "ProtocolVersion": "2024-11-05",
      "Capabilities": ["tools", "resources"]
    }
  },
  "Authentication": {
    "Type": "IAM",
    "ExecutionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/BedrockAgentCoreGatewayRole"
  }
}

```

### Desktop & IDE MCP Configuration

To interface with the agent directly from **Claude Desktop** or **Cursor**, add the runtime specification to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aws-finops-agent": {
      "command": "python",
      "args": ["/path/to/AWS_FinOps_Agent/main.py"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "default"
      }
    }
  }
}

```

---

## Security & Least-Privilege IAM Governance

The agent operates strictly in an inspection capacity. Deploy the execution role with read-only administrative visibility across target discovery resources:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostExplorerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    },
    {
      "Sid": "InfrastructureDiscoveryReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "rds:DescribeDBInstances",
        "elasticloadbalancing:DescribeLoadBalancers",
        "lambda:ListFunctions",
        "dynamodb:ListTables",
        "ecr:DescribeRepositories",
        "apigateway:GET",
        "ecs:ListClusters",
        "eks:ListClusters",
        "autoscaling:DescribeAutoScalingGroups",
        "secretsmanager:ListSecrets",
        "wafv2:ListWebACLs",
        "sqs:ListQueues",
        "sns:ListTopics",
        "events:ListRules",
        "s3:ListAllMyBuckets",
        "iam:ListUsers",
        "iam:ListRoles",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BedrockInferenceAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6"
    }
  ]
}

```

---

## Quickstart

### 1. Environment Setup

```bash
git clone https://github.com/arunprasath403/AWS-FinOps-Agent.git
cd AWS-FinOps-Agent

python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

```

### 2. Operational Execution

```bash
# Configure region and profile
export AWS_REGION="us-east-1"

# Trigger discovery and analysis engine
python main.py

```

---

## Enterprise Output Contract

The discovery runtime produces a deterministic JSON schema containing telemetry metadata, compressed infrastructure metrics, and the synthesized executive briefing:

```json
{
  "sessionId": "e2f18374-7d9a-4c20-a612-9c1234567890",
  "result": {
    "scan_timestamp": "2026-08-20T12:00:00Z",
    "compressed_inventory": {
      "active_regions_count": 16,
      "aggregated_resources": {
        "compute": { "ec2_total": 42, "ec2_running": 31, "lambda": 128 },
        "network_security": { "nat_gateways": 6, "critical_open_sgs": 2 },
        "finops_waste": { "unattached_ebs": 14, "unused_eips": 5 },
        "estimated_monthly_savings": 90.00
      }
    },
    "architectural_report": "1. Executive Summary\n2. Critical Security Findings\n3. Cost Optimization & Estimated Savings\n4. Scalability & Reliability Status\n5. Modernization Recommendations"
  }
}

```

---

## License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).
