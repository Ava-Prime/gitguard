#!/usr/bin/env python3
"""
Sync GitGuard labels to repositories
"""
import sys
import yaml
import requests
import os
from typing import Dict, List

def load_labels() -> List[Dict]:
    """Load labels from config"""
    with open('config/gitguard.settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    labels = []
    for category, items in config['labels'].items():
        for key, label in items.items():
            labels.append({
                'name': label['name'],
                'color': label['color'],
                'description': f'GitGuard {category} label'
            })
    
    return labels

def sync_repo_labels(repo: str, labels: List[Dict]):
    """Sync labels to a repository"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable required")
        sys.exit(1)
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    base_url = f'https://api.github.com/repos/{repo}/labels'
    
    for label in labels:
        # Try to update existing label
        response = requests.patch(
            f"{base_url}/{label['name']}", 
            json=label, 
            headers=headers
        )
        
        if response.status_code == 404:
            # Label doesn't exist, create it
            response = requests.post(base_url, json=label, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ {label['name']}")
        else:
            print(f"❌ {label['name']}: {response.status_code}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python sync_labels.py <org/repo>")
        sys.exit(1)
    
    repo = sys.argv[1]
    labels = load_labels()
    sync_repo_labels(repo, labels)
