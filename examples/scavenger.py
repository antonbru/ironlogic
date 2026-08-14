# Scavenger — сборщик. Собирает патроны, стоит на розетках, избегает ям.
from ironlogic_api import Robot

robot = Robot(
    name="Scavenger",
    front="eye",
    right="cannon",
    back="eye",
    left="eye",
    radar=False,
)

# Запоминаем, куда идём: True — ищем патроны, False — ищем розетку
seek_ammo = True


def on_tick(r):
    global seek_ammo

    # Уже стоим на розетке — отдыхаем и заряжаемся
    if r.eye("front") != "RECHARGE" and r.tick() > 0:
        # Проверяем текущую клетку: если мы на RECHARGE, просто ждём
        pass

    target_kind = "AMMO" if seek_ammo else "RECHARGE"
    found = r.eye("front")
    if found in (target_kind, "EMPTY"):
        r.move("forward")
        return
    if found == "PIT" or found == "STONE":
        r.turn("right")
        return
    # Патроны кончились или полные — сменить цель
    if r.ammo() <= 2:
        seek_ammo = True
    elif r.ammo() >= 18:
        seek_ammo = False
    r.wait()

# TODO: полная реализация охоты за патронами/розетками через сенсоры в Фазе 2