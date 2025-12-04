# Game settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Infinite Platform Shooter"
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Player properties
PLAYER_ACC = 0.5
PLAYER_FRICTION = -0.12
PLAYER_GRAV = 0.8
PLAYER_JUMP = 20

# Abilities
DASH_SPEED = 10
DASH_DURATION = 500  # ms
DASH_COOLDOWN = 5000  # ms
KINETIC_BLAST_COST = 50
ENERGY_REGEN = 0.5

# Enemy properties
ENEMY_SPAWN_RATE = 100
ENEMY_SPEED = 2
ENEMY_DAMAGE = 10

# Boss properties
BOSS_HEALTH = 500
BOSS_SPAWN_KILL_COUNT = 5

# Difficulty settings
DIFFICULTY_LEVELS = {
    "Easy": {
        "ENEMY_SPAWN_RATE": 150,
        "ENEMY_SPEED": 2,
        "ENEMY_DAMAGE": 5,
        "PLAYER_HEALTH": 150,
    },
    "Medium": {
        "ENEMY_SPAWN_RATE": 100,
        "ENEMY_SPEED": 3,
        "ENEMY_DAMAGE": 10,
        "PLAYER_HEALTH": 100,
    },
    "Hard": {
        "ENEMY_SPAWN_RATE": 50,
        "ENEMY_SPEED": 4,
        "ENEMY_DAMAGE": 15,
        "PLAYER_HEALTH": 75,
    },
}
