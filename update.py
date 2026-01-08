"""
One-Click Update Script
Run this to update patterns from latest LangChain docs
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

PATTERNS_FILE = Path("data/patterns.json")
BACKUP_DIR = Path("data/backups")


def backup_current_data():
    """Backup current patterns before update"""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    if PATTERNS_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"patterns_backup_{timestamp}.json"
        
        with open(PATTERNS_FILE, 'r') as f:
            data = json.load(f)
        
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    
    return None


def get_current_stats():
    """Get stats from current patterns"""
    if not PATTERNS_FILE.exists():
        return None
    
    with open(PATTERNS_FILE, 'r') as f:
        data = json.load(f)
    
    return {
        "total": len(data.get('patterns', [])),
        "last_updated": data.get('collected_at', 'Unknown')
    }


def collect_new_data():
    """Run collector to get latest patterns"""
    print("\n📥 Fetching latest LangChain patterns...")
    
    try:
        result = subprocess.run(
            ['python', 'collector.py'],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Collection failed: {e}")
        print(e.stderr)
        return False


def reingest_data():
    """Re-run ingestion with new data"""
    print("\n🔄 Re-ingesting data...")
    
    try:
        result = subprocess.run(
            ['python', 'ingest_simple.py'],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ingestion failed: {e}")
        print(e.stderr)
        return False


def compare_stats(old_stats, new_stats):
    """Compare before and after stats"""
    if not old_stats:
        print("\n📊 New patterns database created!")
        print(f"   Total patterns: {new_stats['total']}")
        return
    
    print("\n📊 Update Summary:")
    print("=" * 50)
    print(f"Before: {old_stats['total']} patterns")
    print(f"After:  {new_stats['total']} patterns")
    print(f"Change: {new_stats['total'] - old_stats['total']:+d} patterns")
    print("=" * 50)
    
    if new_stats['total'] > old_stats['total']:
        print("✅ New patterns added!")
    elif new_stats['total'] < old_stats['total']:
        print("⚠️  Some patterns removed (check backup)")
    else:
        print("ℹ️  No new patterns found")


def main():
    print("=" * 60)
    print("🔄 LangChain Patterns Update Script")
    print("=" * 60)
    
    # Step 1: Get current stats
    old_stats = get_current_stats()
    
    # Step 2: Backup current data
    backup_file = backup_current_data()
    
    # Step 3: Collect new data
    if not collect_new_data():
        print("\n❌ Update failed at collection stage")
        return
    
    # Step 4: Get new stats
    new_stats = get_current_stats()
    
    # Step 5: Compare
    compare_stats(old_stats, new_stats)
    
    # Step 6: Re-ingest
    if new_stats and new_stats['total'] > 0:
        reingest_data()
    
    print("\n✅ Update complete!")
    print("\n💡 Next steps:")
    print("   1. Review changes in data/patterns.json")
    print("   2. Test the app: streamlit run app.py")
    print("   3. Redeploy if needed")
    
    if backup_file:
        print(f"\n📦 Backup saved: {backup_file}")


if __name__ == "__main__":
    main()