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
        md_lines.append("| 📦 Project & Description | 📊 Metrics | 📈 Star History |")
        md_lines.append("|--------------------------|------------|-----------------|")
        
        repos = category_data.get("repos", [])
        
        # Sort repositories dynamically by current stars based on memory before overwriting
        # Actually, let's just fetch them all, then sort by highest star count or growth!
        enriched_repos = []
        
        for repo in repos:
            stats = fetch_repo_stats(repo["url_path"])
            if not stats:
                continue
                
            current_stars = stats.get("stargazers_count", 0)
            last_stars = repo.get("last_stars", current_stars)
            growth = current_stars - last_stars
            
            repo["last_stars"] = current_stars
            
            enriched_repos.append({
                "repo_path": repo["url_path"],
                "name": stats.get("name"),
                "html_url": stats.get("html_url"),
                "description": (stats.get("description") or "No description provided").replace("|", "\\|"),
                "language": stats.get("language") or "N/A",
                "forks": stats.get("forks_count", 0),
                "issues": stats.get("open_issues_count", 0),
                "stars": current_stars,
                "growth": growth,
                "ref": repo
            })
            
        # Sort enriched_repos by total stars descending
        enriched_repos.sort(key=lambda x: x["stars"], reverse=True)
        
        for e in enriched_repos:
            growth_str = f"🚀 **+{e['growth']}**" if e['growth'] > 0 else f"{e['growth']}"
            if e['growth'] > 1000:
                growth_str = f"🔥 {growth_str}"
                
            desc_limited = e['description']
            if len(desc_limited) > 100:
                desc_limited = desc_limited[:97] + "..."
                
            # Formatting Left Column (Project, Links, Desc)
            col1 = f"**[{e['name']}]({e['html_url']})**<br/><sub>{e['repo_path']}</sub><br/><br/><sub>{desc_limited}</sub>"
            
            # Formatting Middle Column (Metrics, Badges)
            lang_badge = f"![{e['language']}](https://img.shields.io/badge/Code-{e['language'].replace('-', '_').replace(' ', '_')}-blue?style=flat-square)" if e['language'] != 'N/A' else ""
            stars_badge = f"![Stars](https://img.shields.io/github/stars/{e['repo_path']}?style=flat-square&color=gold)"
            forks_badge = f"![Forks](https://img.shields.io/github/forks/{e['repo_path']}?style=flat-square&color=lightgrey)"
            
            col2 = f"{stars_badge}<br/>{forks_badge}<br/>{lang_badge}<br/><br/>**7d Δ:** {growth_str}"
            
            # Formatting Right Column (Chart)
            col3 = f"<a href='https://star-history.com/#{e['repo_path']}&Date'><img src='https://api.star-history.com/svg?repos={e['repo_path']}&type=Date' width='300'/></a>"
            
            md_lines.append(f"| {col1} | {col2} | {col3} |")
            
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
    
    print("Fetching repository statistics & building UI...")
    dynamic_md = generate_markdown(projects_data)
    
    print("Saving updated projects.json...")
    save_projects(projects_file, projects_data)
    
    print("Generating README.md...")
    with open(template_file, "r", encoding="utf-8") as f:
        template_content = f.read()
    
    now_utc = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
    final_readme = template_content.replace("<!-- DYNAMIC_CONTENT -->", dynamic_md)
    final_readme = final_readme.replace("{{ timestamp }}", now_utc)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_readme)
        
    print("Update complete! README.md successfully created with rich content.")

if __name__ == "__main__":
    main()
