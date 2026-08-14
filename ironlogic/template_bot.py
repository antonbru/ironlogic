# 🤖 Мой первый робот — шаблон IronLogic
# ========================================
# Скопируй в bots/my_robot.py и правь под себя.
# Правила:
#   * robot = Robot(...) — конфигурация железа (обязательно)
#   * on_tick(r) — вызывается каждый такт (обязательно)
#   * одно действие за такт: move / turn / shoot / wait / radar_on / radar_off
#   * сенсоры: r.eye(dir), r.radar(kind, radius), r.health(), r.energy(),
#              r.ammo(), r.tick(), r.facing(), r.pos()
# Направления: "front", "right", "back", "left".

from ironlogic_api import Robot

# Железо робота: слоты на каждую сторону.
# "eye" — глаз (видит соседнюю клетку), "cannon" — пушка, "empty" — пусто.
robot = Robot(
    name="МойРобот",
    front="eye",      # глаз спереди
    right="empty",    # пусто справа
    back="eye",       # глаз сзади
    left="cannon",    # пушка слева
    radar=False,      # радар выключен (True — включить)
)


def on_tick(r):
    """Поведение робота: вызывается каждый такт."""
    # 1. Враг прямо по курсу — стреляем!
    if r.eye("front") == "ROBOT":
        r.shoot("front")
        return

    # 2. Перед нами свободно — едем вперёд
    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return

    # 3. Яма или стена — поворачиваем
    if r.eye("front") in ("STONE", "PIT"):
        r.turn("right")
        return

    # 4. Ничего не подходит — ждём
    r.wait()