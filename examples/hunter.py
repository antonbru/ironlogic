# Hunter — охотник. Радар ищет врага, едет к нему, стреляет, уходит от ям.
from ironlogic_api import Robot

robot = Robot(name="Hunter", front="cannon", right="eye", back="eye", left="eye", radar=True)

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
        if direction == "front":
            # Враг прямо по курсу — стреляем
            r.shoot("front")
            return
        # Враг сбоку/сзади — поворачиваем в его сторону
        r.turn(direction)
        return
    # Нет цели — блуждаем и избегаем ям
    if r.eye("front") == "STONE":
        r.turn("right")
        return
    if r.eye("front") == "PIT":
        r.turn("left")
        return
    r.move("forward")