import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((30, 40))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.lives = 3
        self.health = 100
        self.energy = 100
        self.invulnerable = False
        self.invulnerability_duration = 500  # ms
        self.last_hit_time = 0
        self.last_dash_time = 0
        self.dashing = False

    def update(self):
        if self.invulnerable and pygame.time.get_ticks() - self.last_hit_time > self.invulnerability_duration:
            self.invulnerable = False

        if self.dashing and pygame.time.get_ticks() - self.last_dash_time > DASH_DURATION:
            self.dashing = False

        self.energy = min(100, self.energy + ENERGY_REGEN)

        self.acc = pygame.math.Vector2(0, PLAYER_GRAV)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.acc.x = -PLAYER_ACC
        if keys[pygame.K_RIGHT]:
            self.acc.x = PLAYER_ACC

        # apply friction
        self.acc.x += self.vel.x * PLAYER_FRICTION
        # equations of motion
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        self.rect.midbottom = self.pos

    def jump(self):
        # jump only if standing on a platform
        self.rect.x += 1
        hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
        self.rect.x -= 1
        if hits:
            self.vel.y = -PLAYER_JUMP

    def dash(self):
        now = pygame.time.get_ticks()
        if now - self.last_dash_time > DASH_COOLDOWN:
            self.last_dash_time = now
            self.dashing = True
            self.vel.x = DASH_SPEED if self.vel.x >= 0 else -DASH_SPEED
            self.invulnerable = True
            self.last_hit_time = now

    def kinetic_blast(self):
        if self.energy >= KINETIC_BLAST_COST:
            self.energy -= KINETIC_BLAST_COST
            blast = KineticBlast(self.pos.x, self.pos.y, self.vel.x >= 0)
            self.game.all_sprites.add(blast)
            self.game.projectiles.add(blast)

    def take_damage(self, amount):
        if not self.invulnerable:
            self.health -= amount
            if self.health <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.health = DIFFICULTY_LEVELS[self.game.difficulty]["PLAYER_HEALTH"]
                    self.pos = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                    self.vel = pygame.math.Vector2(0, 0)
                else:
                    self.game.playing = False # Game over
            self.invulnerable = True
            self.last_hit_time = pygame.time.get_ticks()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Placeholder for new enemies
class GroundPatroller(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.direction = 1
        self.patrol_range = 100
        self.start_x = x
        self.speed = DIFFICULTY_LEVELS[self.game.difficulty]["ENEMY_SPEED"]

    def update(self):
        self.rect.x += self.direction * self.speed
        if self.rect.x > self.start_x + self.patrol_range or self.rect.x < self.start_x:
            self.direction *= -1

class FlyingDrone(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((40, 20))
        self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.shoot_delay = 1000
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            projectile = Projectile(self.rect.centerx, self.rect.bottom)
            self.game.all_sprites.add(projectile)
            self.game.enemy_projectiles.add(projectile)

class SlamEffect(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((SCREEN_WIDTH, 50))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(bottomleft=(0, SCREEN_HEIGHT))
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > 200:
            self.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)
        self.speedy = 5

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom > SCREEN_HEIGHT:
            self.kill()

class AmbushCrawler(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((20, 20))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.speed = DIFFICULTY_LEVELS[self.game.difficulty]["ENEMY_SPEED"]

    def update(self):
        if abs(self.rect.x - self.game.player.rect.x) < 200:
            if self.rect.x < self.game.player.rect.x:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed

class KineticBlast(pygame.sprite.Sprite):
    def __init__(self, x, y, facing_right):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 15
        self.direction = 1 if facing_right else -1

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface((100, 100))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.health = BOSS_HEALTH
        self.attack_delay = 2000
        self.last_attack = pygame.time.get_ticks()
        self.slamming = False

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_attack > self.attack_delay:
            self.last_attack = now
            attack_type = random.choice(["slam", "volley"])
            if attack_type == "slam":
                self.ground_slam()
            else:
                self.projectile_volley()

    def ground_slam(self):
        self.slamming = True
        effect = SlamEffect()
        self.game.effects.add(effect)
        self.game.all_sprites.add(effect)
        if self.game.player.rect.bottom > SCREEN_HEIGHT - 50:
            self.game.player.take_damage(50)

    def projectile_volley(self):
        for i in range(5):
            projectile = Projectile(self.rect.centerx, self.rect.bottom)
            projectile.speedy = random.randint(3, 8)
            projectile.rect.x += random.randint(-50, 50)
            self.game.all_sprites.add(projectile)
            self.game.enemy_projectiles.add(projectile)
