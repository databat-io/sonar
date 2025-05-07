from datetime import datetime, timedelta

# Constants for session management
MIN_RSSI_SAMPLES = 2  # Minimum number of RSSI samples needed for trend analysis
MAX_RSSI_DIFF = 10  # Maximum RSSI difference to consider devices as the same
MIN_RSSI_DIFF = 5  # Minimum RSSI difference to consider devices as different
MAX_SAMPLES = 10  # Maximum number of RSSI samples to keep

class DeviceSession:
    """Represents a continuous session for a device."""
    def __init__(self, fingerprint: str, start_time: datetime, initial_rssi: int) -> None:
        self.fingerprint = fingerprint
        self.start_time = start_time
        self.last_seen = start_time
        self.rssi_samples: list[int] = [initial_rssi]
        self.is_active = True

    def update(self, current_time: datetime, rssi: int) -> None:
        """Update session with new timestamp and RSSI value."""
        self.last_seen = current_time
        self.rssi_samples.append(rssi)
        # Keep only last samples
        if len(self.rssi_samples) > MAX_SAMPLES:
            self.rssi_samples.pop(0)

    def get_dwell_time(self) -> float:
        """Calculate dwell time in seconds."""
        return (self.last_seen - self.start_time).total_seconds()

    def get_rssi_trend(self) -> str | None:
        """Determine RSSI trend based on samples."""
        if len(self.rssi_samples) < MIN_RSSI_SAMPLES:
            return None

        # Calculate average RSSI for first and last half of samples
        mid_point = len(self.rssi_samples) // 2
        first_half_avg = sum(self.rssi_samples[:mid_point]) / mid_point
        second_half_avg = sum(self.rssi_samples[mid_point:]) / (len(self.rssi_samples) - mid_point)

        diff = second_half_avg - first_half_avg
        if abs(diff) < MIN_RSSI_DIFF:
            return "stable"
        return "increasing" if diff > 0 else "decreasing"

class SessionManager:
    """Manages device sessions and handles MAC randomization."""
    def __init__(self) -> None:
        self.sessions: dict[str, DeviceSession] = {}
        self.session_timeout = timedelta(minutes=5)

    def update_session(self, fingerprint: str, current_time: datetime, rssi: int) -> None:
        """Update or create a session for a device."""
        if fingerprint in self.sessions:
            session = self.sessions[fingerprint]
            if (current_time - session.last_seen) <= self.session_timeout:
                session.update(current_time, rssi)
            else:
                # Create new session if timeout exceeded
                self.sessions[fingerprint] = DeviceSession(fingerprint, current_time, rssi)
        else:
            # Check for potential MAC rotation
            matching_session = self._find_potential_match(fingerprint, current_time, rssi)
            if matching_session:
                matching_session.update(current_time, rssi)
                self.sessions[fingerprint] = matching_session
            else:
                self.sessions[fingerprint] = DeviceSession(fingerprint, current_time, rssi)

    def _find_potential_match(self, fingerprint: str, current_time: datetime, rssi: int) -> DeviceSession | None:
        """Find a potential match for a device that may have rotated its MAC address."""
        for session in self.sessions.values():
            if not session.is_active:
                continue
            if (current_time - session.last_seen) <= self.session_timeout:
                # Check RSSI trend and difference
                if session.get_rssi_trend() == "increasing" and abs(rssi - session.rssi_samples[-1]) <= MAX_RSSI_DIFF:
                    return session
        return None

    def cleanup_old_sessions(self, current_time: datetime) -> None:
        """Remove sessions that have timed out."""
        expired_sessions = [
            fp for fp, session in self.sessions.items()
            if (current_time - session.last_seen) > self.session_timeout
        ]
        for fp in expired_sessions:
            del self.sessions[fp]

    def get_session_stats(self) -> dict[str, float]:
        """Get current session statistics."""
        active_sessions = [s for s in self.sessions.values() if s.is_active]
        if not active_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_dwell_time": 0
            }

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "average_dwell_time": sum(s.get_dwell_time() for s in active_sessions) / len(active_sessions)
        }