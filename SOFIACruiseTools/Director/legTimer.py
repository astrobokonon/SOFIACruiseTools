
import datetime
import sys
import logging

class LegTimerObj(object):
    """
    Class to hold the leg timer

    Calculates elapsed time, remaining time for the leg,
    as well as handles response to start, stop, and reset buttons
    """

    def __init__(self):
        """Initialize the leg timer."""
        self.logger = logging.getLogger('default')
        self.logger.info('Leg timer object initialized')
        self.status = 'stopped'
        self.duration = None
        self.init_duration = None
        self.remaining = datetime.timedelta()
        self.elapsed = datetime.timedelta()
        self.timer_start = None
        self.flight_parsed = False

    def minute_adjust(self, key):
        adjustment = datetime.timedelta(minutes=1)
        """Add or subtract one minute from timer. 
        
        Parameters
        ----------
        key : ['add', 'sub']
            Determines if one minutes will be added or subtracted.
        """
        if key == 'add':
            self.logger.info('Add one minute to current leg duration')
            self.duration += adjustment
        elif key == 'sub':
            self.logger.info('Subtract one minute from current leg duration')
            self.duration -= adjustment

    def print_state(self):
        """Print status of class variables to screen."""
        print('\nTimer Stats:')
        print('\tStatus = ', self.status)
        print('\tDuration = ', self.duration, ' (', type(self.duration), ')')
        print('\tRemaining = ', self.remaining, ' (', type(self.remaining), ')')
        print('\tElapsed = ', self.elapsed, ' (', type(self.elapsed), ')')

    def control_timer(self, key):
        """Start, stop, or reset the leg control."""
        # Check if a flight plan has been successfully loaded
        if not self.flight_parsed:
            # Leg_dur_from_mis is only set if a flight plan
            # is successfully parsed. If it is still an empty string,
            # don't do anything
            message = 'No flight plan loaded, cannot start leg timer'
            self.logger.warning(message)
            print(message)
            return

        message = 'Changing state of timer from {}'.format(self.status)
        if key == 'start':
            # Start button is pushed
            if self.status == 'running':
                return
            elif self.status == 'stopped':
                self.status = 'running'
                self.timer_start = datetime.datetime.utcnow().replace(microsecond=0)
                self.duration = self.init_duration
            else:
                # Paused
                self.status = 'running'
                self.timer_start = (datetime.datetime.utcnow().replace(
                                    microsecond=0) - self.elapsed)
        elif key == 'stop':
            # Stop button pushed
            if self.status == 'running':
                self.status = 'paused'
        elif key == 'reset':
            # Reset button pushed
            self.status = 'running'
            self.timer_start = datetime.datetime.utcnow().replace(microsecond=0)
            self.duration = self.init_duration
        else:
            # Invalid key
            print('Invalid key for leg control = {0:s}'.format(key))
            return
        self.logger.debug(message + 'to {}'.format(self.status))

    def timer_string(self, mode):
        """Calculate elapsed and remaining time.

        Returns the desired time format, specified by mode
        (either 'remaining' or 'elapsed') in a nicely formatted
        string.

        Parameters
        ----------
        mode : ['remaining', 'elapsed']
            Sets if the remaining time or elapsed time is returned.
        """
        now = datetime.datetime.utcnow().replace(microsecond=0)
        try:
            self.elapsed = now - self.timer_start
            self.remaining = self.duration - self.elapsed
        except TypeError as e:
            self.logger.exception('Exception while calculating time differences')
            print('\n\nTypeError in timer_string:')
            print(e)
            print(type(self.elapsed), type(now), type(self.timer_start))
            print(type(self.remaining), type(self.duration), type(self.elapsed))
            self.print_state()
            sys.exit()
        if mode == 'remaining':
            if self.remaining < datetime.timedelta(0):
                return '-'+clock_string(-self.remaining)
            return clock_string(self.remaining)
        return clock_string(self.elapsed)


def clock_string(clock):
    """ Format timedelta into HH:MM:SS """
    hours = clock.seconds//3600
    minutes = clock.seconds//60 % 60
    seconds = clock.seconds % 60
    return '{0:02d}:{1:02d}:{2:02d}'.format(hours, minutes, seconds)
