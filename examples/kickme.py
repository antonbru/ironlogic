# KickMe — таран. Без пушек: находит врага радаром и едет прямо на него.
from ironlogic_api import Robot

robot = Robot(
    name="KickMe",
    front="eye",      # глаз спереди
    right="eye",      # глаз справа
    back="eye",       # глаз сзади
    left="eye",       # глаз слева
    radar=True,       # радар видит врага
)

radar_on = False


def on_tick(r):
    global radar_on
    if not radar_on:
        r.radar_on()
        radar_on = True
        return

    target = r.radar("ROBOT", 8)
    if target is not None:
        dist, direction = target
        if direction == "front" and r.eye("front") in ("EMPTY", "AMMO"):
            r.move("forward")        # тараним!
            return
        r.turn(direction if direction in ("left", "right") else "left")
        return

    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return
    r.turn("left")
