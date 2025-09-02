import pygame, sys

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sprite Walk Game")
clock = pygame.time.Clock()

sheet = pygame.image.load("character_sheet.png").convert_alpha()
frame_w = sheet.get_width() // 3
frame_h = sheet.get_height() // 4

frames = []
for row in range(4):
    row_frames = []
    for col in range(3):
        rect = pygame.Rect(col*frame_w, row*frame_h, frame_w, frame_h)
        row_frames.append(sheet.subsurface(rect))
    frames.append(row_frames)

# 0=down, 1=left, 2=right, 3=up
x,y = WIDTH//2, HEIGHT//2
speed=3
direction=0
anim_index=1
anim_timer=0

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False

    keys=pygame.key.get_pressed()
    moving=False
    if keys[pygame.K_w]: y-=speed; direction=3; moving=True
    if keys[pygame.K_s]: y+=speed; direction=0; moving=True
    if keys[pygame.K_a]: x-=speed; direction=1; moving=True
    if keys[pygame.K_d]: x+=speed; direction=2; moving=True

    if moving:
        anim_timer+=1
        if anim_timer>=10:
            anim_index=(anim_index+1)%3
            anim_timer=0
    else:
        anim_index=1  # middle frame = idle

    screen.fill((60,60,60))
    frame=frames[direction][anim_index]
    rect=frame.get_rect(center=(x,y))
    screen.blit(frame,rect)
    pygame.display.flip()
    clock.tick(60)

pygame.quit(); sys.exit()
