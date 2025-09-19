import pygame
import sys
import random
import io
import base64
import xml.etree.ElementTree as ET

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pirate Parkour")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
SILVER = (192, 192, 192)
SKIN = (240, 220, 190)
PANTS_BLUE = (0, 100, 200)
SHIRT_WHITE = (230, 230, 230)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)


# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(DARK_BROWN)
        pygame.draw.rect(self.image, BROWN, (0, 0, w, h - 5))
        self.rect = self.image.get_rect(topleft=(x, y))

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Load spritesheet from SVG
        tree = ET.parse('spritesheet_ghostrunner.svg')
        root = tree.getroot()
        image_tag = root.find('{http://www.w3.org/2000/svg}image')
        href = image_tag.get('{http://www.w3.org/1999/xlink}href')

        encoded_data = href.split(',')[1]
        decoded_data = base64.b64decode(encoded_data)
        image_file = io.BytesIO(decoded_data)
        self.spritesheet = pygame.image.load(image_file).convert_alpha()

        sprite_rect = pygame.Rect(0, 0, 30, 40)
        self.original_image_right = self.spritesheet.subsurface(sprite_rect)
        self.original_image_left = pygame.transform.flip(self.original_image_right, True, False)

        self.image = self.original_image_right
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

        # Movement
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0.5) # Gravity
        self.is_jumping = False
        self.facing_right = True
        self.weapon_index = 0
        self.weapons = ["sword", "dagger"]

        # Dash ability
        self.is_dashing = False
        self.dash_duration = 200 # ms
        self.dash_speed = 10
        self.dash_cooldown = 1000 # ms
        self.last_dash_time = -self.dash_cooldown

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        move_speed = 5

        dash_speed_bonus = 0
        if self.is_dashing:
            if pygame.time.get_ticks() - self.dash_start_time > self.dash_duration:
                self.is_dashing = False
            else:
                dash_speed_bonus = self.dash_speed

        # Horizontal Movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -(move_speed + dash_speed_bonus)
            if self.facing_right:
                self.facing_right = False
                self.image = self.original_image_left
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = move_speed + dash_speed_bonus
            if not self.facing_right:
                self.facing_right = True
                self.image = self.original_image_right
        else:
            self.velocity.x = 0

        self.rect.x += self.velocity.x

        # Vertical Movement
        self.velocity.y += self.acceleration.y
        self.rect.y += self.velocity.y

        # Platform collision
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.velocity.y = -15
            self.is_jumping = True

    def attack(self, all_sprites, attacks):
        weapon_type = self.weapons[self.weapon_index]
        if weapon_type == "sword":
            attack = Sword(self.spritesheet, self.rect, self.facing_right)
        elif weapon_type == "dagger":
            attack = Dagger(self.spritesheet, self.rect, self.facing_right)
        all_sprites.add(attack)
        attacks.add(attack)

    def switch_weapon(self):
        self.weapon_index = (self.weapon_index + 1) % len(self.weapons)

    def dash(self):
        now = pygame.time.get_ticks()
        if now - self.last_dash_time > self.dash_cooldown:
            self.is_dashing = True
            self.dash_start_time = now
            self.last_dash_time = now


class Sword(pygame.sprite.Sprite):
    def __init__(self, spritesheet, player_rect, facing_right):
        super().__init__()
        self.original_image = spritesheet.subsurface(pygame.Rect(50, 100, 40, 20))
        if not facing_right:
            self.original_image = pygame.transform.flip(self.original_image, True, False)

        self.image = self.original_image
        self.rect = self.image.get_rect(center=player_rect.center)

        self.angle = 0
        self.rotation_speed = -20 if facing_right else 20
        self.spawn_time = pygame.time.get_ticks()
        self.player_rect = player_rect

    def update(self, platforms):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > 200:
            self.kill()

        self.angle += self.rotation_speed
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.player_rect.center)


class Dagger(pygame.sprite.Sprite):
    def __init__(self, spritesheet, player_rect, facing_right):
        super().__init__()
        self.original_image = spritesheet.subsurface(pygame.Rect(50, 130, 20, 20))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=player_rect.center)
        self.velocity_x = 20 if facing_right else -20
        self.angle = 0
        self.rotation_speed = 15

    def update(self, platforms):
        self.rect.x += self.velocity_x
        self.angle = (self.angle + self.rotation_speed) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (15, 8), 8)
        pygame.draw.circle(self.image, BLACK, (12, 6), 2)
        pygame.draw.circle(self.image, BLACK, (18, 6), 2)
        pygame.draw.rect(self.image, WHITE, (10, 16, 10, 14))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction = 1
        self.patrol_range = 100
        self.start_x = x

    def update(self, platforms):
        self.rect.x += self.direction
        if self.rect.x > self.start_x + self.patrol_range or self.rect.x < self.start_x:
            self.direction *= -1

def main():
    player = Player()
    platforms = pygame.sprite.Group()

    last_platform_x = 0
    for i in range(20):
        plat_y = SCREEN_HEIGHT - 40 - random.randint(-100, 100)
        plat_x = last_platform_x + random.randint(150, 300)
        plat_w = random.randint(150, 250)
        p = Platform(plat_x, plat_y, plat_w, 20)
        platforms.add(p)
        last_platform_x = p.rect.right

    ground = Platform(-SCREEN_WIDTH * 2, SCREEN_HEIGHT - 20, SCREEN_WIDTH * 6, 20)
    platforms.add(ground)

    enemies = pygame.sprite.Group()
    attacks = pygame.sprite.Group()

    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    all_sprites.add(platforms)
    all_sprites.add(enemies)

    camera_x = 0

    leftmost_x = -SCREEN_WIDTH * 2
    rightmost_x = ground.rect.right

    clock = pygame.time.Clock()
    running = True
    game_over = False
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
                    player.jump()
                if event.key == pygame.K_f:
                    player.attack(all_sprites, attacks)
                if event.key == pygame.K_q:
                    player.switch_weapon()
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    player.dash()

        # Update
        player.update(platforms)
        enemies.update(platforms)
        attacks.update(platforms)

        # Procedural Generation
        if player.rect.right > rightmost_x - SCREEN_WIDTH:
            plat_y = SCREEN_HEIGHT - 40 - random.randint(-100, 100)
            plat_w = random.randint(150, 250)
            p = Platform(rightmost_x + random.randint(150, 300), plat_y, plat_w, 20)
            platforms.add(p)
            all_sprites.add(p)
            rightmost_x = p.rect.right
            if random.random() > 0.3:
                e = Enemy(p.rect.centerx, p.rect.top - 30)
                enemies.add(e)
                all_sprites.add(e)

        if player.rect.left < leftmost_x + SCREEN_WIDTH:
            plat_y = SCREEN_HEIGHT - 40 - random.randint(-100, 100)
            plat_w = random.randint(150, 250)
            p = Platform(leftmost_x - random.randint(150, 300) - plat_w, plat_y, plat_w, 20)
            platforms.add(p)
            all_sprites.add(p)
            leftmost_x = p.rect.left
            if random.random() > 0.3:
                e = Enemy(p.rect.centerx, p.rect.top - 30)
                enemies.add(e)
                all_sprites.add(e)

        # Cleanup
        for p in list(platforms):
            if p.rect.right < player.rect.left - SCREEN_WIDTH or p.rect.left > player.rect.right + SCREEN_WIDTH:
                p.kill()
        for e in list(enemies):
            if e.rect.right < player.rect.left - SCREEN_WIDTH or e.rect.left > player.rect.right + SCREEN_WIDTH:
                e.kill()
        for a in list(attacks):
            if a.rect.right < player.rect.left - SCREEN_WIDTH or a.rect.left > player.rect.right + SCREEN_WIDTH:
                a.kill()

        # Collisions
        pygame.sprite.groupcollide(attacks, enemies, True, True)
        if pygame.sprite.spritecollide(player, enemies, False):
            game_over = True
            running = False

        camera_x = player.rect.x - SCREEN_WIDTH / 2

        # Drawing
        screen.fill(WHITE)
        for sprite in all_sprites:
            screen.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y))

        pygame.display.flip()
        clock.tick(60)

    if game_over:
        font = pygame.font.Font(None, 74)
        text = font.render("YOU LOSE!", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(2000)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
