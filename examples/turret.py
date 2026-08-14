# Turret — турель. Неподвижна (4 пушки), радар видит всё поле,
# доворачивается к врагу и стреляет в упор из пушки в его сторону.
from ironlogic_api import Robot

robot = Robot(
    name="Turret",
    front="cannon",
    right="cannon",
    back="cannon",
    left="cannon",
    radar=True,
)

radar_on = False


def on_tick(r):
    global radar_on
    if not radar_on:
        r.radar_on()
        radar_on = True
        return

    target = r.radar("ROBOT", 20)
    if target is not None:
        dist, direction = target
        if dist <= 1:
            r.shoot(direction)       # враг вплотную — стреляем в его сторону!
            return
        if direction == "front":
            r.wait()                 # ждём, пока враг подойдёт
            return
        r.turn(direction if direction in ("left", "right") else "left")
        return

    r.turn("left")
