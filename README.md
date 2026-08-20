# AWS FinOps & Infrastructure Intelligence Agent

An autonomous, multi-region cloud discovery, FinOps governance, and architectural reasoning engine built on **Amazon Bedrock AgentCore Runtime**, **Anthropic Claude Sonnet**, and the **Model Contex[...]

---

## Architectural Topology

The platform decouples live infrastructure state discovery from generative reasoning through a three-stage orchestrated pipeline:

![AWS FinOps Architecture](./FinOps_architecture.png)

* **Discovery Orchestrator**: Executes concurrent multi-region API sweeps across 15+ AWS resource types alongside Cost Explorer trend and forecast extraction.
* **Deterministic Compression Engine**: Sanitizes, tallies, and condenses raw multi-region infrastructure state into a high-density, context-optimized schema that prevents LLM context window satur[...]
* **AgentCore & MCP Gateway**: Evaluates aggregated telemetry via Claude Sonnet to generate an enterprise cloud audit spanning cost leakages, security boundaries, and modernization opportunities.

---

## Architectural Comparison: AWS Native FinOps vs. Custom AgentCore & MCP Engine

| Dimension | AWS Native Cost Optimization Hub / FinOps | Custom Bedrock AgentCore + MCP FinOps Platform |
| --- | --- | --- |
| **Telemetry Ingestion Model** | Asynchronous batch processing of billing records, CUR reports, and CloudWatch metrics. | Real-time, synchronous multi-region discovery via parallel worker threads[...] |
| **Waste Detection Latency** | 24 to 48 hour processing window for metric aggregation and recommendation engine runs. | Instant runtime detection for unattached EBS storage, idle EIPs, and unasso[...] |
| **LLM Context Optimization** | Opaque managed internal prompt routing. | Deterministic JSON compression minimizing token consumption and eliminating context window overflow. |
| **Evaluation Scope** | Focused primarily on cost, instance sizing, and utilization metrics. | Unified audit covering FinOps waste, perimeter security (`0.0.0.0/0` admin ports), and modernization[...] |
| **Interoperability Standard** | Proprietary AWS Management Console integrations. | Open **Model Context Protocol (MCP)** standard compatible with Bedrock MCP Gateway, Claude Desktop, and develop[...] |
| **Deployment Footprint** | AWS-managed SaaS control plane. | Serverless **Bedrock AgentCore Runtime**, ECS/Fargate container, or secure local execution. |
| **Operational Overhead** | Fixed service/tier pricing and potential Compute Optimizer licensing overhead. | Direct Bedrock Converse token consumption + standard AWS read-only API calls with zero[...] |

---

## Comprehensive Discovery & Governance Surface

The discovery layer performs deep inspection across regional and global AWS services:

### 1. Compute & Containers

* **Amazon EC2**: Audits total instances, active running vs. stopped workloads, and instance distributions across all available regions.
* **Auto Scaling Groups (ASG)**: Identifies active fleet configurations and scale boundaries.
* **AWS Lambda**: Aggregates serverless functions to evaluate serverless adoption and event-driven patterns.
* **Amazon ECS & Amazon EKS**: Maps container clusters across regions to gauge containerization density.

### 2. Networking, Edge & Perimeter Security

* **VPC & Routing**: Inventories VPC boundaries, route tables, and subnet configurations.
* **NAT Gateways**: Calculates base run-rate cost projections ($32.40/month baseline per NAT Gateway) before data transfer.
* **Elastic IP Addresses**: Discovers unassociated and idle EIPs incurring hourly idle charges.
* **Security Groups**: Identifies range-aware ingress exposures permitting unrestricted access (`0.0.0.0/0`) on administrative ports `22` (SSH) and `3389` (RDP).
* **AWS WAFv2**: Verifies regional and CloudFront WebACL coverage across edge deployments.
* **Elastic Load Balancing (ELBv2)**: Catalogs Application and Network Load Balancers.

### 3. Databases, Storage & Identity

* **Amazon RDS**: Inspects database instances and breaks down database engines to identify legacy vs. modern open-source engines (e.g., PostgreSQL, MySQL, Aurora).
* **Amazon DynamoDB**: Catalogs NoSQL tables across all regions.
* **Amazon S3**: Inventories global object storage buckets.
* **Amazon ECR**: Tracks container image repositories.
* **AWS IAM & Secrets Manager**: Catalogs IAM users, IAM roles, and encrypted secrets footprints.

### 4. Integration & Messaging

* **Amazon API Gateway**: Inventories REST API infrastructure.
* **Amazon SQS & Amazon SNS**: Catalogs message queues and notification topics.
* **Amazon EventBridge**: Audits active event bus routing rules.

### 5. Cost Explorer Intelligence

* **Historical Lookback**: Extracts 30-day unblended cost metrics grouped by AWS service.
* **Top Spenders**: Ranks top 10 contributing services by total cost.
* **Predictive Forecasting**: Projects next 30-day billing volume using AWS Cost Explorer predictive models.

---

## Amazon Bedrock AgentCore Runtime Configuration

The agent natively implements the `bedrock-agentcore` SDK, supporting serverless invocation and containerized deployments.

### AgentCore Runtime Entrypoint (`main.py`)

```python
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    session_id = payload.get("sessionId", str(uuid.uuid4()))
    return {"sessionId": session_id, "result": run_full_cloud_analysis()}

if __name__ == "__main__":
    app.run()

```

### Packaging for Bedrock AgentCore

1. Archive the core engine and its dependency manifest:
```bash
zip -r finops-agentcore-runtime.zip main.py requirements.txt
aws s3 cp finops-agentcore-runtime.zip s3://<deployment-artifacts-bucket>/

```


2. Set runtime environment variables:
* `AWS_REGION`: Primary AWS region for Bedrock inference (default: `us-east-1`).
* `BEDROCK_AGENTCORE_TIMEOUT`: `900` (accommodates high-concurrency multi-region discovery).



---

## Bedrock MCP Gateway & Client Configuration

The platform functions as a standardized Model Context Protocol (MCP) tool server, allowing autonomous agent workflows, enterprise LLM platforms, and developer tooling to query live cloud telemet[...]

### 1. Bedrock AgentCore Gateway Target Definition

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

### 2. Desktop & IDE MCP Configuration

To interface with the agent directly from **Claude Desktop** or **Cursor**, add the runtime specification to your client's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aws-finops-agent": {
      "command": "python",
      "args": ["D:\\AWS_agent_template\\AWS_FinOps_Agent\\main.py"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "default"
      }
    },
    "aws-cost-mcp-gateway": {
      "command": "npx",
      "args": ["-y", "@aws-mcp/cost-management-gateway"],
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  }
}

```

---

## Security & Least-Privilege IAM Policy

The agent executes with read-only visibility. Attach this policy to the execution role running the discovery engine:

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

## Installation & Local Execution

### 1. Environment Setup

```bash
git clone https://github.com/arunprasath403/AWS-FinOps-Agent.git
cd AWS-FinOps-Agent

python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

```

### 2. Operational Execution

```bash
# Configure region
export AWS_REGION="us-east-1"

# Run discovery and analysis agent
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
        "compute": {
          "ec2_total": 42,
          "ec2_running": 31,
          "lambda": 128,
          "ecs_clusters": 2,
          "eks_clusters": 1,
          "asg_groups": 4
        },
        "network_security": {
          "vpcs": 4,
          "nat_gateways": 6,
          "critical_open_sgs": 2,
          "elbs": 5,
          "waf_regional_acls": 2,
          "waf_cloudfront_acls": 1
        },
        "databases": {
          "rds": 6,
          "rds_engines": { "postgres": 4, "mysql": 2 },
          "dynamodb": 12
        },
        "finops_waste": {
          "unattached_ebs": 14,
          "unused_eips": 5
        },
        "estimated_monthly_savings": 90.00
      }
    },
    "architectural_report": "1. Executive Summary\n2. Critical Security Findings\n3. Cost Optimization & Estimated Savings\n4. Scalability & Reliability Status\n5. Modernization Recommendations"
  }
}

```

---

## License

Distributed under the [MIT License](https://www.google.com/search?q=LICENSE).
