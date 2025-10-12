# app.py
from flask import Flask, request, jsonify
import os
import tempfile
import subprocess
from github import Github
from github_utils import create_github_repo, push_to_github, enable_github_pages, notify_evaluator
from generator import generate_app_files
from openai import OpenAI

app = Flask(__name__)

# 🔐 Environment secrets
SECRET = os.environ.get("SUBMISSION_SECRET")

# =========================================================
# 🧩 Helper functions
# =========================================================
def get_github_username(token):
    g = Github(token)
    return g.get_user().login

def find_existing_repo(task_name, token):
    """Finds an existing repo that starts with the given task name."""
    g = Github(token)
    user = g.get_user()
    for repo in user.get_repos():
        if repo.name.startswith(task_name):
            return repo.name
    return None

def update_repo_with_llm(repo_name, token, brief):
    """Uses GPT to modify an existing repo based on a new brief."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    g = Github(token)
    user = g.get_user()
    repo = user.get_repo(repo_name)

    temp_dir = tempfile.mkdtemp(prefix="update_")

    # Clone repo locally
    subprocess.run(["git", "clone", repo.clone_url, temp_dir, "--depth", "1"], check=True)

    index_path = os.path.join(temp_dir, "index.html")
    if not os.path.exists(index_path):
        raise Exception("index.html not found in existing repo")

    old_code = open(index_path, "r", encoding="utf-8").read()

    prompt = f"""
    You are a web developer assistant.
    Modify the following HTML/JS/CSS based on this new request.

    Existing index.html:
    {old_code[:3000]}

    New request:
    {brief}

    Output ONLY the full new HTML code.
    """

    print("🧠 Generating updated code with GPT for round 2...")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You update code precisely."},
            {"role": "user", "content": prompt}
        ]
    )

    new_code = resp.choices[0].message.content.strip()
    open(index_path, "w", encoding="utf-8").write(new_code)

    # Commit & push
    subprocess.run(["git", "-C", temp_dir, "add", "."], check=True)
    subprocess.run(["git", "-C", temp_dir, "commit", "-m", "Auto revision by LLM"], check=True)
    subprocess.run(["git", "-C", temp_dir, "push"], check=True)

    print("✅ Repo updated and pushed successfully for round 2.")

# =========================================================
# 🧠 API Routes
# =========================================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "LLM Deployment API is running ✅",
        "usage": "Send POST request to /api-endpoint with JSON payload."
    })

@app.route("/api-endpoint", methods=["POST"])
def api_endpoint():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # 1️⃣ Verify secret
    if data.get("secret") != SECRET:
        return jsonify({"error": "Invalid secret"}), 403

    # 2️⃣ Check required fields
    required = ["email", "task", "round", "nonce", "brief", "evaluation_url"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": "Missing fields", "missing": missing}), 400

    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        return jsonify({"status": "error", "message": "Missing GitHub token"}), 500

    try:
        task = data["task"]
        round_num = int(data["round"])
        username = get_github_username(GITHUB_TOKEN)
        repo_name = None

        if round_num == 1:
            # ---------------------------------------------------------
            # 🧠 Round 1: Fresh generation
            # ---------------------------------------------------------
            task_dir = tempfile.mkdtemp(prefix="task_")
            generate_app_files(data["brief"], task_dir)

            readme_path = os.path.join(task_dir, "README.md")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# {task}\n\n{data['brief']}\n\nGenerated automatically by LLM.\n")

            repo_name = f"{task}-{data['nonce']}"
            repo = create_github_repo(repo_name, GITHUB_TOKEN)
            push_to_github(repo_name, GITHUB_TOKEN, task_dir)
            enable_github_pages(repo)

        elif round_num == 2:
            # ---------------------------------------------------------
            # 🧠 Round 2: Modify existing repo (auto-revision)
            # ---------------------------------------------------------
            repo_name = find_existing_repo(task, GITHUB_TOKEN)
            if not repo_name:
                return jsonify({"error": "Existing repo not found"}), 404
            update_repo_with_llm(repo_name, GITHUB_TOKEN, data["brief"])

        # ---------------------------------------------------------
        # 📤 Notify evaluator
        # ---------------------------------------------------------
        pages_url = f"https://{username}.github.io/{repo_name}/"
        repo_url = f"https://github.com/{username}/{repo_name}"

        payload = {
            "email": data["email"],
            "task": task,
            "round": round_num,
            "nonce": data["nonce"],
            "repo_url": repo_url,
            "commit_sha": "auto-revision" if round_num == 2 else "initial-commit",
            "pages_url": pages_url
        }
        notify_evaluator(data["evaluation_url"], payload)

    except Exception as e:
        print("⚠️ Automation failed:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "ok",
        "message": f"Round {round_num} completed successfully ✅",
        "repo_url": repo_url,
        "pages_url": pages_url
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
