```python
"""Date and Time Utilities"""

from datetime import datetime, timedelta, date
from typing import Optional, Tuple, Union
import re
import logging

logger = logging.getLogger(__name__)


def parse_flexible_date(date_str: str) -> Optional[datetime]:
    """Parse flexible date input (e.g., 'yesterday', '2 weeks ago', '2023-01-15')"""
    try:
        if not date_str:
            return None
        
        date_str = date_str.strip().lower()
        now = datetime.utcnow()
        
        # Handle relative dates
        if date_str in ['now', 'today']:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_str == 'yesterday':
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_str == 'tomorrow':
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Handle "X days/weeks/months ago"
        ago_match = re.match(r'(\d+)\s+(day|week|month|year)s?\s+ago', date_str)
        if ago_match:
            amount = int(ago_match.group(1))
            unit = ago_match.group(2)
            
            if unit == 'day':
                return (now - timedelta(days=amount)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif unit == 'week':
                return (now - timedelta(weeks=amount)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif unit == 'month':
                # Approximate month as 30 days
                return (now - timedelta(days=amount * 30)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif unit == 'year':
                return (now - timedelta(days=amount * 365)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Handle "last X"
        if date_str.startswith('last '):
            period = date_str[5:]
            if period == 'week':
                return (now - timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'month':
                return (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'year':
                return (now - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Try parsing standard date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%d/%m/%y',
            '%Y%m%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date string: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Date parsing failed for '{date_str}': {e}")
        return None


def format_relative_time(dt: datetime, reference: Optional[datetime] = None) -> str:
    """Format datetime as relative time (e.g., '2 hours ago', 'in 3 days')"""
    try:
        if not dt:
            return "unknown"
        
        if reference is None:
            reference = datetime.utcnow()
        
        # Handle timezone-naive datetime objects
        if dt.tzinfo is None and reference.tzinfo is not None:
            dt = dt.replace(tzinfo=reference.tzinfo)
        elif dt.tzinfo is not None and reference.tzinfo is None:
            reference = reference.replace(tzinfo=dt.tzinfo)
        
        delta = reference - dt
        
        # Future dates
        if delta.total_seconds() < 0:
            delta = dt - reference
            future = True
        else:
            future = False
        
        seconds = int(delta.total_seconds())
        
        if seconds < 60:
            time_str = "just now" if not future else "very soon"
        elif seconds < 3600:  # Less than 1 hour
            minutes = seconds // 60
            unit = "minute" if minutes == 1 else "minutes"
            time_str = f"{minutes} {unit}"
        elif seconds < 86400:  # Less than 1 day
            hours = seconds // 3600
            unit = "hour" if hours == 1 else "hours"
            time_str = f"{hours} {unit}"
        elif seconds < 2592000:  # Less than 30 days
            days = seconds // 86400
            unit = "day" if days == 1 else "days"
            time_str = f"{days} {unit}"
        elif seconds < 31536000:  # Less than 1 year
            months = seconds // 2592000
            unit = "month" if months == 1 else "months"
            time_str = f"{months} {unit}"
        else:
            years = seconds // 31536000
            unit = "year" if years == 1 else "years"
            time_str = f"{years} {unit}"
        
        if future:
            return f"in {time_str}"
        else:
            return f"{time_str} ago"
        
    except Exception as e:
        logger.error(f"Relative time formatting failed: {e}")
        return "unknown"


def get_time_range(period: str) -> Tuple[datetime, datetime]:
    """Get datetime range for common periods (today, this week, this month, etc.)"""
    try:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == 'today':
            start = today
            end = today + timedelta(days=1)
        
        elif period == 'yesterday':
            start = today - timedelta(days=1)
            end = today
        
        elif period == 'this_week':
            # Start of current week (Monday)
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=7)
        
        elif period == 'last_week':
            # Start of last week
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=7)
        
        elif period == 'this_month':
            # Start of current month
            start = today.replace(day=1)
            # First day of next month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        
        elif period == 'last_month':
            # First day of current month
            this_month_start = today.replace(day=1)
            # First day of last month
            if this_month_start.month == 1:
                start = this_month_start.replace(year=this_month_start.year - 1, month=12)
            else:
                start = this_month_start.replace(month=this_month_start.month - 1)
            end = this_month_start
        
        elif period == 'this_year':
            start = today.replace(month=1, day=1)
            end = start.replace(year=start.year + 1)
        
        elif period == 'last_year':
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(month=1, day=1)
        
        elif period.startswith('last_'):
            # Handle last_N_days, last_N_weeks, etc.
            match = re.match(r'last_(\d+)_(day|week|month)s?', period)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'day':
                    start = today - timedelta(days=amount)
                    end = today
                elif unit == 'week':
                    start = today - timedelta(weeks=amount)
                    end = today
                elif unit == 'month':
                    start = today - timedelta(days=amount * 30)  # Approximate
                    end = today
                else:
                    raise ValueError(f"Unknown time unit: {unit}")
            else:
                raise ValueError(f"Could not parse period: {period}")
        
        else:
            raise ValueError(f"Unknown time period: {period}")
        
        return start, end
        
    except Exception as e:
        logger.error(f"Time range calculation failed for '{period}': {e}")
        # Return today as fallback
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return today, today + timedelta(days=1)


def is_business_hours(dt: datetime, start_hour: int = 9, end_hour: int = 17) -> bool:
    """Check if datetime falls within business hours"""
    try:
        if not dt:
            return False
        
        # Check if it's a weekend (Saturday=5, Sunday=6)
        if dt.weekday() >= 5:
            return False
        
        # Check if it's within business hours
        return start_hour <= dt.hour < end_hour
        
    except Exception as e:
        logger.error(f"Business hours check failed: {e}")
        return False


def round_to_nearest_hour(dt: datetime) -> datetime:
    """Round datetime to nearest hour"""
    try:
        if not dt:
            return dt
        
        # Round to nearest hour
        if dt.minute >= 30:
            # Round up
            return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            # Round down
            return dt.replace(minute=0, second=0, microsecond=0)
        
    except Exception as e:
        logger.error(f"Hour rounding failed: {e}")
        return dt


def get_age_in_days(dt: datetime, reference: Optional[datetime] = None) -> int:
    """Get age of datetime in days"""
    try:
        if not dt:
            return 0
        
        if reference is None:
            reference = datetime.utcnow()
        
        delta = reference - dt
        return max(0, int(delta.total_seconds() // 86400))
        
    except Exception as e:
        logger.error(f"Age calculation failed: {e}")
        return 0


def format_duration(seconds: Union[int, float]) -> str:
    """Format duration in seconds to human readable format"""
    try:
        if seconds < 0:
            return "0 seconds"
        
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{minutes} minute{'s' if minutes != 1 else ''} {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
            else:
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours < 24:
            parts = [f"{hours} hour{'s' if hours != 1 else ''}"]
            if remaining_minutes > 0:
                parts.append(f"{remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}")
            return " ".join(parts)
        
        days = hours // 24
        remaining_hours = hours % 24
        
        parts = [f"{days} day{'s' if days != 1 else ''}"]
        if remaining_hours > 0:
            parts.append(f"{remaining_hours} hour{'s' if remaining_hours != 1 else ''}")
        
        return " ".join(parts)
        
    except Exception as e:
        logger.error(f"Duration formatting failed: {e}")
        return "unknown duration"

