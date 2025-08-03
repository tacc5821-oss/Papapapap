# replit.md

## Overview

This is a fully operational Telegram bot application (@giftwaychinese_bot) that implements a comprehensive MMK (Myanmar Kyat) currency-based reward system with spinning, event participation, point exchange features, referral system, and help support. The bot uses Python with the python-telegram-bot library and stores data in JSON files for persistence.

**Current Status**: ✅ Running Successfully 
**Bot Username**: @giftwaychinese_bot
**Owner ID**: 1735522859
**Last Updated**: August 3, 2025

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Python with python-telegram-bot library
- **Data Storage**: JSON file-based storage (no database)
- **Architecture Pattern**: Handler-based event-driven architecture
- **Deployment**: Single-process application suitable for small to medium scale

### Key Design Decisions
1. **JSON File Storage**: Chosen for simplicity and ease of deployment without database dependencies
2. **Handler Pattern**: Separates different bot functionalities into distinct handler modules
3. **Configuration-Driven**: All configurable values centralized in config.py
4. **Logging Integration**: Built-in logging to both files and Telegram groups

## Key Components

### Core Modules

1. **main.py**: Application entry point and handler registration
   - Sets up the Telegram bot application
   - Registers all command and callback handlers
   - Manages the main event loop

2. **config.py**: Configuration management
   - Bot tokens and IDs
   - Spin system configuration (limits, rewards, probabilities)
   - MMK exchange amounts and referral settings
   - Help group configuration

3. **database.py**: Data persistence layer
   - JSON file operations for user data and bot state
   - User data management functions
   - Bot state tracking (events, exchanges, referrals)

### Handler Modules

1. **handlers/menu.py**: Main menu and navigation
   - Start command handler
   - Main menu keyboard generation
   - User privilege-based menu options

2. **handlers/spin.py**: Spinning/gambling feature
   - Daily spin limits (configurable)
   - Weighted random rewards system
   - Spin history tracking

3. **handlers/exchange.py**: Point exchange system
   - Point-to-reward exchange
   - Admin approval workflow
   - Exchange history tracking

4. **handlers/event.py**: Event participation
   - Channel joining events
   - Event completion verification
   - Reward distribution

5. **handlers/admin.py**: Administrative functions
   - Event creation and management
   - Exchange approval/rejection
   - Admin-only access controls
   - Add user spins feature (bonus spin distribution)

### Utility Modules

1. **utils/logger.py**: Logging system
   - File and console logging
   - Telegram group logging integration
   - Configurable log levels

2. **utils/helpers.py**: Helper functions
   - Date/time formatting
   - Telegram link validation
   - User ranking calculations
   - History cleanup utilities

## Data Flow

### User Interaction Flow
1. User sends /start command
2. Bot loads/creates user data from JSON
3. User interacts via inline keyboard callbacks
4. Actions update user data and trigger appropriate handlers
5. Results are saved back to JSON files
6. Admin receives notifications for exchange requests

### Data Storage Structure
- **user_data.json**: Stores user points, spin history, event participation
- **bot_state.json**: Stores current events, pending exchanges, global state

### Admin Workflow
1. Admin creates events through admin panel
2. Users participate in events (join channels)
3. Users earn points through spins and events
4. Users request exchanges
5. Admin approves/rejects exchanges
6. Points are deducted and logs are created

## External Dependencies

### Required Python Packages
- python-telegram-bot: Telegram Bot API integration
- Standard library modules: json, os, logging, datetime, random

### External Services
- **Telegram Bot API**: Core bot functionality
- **Telegram Channels**: For event participation requirements

### Environment Variables
- BOT_TOKEN: Telegram bot token
- OWNER_ID: Admin user ID
- LOG_GROUP_ID: Logging group chat ID

## Deployment Strategy

### Current Setup
- Single-process application
- JSON file-based persistence
- Environment variable configuration
- File-based logging

### Deployment Requirements
1. Python 3.7+ environment
2. Bot token from @BotFather
3. Writable directory for JSON files
4. Network access to Telegram APIs

### Scaling Considerations
- JSON storage limits scalability to moderate user bases
- Single-process design suitable for small to medium deployments
- Consider database migration for larger scale (Postgres recommended)
- Current architecture supports easy transition to database storage

### Security Features
- Owner-only admin access
- Input validation for Telegram links
- Error handling and logging
- No sensitive data stored in code (environment variables)

## Recent Updates (August 2025)

### Currency System Migration
- **Points → MMK**: Converted entire system from points to Myanmar Kyat (MMK) currency
- Updated all reward displays and calculations to use MMK
- Modified exchange system to work with MMK amounts

### Referral System
- **Invite Friends**: Added referral link generation for each user
- **One-time Bonus**: Each successful referral gives +3 spins (one-time per user)
- **Referral Tracking**: Users can see their referral count in statistics
- **Anti-abuse**: Referral links work only once per user to prevent abuse

### User Interface Enhancements
- **Help Button**: Added Myanmar language help button linking to support group
- **Statistics Display**: Enhanced user stats showing MMK, referrals, total spins
- **Menu Updates**: Updated all menu items to reflect MMK currency

### Performance Optimizations
- **Batch Logging**: Spin rewards now logged every 5 spins instead of individually
- **Spin Tracking**: Added total spins counter for users
- **Improved Referral Logic**: Optimized referral processing and notifications

### Admin Features
- **Add User Spins**: Admin can distribute bonus spins (1, 5, 10, 20) to users
- **Event Participant Limits**: Events now have configurable participant limits
- **Enhanced Exchange**: Payment method selection (KPay/Wave) with account details

## Development Notes

The application follows a modular design that makes it easy to:
- Add new handler types
- Modify reward systems
- Change storage backends
- Add new admin features
- Integrate additional external services

The JSON-based storage provides simplicity for development and small deployments, while the handler architecture supports easy migration to more robust storage solutions as needed.