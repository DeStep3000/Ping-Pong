import pygame
import sys
import random
import math
import os

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 550
PADDLE_WIDTH = 13
PADDLE_HEIGHT = 90
BALL_SPEED = 7
BALL_RADIUS = 10
PLAYER_SPEED = 320
ENEMY_SPEED = 300
GAP = 20

#         R    G    B
BLACK = (0, 0, 0)
WHITE = (255, 251, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
PADDLE_SIZE = (PADDLE_WIDTH, PADDLE_HEIGHT)
BGCOLOR = BLACK
PLAYER_SIDE = 'left'
TOP_SCORE = 5
COUNTDOWN = 3
FPS = 45
screen_size = (700, 550)
clock = pygame.time.Clock()
screen = pygame.display.set_mode(screen_size)


def terminate():
    pygame.quit()
    sys.exit


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    if color_key is not None:
        if color_key is -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


def start_screen():
    fon = pygame.transform.scale(load_image('zastavka_0.jpg'), screen_size)
    screen.blit(fon, (0, 0))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


class Text(object):

    def __init__(self, value, size, color,
                 left_orientation=False,
                 font=None,
                 x=0, y=0,
                 top=None, bottom=None, left=None, right=None,
                 centerx=None, centery=None):

        self._size = size
        self._color = color
        self._value = value
        self._font = pygame.font.Font(font, self._size)
        self.width, self.height = self._font.size(self._value)
        self._left_orientation = left_orientation

        self.image = self._create_surface()
        self.rect = self.image.get_rect()
        if x: self.rect.x = x
        if y: self.rect.y = y
        if top: self.rect.top = top
        if bottom: self.rect.bottom = bottom
        if left: self.rect.left = left
        if right: self.rect.right = right
        if centerx: self.rect.centerx = centerx
        if centery: self.rect.centery = centery

    def _create_surface(self):
        return self._font.render(self._value, True, self._color)

    def set_value(self, new_value):
        if new_value != self._value:
            self._value = new_value
            self.image = self._create_surface()

            new_rect = self.image.get_rect(x=self.rect.x, y=self.rect.y)
            if self._left_orientation:
                width_diff = new_rect.width - self.rect.width
                new_rect.x = self.rect.x - width_diff
            self.rect = new_rect


class Ball(pygame.sprite.Sprite):

    def __init__(self, game, vector):
        super(Ball, self).__init__()

        self.image = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2))
        self.rect = self.image.get_rect()
        self._draw_ball()

        screen = pygame.display.get_surface()
        self.area = screen.get_rect().inflate(-GAP * 2, 0)

        self.vector = vector
        self.game = game
        self.start_to_the = 'left'
        self.reinit()

    def _draw_ball(self):
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        pygame.draw.circle(self.image, WHITE, (self.rect.centerx, self.rect.centery), BALL_RADIUS)

    def reinit(self):
        self.rect.centerx = self.area.centerx
        self.rect.centery = self.area.centery

        if self.start_to_the == 'left':
            self.vector = Vec2D(-BALL_SPEED, 0)
        else:
            self.vector = Vec2D(BALL_SPEED, 0)

    def update(self, dt):
        self.rect = self.calcnewpos(dt)
        self.handle_collision()

    def calcnewpos(self, dt):
        (dx, dy) = self.vector.get_xy()
        return self.rect.move(dx, dy)

    def handle_collision(self):
        (dx, dy) = self.vector.get_xy()

        if not self.area.contains(self.rect):
            if self._hit_topbottom():
                dy = -dy

            elif self._hit_leftright():
                side = self._hit_leftright()
                self.game.increase_score(side)

                if side == 'left':
                    self.start_to_the = 'right'
                elif side == 'right':
                    self.start_to_the = 'left'

                self.reinit()
                return
        else:
            if self.hit_paddle():
                paddle = self.hit_paddle()
                if paddle.side == 'left':
                    self.rect.left = GAP + PADDLE_WIDTH
                elif paddle.side == 'right':
                    self.rect.right = SCREEN_WIDTH - (GAP + PADDLE_WIDTH)
                dx = -dx

                dy = (self.rect.centery - paddle.rect.centery)
                if dy <= -32:
                    dy = -32
                elif -32 < dy <= -16:
                    dy = -16
                elif -16 < dy < 16:
                    dy = 0
                elif 16 <= dy < 32:
                    dy = 16
                elif dy >= 32:
                    dy = 32
                dy /= 4
                paddle.collided = True

        self.vector = Vec2D(dx, dy)

    def _hit_topbottom(self):
        return self.rect.top < 0 or self.rect.bottom > SCREEN_HEIGHT

    def _hit_leftright(self):
        if self.rect.left < self.area.left:
            return 'left'
        elif self.rect.right > self.area.right:
            return 'right'

    def hit_paddle(self):
        player = self.game.player
        enemy = self.game.enemy
        paddles = [player, enemy]

        for paddle in paddles:
            if self.rect.colliderect(paddle.rect): return paddle


class Paddle(pygame.sprite.Sprite):

    def __init__(self):
        super(Paddle, self).__init__()

        self.image = pygame.Surface(PADDLE_SIZE)
        self.rect = self.image.get_rect()
        self._draw_paddle()

        screen = pygame.display.get_surface()
        self.area = screen.get_rect()

        self.collided = False

    def _draw_paddle(self):
        self.image.fill(WHITE)

    def reinit(self):
        self.state = 'still'
        self.movepos = [0, 0]
        self.rect.centery = self.area.centery

    def update(self):
        new_rect = self.rect.move(self.movepos)
        if self.area.contains(new_rect):
            self.rect = new_rect
        pygame.event.pump()


class Player(Paddle):

    def __init__(self, side):
        super(Player, self).__init__()
        self.side = side
        self.speed = PLAYER_SPEED
        self.score = 0
        self.reinit()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.movepos[1] = -self.speed * dt
        if keys[pygame.K_DOWN]:
            self.movepos[1] = self.speed * dt
        super(Player, self).update()

    def reinit(self):
        super(Player, self).reinit()
        if self.side == 'left':
            self.rect.left = GAP
        elif self.side == 'right':
            self.rect.right = SCREEN_WIDTH - GAP

        self.score = 0


class Enemy(Paddle):

    def __init__(self, game):
        super(Enemy, self).__init__()
        self.game = game
        self.speed = ENEMY_SPEED
        self.side = 'right' if PLAYER_SIDE == 'left' else 'left'
        self.hitpos = 0
        self.score = 0
        self.reinit()

    def update(self, dt):
        super(Enemy, self).update()

        ball = self.game.ball
        hitspot_ypos = self.rect.centery + self.hitpos

        if (hitspot_ypos - ball.rect.centery) not in range(-5, 5):
            if hitspot_ypos > ball.rect.centery:
                self.movepos[1] = -self.speed * dt
            if hitspot_ypos < ball.rect.centery:
                self.movepos[1] = self.speed * dt
        else:
            self.movepos[1] = 0

        if self.collided:
            self.hitpos = random.randrange(-40, 40)
            self.collided = False

    def reinit(self):
        super(Enemy, self).reinit()

        if self.side == 'left':
            self.rect.left = GAP
        elif self.side == 'right':
            self.rect.right = SCREEN_WIDTH - GAP

        self.score = 0


class Vec2D(object):

    def __init__(self, x=0., y=0.):
        self.x = x
        self.y = y
        self.magnitude = self.get_magnitude()

    def __str__(self):
        return "%s, %s" % (self.x, self.y)

    @classmethod
    def from_points(cls, P1, P2):
        return cls(P2[0] - P1[0], P2[1] - P1[1])

    @classmethod
    def from_magn_and_angle(cls, magn, angle):
        x = magn * math.cos(angle)
        y = magn * math.sin(angle)
        return cls(x, y)

    def get_magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def get_xy(self):
        return (self.x, self.y)


class Game(object):

    def __init__(self):
        self.ball = Ball(self, Vec2D(random.choice([-BALL_SPEED, BALL_SPEED]), 0))
        self.enemy = Enemy(self)
        self.player = Player(PLAYER_SIDE)
        self.game_sprites = pygame.sprite.Group(self.ball, self.enemy, self.player)

        screen = pygame.display.get_surface()
        self.background = pygame.Surface(screen.get_size())

        self.reinit()

    def reinit(self):
        for sprite in self.game_sprites:
            sprite.reinit()

        self._draw_background()

        self.player_score = 0
        self.enemy_score = 0
        self.highest_score = 0
        self.winner = None

    def main(self):

        left_score = Text('0', 32, WHITE, True, right=SCREEN_WIDTH / 2 - 20, top=10)
        right_score = Text('0', 32, WHITE, left=SCREEN_WIDTH / 2 + 20, top=10)

        pause_text = Text('PAUSE', 64, RED, centerx=SCREEN_WIDTH / 2, centery=SCREEN_HEIGHT / 2)

        clock = pygame.time.Clock()
        paused = False

        self.countdown_animation()
        screen.blit(self.background, [0, 0])

        while 1:
            dt = clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                        event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        self.player.movepos = [0, 0]
                        self.player.state = 'still'
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        if not paused:

                            paused = True
                        else:

                            paused = False
                    if event.key == pygame.K_r:
                        pong = Game()
                        pong.main()

            if not paused:

                self.game_sprites.clear(screen, self.background)

                screen.blit(self.background, left_score.rect, left_score.rect)
                screen.blit(self.background, right_score.rect, right_score.rect)
                screen.blit(self.background, pause_text.rect, pause_text.rect)

                self.game_sprites.update(dt)

                self.player_score = self.player.score
                self.enemy_score = self.enemy.score

                left_score.set_value(str(self.player.score))
                right_score.set_value(str(self.enemy.score))

                if self.player.side != 'left':
                    left_score.set_value(str(self.enemy.score))
                    right_score.set_value(str(self.player.score))

                self.game_sprites.draw(screen)

                screen.blit(left_score.image, left_score.rect)
                screen.blit(right_score.image, right_score.rect)

                self.highest_score = max(self.player_score, self.enemy_score)

                if self.highest_score == TOP_SCORE:
                    if self.player.score > self.enemy.score:
                        self.winner = 'player'
                    elif self.enemy.score > self.player.score:
                        self.winner = 'enemy'

                    self.game_won_animation()

                    self.reinit()

                    self.countdown_animation()
                    screen.blit(self.background, [0, 0])


            else:
                screen.blit(pause_text.image, pause_text.rect)

            pygame.display.flip()

    def countdown_animation(self):
        font = pygame.font.Font(None, 100)

        count = COUNTDOWN
        while count > 0:
            screen.fill(BLACK)

            font_size = font.size(str(count))

            textpos = [SCREEN_WIDTH / 2 - font_size[0] / 2, SCREEN_HEIGHT / 2 - font_size[1] / 2]

            screen.blit(font.render(str(count), True, WHITE, BGCOLOR), textpos)
            pygame.display.flip()

            count -= 1

            pygame.time.delay(1000)

    def game_won_animation(self):

        screen.blit(self.background, self.ball.rect, self.ball.rect)

        if self.winner == 'player':
            message = 'You win!'
            color = BLUE
        elif self.winner == 'enemy':
            message = 'You Lose!'
            color = RED

        winner_text = Text(message, 128, color,
                           centerx=SCREEN_WIDTH / 2, centery=SCREEN_HEIGHT / 2)
        screen.blit(winner_text.image, winner_text.rect)
        pygame.display.flip()

        pygame.time.delay(4000)
        screen.blit(self.background, winner_text.rect, winner_text.rect)

    def increase_score(self, side):
        if self.player.side == side:
            self.enemy.score += 1
            self.winner = self.enemy.side
        else:
            self.player.score += 1
            self.winner = self.player.side

    def _draw_background(self):
        self.background.fill(BGCOLOR)

        leftcolor = BLUE
        rightcolor = RED
        if self.player.side != 'left':
            leftcolor = RED
            rightcolor = BLUE

        # левая линия
        pygame.draw.line(self.background, leftcolor, (GAP, 0), (GAP, SCREEN_HEIGHT), 2)

        # правая линия
        pygame.draw.line(self.background, rightcolor,
                         (SCREEN_WIDTH - GAP, 0),
                         (SCREEN_WIDTH - GAP, SCREEN_HEIGHT), 2)

        # средняя линия
        pygame.draw.line(self.background, WHITE,
                         (SCREEN_WIDTH / 2, 0),
                         (SCREEN_WIDTH / 2, SCREEN_HEIGHT), 2)


if __name__ == '__main__':
    start_screen()
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Pong')
    pong = Game()
    pong.main()
