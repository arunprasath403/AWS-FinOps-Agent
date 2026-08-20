# AWS FinOps & Infrastructure Intelligence Agent

> Autonomous multi-region AWS discovery, FinOps waste detection, security posture analysis, and architectural reasoning powered by Amazon Bedrock, Claude, Bedrock AgentCore, and Model Context Protocol (MCP).

![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Amazon Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-LLM-purple)
![AgentCore](https://img.shields.io/badge/Bedrock-AgentCore-red)
![MCP](https://img.shields.io/badge/Protocol-MCP-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Table of Contents

- [Overview](#overview)
- [Key Capabilities](#key-capabilities)
- [Architecture](#architecture)
- [Architecture Workflow](#architecture-workflow)
- [Official AWS FinOps Agent vs Custom Agent](#official-aws-finops-agent-vs-custom-agent)
- [Discovery Engine](#discovery-engine)
- [Multi-Region Discovery](#multi-region-discovery)
- [Context Compression Layer](#context-compression-layer)
- [FinOps Intelligence](#finops-intelligence)
- [Security Intelligence](#security-intelligence)
- [Architectural Intelligence](#architectural-intelligence)
- [Amazon Bedrock Intelligence Layer](#amazon-bedrock-intelligence-layer)
- [Model Context Protocol](#model-context-protocol)
- [MCP Client Integration](#mcp-client-integration)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [AWS Billing MCP Integration](#aws-billing-mcp-integration)
- [Services Scanned](#services-scanned)
- [IAM Permissions](#iam-permissions)
- [Security Model](#security-model)
- [Data Flow](#data-flow)
- [Cost Intelligence](#cost-intelligence)
- [Waste Detection](#waste-detection)
- [Output Schema](#output-schema)
- [Example Output](#example-output)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [AWS Configuration](#aws-configuration)
- [Running Locally](#running-locally)
- [Running with MCP](#running-with-mcp)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Multi-Account Extension](#multi-account-extension)
- [Observability](#observability)
- [Performance](#performance)
- [Security Best Practices](#security-best-practices)
- [Known Limitations](#known-limitations)
- [Future Enhancements](#future-enhancements)
- [Example Prompts](#example-prompts)
- [Use Cases](#use-cases)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

# Overview

The **AWS FinOps & Infrastructure Intelligence Agent** is an autonomous cloud intelligence engine designed to inspect AWS environments across multiple regions, identify infrastructure waste, analyze security posture, understand cloud architecture, and generate an enterprise-grade FinOps and infrastructure action plan.

The system combines:

- Amazon Bedrock
- Bedrock AgentCore
- Claude
- AWS Cost Explorer
- AWS resource APIs
- Concurrent multi-region discovery
- Deterministic context compression
- FinOps heuristics
- Security posture analysis
- Model Context Protocol (MCP)

Instead of sending thousands of raw AWS API records directly to an LLM, the system first performs deterministic discovery, aggregation, and compression.

The resulting compact infrastructure state is then passed to the intelligence layer for architectural reasoning.

---

# Key Capabilities

## Multi-Region AWS Discovery

Scans active AWS regions concurrently using Python's `ThreadPoolExecutor`.

## FinOps Waste Detection

Identifies potential sources of unnecessary cloud expenditure, including:

- Unattached EBS volumes
- Unassociated Elastic IPs
- NAT Gateway baseline costs
- Stopped EC2 instances
- Potentially idle infrastructure
- Legacy database engines
- High-cost AWS services

## AWS Cost Analysis

Integrates with AWS Cost Explorer to retrieve:

- 30-day historical spend
- Unblended cost
- Top AWS services by spend
- Cost forecasting

## Security Posture Analysis

Identifies infrastructure security signals such as:

- `0.0.0.0/0` SSH access
- `0.0.0.0/0` RDP access
- WAF deployment coverage
- IAM inventory
- Potentially exposed infrastructure
- Legacy RDS engines

## Architectural Intelligence

The LLM analyzes discovered infrastructure to identify:

- Architecture patterns
- Scalability concerns
- Security concerns
- Networking patterns
- Modernization opportunities
- Potential optimization opportunities

## Context Optimization

Raw AWS inventory is aggregated and compressed before being sent to the model.

This significantly reduces unnecessary context consumption.

## MCP Support

The agent can be exposed through MCP-compatible clients such as:

- Claude Desktop
- Cursor
- Amazon Q CLI
- Other MCP-compatible applications

---

# Architecture

The complete architecture is available in:

```text
architecture.png
