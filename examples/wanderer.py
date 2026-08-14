# Wanderer — бродяга. Едет вперёд, при препятствии поворачивает,
# стреляет во врага перед собой.
from ironlogic_api import Robot

robot = Robot(name="Wanderer", front="eye", right="empty", back="eye", left="cannon")


def on_tick(r):
    if r.eye("front") == "ROBOT":
        r.shoot("front")
        return
    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return
    r.turn("left")