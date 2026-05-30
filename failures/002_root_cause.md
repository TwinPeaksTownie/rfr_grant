# Root Cause Analysis: Lambda Native Extension Mismatch

**Symptom:**
When executing a search from the frontend, the API returns `Error: Could not connect to AWS. API Error: 500`.

**Root Cause:**
AWS CloudWatch logs reveal the following crash:
`[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function': No module named 'pydantic_core._pydantic_core'`

**Technical Failure / Incorrect Assumption:**
I assumed that installing the `apify-client` pip package locally would work seamlessly in AWS Lambda. However, `apify-client` depends on `pydantic`, which relies on `pydantic_core`—a module containing compiled C-extensions (`.so` files). Because I ran `pip install` on your local macOS machine, pip downloaded the **macOS ARM64** binaries. When these were uploaded to the **Amazon Linux x86_64** Lambda environment, the Linux container could not execute the macOS binaries, causing an immediate crash.

**Resolution Plan:**
1. Uninstall the heavy `apify-client` and `pydantic` packages from the deployment directory.
2. Refactor `apify_search` in `run_pipeline.py` to use Python's built-in `urllib.request` to make a direct REST API call to Apify, completely bypassing the need for third-party libraries and native C-extensions.
3. Re-zip the deployment package and update the Lambda function code.
