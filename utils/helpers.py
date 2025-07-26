import logging
from datetime import datetime, timedelta
from database import load_user_data, save_user_data

logger = logging.getLogger(__name__)

def format_datetime(dt_string):
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return dt_string

def validate_telegram_link(url):
    """Validate if URL is a valid Telegram channel link."""
    import re
    pattern = r'^https://t\.me/[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, url))

def get_user_rank(user_id):
    """Get user rank based on points."""
    user_data_dict = load_user_data()
    
    if not user_data_dict:
        return 1, 1
    
    # Convert to list and sort by points
    users = [(uid, data.get('points', 0)) for uid, data in user_data_dict.items()]
    users.sort(key=lambda x: x[1], reverse=True)
    
    total_users = len(users)
    
    for rank, (uid, points) in enumerate(users, 1):
        if str(uid) == str(user_id):
            return rank, total_users
    
    return total_users, total_users

def cleanup_old_history():
    """Clean up old history entries (keep last 30 days)."""
    try:
        user_data_dict = load_user_data()
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for user_id, user_data in user_data_dict.items():
            if 'history' in user_data:
                filtered_history = []
                for entry in user_data['history']:
                    try:
                        entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                        if entry_date > cutoff_date:
                            filtered_history.append(entry)
                    except:
                        # Keep entries with invalid timestamps
                        filtered_history.append(entry)
                
                user_data['history'] = filtered_history
        
        save_user_data(user_data_dict)
        logger.info("Cleaned up old history entries")
        
    except Exception as e:
        logger.error(f"Error cleaning up history: {e}")

def get_top_users(limit=10):
    """Get top users by points."""
    user_data_dict = load_user_data()
    
    if not user_data_dict:
        return []
    
    # Convert to list and sort by points
    users = []
    for uid, data in user_data_dict.items():
        users.append({
            'user_id': uid,
            'username': data.get('username', 'Unknown'),
            'points': data.get('points', 0)
        })
    
    users.sort(key=lambda x: x['points'], reverse=True)
    return users[:limit]

def calculate_daily_stats():
    """Calculate daily statistics."""
    from datetime import date
    
    user_data_dict = load_user_data()
    today = date.today().isoformat()
    
    stats = {
        'total_users': len(user_data_dict),
        'active_today': 0,
        'total_spins_today': 0,
        'total_points_distributed': 0
    }
    
    for user_data in user_data_dict.values():
        stats['total_points_distributed'] += user_data.get('points', 0)
        
        if user_data.get('last_spin_date') == today:
            stats['active_today'] += 1
            stats['total_spins_today'] += user_data.get('spins_today', 0)
    
    return stats
