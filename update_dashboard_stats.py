"""
Update dashboard stats directly in the database
"""
import sys
import os
import requests
import json
from datetime import datetime

# API endpoint
API_URL = "http://localhost:8000"

def update_dashboard_stats():
    """Update dashboard stats via API"""
    print("\n" + "="*70)
    print("UPDATING DASHBOARD STATS")
    print("="*70)
    
    # First, check current stats
    print("\nChecking current dashboard stats...")
    try:
        response = requests.get(f"{API_URL}/api/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"Current stats:")
            print(f"- Total Queries: {stats['total_queries_discovered']}")
            print(f"- Total Optimizations: {stats['total_optimizations']}")
            print(f"- Total Detected Issues: {stats['total_detected_issues']}")
        else:
            print(f"Failed to get dashboard stats: {response.text}")
            return
    except Exception as e:
        print(f"Error checking dashboard stats: {e}")
        return
    
    # Create a test connection if needed
    print("\nChecking for existing connections...")
    try:
        response = requests.get(f"{API_URL}/api/connections")
        if response.status_code == 200:
            connections = response.json()
            if len(connections) == 0:
                print("No connections found. Creating a test connection...")
                connection_data = {
                    "name": "Test PostgreSQL",
                    "engine": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "username": "postgres",
                    "password": "password",
                    "ssl_enabled": False,
                    "monitoring_enabled": True
                }
                response = requests.post(f"{API_URL}/api/connections", json=connection_data)
                if response.status_code == 201 or response.status_code == 200:
                    print("✓ Test connection created")
                else:
                    print(f"Failed to create connection: {response.text}")
            else:
                print(f"✓ Found {len(connections)} existing connections")
        else:
            print(f"Failed to get connections: {response.text}")
    except Exception as e:
        print(f"Error checking connections: {e}")
    
    # Create a test query
    print("\nCreating a test query via monitoring API...")
    try:
        # This is a workaround to create a query without using the database directly
        # We'll trigger the monitoring agent to simulate query discovery
        response = requests.post(f"{API_URL}/api/monitoring/trigger")
        if response.status_code == 200:
            print("✓ Monitoring triggered")
        else:
            print(f"Failed to trigger monitoring: {response.text}")
    except Exception as e:
        print(f"Error triggering monitoring: {e}")
    
    # Check stats again after updates
    print("\nChecking updated dashboard stats...")
    try:
        response = requests.get(f"{API_URL}/api/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"Updated stats:")
            print(f"- Total Queries: {stats['total_queries_discovered']}")
            print(f"- Total Optimizations: {stats['total_optimizations']}")
            print(f"- Total Detected Issues: {stats['total_detected_issues']}")
        else:
            print(f"Failed to get dashboard stats: {response.text}")
    except Exception as e:
        print(f"Error checking dashboard stats: {e}")
    
    print("\n" + "="*70)
    print("✅ DASHBOARD STATS UPDATE COMPLETE")
    print("="*70)
    print("\nIf the stats are still showing as 0, please try the following:")
    print("1. Restart the backend service: docker-compose restart backend")
    print("2. Refresh the dashboard page in your browser")
    print("3. Try running a query optimization through the UI")

if __name__ == "__main__":
    update_dashboard_stats()
