# Hunter — охотник. Радар на 20 клеток: доворачивает врага на прицел
# (справа), стреляет с дистанции до 2, объезжает стены и ямы.
from ironlogic_api import Robot

robot = Robot(
    name="Hunter",
    front="eye",      # глаз спереди — видим, куда едем
    right="cannon",   # пушка справа — прицел
    back="eye",       # глаз сзади
    left="eye",       # глаз слева
    radar=True,       # радар видит врага на расстоянии
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
        if direction == "right" and dist <= 2:
            r.shoot("right")         # враг в прицеле — огонь!
            return
        if direction == "front":
            if dist <= 1:
                r.turn("left")       # враг вплотную — берём на прицел
            elif r.eye("front") in ("EMPTY", "AMMO"):
                r.move("forward")    # враг впереди — едем на него
            else:
                r.turn("right")      # стена или яма — объезжаем
            return
        r.turn(direction if direction in ("left", "right") else "left")
        return

    # Врага не видно — патрулируем
    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return
    r.turn("right")
