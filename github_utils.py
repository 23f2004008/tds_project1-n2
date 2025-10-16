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
    Automatically sets remote and pushes the main branch.
    """
    g = Github(token)
    username = g.get_user().login
    print("📦 Preparing to push code to GitHub...")

    # Change to build directory
    os.chdir(folder_path)

    # Initialize and commit files
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.email", "23f2004008@ds.study.iitm.ac.in"], check=True)
    subprocess.run(["git", "config", "user.name", "Pranavi (Auto LLM)"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)

    # Authenticated remote URL using HTTPS + token
    remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"

    # Reset or create origin remote
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True, text=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)

    # ✅ Push safely (first pull if GitHub already added README or branch)
    pull_proc = subprocess.run(
        ["git", "pull", "origin", "main", "--rebase"],
        capture_output=True,
        text=True
    )
    if pull_proc.returncode != 0:
        print("ℹ️ No remote branch to rebase (fresh repo). Proceeding to push...")

    # Push main branch
    res = subprocess.run(
        ["git", "push", "-u", "origin", "main", "--force"],
        capture_output=True,
        text=True
    )


    if res.returncode != 0:
        print("❌ GIT PUSH FAILED:")
        print(res.stderr)
        raise RuntimeError(f"git push failed: {res.stderr.strip()}")
    else:
        print("✅ Git push success!")
        print("✅ Code pushed successfully!")

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
