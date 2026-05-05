import pygame
import sys

# первый нпс
npc_frames = []
for i in range(1, 3):
    frame = pygame.image.load(f"pic/1_npc/{i}.png")
    new_width = int(frame.get_width() * 0.15)
    new_height = int(frame.get_height() * 0.15)
    frame = pygame.transform.scale(frame, (new_width, new_height))
    npc_frames.append(frame)

first_npc = {
    'picture': 'pic/1_npc/diolog_first_npc.jpg',
    'voiceline': ['Как тебя зовут странник?', '...', 'Вижу, не хочешь отвечать.',
                  'Если хочешь узнать откуда пришла чума, то тебе следует заглянуть в старый замок.',
                  'Но берегись, слабым там не место...']
}


