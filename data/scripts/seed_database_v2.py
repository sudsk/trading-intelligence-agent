"""
Master database seeding script (v2)
Includes all new generators for complete agent-ready data
"""
import subprocess
import sys

def run_script(script_name, description):
    """Run a generator script"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        print(f"\n✅ {description} - Complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - Failed")
        print(f"Error: {e}")
        return False

def main():
    """Run all generators in correct order"""
    
    print("="*60)
    print("🚀 MASTER DATABASE SEEDING (Agent-Ready)")
    print("="*60)
    print("\nThis will generate:")
    print("  1. Clients (50)")
    print("  2. Market Bars (6 months)")
    print("  3. Segment-Specific Trades (realistic patterns)")
    print("  4. Positions")
    print("  5. Headlines (500)")
    print("  6. Trading Features (pre-computed)")
    print("  7. Client Regimes (timeline)")
    print("  8. Switch Probability History")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    scripts = [
        # Core data (from existing scripts)
        ("seed_database.py", "Core Data (clients, positions, headlines)"),
        
        # Enhanced trades with segment patterns
        ("generate_trades_v2.py", "Segment-Specific Trades"),
        
        # Agent-specific data
        ("generate_features.py", "Trading Features"),
        ("generate_regimes.py", "Client Regimes"),
        ("generate_switch_probability.py", "Switch Probability History"),
    ]
    
    results = []
    
    for script, description in scripts:
        success = run_script(script, description)
        results.append((description, success))
        
        if not success:
            print(f"\n⚠️  Warning: {description} failed but continuing...")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SEEDING COMPLETE - Summary")
    print("="*60)
    
    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")
    
    failed = sum(1 for _, success in results if not success)
    
    if failed == 0:
        print("\n🎉 All generators completed successfully!")
        print("\n✅ Database is now agent-ready:")
        print("   - Clients with segments")
        print("   - Realistic segment-specific trades")
        print("   - Pre-computed features")
        print("   - Switch probability history")
        print("   - Timeline regimes")
        print("   - Headlines with sentiment")
        print("\nReady for Gemini agents!")
    else:
        print(f"\n⚠️  {failed} generator(s) failed - check logs")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
