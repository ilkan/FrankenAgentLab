#!/usr/bin/env python3
"""Test marketplace API endpoints (no authentication required)."""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_list_marketplace_blueprints():
    """Test listing all marketplace blueprints."""
    print("\n=== Testing GET /api/marketplace/blueprints ===")
    
    response = requests.get(f"{BASE_URL}/api/marketplace/blueprints")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        blueprints = data.get("blueprints", [])
        print(f"✓ Found {len(blueprints)} blueprints")
        
        # Show first 3 blueprints
        for i, bp in enumerate(blueprints[:3]):
            print(f"\n  Blueprint {i+1}:")
            print(f"    ID: {bp.get('id')}")
            print(f"    Name: {bp.get('name')}")
            print(f"    Category: {bp.get('category')}")
            print(f"    Source: {bp.get('source')}")
            print(f"    Tags: {', '.join(bp.get('tags', []))}")
            print(f"    Rating: {bp.get('rating')}")
            print(f"    Downloads: {bp.get('downloads')}")
    else:
        print(f"✗ Failed: {response.text}")


def test_filter_by_category():
    """Test filtering blueprints by category."""
    print("\n=== Testing GET /api/marketplace/blueprints?category=Productivity ===")
    
    response = requests.get(
        f"{BASE_URL}/api/marketplace/blueprints",
        params={"category": "Productivity"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        blueprints = data.get("blueprints", [])
        print(f"✓ Found {len(blueprints)} Productivity blueprints")
        
        for bp in blueprints[:3]:
            print(f"  - {bp.get('name')} ({bp.get('category')})")
    else:
        print(f"✗ Failed: {response.text}")


def test_get_specific_blueprint():
    """Test getting a specific blueprint."""
    print("\n=== Testing GET /api/marketplace/blueprints/{id} ===")
    
    # First get the list to find a blueprint ID
    list_response = requests.get(f"{BASE_URL}/api/marketplace/blueprints")
    
    if list_response.status_code == 200:
        blueprints = list_response.json().get("blueprints", [])
        
        if blueprints:
            # Test with first blueprint
            blueprint_id = blueprints[0].get("id")
            print(f"Testing with blueprint ID: {blueprint_id}")
            
            response = requests.get(
                f"{BASE_URL}/api/marketplace/blueprints/{blueprint_id}"
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Retrieved blueprint: {data.get('name')}")
                print(f"  Description: {data.get('description')}")
                print(f"  Execution Mode: {data.get('legs', {}).get('execution_mode')}")
                
                # Show head configuration
                head = data.get('head', {})
                print(f"  Model: {head.get('model')} ({head.get('provider')})")
                
                # Show tools
                arms = data.get('arms', [])
                if arms:
                    print(f"  Tools: {len(arms)}")
                    for arm in arms:
                        print(f"    - {arm.get('name')} ({arm.get('type')})")
            else:
                print(f"✗ Failed: {response.text}")
        else:
            print("✗ No blueprints found to test with")
    else:
        print(f"✗ Failed to get blueprint list: {list_response.text}")


def test_yaml_blueprint():
    """Test getting a YAML-based blueprint."""
    print("\n=== Testing YAML Blueprint (research_writing_team) ===")
    
    response = requests.get(
        f"{BASE_URL}/api/marketplace/blueprints/research_writing_team"
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved YAML blueprint: {data.get('name')}")
        print(f"  Source: {data.get('source')}")
        print(f"  Execution Mode: {data.get('legs', {}).get('execution_mode')}")
        
        # Show team members if it's a team
        if data.get('legs', {}).get('execution_mode') == 'team':
            members = data.get('legs', {}).get('team_members', [])
            print(f"  Team Members: {len(members)}")
            for member in members:
                print(f"    - {member.get('name')} ({member.get('role')})")
    else:
        print(f"✗ Failed: {response.text}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("MARKETPLACE API TESTS (No Authentication Required)")
    print("=" * 60)
    
    try:
        test_list_marketplace_blueprints()
        test_filter_by_category()
        test_get_specific_blueprint()
        test_yaml_blueprint()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server")
        print("Make sure the server is running: poetry run uvicorn frankenagent.api.server:app --reload")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


if __name__ == "__main__":
    main()
