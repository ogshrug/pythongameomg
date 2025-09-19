import pygame
import sys

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
        # Draw the platform with a bit of texture
        self.image.fill(DARK_BROWN)
        pygame.draw.rect(self.image, BROWN, (0, 0, w, h - 5))
        self.rect = self.image.get_rect(topleft=(x, y))

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image_right = pygame.Surface((30, 40), pygame.SRCALPHA)
        self.draw_player(self.original_image_right)

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
        self.dash_speed = 15
        self.dash_cooldown = 1000 # ms
        self.last_dash_time = -self.dash_cooldown

    def draw_player(self, surface):
        # Body (shirt)
        pygame.draw.rect(surface, SHIRT_WHITE, (5, 10, 20, 20))
        # Head
        pygame.draw.circle(surface, SKIN, (15, 7), 7)
        # Eye
        pygame.draw.circle(surface, BLACK, (18, 5), 2)
        # Pants
        pygame.draw.rect(surface, PANTS_BLUE, (5, 30, 20, 10))
        # Pirate Hat
        pygame.draw.rect(surface, BLACK, (8, 0, 14, 4))

    def update(self, platforms):
        # Dash logic
        now = pygame.time.get_ticks()
        if self.is_dashing:
            if now - self.dash_start_time > self.dash_duration:
                self.is_dashing = False
            else:
                if self.facing_right:
                    self.rect.x += self.dash_speed
                else:
                    self.rect.x -= self.dash_speed
                # While dashing, we might still want gravity to apply
                self.velocity.y += self.acceleration.y
                self.rect.y += self.velocity.y
                return # Skip regular movement input while dashing

        # Input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= 5
            if self.facing_right:
                self.facing_right = False
                self.image = self.original_image_left
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += 5
            if not self.facing_right:
                self.facing_right = True
                self.image = self.original_image_right

        # Apply gravity
        self.velocity.y += self.acceleration.y
        self.rect.y += self.velocity.y

        # Platform collision
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if self.velocity.y > 0 and hits:
            self.rect.bottom = hits[0].rect.top
            self.velocity.y = 0
            self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.velocity.y = -15
            self.is_jumping = True

    def attack(self, all_sprites, attacks):
        weapon_type = self.weapons[self.weapon_index]
        if weapon_type == "sword":
            attack = Sword(self)
        elif weapon_type == "dagger":
            attack = Dagger(self)
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
    def __init__(self, player):
        super().__init__()
        self.image = pygame.Surface((40, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=player.rect.center)
        if player.facing_right:
            self.rect.left = player.rect.right
        else:
            self.rect.right = player.rect.left
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > 100:
            self.kill()

class Dagger(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.image = pygame.Surface((20, 10))
        self.image.fill(SILVER)
        self.rect = self.image.get_rect(center=player.rect.center)
        self.velocity_x = 20 if player.facing_right else -20

    def update(self):
        self.rect.x += self.velocity_x
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        # Draw a simple skeleton
        pygame.draw.circle(self.image, WHITE, (15, 8), 8) # Head
        pygame.draw.circle(self.image, BLACK, (12, 6), 2) # Left eye
        pygame.draw.circle(self.image, BLACK, (18, 6), 2) # Right eye
        pygame.draw.rect(self.image, WHITE, (10, 16, 10, 14)) # Body
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction = 1
        self.patrol_range = 100
        self.start_x = x

    def update(self):
        self.rect.x += self.direction
        if self.rect.x > self.start_x + self.patrol_range or self.rect.x < self.start_x:
            self.direction *= -1

# Main game loop
def main():
    player = Player()
    platforms = pygame.sprite.Group()
    ground = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    p1 = Platform(200, SCREEN_HEIGHT - 150, 150, 20)
    p2 = Platform(450, SCREEN_HEIGHT - 250, 100, 20)
    platforms.add(ground, p1, p2)

    enemies = pygame.sprite.Group()
    enemy = Enemy(220, SCREEN_HEIGHT - 150 - 30)
    enemies.add(enemy)

    attacks = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    all_sprites.add(platforms)
    all_sprites.add(enemies)


    clock = pygame.time.Clock()
    running = True
    game_over = False
    while running:
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
        enemies.update()
        attacks.update()

        # Check for collisions
        # Player attacks enemies. The first True argument makes the attack sprite disappear.
        pygame.sprite.groupcollide(attacks, enemies, True, True)

        # Player collides with enemies
        if pygame.sprite.spritecollide(player, enemies, False):
            running = False
            game_over = True


        # Drawing
        screen.fill(BLACK)
        all_sprites.draw(screen)

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

    if game_over:
        font = pygame.font.Font(None, 74)
        text = font.render("YOU LOSE!", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(2000) # Wait 2 seconds before closing

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
