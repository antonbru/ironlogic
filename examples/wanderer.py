# Wanderer — бродяга. Простой противник: радар на 6 клеток,
# стреляет в упор слева, иначе бродит по полю.
from ironlogic_api import Robot

robot = Robot(
    name="Wanderer",
    front="eye",      # глаз спереди — видим, куда едем
    right="eye",      # глаз справа
    back="eye",       # глаз сзади
    left="cannon",    # пушка слева
    radar=True,       # радар видит недалеко
)

radar_on = False


def on_tick(r):
    global radar_on
    if not radar_on:
        r.radar_on()
        radar_on = True
        return

    target = r.radar("ROBOT", 6)
    if target is not None:
        dist, direction = target
        if direction == "left" and dist <= 1:
            r.shoot("left")          # враг вплотную слева — выстрел!
            return
        if direction == "front":
            if dist <= 1:
                r.turn("right")      # враг вплотную — берём на прицел
            elif r.eye("front") in ("EMPTY", "AMMO"):
                r.move("forward")
            return
        r.turn(direction if direction in ("left", "right") else "left")
        return

    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return
    r.turn("left")
