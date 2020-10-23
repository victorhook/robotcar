from modes import Modes


class RobotCar:

    def __init__(self):
        self._lights_on = False
        self._honk = False
        self._thrust_m1 = 0
        self._thrust_m2 = 0
        self._velocity = 0
        self._acc = 0
        self._mode = Modes.NORMAL

        self._connected = False
