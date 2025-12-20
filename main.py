import pygame
import random
import sys
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BLACK, WHITE,
                    RED, GREEN, CYAN, YELLOW, PLAYER_ACC, PLAYER_FRICTION,
                    PLAYER_GRAV, PLAYER_JUMP, DASH_SPEED, DASH_DURATION,
                    DASH_COOLDOWN, KINETIC_BLAST_COST, ENERGY_REGEN,
                    ENEMY_SPAWN_RATE, ENEMY_SPEED, ENEMY_DAMAGE,
                    BOSS_HEALTH, BOSS_SPAWN_KILL_COUNT, DIFFICULTY_LEVELS)
from sprites import (Player, Platform, GroundPatroller, FlyingDrone,
                     AmbushCrawler, Boss, Projectile, SlamEffect, KineticBlast)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_name = pygame.font.match_font('arial')
        self.difficulty = "Medium"
        self.boss_incoming = False
        self.boss_incoming_timer = 0
        self.load_data()

    def load_data(self):
        # Load spritesheet image
        self.spritesheet = pygame.image.load("spritesheet.png").convert_alpha()

    def new(self):
        # start a new game
        self.score = 0
        self.kill_count = 0
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.scrollable_sprites = pygame.sprite.Group()
        self.platform_edges = []
        self.player = Player(self)
        self.player.health = DIFFICULTY_LEVELS[self.difficulty]["PLAYER_HEALTH"]
        self.all_sprites.add(self.player)

        p1 = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
        self.all_sprites.add(p1)
        self.platforms.add(p1)
        self.scrollable_sprites.add(p1)
        self.platform_edges.extend([p1.rect.left, p1.rect.right])
        p2 = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT * 3 // 4, 100, 20)
        self.all_sprites.add(p2)
        self.platforms.add(p2)
        self.scrollable_sprites.add(p2)
        self.platform_edges.extend([p2.rect.left, p2.rect.right])

        # Spawn initial enemy
        enemy = GroundPatroller(p2.rect.centerx, p2.rect.top - 30, self)
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)
        self.scrollable_sprites.add(enemy)

        self.run()

    def run(self):
        # Game Loop
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def update(self):
        # Game Loop - Update
        self.all_sprites.update()
        # check if player hits a platform - only if falling
        if self.player.vel.y > 0:
            hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
            if hits:
                self.player.pos.y = hits[0].rect.top
                self.player.vel.y = 0

        # If player falls off the screen
        if self.player.rect.bottom > SCREEN_HEIGHT:
            self.player.take_damage(self.player.health + 1)

        # Enemy collisions
        enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if enemy_hits:
            self.player.take_damage(DIFFICULTY_LEVELS[self.difficulty]["ENEMY_DAMAGE"])

        enemy_projectile_hits = pygame.sprite.spritecollide(self.player, self.enemy_projectiles, True)
        if enemy_projectile_hits:
            self.player.take_damage(DIFFICULTY_LEVELS[self.difficulty]["ENEMY_DAMAGE"])

        for projectile in self.projectiles:
            hits = pygame.sprite.spritecollide(projectile, self.enemies, False)
            for hit in hits:
                if isinstance(hit, Boss):
                    hit.health -= 25
                    projectile.kill()
                    if hit.health <= 0:
                        hit.kill()
                        self.score += 100
                        self.kill_count = 0
                else:
                    hit.kill()
                    self.score += 10
                    self.kill_count += 1
                    if self.kill_count % BOSS_SPAWN_KILL_COUNT == 0:
                        self.spawn_boss()

        # Scroll the screen
        if self.player.rect.right >= SCREEN_WIDTH * 3 // 4:
            self.player.pos.x -= max(abs(self.player.vel.x), 2)
            for sprite in self.scrollable_sprites:
                sprite.rect.x -= max(abs(self.player.vel.x), 2)
                if sprite.rect.right < 0:
                    sprite.kill()
                    if isinstance(sprite, Platform):
                        try:
                            self.platform_edges.remove(sprite.rect.left)
                            self.platform_edges.remove(sprite.rect.right)
                        except ValueError:
                            pass

        if self.player.rect.left <= SCREEN_WIDTH // 4:
            self.player.pos.x += max(abs(self.player.vel.x), 2)
            for sprite in self.scrollable_sprites:
                sprite.rect.x += max(abs(self.player.vel.x), 2)
                if sprite.rect.left > SCREEN_WIDTH:
                    sprite.kill()
                    if isinstance(sprite, Platform):
                        try:
                            self.platform_edges.remove(sprite.rect.left)
                            self.platform_edges.remove(sprite.rect.right)
                        except ValueError:
                            pass

        # Spawn new enemies
        now = pygame.time.get_ticks()
        if now - self.last_enemy_spawn > DIFFICULTY_LEVELS[self.difficulty]["ENEMY_SPAWN_RATE"]:
            self.last_enemy_spawn = now
            if self.platform_edges:
                x = random.choice(self.platform_edges)
                y = random.randrange(SCREEN_HEIGHT // 2, SCREEN_HEIGHT * 3 // 4)
                enemy_type = random.choice([GroundPatroller, FlyingDrone, AmbushCrawler])
                enemy = enemy_type(x, y, self)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
                self.scrollable_sprites.add(enemy)

        # Procedural platform generation
        while len(self.platforms) < 10:
            last_platform = list(self.platforms)[-1]
            width = random.randrange(50, 100)
            p = Platform(last_platform.rect.right + random.randrange(50, 150),
                         last_platform.rect.y + random.randrange(-50, 50),
                         width, 20)
            if p.rect.top < 50:
                p.rect.top = 50
            if p.rect.bottom > SCREEN_HEIGHT - 50:
                p.rect.bottom = SCREEN_HEIGHT - 50
            self.platforms.add(p)
            self.all_sprites.add(p)
            self.scrollable_sprites.add(p)
            self.platform_edges.extend([p.rect.left, p.rect.right])

    def events(self):
        # Game Loop - events
        for event in pygame.event.get():
            # check for closing window
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                if event.key == pygame.K_LSHIFT:
                    self.player.dash()
                if event.key == pygame.K_f:
                    self.player.kinetic_blast()

    def draw(self):
        # Game Loop - draw
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)
        self.draw_ui()
        # *after* drawing everything, flip the display
        pygame.display.flip()

    def spawn_boss(self):
        boss = Boss(SCREEN_WIDTH // 2, 50, self)
        self.all_sprites.add(boss)
        self.enemies.add(boss)
        self.boss_incoming = True
        self.boss_incoming_timer = pygame.time.get_ticks()

    def draw_ui(self):
        # Draw the UI
        font = pygame.font.Font(self.font_name, 24)
        # Score
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        # Health Bar
        health_pct = self.player.health / DIFFICULTY_LEVELS[self.difficulty]["PLAYER_HEALTH"]
        if health_pct < 0:
            health_pct = 0
        pygame.draw.rect(self.screen, RED, (10, 40, 100, 20))
        pygame.draw.rect(self.screen, GREEN, (10, 40, 100 * health_pct, 20))
        # Lives
        lives_text = font.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 70))
        # Energy
        energy_text = font.render(f"Energy: {self.player.energy}", True, CYAN)
        self.screen.blit(energy_text, (10, 100))
        # Dash Cooldown
        dash_cooldown = max(0, (self.player.last_dash_time + DASH_COOLDOWN) - pygame.time.get_ticks()) / 1000
        dash_text = font.render(f"Dash CD: {dash_cooldown:.1f}", True, WHITE)
        self.screen.blit(dash_text, (10, 130))
        # Difficulty
        difficulty_text = font.render(f"Difficulty: {self.difficulty}", True, WHITE)
        self.screen.blit(difficulty_text, (SCREEN_WIDTH - 150, 10))

        if self.boss_incoming:
            now = pygame.time.get_ticks()
            if now - self.boss_incoming_timer < 2000:
                self.draw_text("Boss Incoming!", 48, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            else:
                self.boss_incoming = False

    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def show_start_screen(self):
        self.screen.fill(BLACK)
        self.draw_text("Infinite Platform Shooter", 48, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        self.draw_text("Select Difficulty:", 22, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.draw_text("E - Easy", 22, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)
        self.draw_text("M - Medium", 22, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)
        self.draw_text("H - Hard", 22, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_e:
                        self.difficulty = "Easy"
                        waiting = False
                    if event.key == pygame.K_m:
                        self.difficulty = "Medium"
                        waiting = False
                    if event.key == pygame.K_h:
                        self.difficulty = "Hard"
                        waiting = False

    def wait_for_any_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pygame.KEYUP:
                    waiting = False

    def show_go_screen(self):
        if not self.running:
            return
        self.screen.fill(BLACK)
        self.draw_text("GAME OVER", 48, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        self.draw_text("Press a key to play again", 22, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.display.flip()
        self.wait_for_any_key()

g = Game()
g.show_start_screen()
while g.running:
    g.new()
    g.show_go_screen()

pygame.quit()
sys.exit()
