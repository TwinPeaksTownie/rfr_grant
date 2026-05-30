# Root Cause Analysis: Hardcoded Apify Search

**Symptom:**
User queried for a "Jetson Thor" grant, but the agent did not find a new foundation or draft a new email. Instead, it returned data related to the WRF STEM grant.

**Root Cause:**
In `run_pipeline.py`, the `apify_search()` tool function was never re-wired to use the actual Apify API. It is hardcoded to loop over `mock_apify_data` loaded from `apify_test_raw.json` (which contains the WRF grant) regardless of the `query` string passed to the tool.

**Technical Failure / Incorrect Assumption:**
I assumed the mock data was sufficient for testing the orchestrator loop, but I failed to follow through on the final step of replacing the stub with the live `apify_client`. Furthermore, I never requested the user's Apify API token when they bypassed the `.env` file creation.

**Resolution Plan:**
1. Request the Apify API token from the user.
2. Push the Apify token into AWS Systems Manager (SSM) Parameter Store for secure Lambda access.
3. Refactor `apify_search` in `run_pipeline.py` to use `apify-client` and execute live web searches via Apify Google Search Scraper.
4. Repackage and redeploy the Lambda function.
