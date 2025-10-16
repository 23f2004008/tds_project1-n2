# github_utils.py
import os
import subprocess
import requests
from github import Github

def create_github_repo(repo_name, token):
    """
    Create a new public repository on GitHub.
    Returns the PyGithub Repository object.
    """
    g = Github(token)
    user = g.get_user()
    print(f"🛠️ Creating repository: {repo_name}")
    try:
        # ✅ auto_init=False prevents push conflicts
        repo = user.create_repo(
            name=repo_name,
            private=False,
            auto_init=False,
            description="Auto-generated repository for automated app deployment"
        )
        print(f"✅ Repository created: {repo.html_url}")
        return repo
    except Exception as e:
        # Handle 'name already exists' and other GitHub API errors
        print(f"❌ Repository creation failed: {e}")
        raise RuntimeError(f"Repository creation failed: {e}")

def push_to_github(repo_name, token, folder_path):
    """
    Push local files in folder_path to the specified GitHub repo.
    Works for both Round 1 (new repo) and Round 2 (update existing repo).
    """
    g = Github(token)
    username = g.get_user().login
    print(f"📦 Preparing to push code to GitHub repo: {repo_name}")

    # Change working directory to folder_path
    os.chdir(folder_path)

    # Initialize and configure Git
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "23f2004008@ds.study.iitm.ac.in"], check=True)
    subprocess.run(["git", "config", "user.name", "Pranavi (Auto LLM)"], check=True)

    # Stage and commit all files
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "Auto revision by LLM"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)

    # Authenticated remote URL
    remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"

    # Ensure remote is reset properly
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
    print("🔗 Remote origin set successfully.")

    # Try fetching remote branch (in case repo already exists)
    subprocess.run(["git", "fetch", "origin"], capture_output=True)

    # Force push safely
    print("🚀 Pushing changes to GitHub (with --force)...")
    res = subprocess.run(
        ["git", "push", "-u", "origin", "main", "--force"],
        capture_output=True,
        text=True
    )

    # Handle push result
    if res.returncode != 0:
        print("❌ GIT PUSH FAILED:")
        print(res.stderr)
        raise RuntimeError(f"git push failed with code {res.returncode}: {res.stderr.strip()}")
    else:
        print("✅ Git push success!")
        print("✅ Code pushed successfully to:", remote_url)


def enable_github_pages(repo):
    """
    Enable GitHub Pages for the given repository using PyGithub.
    """
    try:
        repo.create_pages_site(
            source_type="branch",
            source_branch="main",
            source_path="/"
        )
        print("🌐 GitHub Pages enabled successfully.")
    except Exception as e:
        print("⚠️ Could not enable GitHub Pages:", e)

def notify_evaluator(evaluation_url, payload):
    """
    Send a POST request to the evaluator URL with JSON payload.
    """
    try:
        response = requests.post(
            evaluation_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print(f"📤 Notified evaluator: {response.status_code}")
        if response.status_code != 200:
            print("⚠️ Evaluator response:", response.text)
        return response.status_code
    except requests.exceptions.RequestException as e:
        print("⚠️ Failed to notify evaluator:", e)
        return None
