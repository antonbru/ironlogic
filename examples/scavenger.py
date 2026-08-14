# Scavenger — сборщик. Собирает патроны и заряжается на розетках,
# а если враг подобрался вплотную — защищается из пушки справа.
from ironlogic_api import Robot

robot = Robot(
    name="Scavenger",
    front="eye",      # глаз спереди
    right="cannon",   # пушка справа — защита
    back="eye",       # глаз сзади
    left="eye",       # глаз слева
    radar=True,       # радар ищет и врага, и припасы
)

radar_on = False


def on_tick(r):
    global radar_on
    if not radar_on:
        r.radar_on()
        radar_on = True
        return

    # Оборона: враг вплотную справа — стреляем, спереди — берём на прицел.
    enemy = r.radar("ROBOT", 6)
    if enemy is not None:
        dist, direction = enemy
        if direction == "right" and dist <= 1:
            r.shoot("right")
            return
        if direction == "front" and dist <= 1:
            r.turn("left")           # враг окажется справа
            return

    # Сбор: пока патронов мало — ищем ящики, потом — розетку.
    kind = "AMMO" if r.ammo() <= 10 else "RECHARGE"
    supply = r.radar(kind, 20)
    if supply is not None:
        dist, direction = supply
        if direction == "front":
            if r.eye("front") in ("EMPTY", "AMMO", "RECHARGE"):
                r.move("forward")
            else:
                r.turn("right")
            return
        r.turn(direction if direction in ("left", "right") else "left")
        return

    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return
    r.turn("right")
