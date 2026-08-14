# 🤖 Мой первый робот — шаблон IronLogic
# ========================================
# Скопируй в bots/my_robot.py и правь под себя.
# Правила:
#   * robot = Robot(...) — конфигурация железа (обязательно)
#   * on_tick(r) — вызывается каждый такт (обязательно)
#   * одно действие за такт: move / turn / shoot / wait / radar_on / radar_off
#   * сенсоры: r.eye(dir), r.radar(kind, radius), r.health(), r.energy(),
#              r.ammo(), r.tick(), r.facing(), r.pos()
# Направления: "front", "right", "back", "left" (относительно взгляда робота).

from ironlogic_api import Robot

# Железо робота: слоты на каждую сторону.
# "eye" — глаз (видит соседнюю клетку), "cannon" — пушка, "empty" — пусто.
robot = Robot(
    name="МойРобот",
    front="eye",      # глаз спереди — видим, куда едем
    right="eye",      # глаз справа
    back="eye",       # глаз сзади
    left="cannon",    # пушка слева — стреляем влево
    radar=True,       # радар видит врага на расстоянии
)

radar_on = False


def on_tick(r):
    """Поведение робота: вызывается каждый такт."""
    global radar_on

    # 0. Включаем радар один раз в начале боя
    if not radar_on:
        r.radar_on()
        radar_on = True
        return

    # 1. Радар ищет ближайшего врага: (расстояние, направление)
    target = r.radar("ROBOT", 20)
    if target is not None:
        dist, direction = target
        if direction == "left" and dist <= 1:
            # Враг вплотную слева — точный выстрел из пушки!
            r.shoot("left")
            return
        if direction == "front" and dist <= 1:
            # Враг вплотную спереди — поворачиваем и берём его на прицел
            r.turn("right")
            return
        if direction == "front":
            # Враг впереди — едем на него (глаз проверяет дорогу)
            if r.eye("front") in ("EMPTY", "AMMO"):
                r.move("forward")
            else:
                r.turn("right")  # стена или яма — объезжаем
            return
        # Враг сбоку или сзади — доворачиваем его вперёд
        r.turn(direction if direction in ("left", "right") else "left")
        return

    # 2. Врага не видно — едем вперёд, если клетка свободна
    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return

    # 3. Яма или стена — поворачиваем
    if r.eye("front") in ("STONE", "PIT"):
        r.turn("right")
        return

    # 4. Ничего не подходит — ждём
    r.wait()
