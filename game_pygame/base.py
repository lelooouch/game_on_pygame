import pygame
import sys
import math
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
    'voiceline': ['Как тебя зовут, странник?', '...', 'Вижу, не хочешь отвечать.',
                  'Если желаешь узнать откуда пришла чума, то тебе следует заглянуть в старый замок.',
                  'Но для спуска в самый низ, понадобится ключ.',
                  'Возможно кто-то из местных хранил его...',
                  '...',
                  '...И берегись, слабым там не место...']
}

hp_bar = {100: 'pic/health/1.png',
          80: 'pic/health/2.png',
          60: 'pic/health/3.png',
          40: 'pic/health/4.png',
          20: 'pic/health/5.png',
          0: 'pic/health/6.png'}

enemy_1 = {
    'type': 'enemy_neigh',
    'hp': 100,
    'damage': 20
}

text_for_note = 'Я не ключ, но ключ храню, В доме у воды стою. Чтобы дверцу отпереть, Надо в воду посмотреть. Мой ответ — там, где мост,В речке спрятан твой вопрос.'
