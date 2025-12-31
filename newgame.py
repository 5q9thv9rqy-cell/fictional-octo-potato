from browser import document, html, timer, ajax, window
from random import random

canvas = document["gameCanvas"]
ctx = canvas.getContext("2d")
WIDTH, HEIGHT = 800, 400

# --- 圖片處理：交換角色圖片 ---
# 現在發射的是豬，目標是鳥
pig_launcher_img = html.IMG(src="/static/images/pig.png") # 變為發射物
bird_target_img = html.IMG(src="/static/images/bird.png") # 變為目標物

# 遊戲常數
SLING_X, SLING_Y = 120, 300
MAX_SHOTS = 10

# 遊戲狀態
shots_fired = 0
total_score = 0
mouse_down = False
mouse_pos = (SLING_X, SLING_Y)
projectile = None
sent = False
game_phase = "playing"
game_over_countdown = 0

# ------------------------------------------
# 類別
# ------------------------------------------

class BirdTarget:
    """原本是 Pig，現在換成 Bird 躲在房子裡"""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.w, self.h = 40, 40
        self.alive = True
        # 角色對換後，鳥現在躲在木頭房子裡
        self.house_blocks = [
            (0, 40, 120, 15),
            (0, -10, 15, 50),
            (105, -10, 15, 50),
            (0, -25, 120, 15)
        ]

    def draw(self):
        if self.alive:
            # 繪製鳥的房子
            ctx.fillStyle = "saddlebrown"
            for rx, ry, rw, rh in self.house_blocks:
                ctx.fillRect(self.x + rx - 40, self.y + ry, rw, rh)
            
            # 繪製目標：鳥
            if bird_target_img.complete:
                ctx.drawImage(bird_target_img, self.x, self.y, self.w, self.h)

    def hit(self, px, py):
        return self.alive and self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def relocate(self, other_birds):
        MIN_DISTANCE = 120
        MIN_X, MAX_X = 450, WIDTH - self.w - 120
        MIN_Y, MAX_Y = 200, HEIGHT - self.h - 15
        for _ in range(50):
            new_x = MIN_X + random() * (MAX_X - MIN_X)
            new_y = MIN_Y + random() * (MAX_Y - MIN_Y)
            too_close = any(abs(new_x - b.x) < MIN_DISTANCE and abs(new_y - b.y) < MIN_DISTANCE 
                            for b in other_birds if b is not self and b.alive)
            if not too_close:
                self.x, self.y = new_x, new_y
                break

class PigProjectile:
    """原本是 Bird，現在換成發射 Pig"""
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.w, self.h = 35, 35
        self.active = True

    def update(self):
        global total_score
        if not self.active: return
        self.vy += 0.35
        self.x += self.vx
        self.y += self.vy
        
        # 落地或出界
        if self.y > HEIGHT - self.h or self.x > WIDTH or self.x < 0:
            self.active = False
            
        # 碰撞偵測：現在是豬撞鳥
        for b in bird_targets:
            if b.hit(self.x + self.w / 2, self.y + self.h / 2):
                b.relocate(bird_targets)
                total_score += 50
                document["score_display"].text = str(total_score)
                self.active = False
                break

    def draw(self):
        if pig_launcher_img.complete:
            ctx.drawImage(pig_launcher_img, self.x, self.y, self.w, self.h)

# ------------------------------------------
# 遊戲邏輯與輸入處理
# ------------------------------------------
bird_targets = []

def init_level():
    global bird_targets
    bird_targets = [BirdTarget(0, 0) for _ in range(3)]
    for b in bird_targets: b.relocate(bird_targets)

def start_new_game():
    global shots_fired, total_score, projectile, sent, game_phase, game_over_countdown
    total_score, shots_fired = 0, 0
    document["score_display"].text = "0"
    projectile, sent = None, False
    game_phase = "playing"
    game_over_countdown = 0
    init_level()
    update_shots_remaining()

def update_shots_remaining():
    document["shots_remaining"].text = str(MAX_SHOTS - shots_fired)

def get_pos(evt):
    rect = canvas.getBoundingClientRect()
    scale_x = canvas.width / rect.width
    scale_y = canvas.height / rect.height
    
    if hasattr(evt, "touches") and len(evt.touches) > 0:
        client_x, client_y = evt.touches[0].clientX, evt.touches[0].clientY
    elif hasattr(evt, "changedTouches") and len(evt.changedTouches) > 0:
        client_x, client_y = evt.changedTouches[0].clientX, evt.changedTouches[0].clientY
    else:
        client_x, client_y = evt.clientX, evt.clientY
        
    return (client_x - rect.left) * scale_x, (client_y - rect.top) * scale_y

def mousedown(evt):
    global mouse_down, mouse_pos
    evt.preventDefault()
    if game_phase == "playing" and projectile is None and shots_fired < MAX_SHOTS:
        mouse_down = True
        mouse_pos = get_pos(evt)

def mousemove(evt):
    global mouse_pos
    evt.preventDefault()
    if mouse_down:
        mouse_pos = get_pos(evt)

def mouseup(evt):
    global mouse_down, projectile, shots_fired
    evt.preventDefault()
    if mouse_down:
        mouse_down = False
        end_pos = get_pos(evt)
        dx, dy = SLING_X - end_pos[0], SLING_Y - end_pos[1]
        # 發射豬
        projectile = PigProjectile(SLING_X, SLING_Y, dx * 0.25, dy * 0.25)
        shots_fired += 1
        update_shots_remaining()

# 綁定事件
canvas.bind("mousedown", mousedown)
window.bind("mousemove", mousemove)
window.bind("mouseup", mouseup)
canvas.bind("touchstart", mousedown)
canvas.bind("touchmove", mousemove)
canvas.bind("touchend", mouseup)

# ------------------------------------------
# 繪圖與主迴圈
# ------------------------------------------
def draw_sling():
    if game_phase != "playing": return
    ctx.strokeStyle, ctx.lineWidth = "black", 4
    if mouse_down:
        mx, my = mouse_pos
        for offset in [-5, 5]:
            ctx.beginPath()
            ctx.moveTo(SLING_X + offset, SLING_Y)
            ctx.lineTo(mx, my)
            ctx.stroke()
        if pig_launcher_img.complete:
            ctx.drawImage(pig_launcher_img, mx - 17, my - 17, 35, 35)
    elif projectile is None and shots_fired < MAX_SHOTS:
        if pig_launcher_img.complete:
            ctx.drawImage(pig_launcher_img, SLING_X - 17, SLING_Y - 17, 35, 35)

def loop():
    global projectile, game_phase, game_over_countdown
    ctx.clearRect(0, 0, WIDTH, HEIGHT)
    
    # 繪製目標鳥
    for b in bird_targets: b.draw()
    
    # 繪製與更新發射豬
    if projectile:
        projectile.update()
        projectile.draw()
        if not projectile.active: projectile = None

    if game_phase == "playing":
        draw_sling()
        if shots_fired >= MAX_SHOTS and projectile is None:
            game_phase, game_over_countdown = "game_over", 90
            # send_score 邏輯維持原樣
    elif game_phase == "game_over":
        ctx.fillStyle = "rgba(0, 0, 0, 0.7)"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)
        ctx.fillStyle, ctx.textAlign = "white", "center"
        ctx.font = "40px Arial"
        ctx.fillText("Game Over", WIDTH // 2, HEIGHT // 2 - 20)
        ctx.fillText(f"Score: {total_score}", WIDTH // 2, HEIGHT // 2 + 30)
        game_over_countdown -= 1
        if game_over_countdown <= 0: start_new_game()

timer.set_interval(loop, 30)
start_new_game()