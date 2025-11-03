"""
Alert Queue Service

In-memory queue for managing alerts sent via SSE.
Thread-safe implementation for concurrent access.
"""
import threading
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class AlertQueue:
    """
    Thread-safe in-memory queue for alerts.
    
    Features:
    - Add alerts from any thread
    - Retrieve pending alerts (consumed on read)
    - Keep 24-hour history
    - Automatic cleanup of old alerts
    """
    
    def __init__(self, history_hours: int = 24):
        """
        Initialize alert queue.
        
        Args:
            history_hours: How long to keep alert history
        """
        self._pending = deque()  # Alerts waiting to be sent
        self._history = deque(maxlen=1000)  # Last 1000 alerts
        self._lock = threading.Lock()
        self._history_hours = history_hours
        
        logger.info(f"✅ AlertQueue initialized (history={history_hours}h)")
    
    def add(self, alert: Dict[str, Any]) -> None:
        """
        Add alert to queue.
        
        Args:
            alert: Alert dictionary with type, severity, etc.
        """
        with self._lock:
            # Ensure timestamp
            if 'timestamp' not in alert:
                alert['timestamp'] = datetime.utcnow().isoformat()
            
            # Add to pending queue
            self._pending.append(alert)
            
            # Add to history
            self._history.append(alert.copy())
            
            logger.info(f"➕ Alert added: {alert.get('type')} (pending={len(self._pending)})")
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """
        Get all pending alerts and clear the queue.
        
        This is called by the SSE endpoint every few seconds.
        
        Returns:
            List of pending alerts (queue is cleared after retrieval)
        """
        with self._lock:
            if not self._pending:
                return []
            
            # Get all pending alerts
            alerts = list(self._pending)
            
            # Clear pending queue
            self._pending.clear()
            
            logger.debug(f"📤 Retrieved {len(alerts)} pending alerts")
            
            return alerts
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent alert history (non-destructive).
        
        Args:
            limit: Max number of alerts to return
            
        Returns:
            List of recent alerts (newest first)
        """
        with self._lock:
            # Clean old alerts first
            self._cleanup_history()
            
            # Return most recent alerts
            history = list(self._history)
            history.reverse()  # Newest first
            
            return history[:limit]
    
    def clear(self) -> None:
        """
        Clear all pending alerts (for demo reset).
        
        History is preserved.
        """
        with self._lock:
            count = len(self._pending)
            self._pending.clear()
            
            logger.info(f"🗑️ Cleared {count} pending alerts")
    
    def clear_all(self) -> None:
        """
        Clear everything including history.
        """
        with self._lock:
            self._pending.clear()
            self._history.clear()
            
            logger.info("🗑️ Cleared all alerts (pending + history)")
    
    def _cleanup_history(self) -> None:
        """
        Remove alerts older than history_hours.
        
        Called automatically when getting history.
        """
        cutoff = datetime.utcnow() - timedelta(hours=self._history_hours)
        
        # Count alerts to remove
        to_remove = 0
        for alert in self._history:
            timestamp_str = alert.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if timestamp < cutoff:
                        to_remove += 1
                    else:
                        break  # Deque is ordered, so we can stop
                except:
                    pass
        
        # Remove old alerts
        for _ in range(to_remove):
            self._history.popleft()
        
        if to_remove > 0:
            logger.debug(f"🗑️ Cleaned up {to_remove} old alerts")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dict with pending count, history count, etc.
        """
        with self._lock:
            return {
                "pending_count": len(self._pending),
                "history_count": len(self._history),
                "history_hours": self._history_hours,
                "timestamp": datetime.utcnow().isoformat()
            }