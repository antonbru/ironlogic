# Turret — турель. 4 пушки, неподвижен, стреляет по всем сторонам по очереди.
from ironlogic_api import Robot

robot = Robot(
    name="Turret",
    front="cannon",
    right="cannon",
    back="cannon",
    left="cannon",
    radar=False,
)

DIRECTIONS = ["front", "right", "back", "left"]


def on_tick(r):
    r.shoot(DIRECTIONS[r.tick() % 4])