#!/usr/bin/env python3
"""
Complete fresh start script: cleans everything and runs new simulation.
"""

import os
import shutil
import asyncio
from sandbox.world import WorldState
from sandbox.scheduler import build_default

def clean_slate():
    """Remove all existing state files."""
    print("🧹 Cleaning slate...")
    
    # Remove world state
    if os.path.exists("world.json"):
        os.remove("world.json")
        print("  ✅ Removed world.json")
    
    # Remove memory database
    if os.path.exists("mem_db"):
        shutil.rmtree("mem_db")
        print("  ✅ Removed mem_db/")
    
    # Remove logs (optional)
    if os.path.exists("logs"):
        shutil.rmtree("logs")
        print("  ✅ Removed logs/")

def initialize_world():
    """Initialize a fresh world with basic starting conditions."""
    print("🌍 Initializing fresh world...")
    
    world = WorldState()
    
    # Add basic discoverable materials
    world.add_object("wood", {"description": "Fallen branches", "location": "forest", "creator": "nature"})
    world.add_object("stone", {"description": "River rocks", "location": "river", "creator": "nature"}) 
    world.add_object("water", {"description": "Fresh spring water", "location": "spring", "creator": "nature"})
    
    # Set discovery materials for experimentation
    world.environment["discovery_materials"] = ["mysterious_seed", "ancient_fragment", "crystal_shard"]
    
    # Initialize agents at starting location
    world.agents["Adam"] = {"location": "clearing", "skills": [], "knowledge": {}}
    world.agents["Eve"] = {"location": "clearing", "skills": [], "knowledge": {}}
    
    world.save("world.json")
    print("  ✅ Fresh world created with 3 natural objects")
    return world

async def run_simulation(ticks=100):
    """Run the enhanced simulation."""
    print(f"🚀 Starting {ticks}-tick simulation...")
    
    world = WorldState.load("world.json")
    scheduler = build_default(world)
    
    print("👥 Adam and Eve are ready!")
    print("🌱 Starting in spring with exploration focus")
    print("=" * 60)
    
    await scheduler.loop(max_ticks=ticks)
    
    print("=" * 60)
    print("✅ Simulation complete!")
    
    # Print final stats
    print(f"\n📊 Final Statistics:")
    print(f"  • Total ticks: {world.tick}")
    print(f"  • Objects created: {len([obj for obj in world.objects.values() if obj.get('creator') not in ['nature', None]])}")
    print(f"  • Total objects: {len(world.objects)}")
    print(f"  • Environmental events: {len(world.environment.get('event_history', []))}")
    print(f"  • Innovation rewards: {len(world.environment.get('innovation_rewards', []))}")
    
    # Agent progress
    for agent_name, agent_data in world.agents.items():
        skills = agent_data.get('skills', [])
        knowledge = agent_data.get('knowledge', {})
        location = agent_data.get('location', 'unknown')
        print(f"  • {agent_name}: {len(skills)} skills, {len(knowledge)} knowledge, at {location}")

def main():
    """Complete fresh start and simulation."""
    print("🔄 FRESH START: Enhanced Empty-Earth Sandbox")
    print("=" * 50)
    
    # Get user preferences
    print("Options:")
    print("1. Quick start (100 ticks)")
    print("2. Medium run (250 ticks)")  
    print("3. Long simulation (500 ticks)")
    print("4. Custom tick count")
    
    try:
        choice = input("\nChoice (1-4): ").strip()
        
        if choice == "1":
            ticks = 100
        elif choice == "2":
            ticks = 250
        elif choice == "3":
            ticks = 500
        elif choice == "4":
            ticks = int(input("Enter tick count: "))
        else:
            ticks = 100
            print("Invalid choice, defaulting to 100 ticks")
    except (ValueError, KeyboardInterrupt):
        ticks = 100
        print("\nDefaulting to 100 ticks")
    
    # Execute fresh start
    clean_slate()
    initialize_world()
    
    print(f"\n🎮 Running {ticks} ticks...")
    asyncio.run(run_simulation(ticks))

if __name__ == "__main__":
    main() 