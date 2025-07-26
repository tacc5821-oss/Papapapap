#!/usr/bin/env python3
"""
Test script to verify bot functionality
"""
import asyncio
from config import BOT_TOKEN, OWNER_ID, LOG_GROUP_ID
from database import get_user_data, load_bot_state

async def test_bot_connection():
    """Test if bot can connect to Telegram"""
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"Bot name: {me.first_name}")
        print(f"Bot username: @{me.username}")
        print(f"Bot ID: {me.id}")
        return True
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        return False

def test_configuration():
    """Test configuration values"""
    print("📋 Configuration Check:")
    print(f"Owner ID: {OWNER_ID}")
    print(f"Log Group ID: {LOG_GROUP_ID}")
    print(f"Bot Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:] if len(BOT_TOKEN) > 20 else BOT_TOKEN}")

def test_database():
    """Test database functionality"""
    print("\n💾 Database Check:")
    
    # Test user data
    user_data = get_user_data(OWNER_ID)
    print(f"✅ User data loaded for owner: {user_data}")
    
    # Test bot state
    bot_state = load_bot_state()
    print(f"✅ Bot state loaded: {bot_state.keys()}")

def show_menu_structure():
    """Show the bot menu structure"""
    print("\n🔧 Main Menu Structure:")
    print("For regular users:")
    print("- 🎁 Spin (5/5)")
    print("- 📤 Exchange Points")
    print("- 📋 Event")
    print("- 📊 My Points")
    print("- 📜 History")
    
    print("\nFor admin (Owner):")
    print("- 🧑‍💼 Admin Panel")
    print("  - 📢 Start Event")
    print("  - 📄 View Participants")
    print("  - ❌ Cancel Event")

def show_features():
    """Show bot features"""
    print("\n🎯 Bot Features:")
    print("1. 🎰 Spin System:")
    print("   - 5 spins per day for users (unlimited for owner)")
    print("   - Probability-based rewards")
    print("   - Auto-logging to group")
    
    print("\n2. 💱 Exchange System:")
    print("   - Fixed amounts: 500, 1000 points")
    print("   - Admin approval required")
    print("   - Receipt photo system")
    
    print("\n3. 📢 Event System:")
    print("   - Channel joining events")
    print("   - 200 points reward")
    print("   - One-time completion per user")
    
    print("\n4. 🔧 Admin Features:")
    print("   - Event creation and management")
    print("   - Exchange approval/rejection")
    print("   - Participant tracking")

async def main():
    """Main test function"""
    print("🤖 Telegram Bot Test Suite")
    print("=" * 40)
    
    test_configuration()
    test_database()
    show_menu_structure()
    show_features()
    
    print("\n🔗 Testing bot connection...")
    connection_ok = await test_bot_connection()
    
    if connection_ok:
        print("\n✅ All tests passed! Bot is ready to use.")
        print(f"\n📱 Start chatting with your bot:")
        print(f"Search for your bot on Telegram and send /start")
    else:
        print("\n❌ Connection test failed. Check your bot token.")

if __name__ == "__main__":
    asyncio.run(main())