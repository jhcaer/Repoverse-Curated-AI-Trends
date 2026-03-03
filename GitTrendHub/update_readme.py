import os
import json
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def load_projects(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_projects(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_repo_stats(repo_path):
    url = f"https://api.github.com/repos/{repo_path}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {repo_path}: {response.status_code}")
        return None

def generate_markdown(projects_data):
    md_lines = []
    
    for category_key, category_data in projects_data.items():
        title = category_data.get("title", category_key.title())
        md_lines.append(f"## {title}")
        md_lines.append("")
        md_lines.append("| Project | Description | ⭐ Stars | 7d Δ | 📈 Star History |")
        md_lines.append("|---------|-------------|---------|------|-----------------|")
        
        repos = category_data.get("repos", [])
        
        # We will iterate and optionally sort by growth if desired, 
        # but for now we maintain the order in projects.json
        for repo in repos:
            stats = fetch_repo_stats(repo["url_path"])
            if not stats:
                continue
            
            current_stars = stats.get("stargazers_count", 0)
            last_stars = repo.get("last_stars", current_stars)
            growth = current_stars - last_stars
            growth_str = f"🚀 +{growth}" if growth > 0 else str(growth)
            
            # Update last_stars for next run
            repo["last_stars"] = current_stars
            
            name = stats.get("name")
            html_url = stats.get("html_url")
            description = (stats.get("description") or "-").replace("|", "\\|")
            if len(description) > 80:
                description = description[:77] + "..."
            
            stars_badge = f"![Stars](https://img.shields.io/github/stars/{repo['url_path']}?style=flat-square)"
            history_svg = f"<img src='https://api.star-history.com/svg?repos={repo['url_path']}&type=Date' width='250'/>"
            
            md_lines.append(f"| [{name}]({html_url}) <br/> `{repo['url_path']}` | {description} | {stars_badge} | **{growth_str}** | {history_svg} |")
            
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        
    return "\n".join(md_lines)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    projects_file = os.path.join(base_dir, "projects.json")
    template_file = os.path.join(base_dir, "README.md.template")
    output_file = os.path.join(base_dir, "README.md")
    
    print("Loading projects...")
    projects_data = load_projects(projects_file)
    
    print("Fetching repository statistics...")
    dynamic_md = generate_markdown(projects_data)
    
    print("Saving updated projects.json...")
    save_projects(projects_file, projects_data)
    
    print("Generating README.md...")
    with open(template_file, "r", encoding="utf-8") as f:
        template_content = f.read()
    
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    final_readme = template_content.replace("<!-- DYNAMIC_CONTENT -->", dynamic_md)
    final_readme = final_readme.replace("{{ timestamp }}", now_utc)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_readme)
        
    print("Update complete! README.md successfully created.")

if __name__ == "__main__":
    main()
