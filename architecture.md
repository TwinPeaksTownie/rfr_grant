# System Architecture: AWS Agent Loop

```mermaid
flowchart TD
    subgraph USER_START [User]
        Start["Send POST Request with Goal"]
    end

    subgraph AWS [AWS Cloud]
        Gateway["API Gateway"]
        Lambda["AWS Lambda (Python Loop)"]
        Bedrock["AWS Bedrock (Reasoning)"]
    end

    subgraph APIFY [Apify]
        Scraper["Web Scraper"]
    end

    subgraph BOX [Box Cloud]
        Storage["Box Storage (Vault)"]
        BoxAI["Box AI (Extraction & Drafting)"]
    end

    subgraph USER_END [User]
        Review["Review Final Drafts"]
    end

    Start -->|"Trigger"| Gateway
    Gateway -->|"Payload"| Lambda
    
    Lambda -->|"1. What next?"| Bedrock
    Bedrock -->|"Decision: Expand Query & Scrape"| Lambda
    
    Lambda -->|"2. Run Search"| Scraper
    Scraper -->|"Raw HTML or Directory Links"| Lambda
    Lambda -->|"3. Save HTML"| Storage
    
    Lambda -->|"4. What next?"| Bedrock
    
    %% Aggregator Mining Loop
    Bedrock -->|"Decision: Found Aggregator"| Lambda
    Lambda -.->|"Mine Sub-Links"| Scraper
    
    %% Primary Extraction Loop
    Bedrock -->|"Decision: Extract Data"| Lambda
    Lambda -->|"5. Parse Single Grant"| BoxAI
    BoxAI -->|"JSON Data"| Lambda
    Lambda -->|"6. Save JSON"| Storage
    
    Lambda -->|"7. What next?"| Bedrock
    Bedrock -->|"Decision: Draft Email"| Lambda
    
    Lambda -->|"8. Write Draft"| BoxAI
    BoxAI -->|"Email Text"| Lambda
    Lambda -->|"9. Save Draft"| Storage
    
    Lambda -->|"10. Goal Met?"| Bedrock
    Bedrock -->|"No, keep searching"| Lambda
    Lambda -.->|"Loop Back"| Bedrock
    
    Bedrock -->|"Yes, Stop"| Lambda
    
    Storage -.->|"View Files securely"| Review
```
