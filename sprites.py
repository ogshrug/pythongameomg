import pygame
import random
from settings import *
from utils import resource_path

class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pygame.image.load(resource_path(filename)).convert_alpha()

    def get_image(self, x, y, width, height):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        return image

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.original_image = self.game.spritesheet.spritesheet
        self.image = self.original_image
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
        self.last_direction = "right"

    def update(self):
        if self.invulnerable and pygame.time.get_ticks() - self.last_hit_time > self.invulnerability_duration:
            self.invulnerable = False

        self.energy = min(100, self.energy + ENERGY_REGEN)

        self.acc = pygame.math.Vector2(0, PLAYER_GRAV)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
            self.last_direction = "left"
        if keys[pygame.K_d]:
            self.acc.x = PLAYER_ACC
            self.last_direction = "right"

        if self.last_direction == "left":
            self.image = pygame.transform.flip(self.original_image, True, False)
        else:
            self.image = self.original_image

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
            vel = pygame.math.Vector2(0, -PROJECTILE_SPEED)
            blast = Projectile(self.game, self.pos.x, self.pos.y, vel)
            self.game.all_sprites.add(blast)
            self.game.projectiles.add(blast)

    def melee_attack(self):
        # Create a hitbox for the melee attack
        if self.last_direction == "right":  # Facing right
            hitbox_rect = pygame.Rect(self.rect.right, self.rect.top, 64, self.rect.height)
        else:  # Facing left
            hitbox_rect = pygame.Rect(self.rect.left - 64, self.rect.top, 64, self.rect.height)

        sword = Sword(self)
        self.game.all_sprites.add(sword)

        for enemy in self.game.enemies:
            if hitbox_rect.colliderect(enemy.rect):
                if isinstance(enemy, Boss):
                    damage = MELEE_DAMAGE * (1 - enemy.melee_resistance)
                    enemy.health = max(0, int(enemy.health - damage))
                    if enemy.health == 0:
                        enemy.kill()
                        self.game.score += 100
                else:
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
                    self.game.playing = False
            self.invulnerable = True
            self.last_hit_time = pygame.time.get_ticks()

class Sword(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        if self.player.game.sword_spritesheet:
            self.image = self.player.game.sword_spritesheet.spritesheet
        else:
            self.image = pygame.Surface((64, 32), pygame.SRCALPHA)
            self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        if self.player.last_direction == "right":
            self.rect.left = self.player.rect.right
        else:
            self.rect.right = self.player.rect.left
        self.rect.centery = self.player.rect.centery
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > 100:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, texture):
        super().__init__()
        self.image = pygame.Surface((w, h))
        texture_width, texture_height = texture.get_size()
        for i in range(0, w, texture_width):
            for j in range(0, h, texture_height):
                self.image.blit(texture, (i, j))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.off_screen_timer = 0
        self.is_off_screen = False

    def update(self):
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            if not self.is_off_screen:
                self.is_off_screen = True
                self.off_screen_timer = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - self.off_screen_timer > 3000:
                self.kill()
        else:
            self.is_off_screen = False

class GroundPatroller(Enemy):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.sprite_coords = (0, 0, 32, 32)
        self.image = self.game.groundenemy_spritesheet.get_image(*self.sprite_coords)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.direction = 1
        self.patrol_range = 100
        self.start_x = x
        self.speed = DIFFICULTY_LEVELS[self.game.difficulty]["ENEMY_SPEED"]

    def update(self):
        super().update()
        self.rect.x += self.direction * self.speed
        if self.rect.x > self.start_x + self.patrol_range or self.rect.x < self.start_x:
            self.direction *= -1

class FlyingDrone(Enemy):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.sprite_coords = (0, 0, 32, 32)
        self.image = self.game.drone_spritesheet.spritesheet
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.shoot_delay = 1000
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        super().update()
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            vel = pygame.math.Vector2(0, PROJECTILE_SPEED)
            projectile = Projectile(self.game, self.rect.centerx, self.rect.bottom, vel)
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
    def __init__(self, game, x, y, vel):
        super().__init__()
        self.game = game
        self.image = self.game.bullet_spritesheet.spritesheet
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.vel = vel
        self.image = pygame.transform.rotate(self.image, -self.vel.angle_to(pygame.math.Vector2(0, -1)))

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        if (
            self.rect.bottom > SCREEN_HEIGHT
            or self.rect.top < 0
            or self.rect.right < 0
            or self.rect.left > SCREEN_WIDTH
        ):
            self.kill()

class Boss(Enemy):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.image = self.game.boss_spritesheet.spritesheet
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.health = BOSS_HEALTH
        self.melee_resistance = BOSS_MELEE_RESISTANCE
        self.attack_delay = 2000
        self.last_attack = pygame.time.get_ticks()
        self.spiral_attack_cooldown = 5000
        self.last_spiral_attack = 0
        self.slamming = False

    def update(self):
        super().update()
        now = pygame.time.get_ticks()
        if now - self.last_attack > self.attack_delay:
            self.last_attack = now
            if self.health < BOSS_HEALTH / 2 and now - self.last_spiral_attack > self.spiral_attack_cooldown:
                self.spiral_attack()
                self.last_spiral_attack = now
            else:
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
            vel = pygame.math.Vector2(random.randint(-5, 5), random.randint(3, 8)).normalize() * PROJECTILE_SPEED
            projectile = Projectile(self.game, self.rect.centerx, self.rect.bottom, vel)
            self.game.all_sprites.add(projectile)
            self.game.enemy_projectiles.add(projectile)

    def spiral_attack(self):
        for i in range(18):
            angle = i * 20
            vel = pygame.math.Vector2(1, 0).rotate(angle) * PROJECTILE_SPEED
            projectile = Projectile(self.game, self.rect.centerx, self.rect.centery, vel)
            self.game.all_sprites.add(projectile)
            self.game.enemy_projectiles.add(projectile)
