# Reach Forward Robotics — Autonomous Agent

This repository contains the backend codebase for the Reach Forward Robotics **Autonomous Grant & Sponsorship Agent**.

## Overview
Reach Forward Robotics is a student-led initiative building open-source robotics curriculum. This agent accelerates our fundraising and hardware procurement by autonomously scouring the web, analyzing opportunities, and drafting highly tailored outreach emails.

Unlike a rigid pipeline, this system uses an **LLM Orchestrator** (Amazon Bedrock / Nova Pro) that dynamically determines how to fulfill a user's natural language goal.

## Hackathon Demonstration
<video src="https://github.com/TwinPeaksTownie/rfr_grant/raw/main/assets/hackathon_video.mov" controls="controls" muted="muted" style="max-width:100%; max-height:640px;"></video>

## Architecture & Tech Stack
- **Frontend (HuggingFace Spaces)**: A lightweight UI where users submit natural language goals (e.g., *"Find me a Jetson Thor and some motors"*).
- **Agent Orchestrator (AWS Bedrock & AWS Lambda)**: The brain of the operation. It interprets the goal, decides which tools to call, and orchestrates the entire workflow asynchronously to bypass API Gateway timeouts.
- **Web Scraper Tool (Apify)**: Scours live Google search results to find relevant grants, corporate product pages, or supplier directories.
- **Data Extractor & Classifier Tool (Box AI)**: Reads the raw HTML of scraped websites, extracts specific eligibility requirements, and classifies them as either `single-grant`, `potential-sponsor`, `aggregator`, or `not-fundable`.
- **Drafter Tool (Box AI)**: Uses our verified organizational profile (`Reach_Forward_Profile.txt`) to write highly personalized, factual outreach emails requesting cash grants or in-kind hardware donations.
- **Storage (Box)**: All raw scrapes, extracted JSON dossiers, and final drafted emails are persisted securely in Box.

## Capabilities
1. **Dynamic Web Search**: It performs live, synchronous web scraping using Apify to find the most up-to-date opportunities.
2. **Hardware Sponsorships**: It doesn't just find cash grants. If you ask for specific hardware (like a Jetson Thor), it will locate the manufacturer's corporate page and draft an in-kind donation request!
3. **Factual Drafting**: The agent is strictly instructed to **never invent statistics or outcomes**. It uses a verified organizational profile to ground all of its claims in reality.
4. **Asynchronous Processing**: The agent forks itself into a background AWS Lambda worker to process heavy, long-running web scraping tasks without hitting frontend timeouts.

## Getting Started
The agent runs serverlessly via an AWS API Gateway endpoint that triggers the `reach_forward_agent` Lambda function.

To deploy backend changes manually:
```bash
python3 deploy_aws.py
```
*(Ensure your AWS credentials are authenticated in your terminal environment).*

## Where to find the output
When the agent successfully completes a task, the resulting drafted emails are automatically uploaded to your **Box Account** inside the `03_drafts` folder.
