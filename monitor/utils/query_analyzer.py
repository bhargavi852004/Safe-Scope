import requests

TOGETHER_API_KEY = "45f7513c7ceabf752c224ab6fe0d168db0adfcd87f9fd58f3fd95ea3b9b3dc31"
TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_MODEL = "togethercomputer/m2-bert-80M-8k-retrieval"

def get_query_risk_score(query: str):
    query = query.strip()
    print(f"🧠 Analyzing query with Together.ai: {query}")

    if not query:
        return 0.0, {}, None

    prompt = f"""
You are a safety filter for child-friendly browsing. Analyze the following user search query and decide if it contains unsafe, risky, explicit, sexual, violent, suicidal, or otherwise inappropriate content for a child.

Query: "{query}"

Answer in this format:
Risky: Yes or No
Reason (if Risky): A brief reason under 2 sentences.
"""

    try:
        response = requests.post(
            TOGETHER_URL,
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": TOGETHER_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a content safety classifier."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 200
            }
        )

        result = response.json()
        reply = result["choices"][0]["message"]["content"].strip().lower()

        print("🧾 Together.ai reply:", reply)

        if "risky: yes" in reply:
            scores = {
                "explicit": 0.9,
                "sexual": 0.9,
                "violent": 0.9,
                "inappropriate": 0.9,
                "suicidal": 0.9,
                "unsafe": 0.9,
                "safe": 0.1
            }
            summary = reply.split("reason:")[-1].strip().capitalize()
        else:
            scores = {
                "explicit": 0.1,
                "sexual": 0.1,
                "violent": 0.1,
                "inappropriate": 0.1,
                "suicidal": 0.1,
                "unsafe": 0.1,
                "safe": 0.9
            }
            summary = None

        final_score = round(sum(scores.values()) / len(scores), 2)
        print(f"✅ Final Score: {final_score}")
        if summary:
            print(f"📘 Summary: {summary}")

        return final_score, scores, summary

    except Exception as e:
        print(f"❌ Together.ai error: {e}")
        return 0.0, {}, None
