import os
import uuid
import boto3
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from botocore.config import Config
from bedrock_agentcore import BedrockAgentCoreApp

# =====================================================
# 1. AgentCore App
# =====================================================
app = BedrockAgentCoreApp()

# =====================================================
# 2. Environment Variables & Constants
# =====================================================
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "global.anthropic.claude-sonnet-4-6"

# FinOps Dates
TODAY = datetime.utcnow().date()
START_DATE = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")
FORECAST_START = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")
FORECAST_END = (TODAY + timedelta(days=31)).strftime("%Y-%m-%d")

# =====================================================
# 3. AWS Client Setup
# =====================================================
bedrock_config = Config(
    read_timeout=900, 
    connect_timeout=900,
    retries={"max_attempts": 3}
)

session = boto3.Session()
bedrock_runtime = session.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    config=bedrock_config
)

# =====================================================
# 4. Helpers 
# =====================================================
def get_all_regions():
    try:
        ec2 = session.client("ec2", region_name="us-east-1")
        return [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
    except Exception as e:
        print(f"Error fetching regions: {e}")
        return ["us-east-1"]

# =====================================================
# 5. Regional Scanners
# =====================================================
def scan_regional_infrastructure(region):
    print(f"Scanning region: {region}...")
    
    inventory = {
        "region": region,
        "ec2": {}, "vpc_security": {}, "rds": {}, "elb": {}, 
        "lambda": {}, "dynamodb": {}, "ecr": {}, "apigateway": {},
        "ecs": {}, "eks": {}, "autoscaling": {}, "secretsmanager": {},
        "wafv2": {"cloudfront_acls": 0, "regional_acls": 0}, 
        "sqs": {}, "sns": {}, "eventbridge": {}
    }

    try:
        # --- EC2 & SECURITY ---
        ec2 = session.client("ec2", region_name=region)
        
        total_instances, running, stopped = 0, 0, 0
        for page in ec2.get_paginator("describe_instances").paginate():
            for res in page.get("Reservations", []):
                for inst in res.get("Instances", []):
                    total_instances += 1
                    state = inst.get("State", {}).get("Name")
                    if state == "running": running += 1
                    if state == "stopped": stopped += 1
        
        # Unattached EBS Volumes (FinOps)
        unattached_ebs = 0
        for page in ec2.get_paginator("describe_volumes").paginate():
            for vol in page.get("Volumes", []):
                if not vol.get("Attachments"):
                    unattached_ebs += 1

        inventory["ec2"] = {
            "total": total_instances,
            "running": running,
            "stopped": stopped,
            "unattached_ebs": unattached_ebs
        }

        # Security Groups Analysis (Range-aware 0.0.0.0/0 on 22/3389)
        open_admin_ports = 0
        sgs = ec2.describe_security_groups().get("SecurityGroups", [])
        for sg in sgs:
            for perm in sg.get("IpPermissions", []):
                from_port = perm.get("FromPort")
                to_port = perm.get("ToPort")
                
                if (from_port is not None and to_port is not None and 
                    ((22 >= from_port and 22 <= to_port) or 
                     (3389 >= from_port and 3389 <= to_port))):
                    
                    for ip_range in perm.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            open_admin_ports += 1

        # Unused Elastic IPs (FinOps)
        unused_eips = 0
        for address in ec2.describe_addresses().get("Addresses", []):
            if "InstanceId" not in address and "NetworkInterfaceId" not in address:
                unused_eips += 1

        nat_count = len(ec2.describe_nat_gateways().get("NatGateways", []))
        
        inventory["vpc_security"] = {
            "vpcs": len(ec2.describe_vpcs().get("Vpcs", [])),
            "security_groups": len(sgs),
            "critical_open_sgs": open_admin_ports,
            "elastic_ips": len(ec2.describe_addresses().get("Addresses", [])),
            "unused_eips": unused_eips,
            "nat_gateways": nat_count,
            "est_monthly_nat_base_cost": round(nat_count * 32.40, 2),  # Reflects base cost only, minus data transfer
            "route_tables": len(ec2.describe_route_tables().get("RouteTables", []))
        }

        # --- ELB ---
        elbv2 = session.client("elbv2", region_name=region)
        inventory["elb"]["total"] = sum(len(p.get("LoadBalancers", [])) for p in elbv2.get_paginator("describe_load_balancers").paginate())

        # --- RDS ---
        rds = session.client("rds", region_name=region)
        rds_total = 0
        engine_breakdown = {}
        for page in rds.get_paginator("describe_db_instances").paginate():
            instances = page.get("DBInstances", [])
            rds_total += len(instances)
            for db in instances:
                engine = db.get("Engine", "unknown")
                engine_breakdown[engine] = engine_breakdown.get(engine, 0) + 1
                
        inventory["rds"] = {
            "total": rds_total,
            "engines": engine_breakdown
        }

        # --- LAMBDA ---
        lmbda = session.client("lambda", region_name=region)
        inventory["lambda"]["total"] = sum(len(p.get("Functions", [])) for p in lmbda.get_paginator("list_functions").paginate())

        # --- DYNAMODB ---
        ddb = session.client("dynamodb", region_name=region)
        inventory["dynamodb"]["total"] = sum(len(p.get("TableNames", [])) for p in ddb.get_paginator("list_tables").paginate())

        # --- ECR ---
        ecr = session.client("ecr", region_name=region)
        inventory["ecr"]["total"] = sum(len(p.get("repositories", [])) for p in ecr.get_paginator("describe_repositories").paginate())

        # --- API GATEWAY ---
        apigw = session.client("apigateway", region_name=region)
        inventory["apigateway"]["total"] = sum(len(p.get("items", [])) for p in apigw.get_paginator("get_rest_apis").paginate())

        # --- ECS ---
        ecs = session.client("ecs", region_name=region)
        inventory["ecs"]["clusters"] = sum(len(p.get("clusterArns", [])) for p in ecs.get_paginator("list_clusters").paginate())

        # --- EKS ---
        eks = session.client("eks", region_name=region)
        inventory["eks"]["clusters"] = sum(len(p.get("clusters", [])) for p in eks.get_paginator("list_clusters").paginate())

        # --- AUTOSCALING ---
        asg = session.client("autoscaling", region_name=region)
        inventory["autoscaling"]["groups"] = sum(len(p.get("AutoScalingGroups", [])) for p in asg.get_paginator("describe_auto_scaling_groups").paginate())

        # --- SECRETS MANAGER ---
        sm = session.client("secretsmanager", region_name=region)
        inventory["secretsmanager"]["secrets"] = sum(len(p.get("SecretList", [])) for p in sm.get_paginator("list_secrets").paginate())

        # --- WAFv2 ---
        waf = session.client("wafv2", region_name=region)
        inventory["wafv2"]["regional_acls"] = len(waf.list_web_acls(Scope="REGIONAL").get("WebACLs", []))
        
        if region == "us-east-1":
            inventory["wafv2"]["cloudfront_acls"] = len(waf.list_web_acls(Scope="CLOUDFRONT").get("WebACLs", []))

        # --- SQS ---
        sqs = session.client("sqs", region_name=region)
        inventory["sqs"]["queues"] = len(sqs.list_queues().get("QueueUrls", []))

        # --- SNS ---
        sns = session.client("sns", region_name=region)
        inventory["sns"]["topics"] = sum(len(p.get("Topics", [])) for p in sns.get_paginator("list_topics").paginate())

        # --- EVENTBRIDGE ---
        events = session.client("events", region_name=region)
        inventory["eventbridge"]["rules"] = sum(len(p.get("Rules", [])) for p in events.get_paginator("list_rules").paginate())

    except Exception as e:
        inventory["regional_error"] = str(e)

    # Return raw regional inventory; let compression handle empty attributes
    return inventory

# =====================================================
# 6. Global Scanners & Forecasts
# =====================================================
def scan_global_infrastructure():
    print("Scanning global services and FinOps data...")
    inventory = {"s3": {}, "iam": {}, "cloudfront": {}, "finops": {}}
    
    try:
        # S3
        s3 = session.client("s3")
        inventory["s3"]["total_buckets"] = len(s3.list_buckets().get("Buckets", []))

        # IAM
        iam = session.client("iam")
        inventory["iam"]["users"] = sum(len(p.get("Users", [])) for p in iam.get_paginator("list_users").paginate())
        inventory["iam"]["roles"] = sum(len(p.get("Roles", [])) for p in iam.get_paginator("list_roles").paginate())

        # CloudFront
        cf = session.client("cloudfront")
        inventory["cloudfront"]["total"] = sum(len(p.get("DistributionList", {}).get("Items", [])) for p in cf.get_paginator("list_distributions").paginate())

        # FinOps (Cost & Usage)
        ce = session.client("ce", region_name="us-east-1")
        cost_res = ce.get_cost_and_usage(
            TimePeriod={"Start": START_DATE, "End": END_DATE},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )
        
        total_cost = 0.0
        top_services = []
        results_by_time = cost_res.get("ResultsByTime", [])
        
        # Safely extract Cost Explorer groupings
        if results_by_time and "Groups" in results_by_time[0]:
            for group in results_by_time[0].get("Groups", []):
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                total_cost += cost
                top_services.append({"service": group["Keys"][0], "cost": round(cost, 2)})
            
        inventory["finops"]["total_30_day_cost"] = round(total_cost, 2)
        inventory["finops"]["top_services"] = sorted(top_services, key=lambda x: x["cost"], reverse=True)[:10]

        # Forecast
        try:
            forecast = ce.get_cost_forecast(
                TimePeriod={"Start": FORECAST_START, "End": FORECAST_END},
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY"
            )
            inventory["finops"]["30_day_forecast"] = round(float(forecast.get("Total", {}).get("Amount", 0)), 2)
        except Exception as fe:
            inventory["finops"]["forecast_error"] = str(fe)

    except Exception as e:
        inventory["global_error"] = str(e)

    return inventory

# =====================================================
# 7. Compression Layer
# =====================================================
def compress_inventory(raw_inventory):
    summary = {
        "metadata": raw_inventory["scan_metadata"],
        "active_regions_count": len(raw_inventory["regional_findings"]),
        "global_infrastructure": raw_inventory["global_findings"],
        "aggregated_resources": {
            "compute": {"ec2_total": 0, "ec2_running": 0, "lambda": 0, "ecs_clusters": 0, "eks_clusters": 0, "asg_groups": 0},
            "network_security": {"vpcs": 0, "elbs": 0, "nat_gateways": 0, "critical_open_sgs": 0, "waf_regional_acls": 0, "waf_cloudfront_acls": 0},
            "databases": {"rds": 0, "rds_engines": {}, "dynamodb": 0},
            "integration": {"apigateway": 0, "sqs": 0, "sns": 0, "eventbridge": 0},
            "finops_waste": {"unattached_ebs": 0, "unused_eips": 0},
            "estimated_monthly_savings": 0,
            "misc": {"ecr_repos": 0, "secrets": 0}
        },
        "notable_regional_spikes": [] 
    }

    # Aggregate regional findings
    for region_data in raw_inventory.get("regional_findings", []):
        reg = region_data.get("region", "unknown")
        
        # Tally Compute
        summary["aggregated_resources"]["compute"]["ec2_total"] += region_data.get("ec2", {}).get("total", 0)
        summary["aggregated_resources"]["compute"]["ec2_running"] += region_data.get("ec2", {}).get("running", 0)
        summary["aggregated_resources"]["compute"]["lambda"] += region_data.get("lambda", {}).get("total", 0)
        summary["aggregated_resources"]["compute"]["ecs_clusters"] += region_data.get("ecs", {}).get("clusters", 0)
        summary["aggregated_resources"]["compute"]["eks_clusters"] += region_data.get("eks", {}).get("clusters", 0)
        summary["aggregated_resources"]["compute"]["asg_groups"] += region_data.get("autoscaling", {}).get("groups", 0)

        # Tally Network/Sec
        summary["aggregated_resources"]["network_security"]["vpcs"] += region_data.get("vpc_security", {}).get("vpcs", 0)
        summary["aggregated_resources"]["network_security"]["nat_gateways"] += region_data.get("vpc_security", {}).get("nat_gateways", 0)
        summary["aggregated_resources"]["network_security"]["critical_open_sgs"] += region_data.get("vpc_security", {}).get("critical_open_sgs", 0)
        summary["aggregated_resources"]["network_security"]["elbs"] += region_data.get("elb", {}).get("total", 0)
        summary["aggregated_resources"]["network_security"]["waf_regional_acls"] += region_data.get("wafv2", {}).get("regional_acls", 0)
        summary["aggregated_resources"]["network_security"]["waf_cloudfront_acls"] += region_data.get("wafv2", {}).get("cloudfront_acls", 0)

        # Tally DBs
        summary["aggregated_resources"]["databases"]["rds"] += region_data.get("rds", {}).get("total", 0)
        for engine, count in region_data.get("rds", {}).get("engines", {}).items():
            summary["aggregated_resources"]["databases"]["rds_engines"][engine] = summary["aggregated_resources"]["databases"]["rds_engines"].get(engine, 0) + count
        summary["aggregated_resources"]["databases"]["dynamodb"] += region_data.get("dynamodb", {}).get("total", 0)

        # Tally Integration
        summary["aggregated_resources"]["integration"]["apigateway"] += region_data.get("apigateway", {}).get("total", 0)
        summary["aggregated_resources"]["integration"]["sqs"] += region_data.get("sqs", {}).get("queues", 0)
        summary["aggregated_resources"]["integration"]["sns"] += region_data.get("sns", {}).get("topics", 0)
        summary["aggregated_resources"]["integration"]["eventbridge"] += region_data.get("eventbridge", {}).get("rules", 0)

        # Tally FinOps Waste & Savings Calculation
        unattached_ebs = region_data.get("ec2", {}).get("unattached_ebs", 0)
        unused_eips = region_data.get("vpc_security", {}).get("unused_eips", 0)
        
        summary["aggregated_resources"]["finops_waste"]["unattached_ebs"] += unattached_ebs
        summary["aggregated_resources"]["finops_waste"]["unused_eips"] += unused_eips
        summary["aggregated_resources"]["estimated_monthly_savings"] += (unattached_ebs * 5) + (unused_eips * 4)

        # Tally Misc
        summary["aggregated_resources"]["misc"]["ecr_repos"] += region_data.get("ecr", {}).get("total", 0)
        summary["aggregated_resources"]["misc"]["secrets"] += region_data.get("secretsmanager", {}).get("secrets", 0)

        # Note heavy regions to give Claude geographic context
        if region_data.get("ec2", {}).get("total", 0) > 10 or region_data.get("lambda", {}).get("total", 0) > 20:
            summary["notable_regional_spikes"].append({
                "region": reg,
                "ec2": region_data.get("ec2", {}).get("total", 0),
                "lambda": region_data.get("lambda", {}).get("total", 0)
            })

    return summary

# =====================================================
# 8. Orchestrator 
# =====================================================
def run_discovery_orchestrator():
    inventory = {
        "scan_metadata": {
            "timestamp": str(datetime.utcnow()),
            "cost_period": f"{START_DATE} to {END_DATE}"
        },
        "regions_scanned": [],
        "regional_findings": [],
        "global_findings": {}
    }

    regions = get_all_regions()
    inventory["regions_scanned"] = regions

    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_region = {
            executor.submit(scan_regional_infrastructure, region): region
            for region in regions
        }

        for future in as_completed(future_to_region):
            region = future_to_region[future]
            try:
                result = future.result()
                if result:
                    inventory["regional_findings"].append(result)
            except Exception as e:
                print(f"Region scan failed for {region}: {e}")

    inventory["global_findings"] = scan_global_infrastructure()

    return inventory

# =====================================================
# 9. Intelligence Agent
# =====================================================
INTELLIGENCE_AGENT_PROMPT = """
You are a Senior Enterprise Cloud Architect.

CRITICAL RULES:
- Use ONLY the provided compressed infrastructure summary.
- Do NOT narrate your process or explain steps.
- Produce a highly structured final enterprise analysis immediately.

Analyze:
- FinOps (Review historical costs, forecasts, NAT base costs, unused EIPs, unattached EBS volumes, and the estimated monthly savings).
- Scalability (Review AutoScaling, ELBs, ECS/EKS vs EC2 usage).
- Security (Call out Critical Open SGs, WAF usage, Secrets Manager).
- Modernization (Identify event-driven/serverless footprints, and potential RDS engine modernization paths based on legacy vs. open-source usage).

Return ONLY:
1. Executive Summary
2. Critical Security Findings
3. Cost Optimization & Estimated Savings
4. Scalability & Reliability Status
5. Modernization Recommendations
"""

def run_intelligence_agent(compressed_inventory):
    user_prompt = f"Analyze the following AWS infrastructure summary:\n\n{json.dumps(compressed_inventory, indent=2)}"
    
    messages = [{"role": "user", "content": [{"text": user_prompt}]}]
    system = [{"text": INTELLIGENCE_AGENT_PROMPT}]
    
    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system
        )
        return response["output"]["message"]["content"][0]["text"]
        
    except Exception as e:
        return f"Error generating intelligence report: {str(e)}"

# =====================================================
# 10. Full Workflow
# =====================================================
def run_full_cloud_analysis():
    print("\n================================")
    print("DISCOVERY ORCHESTRATOR STARTED")
    print("================================")
    
    raw_inventory = run_discovery_orchestrator()
    compressed_inventory = compress_inventory(raw_inventory)

    print("\n================================")
    print("DISCOVERY ORCHESTRATOR COMPLETED")
    print("================================")
    
    print("\n================================")
    print("INTELLIGENCE AGENT STARTED")
    print("================================")
    
    report = run_intelligence_agent(compressed_inventory)

    print("\n================================")
    print("INTELLIGENCE AGENT COMPLETED")
    print("================================")

    return {
        "scan_timestamp": str(datetime.utcnow()),
        "compressed_inventory": compressed_inventory,  
        "architectural_report": report
    }

# =====================================================
# 11. AgentCore Entrypoint
# =====================================================
@app.entrypoint
def invoke(payload):
    session_id = payload.get("sessionId", str(uuid.uuid4()))
    print(f"\nNEW CLOUD ANALYSIS REQUEST | Session: {session_id}")
    return {"sessionId": session_id, "result": run_full_cloud_analysis()}

# =====================================================
# 12. Local Runtime
# =====================================================
if __name__ == "__main__":
    app.run()