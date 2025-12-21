import pygame
import random
from settings import *

class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pygame.image.load(filename).convert_alpha()

    def get_image(self, x, y, width, height):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        return image

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = self.game.spritesheet.get_image(0, 48, 32, 48)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.lives = 3
        self.health = 100
        self.energy = 100
        self.invulnerable = False
        self.invulnerability_duration = 500  # ms
        self.last_hit_time = 0

    def update(self):
        if self.invulnerable and pygame.time.get_ticks() - self.last_hit_time > self.invulnerability_duration:
            self.invulnerable = False

        self.energy = min(100, self.energy + ENERGY_REGEN)

        self.acc = pygame.math.Vector2(0, PLAYER_GRAV)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
        if keys[pygame.K_d]:
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

    def kinetic_blast(self):
        if self.energy >= KINETIC_BLAST_COST:
            self.energy -= KINETIC_BLAST_COST
            blast = Projectile(self.pos.x, self.pos.y, "up")
            self.game.all_sprites.add(blast)
            self.game.projectiles.add(blast)

    def melee_attack(self):
        # Create a hitbox for the melee attack
        if self.vel.x >= 0:  # Facing right
            hitbox_rect = pygame.Rect(self.rect.right, self.rect.top, 64, self.rect.height)
        else:  # Facing left
            hitbox_rect = pygame.Rect(self.rect.left - 64, self.rect.top, 64, self.rect.height)

        for enemy in self.game.enemies:
            if hitbox_rect.colliderect(enemy.rect):
                enemy.kill()
                self.game.score += 5

    def take_damage(self, amount):
        if not self.invulnerable:
            self.health -= amount
            if self.health <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.health = DIFFICULTY_LEVELS[self.game.difficulty]["PLAYER_HEALTH"]
                    self.pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
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
        self.image = self.game.spritesheet.get_image(0, 0, 32, 48)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.direction = 1
        self.patrol_range = 100
        self.start_x = x
        self.speed = DIFFICULTY_LEVELS[self.game.difficulty]["ENEMY_SPEED"]

    def update(self):
        # GroundPatroller is a melee enemy that moves left and right
        # Damage is handled on collision in main.py
        self.rect.x += self.direction * self.speed
        if self.rect.x > self.start_x + self.patrol_range or self.rect.x < self.start_x:
            self.direction *= -1

class FlyingDrone(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.image = self.game.spritesheet.get_image(32, 0, 32, 48)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.shoot_delay = 1000
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        # Drones are stationary and shoot downwards
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
    def __init__(self, x, y, direction="down"):
        super().__init__()
        self.image = pygame.Surface((10, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)
        self.speedy = 5 if direction == "down" else -5

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom > SCREEN_HEIGHT or self.rect.top < 0:
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
