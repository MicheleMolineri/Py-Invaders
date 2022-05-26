import os, time,serial
import threading, queue ,random , time , pygame 
from pygame.mixer import Sound


#pygame config
WIDTH, HEIGHT = 750, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Py-Invaders")
pygame.font.init()
clock = pygame.time.Clock()

#enemies
RED_SPACE_SHIP = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_ship_blue_small.png"))
#player ship
PLAYER_SPACE_SHIP = pygame.image.load(os.path.join("py-invaders_imgs", "player.png"))
#health regenerator
HEALT_REGENERATOR = pygame.image.load(os.path.join("py-invaders_imgs", "health_reg.png"))
# Lasers
RED_LASER = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_laser_blue.png"))
PLAYER_LASER = pygame.image.load(os.path.join("py-invaders_imgs", "pixel_laser_yellow.png"))
# Sounds
pygame.mixer.init()
SHOOT_SOUND = Sound(os.path.join("py-invaders_sounds", "pem.wav"))
CRASH_SOUND = Sound(os.path.join("py-invaders_sounds", "crash_sound.mp3"))
WIN_SOUND = Sound(os.path.join("py-invaders_sounds", "win.mp3"))
# Background
BACKGROUND = pygame.transform.scale(pygame.image.load(os.path.join("py-invaders_imgs", "background-black.png")), (WIDTH, HEIGHT))
LOST_LABEL = pygame.image.load(os.path.join("py-invaders_imgs", "game_over.png"))
WIN_LABEL = pygame.image.load(os.path.join("py-invaders_imgs", "win.png"))
TITLE_LABEL = pygame.image.load(os.path.join("py-invaders_imgs", "title.png"))
#queue config
q_button_a , q_button_b = queue.Queue() , queue.Queue()
q_acceleration = queue.Queue()

class Read_Microbit(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._running = True
      
    def terminate(self):
        self._running = False
        
    def run(self):
        port = "/dev/ttyACM0"
        s = serial.Serial(port)
        s.baudrate = 115200

        while self._running:
            try:
                data = s.readline().decode() 
                #print(data)
                sp = data.split(" ") #12 34 True False\r\n 
                if (sp[2]=="True"): button_A = True
                else : button_A = False
                if (sp[3][:-2]=="True"): button_B = True
                else : button_B = False
                
                acc=(float(sp[0]) ,float(sp[1]))
                #print(f"button a : {button_A}  button b : {button_B}")
                q_button_b.put(button_B)
                q_acceleration.put(acc)
                q_button_a.put(button_A)
                time.sleep(0.01)
            except IndexError:
                pass
            except UnicodeDecodeError :
                pass
            except ValueError:
                pass            

class Laser:
    
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, screen):
        screen.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        if self.y <= height and self.y >= 0: return False
        else : return True
    
    def collision(self, obj):
        return collide(self, obj)

class HealthRegenerator:

    def __init__(self,x, y):
        self.x = x
        self.y = y
        self.img = HEALT_REGENERATOR
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, screen):
        self.move(7)
        screen.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel
        self.x += random.randrange(-vel*3,vel*3)

    def off_screen(self, height):
        if self.y <= height and self.y >= 0: return False
        else : return True

    def collision(self, obj):
        return collide(self, obj)

class Ship:

    COOLDOWN = 30

    def __init__(self, x, y ,shipImg,laserImg):
        self.shipImg = shipImg
        self.laserImg = laserImg
        self.x = x
        self.y = y
        self.health = 100
        self.lasers = []
        self.coolDownCounter = 0

    def draw(self, screen):
        screen.blit(self.shipImg , (self.x, self.y))
        for laser in self.lasers:
            laser.draw(screen)

    def moveLasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.coolDownCounter >= self.COOLDOWN:
            self.coolDownCounter = 0
        elif self.coolDownCounter > 0:
            self.coolDownCounter += 1

    def shoot(self):
        if self.coolDownCounter == 0:
            self.laser = Laser(self.x, self.y, self.laserImg)
            self.lasers.append(self.laser)
            self.coolDownCounter = 1

    def get_width(self):
        return self.shipImg.get_width()

    def get_height(self):
        return self.shipImg.get_height()

class Player(Ship):
    
    def __init__(self, x, y):
        super().__init__(x, y,PLAYER_SPACE_SHIP,PLAYER_LASER)
        self.mask = pygame.mask.from_surface(self.shipImg)
        self.maxHealth = 100

    def moveLasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj) :
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, screen):
        super().draw(screen)
        self.healthbar(screen)

    def healthbar(self, window):
        pygame.draw.rect(window, (255,0,0), (150, 15, 200, 20))
        pygame.draw.rect(window, (0,255,0), (150,  15, 200 * (self.health/self.maxHealth), 20))

    def off_screen_height(self, height,var):
        if self.y  + height+1.5+ var <= HEIGHT and self.y - height/2 + var >= 0: return False
        else : return True
        
    def off_screen_width(self, width ,var):
        if self.x + width + var <= WIDTH and self.x + var >= 0: return False
        else : return True

    def shootSound(self):
        if self.coolDownCounter == 0:
            SHOOT_SOUND.play()
            self.laser = Laser(self.x, self.y, self.laserImg)
            self.lasers.append(self.laser)
            self.coolDownCounter = 1
    

class Enemy(Ship):
    COLORS = [RED_SPACE_SHIP,GREEN_SPACE_SHIP,BLUE_SPACE_SHIP , RED_LASER , GREEN_LASER ,BLUE_LASER]
                
    def __init__(self, x, y  ):
        index = random.randrange(0,2)
        super().__init__(x, y,self.COLORS[index],self.COLORS[index+3])
        self.mask = pygame.mask.from_surface(self.shipImg)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.coolDownCounter == 0:
            self.laser = Laser(self.x-20, self.y, self.laserImg)
            self.lasers.append(self.laser)
            self.coolDownCounter = 1

def collide(obj1, obj2):
    x = obj2.x - obj1.x
    y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (x, y)) != None

def updateWindow(lvl,enemies,player,regenerators,lost,win):

    mainFont = pygame.font.SysFont("comicsans", 50)
    screen.blit(BACKGROUND, (0,0))
    # draw text
    lifeLabel = mainFont.render(f"Life : ", 1, (255,255,255))
    levelLabel = mainFont.render(f"Level: {lvl}", 1, (255,255,255))
    screen.blit(levelLabel, (WIDTH - levelLabel.get_width() - 10, 10))
    screen.blit(lifeLabel, (10, 10))

    for enemy in enemies:
        enemy.draw(screen)
    
    player.draw(screen)

    for reg in regenerators:
        reg.draw(screen)

    if lost:
        drawGameOverMenu()

    if win :
        drawWinMenu()

    pygame.display.update()

def mainGame():
    #game setup
    run ,FPS , level , won , count = True, 60 , 0 ,False ,0
    # enemies setup
    enemies , waveLength , enemy_vel = [], 8 , 1
    # player setup
    playerVel , laserVel , player =  5 , 5 , Player(300, 630)
    # regenerator setup
    regenerators , regVel  = [], 7 
    lost ,lostCount = False , 0 
    dt = 2
    gamma = 0.005
    # thread setup
    rmain_game = Read_Microbit()
    rmain_game.start()

    while True:
        if level > 1: 
            won = True
            
        acc , _ , btn_b = q_acceleration.get() , q_button_a.get() , q_button_b.get() 
        x = (gamma)*acc[0] + dt*float(acc[0])/1024
        y = (gamma)*acc[1]+ dt*float(acc[1])/1024

        if player.off_screen_width(player.get_width(),x)==False:
            player.x += x # X
        if player.off_screen_height(player.get_height(),y) == False:
            player.y += y # Y
        
        updateWindow(level , enemies , player ,regenerators, lost , won )
        #health control
        if  player.health <= 0:
            lost = True
            lostCount += 1
        #lost control
        if lost:
            if lostCount > FPS * 3:
                run = False
                CRASH_SOUND.play()
            else:
                continue
        #enemies control
        if len(enemies) == 0:
            level += 1
            waveLength += 5
            for i in range(waveLength):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1000, -100))
                enemies.append(enemy)
        # spawn regenerator
        if level%2 == 0  and len(regenerators)==0 :
            healthReg = HealthRegenerator(random.randrange(50, WIDTH-100),random.randrange(-2000, -100))
            regenerators.append(healthReg)
        
        if btn_b:
            player.shootSound()

        for enemy in enemies:
            enemy.move(enemy_vel)
            enemy.moveLasers(laserVel, player)
            
            if random.randrange(0, 2*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)

            elif enemy.y  > HEIGHT:
                player.health -= 10
                enemies.remove(enemy)

        for reg in regenerators:
            reg.move(regVel)

            if reg.collision(player) :
                player.health = 100 
                regenerators.remove(reg)

            

        player.moveLasers(-laserVel, enemies )
    

def drawStartMenu():
    titleFont = pygame.font.SysFont("comicsans",70)
    screen.blit(BACKGROUND, (0,0))
    screen.blit(TITLE_LABEL,(0,150))
    titleLabel = titleFont.render("Press A to begin...", 1, (255,255,255))
    screen.blit(titleLabel, (WIDTH/2 - titleLabel.get_width()/2, 350))

def drawGameOverMenu():
    screen.blit(BACKGROUND, (0,0))
    screen.blit(LOST_LABEL, (0,150))

def drawWinMenu():
    WIN_SOUND.play()
    screen.blit(BACKGROUND, (0,0))
    screen.blit(WIN_LABEL, (100,350))


def main():
    run = True
    rm = Read_Microbit()
    rm.start()
    WIDTH
    while run:
        drawStartMenu()
        _ , btn_a , _ = q_acceleration.get() , q_button_a.get() , q_button_b.get() 
        pygame.display.update()  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        if btn_a:
            rm.terminate()
            rm.join()
            mainGame()
    
    time.sleep(100)
                
    pygame.quit()
    



if __name__ == "__main__":
    main()
                  

