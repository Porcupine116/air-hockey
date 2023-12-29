import pygame, sys, math, random, os, sqlite3
from pygame.locals import *

pygame.init()

BLACK = pygame.color.THECOLORS["black"]
WHITE = pygame.color.THECOLORS["white"]
RED = pygame.color.THECOLORS["red"]
GREEN = pygame.color.THECOLORS["green"]
BLUE = pygame.color.THECOLORS["blue"]
SCREEN_HEIGTH = 720
SCREEN_WIDTH = 1080

PADDLE_SIZE = 40
PADDLE_SPEED = 100
PADDLE_MASS = 2000

PADDLE1X = 20
PADDLE1Y = SCREEN_HEIGTH / 2

PADDLE2X = SCREEN_WIDTH - 20
PADDLE2Y = SCREEN_HEIGTH / 2

PUCK_SIZE = 30
PUCK_SPEED = 465
PUCK_MASS = 500

GOAL_WIDTH = 180

SCORE_LIMIT = 5
ROUND_LIMIT = 2
FRICTION = 0.998
MAX_SPEED = 1500


class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PADDLE_SIZE
        self.speed = PADDLE_SPEED
        self.mass = PADDLE_MASS
        self.angle = 0

    def check_vertical_bounds(self, height):
        if self.y - self.radius <= 0:
            self.y = self.radius

        elif self.y + self.radius > height:
            self.y = height - self.radius

    def check_left_boundary(self, width):
        if self.x - self.radius <= 0:
            self.x = self.radius

        elif self.x + self.radius > int(width / 2):
            self.x = int(width / 2) - self.radius

    def check_right_boundary(self, width):
        if self.x + self.radius > width:
            self.x = width - self.radius

        elif self.x - self.radius < int(width / 2):
            self.x = int(width / 2) + self.radius

    def move(self, up, down, left, right, time_delta):
        dx, dy = self.x, self.y

        self.x += (right - left) * self.speed * time_delta
        self.y += (down - up) * self.speed * time_delta

        dx = self.x - dx
        dy = self.y - dy

        self.angle = math.atan2(dy, dx)

    def draw(self, screen, color):
        position = (int(self.x), int(self.y))

        pygame.draw.circle(screen, BLACK, position, self.radius, 2)
        pygame.draw.circle(screen, color, position, self.radius - 2, 0)

    def reset(self, start_x, start_y):
        self.x = start_x
        self.y = start_y


class Puck:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PUCK_SIZE
        self.speed = PUCK_SPEED
        self.mass = PUCK_MASS
        self.angle = 0

    def move(self, time_delta):
        self.x += math.sin(self.angle) * self.speed * time_delta
        self.y -= math.cos(self.angle) * self.speed * time_delta

        self.speed *= FRICTION

    def check_boundary(self, width, height):
        if self.x + self.radius > width:
            self.x = 2 * (width - self.radius) - self.x
            self.angle = -self.angle

        elif self.x - self.radius < 0:
            self.x = 2 * self.radius - self.x
            self.angle = -self.angle

        if self.y + self.radius > height:
            self.y = 2 * (height - self.radius) - self.y
            self.angle = math.pi - self.angle

        elif self.y - self.radius < 0:
            self.y = 2 * self.radius - self.y
            self.angle = math.pi - self.angle

    def add_vectors(self, a1, a2):
        x = math.sin(a1[0]) * a1[1] + math.sin(a2[0]) * a2[1]
        y = math.cos(a1[0]) * a1[1] + math.cos(a2[0]) * a2[1]

        length = math.hypot(x, y)
        angle = math.pi / 2 - math.atan2(y, x)
        return angle, length

    def collision_paddle(self, paddle):
        dx = self.x - paddle.x
        dy = self.y - paddle.y

        distance = math.hypot(dx, dy)

        if distance > self.radius + paddle.radius:
            return False

        tangent = math.atan2(dy, dx)
        temp_angle = math.pi / 2 + tangent
        total_mass = self.mass + paddle.mass

        vec_a = (self.angle, self.speed * (self.mass - paddle.mass) / total_mass)
        vec_b = (temp_angle, 2 * paddle.speed * paddle.mass / total_mass)

        (self.angle, self.speed) = self.add_vectors(vec_a, vec_b)
        if self.speed > MAX_SPEED:
            self.speed = MAX_SPEED

        vec_a = (paddle.angle, paddle.speed * (paddle.mass - self.mass) / total_mass)
        vec_b = (temp_angle + math.pi, 2 * self.speed * self.mass / total_mass)

        temp_speed = paddle.speed
        (paddle.angle, paddle.speed) = self.add_vectors(vec_a, vec_b)
        paddle.speed = temp_speed
        offset = 0.5 * (self.radius + paddle.radius - distance + 1)

        self.x += math.sin(temp_angle) * offset
        self.y -= math.cos(temp_angle) * offset

        paddle.x -= math.sin(temp_angle) * offset
        paddle.y += math.cos(temp_angle) * offset
        return True

    def round_reset(self):
        self.y = SCREEN_HEIGTH / 2
        self.x = SCREEN_WIDTH / 2
        self.angle = 0
        self.speed = 0

    def reset(self, speed, player):
        if player == 1:
            self.angle = random.uniform(-math.pi, 0)
            self.x = SCREEN_WIDTH / 2 - 140

        elif player == 2:
            self.angle = random.uniform(0, math.pi)
            self.x = SCREEN_WIDTH / 2 + 140

        self.speed = speed
        self.y = SCREEN_HEIGTH / 2

    def end_reset(self, speed):
        self.angle = 0
        self.speed = speed
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGTH / 2

    def draw(self, screen):
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius)


def input_in_db(player_name):
    db = sqlite3.connect('data/score.db')
    cursor = db.cursor()
    cursor.execute(f"INSERT INTO for_game (winner, score) VALUES('{player_name}', '{score1}:{score2}');")
    db.commit()
    cursor.close()
    db.close()


def output_off_db():
    db = sqlite3.connect('data/score.db')
    cursor = db.cursor()
    result = cursor.execute('SELECT * FROM for_game').fetchall()

    winner = []
    cifarki = []

    if len(result) > 8:
        a = 8
    else:
        a = len(result)

    for i in range(a):
        winner.append(result[i][0])
        cifarki.append(result[i][1])

    cursor.close()
    db.close()
    return winner, cifarki


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def inside_goal(side):
    if side == 0:
        return (puck.x - puck.radius <= 0) and (puck.y >= 180) and (puck.y <= 540)  # red
    if side == 1:
        return (puck.x + puck.radius >= SCREEN_WIDTH) and (puck.y >= 180) and (puck.y <= 540)  # blue


def reset_round():
    puck.round_reset()
    player1.reset(20, SCREEN_HEIGTH / 2)
    player2.reset(SCREEN_WIDTH - 20, SCREEN_HEIGTH / 2)


def score(score1, score2, player_1_name, player_2_name):
    text1 = font.render("{0} : {1}".format(player_1_name, str(score1)), True, BLACK)
    text2 = font.render("{0} : {1}".format(player_2_name, str(score2)), True, BLACK)

    screen.blit(text1, [40, 0])
    screen.blit(text2, [SCREEN_WIDTH - 150, 0])


def main_menu():
    global clock, font, screen, large_font, fon
    pygame.display.set_icon(pygame.image.load(os.path.join('data', 'icon.jpg')))
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGTH), )
    pygame.display.set_caption("Аэрохоккей")
    fon = pygame.transform.scale(load_image('background.jpg'),
                                 (SCREEN_WIDTH, SCREEN_HEIGTH))
    font = pygame.font.SysFont('Arial', 30, bold=True)
    clock = pygame.time.Clock()
    large_font = pygame.font.SysFont('Arial', 60, bold=True)
    game_title = large_font.render("Аэрохоккей", True, BLUE)
    game_title_pos = (int((SCREEN_WIDTH - game_title.get_width()) / 2), 175)
    cursor_img = pygame.Surface((20, 20)).convert()
    cursor_img.set_colorkey(cursor_img.get_at((0, 0)))
    pygame.draw.polygon(cursor_img, RED, [(0, 0), (16, 8), (0, 16)], 0)
    cursor_img_pos = [396, 262]
    menu_choices = ['Играть', 'Счёт', 'Информация', 'Выход']
    for i in range(len(menu_choices)):
        menu_choices[i] = font.render(menu_choices[i], True, BLACK)
    choice = 0
    choices_length = len(menu_choices) - 1
    pygame.mixer.music.load(os.path.join('data/StartScreenBack.mp3'))
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(.03)
    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == K_UP:
                    cursor_img_pos[1] -= 40
                    choice -= 1
                    if choice < 0:
                        choice = choices_length
                        cursor_img_pos[1] = 302
                elif event.key == K_DOWN:
                    cursor_img_pos[1] += 40
                    choice += 1
                    if choice > choices_length:
                        choice = 0
                        cursor_img_pos[1] = 254

                if event.key == K_RETURN:
                    if choice == 0:
                        new_game(screen)
                    if choice == 1:
                        show_score()
                    if choice == 2:
                        show_info()
                    elif choice == 3:
                        return

        screen.blit(fon, (0, 0))
        y = 250
        for menu_choice in menu_choices:
            screen.blit(menu_choice, (431, y))
            y += 40
        screen.blit(game_title, game_title_pos)
        screen.blit(cursor_img, cursor_img_pos)
        pygame.display.flip()


def new_game(screen):
    global player1, player2, puck, score1, score2
    score1, score2 = 0, 0
    pole_image = pygame.transform.scale(load_image('pole.png'),
                                        (SCREEN_WIDTH, SCREEN_HEIGTH))
    screen.blit(pole_image, (0, 0))
    puck = Puck(SCREEN_WIDTH / 2, SCREEN_HEIGTH / 2)
    player1 = Paddle(20, SCREEN_HEIGTH / 2)
    player2 = Paddle(1060, SCREEN_HEIGTH / 2)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        time_delta = clock.get_time() / 1000.0

        k_p = pygame.key.get_pressed()
        w, a, s, d = k_p[K_w], k_p[K_a], k_p[K_s], k_p[K_d]

        up, down, r, l = k_p[K_UP], k_p[K_DOWN], k_p[K_RIGHT], k_p[K_LEFT]

        player1.move(w, s, a, d, time_delta)
        player1.check_vertical_bounds(SCREEN_HEIGTH)
        player1.check_left_boundary(SCREEN_WIDTH)

        player2.move(up, down, l, r, time_delta)
        player2.check_vertical_bounds(SCREEN_HEIGTH)
        player2.check_right_boundary(SCREEN_WIDTH)

        puck.move(time_delta)

        if inside_goal(0):
            score2 += 1
            reset_game(0, 1)  # забили красному

        if inside_goal(1):
            score1 += 1
            reset_game(0, 2)  # забили синему

        puck.check_boundary(SCREEN_WIDTH, SCREEN_HEIGTH)
        puck.collision_paddle(player1)
        puck.collision_paddle(player2)

        if score1 == 5:
            input_in_db("Red")
            score1, score2 = 0, 0
            reset_round()
            game_end('Red')

        if score2 == 5:
            input_in_db("Blue")
            score1, score2 = 0, 0
            reset_round()
            game_end('Blue')

        screen.blit(pole_image, (0, 0))

        score(score1, score2, "Red", "Blue")

        player1.draw(screen, RED)
        player2.draw(screen, BLUE)
        puck.draw(screen)

        pygame.display.flip()


def show_info():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        screen.fill((60, 90, 100))
        game_play = large_font.render('Информация', True, BLACK)
        screen.blit(game_play, (380, 70))

        line = font.render("1. Управление 1 игрока: W, A, S, D.", True, WHITE)
        screen.blit(line, (50, 220))
        line = font.render("2. Управление 2 игрока: вверх, вниз, вправо, влево.", True, WHITE)
        screen.blit(line, (50, 260))
        line = font.render("3. Игра идет до 5 очков", True, WHITE)
        screen.blit(line, (50, 300))
        line = font.render("4. Перезапуск игры на пробел", True, WHITE)
        screen.blit(line, (50, 340))
        line = font.render("5. Веселитесь", True, WHITE)
        screen.blit(line, (50, 380))

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if abs(mouse[0] - SCREEN_WIDTH / 2 - 50) < 120 and abs(mouse[1] - 550) < 40:
            pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH / 2 - 50, 520, 90, 30))
            if click[0] == 1:
                return
        else:
            pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH / 2 - 50, 520, 90, 30))
        back = font.render("BACK", True, BLACK)
        screen.blit(back, (SCREEN_WIDTH / 2 - 40, 525))
        pygame.display.flip()
        clock.tick(10)


def show_score():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        screen.fill((60, 90, 100))

        game_play = large_font.render('Счёт', True, BLACK)

        screen.blit(game_play, (470, 70))

        winner, cifarki = output_off_db()
        for i in range(len(winner)):
            line = font.render(f"{i + 1}. Победитель: {winner[i]}, счёт: {cifarki[i]}", True, WHITE)
            y = i * 40 + 160
            screen.blit(line, (300, y))

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if abs(mouse[0] - SCREEN_WIDTH / 2 - 50) < 120 and abs(mouse[1] - 630) < 40:
            pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH / 2 - 50, 600, 90, 30))
            if click[0] == 1:
                return
        else:
            pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH / 2 - 50, 600, 90, 30))

        back = font.render("BACK", True, BLACK)
        screen.blit(back, (SCREEN_WIDTH / 2 - 40, 605))
        pygame.display.flip()
        clock.tick(10)


def reset_game(speed, player):
    puck.reset(speed, player)
    player1.reset(22, SCREEN_HEIGTH / 2)
    player2.reset(SCREEN_WIDTH - 20, SCREEN_HEIGTH / 2)


def text_obj(text, color):
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()


def disp_text(text, center, color):
    text_surf, text_rect = text_obj(text, color)
    text_rect.center = center
    screen.blit(text_surf, text_rect)


def game_end(player_name):
    while True:

        delay = 0

        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return 1


        if delay == 0:
            disp_text("{0} Победил".format(player_name), (SCREEN_WIDTH / 2, SCREEN_HEIGTH / 2 - 150)
                      , BLACK)

        pygame.display.update()
        clock.tick(10)


if __name__ == "__main__":
    main_menu()