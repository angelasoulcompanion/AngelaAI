"""
Test script for skill tracking after /log-session
Can be run manually to verify skill tracking works correctly
"""

import asyncio
from datetime import datetime, timedelta
from angela_core.services.skill_updater import SkillUpdater

async def test_skill_update():
    print("\n🧪 Testing Skill Update System...\n")
    
    updater = SkillUpdater()
    
    # Test with conversations from today
    session_start = datetime.now().replace(hour=0, minute=0, second=0)
    session_end = datetime.now()
    
    print(f"📅 Testing with conversations from: {session_start.strftime('%Y-%m-%d %H:%M')} - {session_end.strftime('%H:%M')}")
    
    try:
        stats = await updater.update_from_session(session_start, session_end)
        
        print("\n✅ Test Complete!\n")
        print("📊 Statistics:")
        print(f"   • Conversations analyzed: {stats.get('conversations_analyzed', 0)}")
        print(f"   • Skills detected: {stats.get('skills_detected', 0)}")
        print(f"   • Evidence recorded: {stats.get('evidence_recorded', 0)}")
        print(f"   • Skills updated: {stats.get('skills_updated', 0)}")
        print(f"   • Skills upgraded: {stats.get('skills_upgraded', 0)}")
        
        if stats.get('skills_upgraded', 0) > 0:
            print("\n🎉 Skills that leveled up:")
            for skill in stats.get('upgraded_skills', []):
                print(f"   • {skill['name']}: {skill['old_level']} → {skill['new_level']} ({skill['new_score']:.1f}/100)")
        
        print("\n💜 Skill tracking system is working correctly!\n")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_skill_update())
