from math import pi as PI

from pygame.math import Vector2 as vec


class SecondOrderDynamics:
    """
    https://www.youtube.com/watch?v=KPoeNZZ6H4s&t=810s
    """

    def __init__(self, f: float, z: float, r: float, x0: vec) -> None:
        """
        f: natural frequency of the system [Hz] == [cycles/s]
        z: zeta, damping coefficient (0 => infinite oscillation)
        r: initial response of the system, 2 is typical for mechanical connection
        x0: start position
        """
        # f: response speed of the system and frequency of system vibration
        # z: how the system comes to settles to the target
        #    0 < z < 1 : underdamped
        #        z = 1 : critical damping
        #    1 < z     : no oscillation, slowly settle toward target x
        # r: how much time system needs time to begin accelerate from rest
        #    0 < r     : immediate reaction
        #    1 < r     : system will overshoot the target
        #        r < 0 : system will anticipate the motion (will first move back, than forward)
        #
        # lazy, slow reaction
        #  f = 0.5
        #  z = 1
        #  r = 0
        #
        # delayed a bit, slow
        #  f =  4.86
        #  z =  1
        #  r =  0
        #
        # wavy, slow oscillation before reaching target
        #  f =  0.5
        #  z =  0.15
        #  r =  2
        #
        # wavy, quick oscillation before reaching target
        #  f =  3.8
        #  z =  0.15
        #  r =  2
        #

        # Constants based on dynamics
        self.k1 = z / (PI * f)
        self.k2 = 1 / ((2 * PI * f) ** 2)
        self.k3 = r * z / (2 * PI * f)

        # Initialize variables
        self.xp = x0  # vec(x0)  # previous input
        self.y = x0  # vec(x0)   # state variable
        self.yd = vec(0, 0)  # derivative of state variable

    def reset(self, x0: vec) -> None:
        self.xp = x0
        self.y  = x0

    def update(self, T: float, x: vec, xd: vec | None = None) -> vec:
        """
        get next position

        T: time
        x: current position
        xd: current speed (first derivative of distance)
        """
        # x = vec(x)

        # If velocity is not provided, estimate it
        if xd is None:
            xd = (x - self.xp) / T
            self.xp = x

        # Integrate position by velocity
        self.y += T * self.yd

        # Integrate velocity by acceleration
        self.yd += T * (x + self.k3 * xd - self.y - self.k1 * self.yd) / self.k2

        return self.y


def main():
    f = 0.01  # slow
    z = 0.3  # overshoot
    r = -2.0  # anticipation
    SOD = SecondOrderDynamics(f, z, r, x0=vec(0, 0))
    pos = vec(80, 0)
    # speed = vec(50, 0)
    print(f"{f=} {z=} {r=}")
    print("=" * 100)
    for t in range(1, 500):
        res = SOD.update(t / 500, pos,)
        # pos += res
        x = min(100, int(res[0]))
        x = max(-100, x)
        print(int(res[0]), t / 500, "*" * (x + 100))


if __name__ == "__main__":
    main()
