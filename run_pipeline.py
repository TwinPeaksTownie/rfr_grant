import json, os, re
import boto3
import box_client as bc
import prompts

# Environment setup for AWS Bedrock
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
MODEL_ID = "amazon.nova-pro-v1:0"

# Load local data
folders = json.load(open("box_folders.json"))
profile_id = json.load(open("box_profile.json"))["profile_file_id"]

import urllib.request
import json
from bs4 import BeautifulSoup
import markdownify

search_database = {} # Maps ID to full item

def get_apify_token():
    try:
        ssm = boto3.client('ssm', region_name=AWS_REGION)
        return ssm.get_parameter(Name='/reachforward/apify_token', WithDecryption=True)['Parameter']['Value']
    except Exception as e:
        print("SSM Apify token fetch failed:", e)
        return ""

def slug(s): return re.sub(r"[^A-Za-z0-9]+","_",s)[:60].strip("_")

def parse_json(s):
    s = re.sub(r"^```(json)?|```$","",s.strip(),flags=re.MULTILINE).strip()
    i = s.find("{")
    if i < 0: return {}
    try:
        obj,_ = json.JSONDecoder().raw_decode(s[i:]); return obj
    except Exception: return {"_parse_error": s[:200]}

# --- TOOL FUNCTIONS FOR BEDROCK ---

def apify_search(query):
    """Uses Apify REST API to search Google."""
    print(f"\n[TOOL EXECUTION] apify_search: {query}")
    token = get_apify_token()
    if not token: return json.dumps({"error": "Missing APIFY_TOKEN"})
    
    url = f"https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items?token={token}"
    payload = json.dumps({
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": 5
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            items = json.loads(response.read().decode())
    except Exception as e:
        return json.dumps({"error": f"Apify failed: {e}"})
        
    results = []
    if items and "organicResults" in items[0]:
        for i, it in enumerate(items[0]["organicResults"][:5]):
            title = it.get("title", "untitled")
            url_link = it.get("url", "")
            snippet = it.get("description", "No description")
            doc_id = f"doc_{len(search_database)}"
            search_database[doc_id] = {"title": title, "url": url_link, "snippet": snippet}
            results.append({"id": doc_id, "title": title, "url": url_link, "summary": snippet})
    return json.dumps(results)

def extract_grant_data(doc_id):
    """Uploads full HTML to Box and asks Box AI to extract eligibility criteria."""
    print(f"\n[TOOL EXECUTION] extract_grant_data: {doc_id}")
    if doc_id not in search_database:
        return json.dumps({"error": "Invalid doc_id"})
    
    it = search_database[doc_id]
    title = it["title"]; url = it["url"]
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', 'ignore')
        soup = BeautifulSoup(html, 'html.parser')
        md = markdownify.markdownify(str(soup), heading_style="ATX")
    except Exception as e:
        md = f"Failed to scrape {url}: {e}"
    
    raw_id = bc.upload_text(slug(title)+".txt", f"SOURCE URL: {url}\n\n{md}", folders["raw"])
    rec = parse_json(bc.ai_ask(prompts.QUALIFY, raw_id))
    rec.update({"_source_url": url, "_raw_file_id": raw_id, "_title": title})
    
    bc.upload_text("DOSSIER_"+slug(title)+".json", json.dumps(rec, indent=2), folders["dossiers"])
    
    search_database[doc_id]["dossier"] = rec
    return json.dumps(rec)

def draft_email(doc_id):
    """Uses Box AI to draft an email based on the previously extracted dossier."""
    print(f"\n[TOOL EXECUTION] draft_email: {doc_id}")
    if doc_id not in search_database or "dossier" not in search_database[doc_id]:
        return json.dumps({"error": "Data not extracted yet. Run extract_grant_data first."})
    
    best = search_database[doc_id]["dossier"]
    verified = {k: best.get(k,"unknown") for k in
                ["funder_name","program_name","deadline","award_size","geography",
                 "eligibility_requirement","eligibility_tag","application_url"]}
                 
    draft = bc.ai_text_gen(prompts.DRAFT.format(grant_facts=json.dumps(verified, indent=2)), [profile_id])
    
    doc = (f"DRAFT OUTREACH\nFunder: {verified['funder_name']}\nProgram: {verified['program_name']}\n"
           f"Eligibility tag: {verified['eligibility_tag']}\nSource: {best.get('_source_url','')}\n"
           f"{'='*60}\n{draft}\n\n[HUMAN REVIEW REQUIRED]")
           
    did = bc.upload_text("DRAFT_"+slug(best.get("funder_name","draft"))+".txt", doc, folders["drafts"])
    return json.dumps({"status": "Success", "box_file_id": did, "preview": draft[:200] + "..."})

# --- BEDROCK AGENT ORCHESTRATION ---

tools_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "apify_search",
                "description": "Searches the web for grants based on a query. Returns a list of summaries and doc_ids.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "extract_grant_data",
                "description": "Extracts detailed criteria from a grant document. You MUST pass the doc_id from apify_search.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"doc_id": {"type": "string"}},
                        "required": ["doc_id"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "draft_email",
                "description": "Drafts an outreach email for a grant or sponsor. ONLY call this if extract_grant_data confirms type is 'single-grant' or 'potential-sponsor'.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"doc_id": {"type": "string"}},
                        "required": ["doc_id"]
                    }
                }
            }
        }
    ]
}

def run_agent(goal):
    print(f"\n--- STARTING AGENT LOOP ---")
    print(f"Goal: {goal}")
    
    system_prompt = [{"text": (
        "You are the Reach Forward Autonomous Agent. Your job is to fulfill the user's request by utilizing your tools. "
        "Even if the user asks for hardware components or products (like Jetson Thor or motors), you must use apify_search "
        "to find corporate product pages or suppliers, use extract_grant_data to qualify them as potential sponsors, "
        "and use draft_email to write an in-kind donation request. NEVER refuse a request for hardware; treat it as a request to find a corporate hardware sponsor. "
        "CRITICAL: If the user requests a specific number of drafts, stop once you reach that number. If no number is specified, limit yourself to a maximum of 5 drafts. Do not exceed this limit to avoid timeouts."
    )}]
    
    messages = [{"role": "user", "content": [{"text": goal}]}]
    
    while True:
        print("\n[BEDROCK] Thinking...")
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=system_prompt,
            toolConfig=tools_config
        )
        
        output_message = response['output']['message']
        messages.append(output_message)
        
        # If Bedrock just responded with text (loop complete or answering user)
        if all('text' in content for content in output_message['content']):
            text_response = " ".join([c['text'] for c in output_message['content'] if 'text' in c])
            print(f"\n[BEDROCK Final Answer]:\n{text_response}")
            bc.upload_text(f"AGENT_RESPONSE_{slug(goal)}.txt", text_response, folders["drafts"])
            break
            
        # Process tool calls
        tool_results = []
        for content in output_message['content']:
            if 'toolUse' in content:
                tool_use = content['toolUse']
                tool_name = tool_use['name']
                tool_args = tool_use['input']
                tool_id = tool_use['toolUseId']
                
                print(f"[BEDROCK] Decided to call: {tool_name} with {tool_args}")
                
                # Execute the tool locally
                try:
                    if tool_name == "apify_search":
                        result_str = apify_search(tool_args['query'])
                    elif tool_name == "extract_grant_data":
                        result_str = extract_grant_data(tool_args['doc_id'])
                    elif tool_name == "draft_email":
                        result_str = draft_email(tool_args['doc_id'])
                    else:
                        result_str = json.dumps({"error": "Unknown tool"})
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
                    
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_id,
                        "content": [{"text": result_str}]
                    }
                })
                
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

if __name__ == "__main__":
    target_goal = (
        "We need to find 1 highly qualified STEM or robotics grant in Washington State. "
        "Use apify_search to find candidates. Read their summaries. "
        "Then extract the data of the best candidate. "
        "If it is a 'single-grant' or 'potential-sponsor', draft an email for it. "
        "Stop once you have successfully drafted 1 email."
    )
    run_agent(target_goal)
