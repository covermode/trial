# ----------------------------- Autor: Ilya Latypov ---------------------------
# +++          TRIAL: pygame project
#

import pygame as pg
import os
import abc
from random import randint


# DAY1:     Created base, don't tested.
# DAY2:     Manage drawing, start working on UserInput, make player
# DAY3:     Make animation_class, start working on a float-pos problem
# DAY4:     Solve a float-pos problem, add screen motion, make stable build of preview
# DAY5:TODO Create a cube.


def perform(func, *args, **kwargs):
    """Вспомогательная функция. При выполнении возвращаемой функции указанные аргументы
    будут подставлены вместо переданных при вызове. Создана для следующей функции"""
    def f(*_, **__):
        nonlocal func, args, kwargs
        func(*args, **kwargs)
    return f


def concat(*funcs):
    """Вспомогательная функция. При выполнении возвращаемой функции будут последовательно
    выполнены все функции, переданные в качестве аргумента. Аргументы в вызываемые функции
    ставиться не будут. (пользоваться perform)"""
    return lambda *_: [i() for i in funcs]


def load_image(name, chr_key=None) -> pg.Surface:
    """Загрузить изображение из папки data с указанным именем и конвертировать"""
    fullname = os.path.join('data', name)
    image = pg.image.load(fullname).convert()

    if chr_key is not None:
        if chr_key == -1:
            chr_key = image.get_at((0, 0))
        image.set_colorkey(chr_key)
    else:
        image = image.convert_alpha()
    return image


def load_data():
    """Загрузка всех файлов игры"""
    global IMG
    IMG["empty"] = load_image("empty.png")
    IMG["wall"] = load_image("wall.png")
    IMG["player"] = load_image("player.png", -1)
    IMG["default"] = load_image("default.png", -1)
    IMG["button"] = load_image("button.png")
    IMG["door_open"] = load_image("door_open.png")
    IMG["door_closed"] = load_image("door_closed.png")


IMG = {}            # Словарь, содержащий загруженные изображения
me = None           # Будущий Объект GMain. Хранится для доступа без передачи в качестве аргумента
action_socket = {}  # Хранилище логических ячеек, нужен для указания того, может ли GAction выполниться сейчас


#  CONSTS --------------------
FIELD_SIZE = FIELD_WIDTH, FIELD_HEIGHT = 10, 10
CELL_SIZE = 50                          # Position = center
DEFAULT_IMAGE = "default"


# \CONSTS --------------------


class GMachine(metaclass=abc.ABCMeta):
    """
    Абстрактный класс игровой машины. Представлен следующей структурой:
        [START] -> ([HANDLE_INPUT] -> [MANAGE_CYCLE]) -> [QUIT].
    От него наследуются состояния игры (запущен уровень/находимся в меню/...)"""
    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def quit(self):
        pass

    @abc.abstractmethod
    def handle_input(self):
        """Функция, которая обрабатывает действия пользователя и вызывает необходимые функции."""
        pass

    @abc.abstractmethod
    def manage_cycle(self):
        """Функция, которая очищает очередь и обновляет графику."""
        pass
    
    def main(self):
        self.start()
        self.exit_code = -1
        while self.exit_code == -1:
            self.handle_input()
            self.manage_cycle()
        self.quit()
        return self.exit_code


class GSprite(pg.sprite.Sprite):
    """Наследование класса спрайта. Создан, в основном, для удобства, а также решения проблемы
    нецелых координат"""
    def __init__(self, rectf=None, image=None, groups=()):
        super(GSprite, self).__init__(*groups)
        self.image = image if image is not None else IMG[DEFAULT_IMAGE]
        self.image: pg.Surface
        self.ident = str(randint(100, 100000000000))
        if rectf is None:
            self.rectf = self.image.get_rect()
        else:
            pg.transform.scale(self.image, rectf[2:4])
            self.rectf = rectf
        self.commit()

    def move(self, dx, dy):     # Передвинуть на dx dy
        self.rectf[0] += dx
        self.rectf[1] += dy
        self.commit()

    def stand(self, nx, ny):    # Поместить в nx ny
        self.rectf[0] = nx
        self.rectf[1] = ny
        self.commit()

    def scale(self, nw, nh, image_scale=False):     # Установить размер
        self.rectf[2] = nw
        self.rectf[3] = nh
        if image_scale:
            pg.transform.scale(self.image, (nw, nh))
        self.commit()

    def pos(self):
        return self.rectf[0], self.rectf[1]

    def size(self):
        return self.rectf[2], self.rectf[3]

    def commit(self):                               # Перевод нецелых координат в целые. Вызывается
        self.rect = pg.Rect(int(self.rectf[0]),     # после любого изменения объекта
                            int(self.rectf[1]),
                            int(self.rectf[2]),
                            int(self.rectf[3]))


class GAction:
    """Класс запрограммированного действия. В зависимости от значения в action_socket
    может выполниться или нет. Если выполнился, то без изменения значения в ячейке более не запустится."""
    def __init__(self, socket_name: str, action):
        self.socket = socket_name
        if socket_name not in action_socket:
            action_socket[socket_name] = False
        assert callable(action)
        self.action = action

    def __call__(self, *args, **kwargs):
        if not action_socket[self.socket]:
            action_socket[self.socket] = True
            self.action(*args, **kwargs)

    def socket_receive(self):
        action_socket[self.socket] = False

    exec = __call__


class GAnimation(GAction):
    """Класс анимации. Является долгосрочным вариантом GAction. Делает работу в течении
    dur циклов, после чего освобождает свой сокет. На каждом цикле вызывает функцию do.
    Сам цикл выполняется вместе с циклом машины, и будет помещаться в очередь, пока
    не пройдет dur циклов. При окончании вызывает функцию on_end.
    Сам по себе является абстрактным, и в коде в чистом виде быть не должен."""
    def __init__(self, dur: int, socket_name: str, on_end):
        super(GAnimation, self).__init__(socket_name, self.start)
        self.dur = dur
        self.time = 0
        self.on_end = on_end

    @abc.abstractmethod
    def do(self):
        pass

    def cycle(self):
        self.time += 1
        self.do()
        if self.time < self.dur:
            me.queue.append(self.cycle)
        else:
            action_socket[self.socket] = False
            self.on_end()

    def start(self):
        me.queue.append(self.cycle)


class GSpriteMoveAnimation(GAnimation):
    """Специализированный класс анимации для плавного передвижения спрайта target по экрану"""
    def __init__(self, target: GSprite, dx, dy, dur: int, on_end=lambda: None):
        super(GSpriteMoveAnimation, self).__init__(dur, "MOVE_ANIMATION-GS{}".format(str(target.ident)), on_end)
        self.tar = target
        self.dx = dx / dur
        self.dy = dy / dur

    def do(self):
        self.tar.move(self.dx, self.dy)


class GSpriteFadeAnimation(GAnimation):
    """Экспериментальный и непроверенный класс анимации плавного изменения изображения спрайта"""
    def __init__(self, target: GSprite, new_image: pg.Surface, dur: int, on_end=lambda: None):
        super(GSpriteFadeAnimation, self).__init__(dur, "FADE_ANIMATION-GS{}".format(str(target.ident)), on_end)
        self.tar = target
        self.new = new_image
        self.src = self.tar.image
        self.new.set_alpha(0)
        self.st1 = target.image.get_alpha()
        self.dt1 = -self.st1 / dur
        self.st2 = 0
        self.dt2 = 100 / dur

    def do(self):
        self.st1 += self.dt1
        self.st2 += self.dt2
        self.src.set_alpha(int(self.st1))
        self.new.set_alpha(int(self.st2))
        im = self.src
        im.blit(self.new, special_flags=pg.BLEND_ADD)
        self.tar.image = im


class GCamera:
    """Класс камеры. По умолчанию наблюдает за игроком"""
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj: GSprite):
        obj.move(self.dx, self.dy)

    def update(self, target: GSprite, screen_size):
        x, y = target.pos()
        w, h = target.size()
        self.dx = -(x + w // 2 - screen_size[0] // 2)
        self.dy = -(y + h // 2 - screen_size[1] // 2)


class Cell(GSprite):
    """Класс клетки клетчатого поля. Является в некотором роде абстрактным и
    явно использоваться не должен. Имеет словарь свойств (используются игрой) и
    массив connect. Он используется для коммуникации м-у клетками. Для отправки сигнала
    всем клеткам используется send(), при получении вызывается receive(). Остальные
    функции вызываются игрой"""
    def __init__(self, image=None):
        super(Cell, self).__init__(image=image)
        self.params = {
            "walkable": True,
        }
        self.connect = []
        self.field = None
        self.pos = None

    def setup(self, field, self_pos):
        field: Field
        self.field = field
        self.pos = self_pos
        self.add(*self.field.mt_groups)

    def send(self):
        for c in self.connect:
            c.on_receive()

    def on_stand(self):
        pass

    def on_activation(self):
        pass

    def on_receive(self):
        pass


def GetCell(char: str):
    """Функция перекодировки символа в класс клетки. Используется при чтении и интерпретации файла уровня
    в текстовом виде"""
    return {
        " ": EmptyCell(),
        "*": WallCell(),
        "B": EButtonCell(),
        "d": DoorCell(False),
        "D": DoorCell(True),
    }[char]


class EmptyCell(Cell):      # Класс пустой клетки (по ней можно ходить)
    def __init__(self):
        super(EmptyCell, self).__init__(IMG["empty"])


class WallCell(Cell):       # Класс клетки стены (в этой версии она цвета фона)
    def __init__(self):
        super(WallCell, self).__init__(IMG["default"])
        self.params["walkable"] = False


class EButtonCell(Cell):    # Класс клетки, встав на которую и нажав английскую E что-то произойдет
    def __init__(self):
        super(EButtonCell, self).__init__(IMG["button"])

    def on_activation(self):
        self.send()


class DoorCell(Cell):       # Класс клетки двери, которая меняет свое состояние при получении сигнала
    def __init__(self, closed=True):
        if closed:
            super(DoorCell, self).__init__(IMG["door_closed"])
        else:
            super(DoorCell, self).__init__(IMG["door_open"])
        self.params["walkable"] = False
        self.open = False

    def on_receive(self):
        print("got it!")
        self.open = not self.open

        self.params["walkable"] = self.open
        if self.open:
            self.image = IMG["door_open"]
        else:
            self.image = IMG["door_closed"]


class Field(GSprite):
    """Класс игрвого клетчатого поля. Реализует расстоновку клеток, также вычислению
    абсолютной позиции предмета в клетке, также генерацию уровня из текстового файла
    """
    def __init__(self, matrix=None, groups=()):
        super(Field, self).__init__(rectf=None, image=None, groups=groups)
        self.mt_groups = groups
        if matrix is None:
            log("Init without matrix", "__init__", "field")
            self.mt = [[EmptyCell() for i in range(FIELD_WIDTH)] for k in range(FIELD_HEIGHT)]
            log("Matrix creation ended.", "__init__", "field")
        else:
            log("Init with matrix", "__init__", "field")
            self.mt = matrix
            for y, row in enumerate(self.mt):
                for x, item in enumerate(row):
                    item.image = pg.transform.scale(item.image, (CELL_SIZE, CELL_SIZE))
                    item.setup(self, (x, y))
            log("Matrix check and transform ended.", "__init__", "field")

        self.size = self.width, self.height = len(self.mt), len(self.mt[0])
        self.scale(self.width * CELL_SIZE, self.height * CELL_SIZE)

    def set_view(self, pos):
        log("Replacing my view...", "set_view", "field")
        self.stand(*pos)

    def draw_cells(self):
        for r, row in enumerate(self.mt):
            for c, item in enumerate(row):
                item.stand(*self.place((c, r)))

    def place(self, point):
        x, y = self.pos()
        return x + point[0] * CELL_SIZE, y + point[1] * CELL_SIZE

    @staticmethod
    def Load(file_name, *groups):
        """Интерпретирует текстовый вид уровня в сам уровень с помощью имеющегося синтаксиса
        TODO документация по синтаксису"""
        inp = open(file_name, "r").read().split("\n\n")

        mt = [[GetCell(c) for c in row] for row in inp[0].split("\n")]
        for con in inp[1].split("\n"):
            points = [tuple(map(int, i.split(","))) for i in con.split(" ")]
            for p in range(1, len(points)):
                mt[points[0][0]][points[0][1]].connect.append(mt[points[p][0]][points[p][1]])

        return Field(mt, *groups)


class Player(GSprite):
    """Класс игрока, как объекта, наделенного способностью красиво (анимированно) ходить по полю"""
    def __init__(self, field, field_pos, *groups):
        super(Player, self).__init__(rectf=[0, 0, CELL_SIZE, CELL_SIZE], image=IMG["player"], groups=groups)
        self.field = field
        self.field_pos = self.r, self.c = field_pos

    def change_cell(self, dr, dc):
        nr = self.r + dr
        nc = self.c + dc
        nx, ny = self.field.place((nc, nr))
        if self.field.mt[nr][nc].params["walkable"]:
            act = GAction("PLAYER_WALK".format(str(nr), str(nc)), lambda: None)
            # Создается экземпляр GAction с пустой функцией
            act.action = concat(GSpriteMoveAnimation(self, nx - self.pos()[0], ny - self.pos()[1],
                                                     5, on_end=act.socket_receive).exec,
                                perform(self.set_field_pos, nr, nc))
            # Пустая функция заменяется на:
            #   1) Запустить анимацию, после окончания очистить сокет "PLAYER_WALK"
            #   2) Сменить фактическое положение персонажа на клетчатом поле
            act.exec()

    def set_field_pos(self, nr, nc):    # Присвоение позиции на поле
        self.field_pos = self.r, self.c = nr, nc


class GMain(GMachine):
    """Класс Main, занимающийся исполнением уровней. Пока игра содержит лишь один уровень
    - вызывается по умолчанию. Содержит очередь функций, счетчик цикла, а также группы спрайтов"""
    def __init__(self, *args):
        self.exit_code = 1
        self.g_cycle = 0
        self.args = args
        self.queue = []
        self.all_sprites = pg.sprite.Group()
        self.player_group = pg.sprite.Group()
        self.cell_group = pg.sprite.Group()

    def start(self):
        log("Started starting up...", "Start machine", "main")
        pg.init()
        self.window_size = self.window_width, self.window_height = 1280, 720

        # self.screen = pg.display.set_mode(self.window_size, pg.FULLSCREEN)
        self.screen = pg.display.set_mode(self.window_size)
        load_data()

        self.field = Field.Load(r"C:\Olymp\yandee\PROJECT_BOX\Trial\data\testlevel.txt",
                                (self.all_sprites, self.cell_group))
        self.field.set_view(((self.window_width - CELL_SIZE * self.field.width) // 2,
                             (self.window_height - CELL_SIZE * self.field.height) // 2))
        self.camera = GCamera()
        self.player = Player(self.field, (5, 2), self.all_sprites)
        self.player.stand(*self.field.place((self.player.c, self.player.r)))

        self.clock = pg.time.Clock()
        log("Successfully started up", "Start machine", "main")

    def quit(self):
        log("Started quiting...", "Quit machine", "main")
        pg.quit()
        log("Successfully quited", "Quit machine", "main")

    def handle_input(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                log("Exit_button pressed", "Cycle {}".format(str(self.g_cycle)), "main")
                self.exit_code = 0
            if event.type == pg.MOUSEBUTTONDOWN:
                log(event)
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.player.change_cell(-1, 0)
                elif event.key == pg.K_LEFT:
                    self.player.change_cell(0, -1)
                elif event.key == pg.K_DOWN:
                    self.player.change_cell(1, 0)
                elif event.key == pg.K_RIGHT:
                    self.player.change_cell(0, 1)
                elif event.key == pg.K_e:
                    r, c = self.player.field_pos
                    self.field.mt[int(r)][int(c)].on_activation()

    def manage_cycle(self):
        self.g_cycle += 1

        _ = self.queue.copy()
        while len(_) > 0:
            # print(_)
            _.pop(0)()
            self.queue.pop(0)

        # noinspection PyArgumentList
        pg.draw.rect(self.screen, pg.Color(1, 5, 14), pg.Rect(0, 0, self.window_width, self.window_height))
        self.camera.update(self.player, self.window_size)
        self.camera.apply(self.player)
        self.camera.apply(self.field)
        self.field.draw_cells()
        self.all_sprites.draw(self.screen)
        pg.display.flip()
        self.clock.tick(60)


def log(mes, sender=None, father=None, say=print):
    if father is not None:
        if sender is None:
            sender = str(father).upper()
        else:
            sender = "{}/{}".format(str(father).upper(), str(sender))
    if sender is not None:
        mes = "[{}] ".format(str(sender)) + mes
    say(mes)


def main(*args):
    global me
    me = GMain(*args)
    return me.main()


if __name__ == "__main__":
    import sys
    sys.exit(main(*sys.argv))
