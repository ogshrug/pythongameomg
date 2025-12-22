import pygame

# Initialize Pygame
pygame.init()

# Set screen dimensions
screen_width = 800
screen_height = 600

# Create a black surface
background_image = pygame.Surface((screen_width, screen_height))
background_image.fill((0, 0, 0))  # Black color

# Save the surface as a PNG file
pygame.image.save(background_image, "background.png")

pygame.quit()
