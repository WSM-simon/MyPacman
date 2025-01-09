from assets.board import boards
from copy import deepcopy
from random import randint, choice
import pygame
import math

pygame.init()
screen_size = pygame.Vector2(900, 990)
screen = pygame.display.set_mode(screen_size)
board_offset = 30 
canvas_size = pygame.Vector2(screen_size.x, screen_size.y - board_offset)
clock = pygame.time.Clock()
font = pygame.font.Font('assets/fonts/Retro Gaming.ttf', 20)
font2 = pygame.font.Font('assets/fonts/Retro Gaming.ttf', 32)
running = True
game_over = False
game_started = False
gamewon = False
fps = 120 
level = 0
lives = 3 
power_count_down = 0
power_up_duration = 10000 # in millisec
moving_offset = 16 
moving = False
startup_counter = 0  
startup_duration = 3000 # 2.5 sec
ghost_start_counter = 0

board = deepcopy(boards[level])
board_width = len(board[0]) 
board_height = len(board) 
line_color = 'blue'

# score
score = 0
small_dot = 242
big_dot = 4

flicker_counter = 0
flicker_round = 800

mode_counter = 0
scatter_duration = 7000 # 7 sec
chasing_duration = 20000 # 20 sec

#sound 
munching_sound = pygame.mixer.Sound('assets/sounds/pacman_munching.mp3')
munching_sound.set_volume(0.2)
beginning_sound = pygame.mixer.Sound('assets/sounds/pacman_beginning.wav')
beginning_sound.set_volume(0.2)
pacman_death_sound = pygame.mixer.Sound('assets/sounds/pacman_death.wav')
pacman_death_sound.set_volume(0.2)
pacman_eatghost_sound = pygame.mixer.Sound('assets/sounds/pacman_eatghost.wav')
pacman_eatghost_sound.set_volume(0.2)

class Player:
    def __init__(self, player_size, images, initial_position, mouth_animation_freq, live):
        self.size = player_size
        self.images = images
        self.freq = mouth_animation_freq
        self.pos = initial_position.copy()
        self.init_pos = self.pos.copy()
        self.live = live
        self.counter = 0
        self.direction = 0
        self.moving = False
        self.power = False
    
    def die(self):
        self.live -= 1
        self.direction = 0
        self.pos = self.init_pos.copy()
        self.moving = False
           
    def update_counter(self, time_elapse):
        if (self.counter + time_elapse) < self.freq:
            self.counter += time_elapse
        elif time_elapse >= self.freq: 
            self.counter = 0
        else:
            self.counter = time_elapse
            
    def draw(self):
        # 0 right, 1 left, 2 up, 3 down
        image = self.images[int((self.counter - 0.01) // (self.freq // 4))]
        if self.direction == 0:
            screen.blit(image, self.pos)
        if self.direction == 1:
            screen.blit(pygame.transform.rotate(image, 180), self.pos)
        if self.direction == 2:
            screen.blit(pygame.transform.rotate(image, 90), self.pos)
        if self.direction == 3:
            screen.blit(pygame.transform.rotate(image, 270), self.pos)
    
    def check_turns(self, board, canvas_size):    
        valid_dir = [False, False, False, False]
        unit_width = canvas_size.x / len(board[0])
        unit_height = canvas_size.y / len(board)
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        
        # out of the map
        if center_pos.x < moving_offset or center_pos.x > canvas_size.x - (moving_offset + 5):
            valid_dir[0] = valid_dir[1] = True 

        elif self.direction == 0 or self.direction == 1:
            if (board[int(center_pos.y // unit_height)][int((center_pos.x + moving_offset) // unit_width)] < 3): 
                valid_dir[0] = True
            if (board[int(center_pos.y // unit_height)][int((center_pos.x - moving_offset) // unit_width)] < 3):
                valid_dir[1] = True
            if 13 <= center_pos.x % unit_width <= 17:
                if (board[int((center_pos.y - moving_offset) // unit_height)][int(center_pos.x // unit_width)] < 3):
                    valid_dir[2] = True
                if (board[int((center_pos.y + moving_offset) // unit_height)][int(center_pos.x // unit_width)] < 3):
                    valid_dir[3] = True

        elif self.direction == 2 or self.direction == 3:
            if (board[int((center_pos.y - moving_offset) // unit_height)][int(center_pos.x // unit_width)] < 3):
                valid_dir[2] = True
            if (board[int((center_pos.y + moving_offset) // unit_height)][int(center_pos.x // unit_width)] < 3):
                valid_dir[3] = True
            if 13 <= center_pos.y % unit_height <= 17:
                if (board[int(center_pos.y // unit_height)][int((center_pos.x + moving_offset) // unit_width)] < 3): 
                    valid_dir[0] = True
                if (board[int(center_pos.y // unit_height)][int((center_pos.x - moving_offset) // unit_width)] < 3):
                    valid_dir[1] = True

        return valid_dir
    
    def change_direction(self, new_direction, board, canvas_size):
        allowed_moves = self.check_turns(board, canvas_size)
        unit_width = canvas_size.x / len(board[0])
        unit_height = canvas_size.y / len(board)
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        block_pos = pygame.Vector2(int(center_pos.x // unit_width), int(center_pos.y // unit_height))

        if not allowed_moves[new_direction] or (self.direction == new_direction):
            return

        # in case out of list range
        if (block_pos.x <= 0 or block_pos.x >= len(board[0]) - 1):
            self.direction = new_direction
        elif new_direction == 0 and board[int(block_pos.y)][int(block_pos.x + 1)] < 3:
            self.direction = new_direction
        elif new_direction == 1 and board[int(block_pos.y)][int(block_pos.x - 1)] < 3:
            self.direction = new_direction
        elif new_direction == 2 and board[int(block_pos.y - 1)][int(block_pos.x)] < 3:
            self.direction = new_direction
        elif new_direction == 3 and board[int(block_pos.y + 1)][int(block_pos.x)] < 3:
            self.direction = new_direction
        
    def move(self, dx, board, canvas_size):
        allowed_moves = self.check_turns(board, canvas_size)
        unit_width = canvas_size.x / len(board[0])
        unit_height = canvas_size.y / len(board)
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        
        if (not self.moving) or (not allowed_moves[self.direction]):
            return

        if center_pos.x <= unit_width or center_pos.x >= canvas_size.x - unit_width:
            if self.direction == 0:
                self.pos.x += dx
                if center_pos.x >= canvas_size.x:
                    self.pos.x = -self.size / 2 
            elif self.direction == 1:
                self.pos.x -= dx
                if center_pos.x <= 0: 
                    self.pos.x = canvas_size.x + self.size / 2 
        
        elif self.direction == 0:
            while board[int(center_pos.y // unit_height)][int((center_pos.x + moving_offset + dx) // unit_width)] >= 3:
                dx /= 2
            self.pos.x += dx
        elif self.direction == 1:
            while board[int(center_pos.y // unit_height)][int((center_pos.x - moving_offset - dx) // unit_width)] >= 3:
                dx /=2   
            self.pos.x -= dx
        elif self.direction == 2:
            while board[int((center_pos.y - moving_offset - dx) // unit_height)][int(center_pos.x // unit_width)] >= 3:
                dx /=2
            self.pos.y -= dx
        elif self.direction == 3:
            while board[int((center_pos.y + moving_offset + dx) // unit_height)][int(center_pos.x // unit_width)] >= 3:
                dx /=2
            self.pos.y += dx
       
    def get_rect(self):
        return pygame.rect.Rect(self.pos, (self.size - 3, self.size - 3))

    def is_collide_with(self, ghost_rect):
        return self.get_rect().colliderect(ghost_rect)
        
player_pos = pygame.Vector2(450, 686.5)
player_mouth_freq = 400   # in milliseconds
player_size = 45 
player_images = []
for i in range(1, 5):
    player_images.append(pygame.transform.scale(pygame.image.load(f'assets/player_images/{i}.png'), (player_size, player_size)))

player = Player(player_size, player_images, player_pos.copy(), player_mouth_freq, lives)

class Ghost:
    def __init__(self, initial_pos, ghost_size, ghost_image, spooked_image, dead_image, get_target):
        # properties
        self.init_pos = initial_pos.copy()
        self.pos = self.init_pos.copy() 
        self.size = ghost_size
        self.ghost_image = ghost_image
        self.spooked_image = spooked_image
        self.dead_image = dead_image

        # status
        self.start = False
        self.moving = True
        self.direction = 0
        self.dead = False
        self.spooked = False

        # movement
        self.scatter = True
        self.get_target = get_target
        self.target = self.get_target(self)
        self.last_turned_pos = pygame.Vector2(0, 0)
        self.allowed_blocks = {0, 1, 2}
        
        # respawn
        self.respawning = False
        self.respawn1 = True
        self.respawn2 = True
        self.respawn3 = True
        
        # spawn
        self.spawned = False
        self.spawning = False
        self.spawn1 = False
        self.spawn2 = False

    def get_g_target(self):
        return self.get_target(self)
    
    def die(self):
        self.dead = True
        self.spooked = False
        self.respawning = True
        self.respawn1 = False
        self.respawn2 = False
        self.respawn3 = False
        
    def draw(self):
        if self.dead:
            screen.blit(self.dead_image, self.pos)
        elif self.spooked:
            screen.blit(self.spooked_image, self.pos)
        else:
            screen.blit(self.ghost_image, self.pos) 
        
    def check_turns(self, board, canvas_size):    
        valid_dir = [False, False, False, False]
        unit_width = canvas_size.x / len(board[0])
        unit_height = canvas_size.y / len(board)
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        block_pos = pygame.Vector2(int(center_pos.x // unit_width), int(center_pos.y // unit_height))
        
        # out of the map
        if center_pos.x < moving_offset or center_pos.x > canvas_size.x - (moving_offset + 5):
            if self.direction == 0:
                valid_dir[0] = True
            if self.direction == 1:
                valid_dir[1] = True
            return valid_dir

        if board[int(block_pos.y)][int(block_pos.x + 1)] in self.allowed_blocks:
            valid_dir[0] = True
        if board[int(block_pos.y)][int(block_pos.x - 1)] in self.allowed_blocks:
            valid_dir[1] = True
        if board[int(block_pos.y - 1)][int(block_pos.x)] in self.allowed_blocks:
            valid_dir[2] = True
        if board[int(block_pos.y + 1)][int(block_pos.x)] in self.allowed_blocks: 
            valid_dir[3] = True
           
        if self.direction == 0:
            valid_dir[1] = False 
        if self.direction == 1:
            valid_dir[0] = False 
        if self.direction == 2:
            valid_dir[3] = False 
        if self.direction == 3:
            valid_dir[2] = False 

        return valid_dir
    
    def calculate_direction(self, board, canvas_size):
        unit_width = canvas_size.x / len(board[0])
        unit_height = canvas_size.y / len(board)
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        inblock_pos = pygame.Vector2(center_pos.x % unit_width, center_pos.y % unit_height)
        block_pos = pygame.Vector2(int(center_pos.x // unit_width), int(center_pos.y // unit_height))

        # not in the detecting position
        if not self.arrived(ghost_door_pos):
            if inblock_pos.x < 13 or inblock_pos.x > 17 or inblock_pos.y < 13 or inblock_pos.y > 17:
                return self.direction

            if block_pos == self.last_turned_pos:
                return 
        
        allowed_moves = self.check_turns(board, canvas_size)        
        
        if not any(allowed_moves):
            return

        if g.spooked: 
            self.last_turned_pos = block_pos
            self.direction = choice([index for index, value in enumerate(allowed_moves) if value])
            return

        min_dis = math.inf
        new_dir = 0
        if allowed_moves[0]:
            new_dis = (self.target.x - (center_pos.x + unit_width)) ** 2 + (self.target.y - center_pos.y) ** 2
            if min_dis > new_dis:
                min_dis = new_dis
                new_dir = 0
        if allowed_moves[1]:
            new_dis = (self.target.x - (center_pos.x - unit_width)) ** 2 + (self.target.y - center_pos.y) ** 2
            if min_dis > new_dis:
                min_dis = new_dis
                new_dir = 1 
        if allowed_moves[2]:
            new_dis = (self.target.x - center_pos.x) ** 2 + (self.target.y - (center_pos.y - unit_height)) ** 2
            if min_dis > new_dis:
                min_dis = new_dis
                new_dir = 2 
        if allowed_moves[3]:
            new_dis = (self.target.x - center_pos.x) ** 2 + (self.target.y - (center_pos.y + unit_height)) ** 2
            if min_dis > new_dis:
                min_dis = new_dis
                new_dir = 3 
                
        self.last_turned_pos = block_pos
        self.direction = new_dir
                
    def move(self, dx, board, canvas_size):
        unit_width = canvas_size.x / len(board[0])
        unit_height = canvas_size.y / len(board)
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        
        if self.dead:
            dx *= 1.8 
        
        if not self.moving or not self.spawned:
            if not self.spawning: 
                return

        stupid_conuter_counts_time_hit_the_wall = 0
        if center_pos.x <= unit_width or center_pos.x >= canvas_size.x - unit_width:
            if self.direction == 0:
                self.pos.x += dx
                if center_pos.x >= canvas_size.x:
                    self.pos.x = -self.size / 2 
            elif self.direction == 1:
                self.pos.x -= dx
                if center_pos.x <= 0: 
                    self.pos.x = canvas_size.x + self.size / 2 
       
        elif self.direction == 0:
            while board[int(center_pos.y // unit_height)][int((center_pos.x + moving_offset + dx) // unit_width)] not in self.allowed_blocks:
                dx /= 2
                stupid_conuter_counts_time_hit_the_wall += 1
                if stupid_conuter_counts_time_hit_the_wall >= 6:
                    self.direction = randint(0, 3)
                    break
            self.pos.x += dx
        elif self.direction == 1:
            while board[int(center_pos.y // unit_height)][int((center_pos.x - moving_offset - dx) // unit_width)] not in self.allowed_blocks:
                dx /= 2   
                stupid_conuter_counts_time_hit_the_wall += 1
                if stupid_conuter_counts_time_hit_the_wall >= 6:
                    self.direction = randint(0, 3)
                    break
            self.pos.x -= dx
        elif self.direction == 2:
            while board[int((center_pos.y - moving_offset - dx) // unit_height)][int(center_pos.x // unit_width)] not in self.allowed_blocks:
                dx /= 2
                stupid_conuter_counts_time_hit_the_wall += 1
                if stupid_conuter_counts_time_hit_the_wall >= 6:
                    self.direction = randint(0, 3)
                    break
            self.pos.y -= dx
        elif self.direction == 3:
            while  board[int((center_pos.y + moving_offset + dx) // unit_height)][int(center_pos.x // unit_width)] not in self.allowed_blocks:
                dx /= 2
                stupid_conuter_counts_time_hit_the_wall += 1
                if stupid_conuter_counts_time_hit_the_wall >= 6:
                    self.direction = randint(0, 3)
                    break
            self.pos.y += dx

    def get_rect(self):
        return pygame.rect.Rect(self.pos, (self.size - 3, self.size - 3))

    def arrived(self, pos):
        center_pos = pygame.Vector2(self.pos.x + self.size / 2, self.pos.y + self.size / 2) 
        return (pos.x - 5 <= center_pos.x <= pos.x + 5) and (pos.y - 5 <= center_pos.y <= pos.y + 5)

    def respawn(self, board, canvas_size):
        if not g.respawn1:
            self.target = ghost_door_pos.copy()
            self.calculate_direction(board, canvas_size)
            if self.arrived(ghost_door_pos):
                self.respawn1 = True
        elif not self.respawn2:
            self.allowed_blocks.add(9)
            self.target = ghost_room_pos.copy()
            self.direction = 3
            if self.arrived(ghost_room_pos):
                self.respawn2 = True
        elif not self.respawn3:
            self.dead = False
            self.direction = 2
            if self.arrived(ghost_door_pos):
                self.respawn3 = True
                self.allowed_blocks.remove(9)
                self.target = self.get_g_target()
                self.calculate_direction(board, canvas_size)
        else:
            self.respawning  = False

    def spawn(self, board, canvas_size):
        self.allowed_blocks.add(9)
        if not self.spawn1:
            self.target = ghost_room_center
            self.calculate_direction(board, canvas_size)
            if self.arrived(ghost_room_center):
                self.spawn1 = True
        elif not self.spawn2:
            self.direction = 2
            if self.arrived(ghost_door_pos):
                self.spawn2 = True
                self.allowed_blocks.remove(9)
                self.target = self.get_g_target()
                self.calculate_direction(board, canvas_size)
        else:
            self.allowed_blocks.remove(9)
            self.spawned = True
            self.spawning = False
            
        
ghost_size = 45
ghost_room_center = pygame.Vector2(452.5, 447.5)
ghost_room_pos = pygame.Vector2(450, 425)
ghost_door_pos = pygame.Vector2(450, 360.75)

blue_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/blue.png'), (ghost_size, ghost_size))
orange_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/orange.png'), (ghost_size, ghost_size))
pink_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/pink.png'), (ghost_size, ghost_size))
red_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/red.png'), (ghost_size, ghost_size))
spooked_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/spooked.png'), (ghost_size, ghost_size))
dead_img = pygame.transform.scale(pygame.image.load(f'assets/ghost_images/dead.png'), (ghost_size, ghost_size))

blinky_pos = pygame.Vector2(427, 340)
inky_pos = pygame.Vector2(380, 425)
# pinky_pos = pygame.Vector2(473.75, 51.68)
pinky_pos = pygame.Vector2(430, 425)
# clyde_pos = pygame.Vector2(381.5, 51.68)
clyde_pos = pygame.Vector2(480, 425)
# inky_pos = pygame.Vector2(801.5, 52.6)

def get_blinky_target(self):
    if self.scatter:
        return pygame.Vector2(800, -50)
    center_pos = pygame.Vector2(player.pos.x + player.size / 2, player.pos.y + player.size / 2) 
    return center_pos

def get_inky_target(self):
    if self.scatter:
        return pygame.Vector2(900, 1000)
    unit_width = canvas_size.x / len(board[0])
    unit_height = canvas_size.y / len(board)
    center_pos = pygame.Vector2(player.pos.x + player.size / 2, player.pos.y + player.size / 2) 
    t = pygame.Vector2(center_pos.x - 2 * unit_width, center_pos.y - 2 * unit_height) 
    t += t - blinky.pos
    return t  

def get_pinky_target(self):
    if self.scatter:
        return pygame.Vector2(100, -50)

    unit_width = canvas_size.x / len(board[0])
    unit_height = canvas_size.y / len(board)
    center_pos = pygame.Vector2(player.pos.x + player.size / 2, player.pos.y + player.size / 2) 
    if player.direction == 0:
        return pygame.Vector2(center_pos.x - 4 * unit_width, center_pos.y - 4 * unit_height)
    elif player.direction == 1:
        return pygame.Vector2(center_pos.x - 4 * unit_width, center_pos.y)
    elif player.direction == 2:
        return pygame.Vector2(center_pos.x, center_pos.y - 4 * unit_height)
    elif player.direction == 3:
        return pygame.Vector2(center_pos.x, center_pos.y + 4 * unit_height)

def get_clyde_target(self):
    unit_width = canvas_size.x / len(board[0])
    if self.scatter or self.pos.distance_to(player.pos) <= 8 * unit_width:
        return pygame.Vector2(0, 1000)
    return pygame.Vector2(player.pos.x + 8 * unit_width, player.pos.y)

blinky = Ghost(blinky_pos, ghost_size, red_img, spooked_img, dead_img, get_blinky_target) 
inky = Ghost(inky_pos, ghost_size, blue_img, spooked_img, dead_img, get_inky_target)
pinky = Ghost(pinky_pos, ghost_size, pink_img, spooked_img, dead_img, get_pinky_target)
clyde = Ghost(clyde_pos, ghost_size, orange_img, spooked_img, dead_img, get_clyde_target)
blinky.spawned = True

ghost_group = [blinky, inky, pinky, clyde]

def draw_board():
    tile_height = ((screen.get_height() - board_offset) // board_height)
    tile_width = (screen.get_width() // board_width)
    
    for i in range(board_height):
        for j in range(board_width):
            # small dot
            if board[i][j] == 1: 
            #if True:
                 pygame.draw.circle(screen, 'white', ((j + 0.5) * tile_width , (i + 0.5) * tile_height), 3)
            # big dot
            elif board[i][j] == 2 and flicker_counter < flicker_round/2:
                 pygame.draw.circle(screen, 'white', ((j + 0.5) * tile_width , (i + 0.5) * tile_height), 10)
            # vertial line
            elif board[i][j] == 3:
                pygame.draw.line(screen, line_color, ((j + 0.5) * tile_width, i * tile_height), ((j + 0.5) * tile_width, (i + 1) * tile_height), 3)
            # horizontal line
            elif board[i][j] == 4:
                pygame.draw.line(screen, line_color, (j * tile_width, (i + 0.5) * tile_height), ((j + 1) * tile_width, (i + 0.5) * tile_height), 3)
            # top right corner arc
            elif board[i][j] == 5:
                pygame.draw.arc(screen, line_color, ((j - 0.5) * tile_width, (i + 0.5) * tile_height, tile_width, tile_height), 0, math.pi / 2, 3)
            # top left corner arc 
            elif board[i][j] == 6:
                pygame.draw.arc(screen, line_color, ((j + 0.5) * tile_width, (i + 0.5) * tile_height, tile_width, tile_height), math.pi / 2, math.pi, 3)
            # bottom left corner arc
            elif board[i][j] == 7:
                pygame.draw.arc(screen, line_color, ((j + 0.5) * tile_width, (i - 0.5) * tile_height + 2, tile_width, tile_height), math.pi, 1.5 * math.pi, 3)
            # bottom right corner
            elif board[i][j] == 8:
                pygame.draw.arc(screen, line_color, ((j - 0.5) * tile_width, (i - 0.5) * tile_height + 2, tile_width, tile_height), 1.5 * math.pi, 2 * math.pi, 3)
            # ghost door
            elif board[i][j] == 9:
                pygame.draw.line(screen, 'white', (j * tile_width, (i + 0.5) * tile_height), ((j + 1) * tile_width, (i + 0.5) * tile_height), 3)

def draw_misc():
    score_text = font.render(f'Score: {score}', True, 'white')
    screen.blit(score_text, (10, screen_size.y - board_offset))

    for i in range(player.live):
        screen.blit(pygame.transform.scale(player_images[0], (player_size - 15, player_size - 15)), (650 + i * 40, screen_size.y - board_offset - 5))
       
def get_spooked(ghost):
    ghost.spooked = True
    if ghost.direction == 1:
        ghost.direction = 0 
    if ghost.direction == 0:
        ghost.direction = 1 
    if ghost.direction == 2:
        ghost.direction = 3 
    if ghost.direction == 3:
        ghost.direction = 2 

def update_score():
    global score, power_count_down, small_dot, big_dot
    
    if not player.moving:
        return
    if not (0 < player.pos.x < screen_size.x - player_size and 0 < player.pos.y < screen_size.y - board_offset - player_size):
        return
    
    unit_width = screen_size.x / board_width
    unit_height = (screen_size.y - board_offset) / board_height 
    center_pos = pygame.Vector2(player.pos.x + player.size / 2, player.pos.y + player.size / 2) 
    block_pos = pygame.Vector2(int(center_pos.x // unit_width), int(center_pos.y // unit_height))
    
    if board[int(block_pos.y)][int(block_pos.x)] == 1:
        board[int(block_pos.y)][int(block_pos.x)] = 0
        munching_sound.play()
        small_dot -= 1
        score += 10 
    if board[int(block_pos.y)][int(block_pos.x)] == 2:
        board[int(block_pos.y)][int(block_pos.x)] = 0
        munching_sound.play()
        big_dot -= 1       
        score += 50
        power_count_down += power_up_duration
        for g in ghost_group:
            if g.spawned:
                get_spooked(g)

def reset_ghost():
    global blinky, inky, pinky, clyde, ghost_group, ghost_start_counter
    
    ghost_start_counter = 0

    blinky = Ghost(blinky_pos, ghost_size, red_img, spooked_img, dead_img, get_blinky_target) 
    inky = Ghost(inky_pos, ghost_size, blue_img, spooked_img, dead_img, get_inky_target)
    pinky = Ghost(pinky_pos, ghost_size, pink_img, spooked_img, dead_img, get_pinky_target)
    clyde = Ghost(clyde_pos, ghost_size, orange_img, spooked_img, dead_img, get_clyde_target)
    blinky.spawned = True

    ghost_group = [blinky, inky, pinky, clyde]

def reset_player():
    global player, score, board, small_dot, big_dot
    
    player = Player(player_size, player_images, player_pos.copy(), player_mouth_freq, lives)
    player.counter = 0
    player.moving = False
    score = 0
    small_dot = 242
    big_dot = 4
    board = deepcopy(boards[level])

while running:
    elapse = clock.tick(fps)
    player.update_counter(elapse)
    flicker_counter = (flicker_counter + elapse if flicker_counter + elapse < flicker_round else elapse) 
    
    screen.fill("black")
    update_score()
    draw_misc()
    draw_board()

    # game over
    if game_over:
        # pygame.event.clear()
        player.moving = False
        for g in ghost_group:
            g.moving = False
        gameover_caption = font2.render("GAMEOVER", True, 'red')
        screen.blit(gameover_caption,  (360, 515))
        
        pygame.display.flip()
        event = pygame.event.wait()
        print('gameover now')
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print('restart game')
                reset_ghost()
                reset_player()
                game_over = False   
                game_started = False
        continue
    
    if small_dot <= 0 and big_dot <= 0:
        player.moving = False
        for g in ghost_group:
            g.moving = False
        gameover_caption = font2.render("YOU WON", True, 'red')
        screen.blit(gameover_caption,  (367, 517))
        
        pygame.display.flip()
        event = pygame.event.wait()
        print('gamewon now')
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print('restart game')
                reset_ghost()
                reset_player()
                game_over = False   
                game_started = False
                gamewon = False
        continue
                
    # game start
    if not game_started:
        beginning_sound.play()
        game_started = True
        
    # ghost startup
    ghost_start_counter += min(elapse, 30)
    if not pinky.spawned and ghost_start_counter >= 10 * 1000: # 10 sec
        pinky.spawning = True
    if not inky.spawned and ghost_start_counter >= 20 * 1000: # 20 sec
        inky.spawning = True
    if not clyde.spawned and ghost_start_counter >= 30 * 1000: # 30 sec
        clyde.spawning = True

    # power up + spook
    if power_count_down: 
        if power_count_down - elapse <= 0:
            power_count_down = 0
            player.power = False
            for g in ghost_group:
                g.spooked = False
        else:
            power_count_down -= elapse
            player.power = True
            
    # player movement 
    if not player.moving:
        if startup_counter + elapse < startup_duration:
            startup_counter += elapse
            ready_caption = font2.render("READY!", True, 'red')
            screen.blit(ready_caption, (385, 515))
            for g in ghost_group:
                g.moving = False
        else: 
            startup_counter = 0
            for g in ghost_group:
                g.moving = True
            player.moving = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.draw()
    for g in ghost_group:
        g.draw()
    
    speed = 250 
    dt = elapse / 1000
    dx = speed * dt
    keys =  pygame.key.get_pressed()

    # player move
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.change_direction(0, board, canvas_size)
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.change_direction(1, board, canvas_size)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player.change_direction(2, board, canvas_size)
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player.change_direction(3, board, canvas_size)
    player.move(dx, board, canvas_size)
    
    if mode_counter + elapse > scatter_duration + chasing_duration:
        mode_counter = min(elapse, scatter_duration + chasing_duration - 1000)
    elif mode_counter + elapse < chasing_duration:
        mode_counter += elapse
        for g in ghost_group:
            g.scatter = False 
    elif chasing_duration < mode_counter + elapse < scatter_duration + chasing_duration:
        mode_counter += elapse
        for g in ghost_group:
            g.scatter = True

    # ghost move
    for g in ghost_group:
        if g.spawning:
            g.spawn(board, canvas_size)
        elif g.respawning:
            g.respawn(board, canvas_size)
        else:
            g.target = g.get_g_target()
            g.calculate_direction(board, canvas_size)
        # g.move(dx * 0.8 , board, canvas_size)

        # ghost collision
        if player.is_collide_with(g.get_rect()):
            if g.dead:
                continue
            elif g.spooked:
                pacman_eatghost_sound.play()
                score += 200
                g.die()
            elif player.live > 1:
                pacman_death_sound.play()
                player.die()
                reset_ghost()
            else:  
                player.die()
                pacman_death_sound.play()
                game_over = True

    p_center_pos = pygame.Vector2(pinky.pos.x + pinky.size / 2, pinky.pos.y + pinky.size / 2) 
    pygame.display.flip()
pygame.quit()