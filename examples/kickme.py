# KickMe — «болван». Просто стоит и ждёт, пока его победят.
from ironlogic_api import Robot

robot = Robot(name="KickMe", front="eye", right="empty", back="empty", left="empty")


def on_tick(r):
    r.wait()