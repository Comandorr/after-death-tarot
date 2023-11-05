import arcade
import random
import math
from operator import attrgetter

# TODO

# 5 - добавить музыку

# 6 - прокомментировать функции карт и все остальное
    # (возможно не нужно совсем)
# 7 - добавить звук атаки, получения урона, восстановления
    # (возможно не нужно совсем)

# 11 - отбалансировать здоровье

# описания волшебника и силы тут же закрываются другими описаниями

pick_sound = arcade.Sound('sounds/click_002.ogg')
take_sound = arcade.Sound('sounds/click_003.ogg')
error_sound = arcade.Sound('sounds/error.ogg')
new_card_sound = arcade.Sound('sounds/switch_007.ogg')
use_sound = arcade.Sound('sounds/glass_004.ogg')
music = arcade.Sound('sounds/music.mp3')

card_pack = list(range(0, 78))
cards_played = {}
for i in list(range(0, 27)):
    cards_played[i] = False
card_hints = {
    0: 'шут - выбрасывает и заменяет все твои карты',
    1: 'маг - играет случайную карту из колоды',
    2: 'жрица - призывает верховного жреца',
    3: 'императрица - перемешивает все твои карты',
    4: 'император - призывает императрицу',
    5: 'верховный жрец - возвращает последнюю сыгранную карту',
    6: 'любовники - дублируют случайную карту в руке',
    7: 'колесница - возвращает все сыгранные карты в колоду',
    8: 'сила - играет три карты из твоей руки',
    9: 'отшельник - выбрасывает всё, оставляя только одну карту',
    10:'фортуна - дает случайную карту',
    11:'справедливость - уравнивает мое здоровье с твоим',
    12:'повешенный - забирает у тебя 3 жизни',
    13:'смерть - оставляет по 1 жизни у нас обоих',
    14:'умеренность - выбрасывает половину твоих карт',
    15:'дьявол - выбрасывает все старшие арканы',
    16:'башня - выбрасывает все младшие арканы',
    17:'звезда - дает тебе три карты',
    18:'луна - заменяет все старшие арканы на младшие',
    19:'солнце - заменяет все младшие арканы на старшие',
    20:'суд - мы оба теряем по три жизни',
    21:'мир - повышает ранг младших арканов до максимума',
    22:'масть жезлов - заменяет карты в твоей руке',
    23:'масть кубков - восполняет твои жизни',
    24:'масть мечей - атакует',
    25:'масть колец - дает новые карты',
    26:'ты можешь взять карту, но это стоит частицу твоей жизни'
}


class DeathHp(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__('deathhp.png', center_x = x, center_y = y, scale = .3)
        self.alpha = 80
        self.dying = False
    def update(self):
        if self.dying:
            if self.alpha > 0:
                self.alpha -=1
            else:
                self.kill()
                scene = game_view.scene
                if not len(scene['Death Hp']):
                    window.show_view(win_view)


class SelfHp(arcade.Sprite):
    def __init__(self):
        super().__init__('life.png', scale=.09, center_x=1280+50, center_y=40)
        self.origin_x = self.center_x
        self.origin_y = self.center_y
        self.speed = 20
        self.color_gb = 255
        self.dying = False

    def update(self):
        if self.center_x != self.origin_x:
            if self.center_x > self.origin_x:
                self.change_x = -self.speed
            else:
                self.change_x = self.speed
            self.center_x += self.change_x
            if abs(self.center_x - self.origin_x) <= self.speed:
                self.center_x = self.origin_x
                self.change_x = 0
        if self.dying:
            self.animate_hit()
            
    def animate_hit(self):
        if self.color_gb >= 10:
            self.color_gb -= 10
            self.color = (255, self.color_gb, self.color_gb)
        if self.color_gb <= 10:
            self.alpha -= 10
            if self.alpha <= 10:
                self.kill()
                rearrange_lives()
                scene = game_view.scene
                if not len(scene['Self Hp']):
                    window.show_view(lose_view)
        

class CardGiver(arcade.Sprite):
    def __init__(self):
        super().__init__(
            'taro/827_78.jpg', 
            center_x = 1280-120,
            center_y = 400,
            scale = 0.8,
            angle=90)


class Card(arcade.Sprite):
    def __init__(self, filename, center_x, center_y, scene, number):
        super().__init__(filename, center_x=center_x, center_y=center_y)
        self.scale = 0.8
        self.dragged = False
        self.origin_x = self.center_x
        self.origin_y = self.center_y
        self.scene = scene
        self.target_scale = 0.8
        self.speed = 30
        self.mask = arcade.SpriteSolidColor(int(self.width), int(self.height), arcade.color.WHITE)
        self.mask.center_x, self.mask.center_y = self.center_x, self.center_y
        self.mask.alpha = 0
        self.change_alpha = 7
        self.number = number
        self.instruction = {
            0: self.fool,
            1: self.magician,
            2: self.priestes,
            3: self.empress,
            4: self.emperor,
            5: self.hierophant,
            6: self.lovers,
            7: self.chariot,
            8: self.strength,
            9: self.hermit,
            10: self.fortune,
            11: self.justice,
            12: self.hanged,
            13: self.death,
            14: self.temperance,
            15: self.devil,
            16: self.tower,
            17: self.star,
            18: self.moon,
            19: self.sun,
            20: self.judgement,
            21: self.world
        }

    def use(self):
        global cards_played
        if self in self.scene['Hovered Cards']:
            self.scene['Hovered Cards'].remove(self)
        self.scene['Deck'].remove(self)
        self.scene['Using Cards'].append(self)
        use_sound.play(volume=0.3)

        # старшие арканы
        if self.number < 22:
            if not cards_played[self.number]:
                cards_played[self.number] = True
                change_text(card_hints[self.number])
            self.instruction[self.number]()

        # жезлы
        elif 22 <= self.number <= 35:
            if not cards_played[22]:
                cards_played[22] = True
                change_text(card_hints[22])
            num = self.number - 21
            if num > len(self.scene['Deck']):
                num = len(self.scene['Deck'])
            for i in range(num):
                self.scene['Deck'].pop(-1)
            for i in range(num):
                create_card()

        # кубки
        elif 36 <= self.number <= 49:
            if not cards_played[23]:
                cards_played[23] = True
                change_text(card_hints[23])
            num = self.number-35
            health = random.randint(1, num)
            for i in range(health):
                ld = len(self.scene['Self Hp'])
                self.scene['Self Hp'].append(SelfHp())

        # мечи
        elif 50 <= self.number <= 63:
            if not cards_played[24]:
                cards_played[24] = True
                change_text(card_hints[24])
            damage = (self.number-49)
            for i in range(damage):
                take_death_hp()
            self.scene['Death'][0].state = 'hit'

        # пентакли
        elif 64 <= self.number <= 77:
            if not cards_played[25]:
                cards_played[25] = True
                change_text(card_hints[25])
            num = self.number-63
            cards = random.randint(1, num)
            for i in range(cards):
                create_card()

        self.scene.last_card_number = self.number
        take_one_hp()
        rearrange_cards(self.number != 3)

    def animate_use(self):
        if self.mask.alpha < 255:
            self.mask.alpha += self.change_alpha

            if (255-self.mask.alpha) < abs(self.change_alpha):
                self.mask.alpha = 255
            if self.mask.alpha < abs(self.change_alpha):
                self.mask.alpha = 0
            if (255-self.alpha) < abs(self.change_alpha):
                self.alpha = 255
            if self.alpha < abs(self.change_alpha):
                self.alpha = 0

            if self.change_alpha < 0:
                self.alpha += self.change_alpha
            if self.mask.alpha == 0:
                self.kill()

        if self.mask.alpha == 255:
            self.change_alpha = -self.change_alpha 
            self.mask.alpha += self.change_alpha

    def update(self):
        self.mask.center_x, self.mask.center_y = self.center_x, self.center_y
        self.mask.width, self.mask.height = int(self.width), int(self.height)

        if self in self.scene['Using Cards']:
            self.animate_use()
            return None

        if self in self.scene['Hovered Cards']:
            self.target_scale = 1.1
        else:
            self.target_scale = 0.8

        if self.target_scale > self.scale:
            self.scale += 0.04
        elif self.target_scale < self.scale:
            self.scale -= 0.04
        if abs(self.scale-self.target_scale) < 0.04:
            self.scale = self.target_scale
        
        if (self.center_x, self.center_y) != (self.origin_x, self.origin_y) and not self.dragged:
            angle = arcade.get_angle_degrees(self.center_x, self.center_y, self.origin_x, self.origin_y)
            angle_rad = math.radians(angle)
            self.change_x = self.speed * math.sin(angle_rad)
            self.change_y = self.speed * math.cos(angle_rad)
            self.center_x += self.change_x
            self.center_y += self.change_y
            if arcade.get_distance(self.center_x, self.center_y, self.origin_x, self.origin_y) <= self.speed:
                self.center_x, self.center_y = self.origin_x, self.origin_y

    def release(self):
        self.dragged = False

    def draw(self):
        self.mask.draw()

    def fool(self):
        ld = len(self.scene['Deck'])
        self.scene['Deck'].clear()
        for i in range(ld):
            create_card()
    
    def magician(self):
        card = create_card()
        if card:
            card.center_x = 1280/2
            card.center_y = 720/2
            card.origin_x, card.origin_y = card.center_x, card.center_y
            card.scale = 1.1
            card.target_scale = 1.1
            card.use()

    def priestes(self):
        create_card(5)

    def empress(self):
        self.scene['Deck'].shuffle()
    
    def emperor(self):
        create_card(3)
    
    def hierophant(self):
        if self.scene.last_card_number != None:
            create_card(self.scene.last_card_number)
    
    def lovers(self):
        if len(self.scene['Deck']):
            num = random.choice(self.scene['Deck']).number
            create_card(num)

    def chariot(self):
        global card_pack
        card_pack = list(range(0, 78))
        new_card_sound.play()

    def strength(self):
        for i in range(3):
            if not len(self.scene['Deck']):
                break
            card = random.choice(self.scene['Deck'])
            card.center_x = 1280/2
            card.center_y = 720/2
            card.origin_x, card.origin_y = card.center_x, card.center_y
            card.scale = 1.1
            card.target_scale = 1.1
            card.use()

    def hermit(self):
        ld = len(self.scene['Deck'])
        if ld:
            num = random.randint(0, ld-1)
            self.scene['Deck'].clear()
            create_card(num)

    def fortune(self):
        create_card()

    def justice(self):
        d_ld = len(self.scene['Death Hp'])
        p_ld = 0
        for hp in self.scene['Self Hp']:
            if not hp.dying:
                p_ld += 1
        if d_ld > p_ld:
            for i in range(p_ld-1, d_ld):
                self.scene['Death Hp'][i].dying = True
            self.scene['Death'][0].state = 'hit'
        elif p_ld > d_ld:
            for i in range(d_ld-1, p_ld):
                self.scene['Death Hp'].append(DeathHp(((i+d_ld)%21)*60+35, 760-((i+d_ld)//21)*60))

    def hanged(self):
        for i in range(2):
            take_one_hp()

    def death(self):
        p_ld = 0
        for hp in self.scene['Self Hp']:
            if not hp.dying:
                p_ld += 1
        d_ld = 0
        for hp in self.scene['Death Hp']:
            if not hp.dying:
                d_ld += 1

        for i in range(p_ld-2):
            take_one_hp()

        self.scene['Death'][0].state = 'hit'
        for i in range(d_ld-1):
            take_death_hp()
    
    def temperance(self):
        ld = len(self.scene['Deck'])//2
        if ld != 0:
            for i in range(ld):
                self.scene['Deck'].pop(0)

    def devil(self):
        delete_list = []
        for card in self.scene['Deck']:
            if card.number < 22:
                delete_list.append(card)
        for card in delete_list:
            self.scene['Deck'].remove(card)

    def tower(self):
        delete_list = []
        for card in self.scene['Deck']:
            if card.number >= 22:
                delete_list.append(card)
        for card in delete_list:
            self.scene['Deck'].remove(card)

    def star(self):
        for i in range(3):
            create_card()

    def moon(self):
        delete_list = []
        majors = 0
        for card in self.scene['Deck']:
            if card.number < 22:
                delete_list.append(card)
                majors+=1
        for card in delete_list:
            self.scene['Deck'].remove(card)
        for i in range(majors):
            create_card(random.randint(22, 77))

    def sun(self):
        delete_list = []
        minors = 0
        for card in self.scene['Deck']:
            if card.number >= 22:
                delete_list.append(card)
                minors+=1
        for card in delete_list:
            self.scene['Deck'].remove(card)
        for i in range(minors):
            create_card(random.randint(0, 21))

    def judgement(self):
        for i in range(3):
            take_death_hp()
        for i in range(3):
            take_one_hp()

    def world(self):
        for card in self.scene['Deck']:
            if 22 <= card.number <= 35:
                card.number = 35
            elif 36 <= card.number <= 49:
                card.number = 49
            elif 50 <= card.number <= 63:
                card.number = 63
            elif 64 <= card.number <= 77:
                card.number = 77

            if card.number < 10:
                num = '0'+str(card.number)
            else:
                num = str(card.number)
            card.texture = arcade.load_texture('taro/827_'+num+'.jpg')
            card.scale = 1.1


class Death(arcade.Sprite):
    def __init__(self):
        super().__init__(
            'death.png',
            center_x = 1280/2,
            center_y = 1280/2-50,
            scale = 1.3
        )
        self.origin_x = self.center_x
        self.origin_y = self.center_y
        self.target_x = self.center_x
        self.target_y = self.center_y
        self.change_scale = -0.0007
        self.change_angle = 0.01
        self.color_gb = 255
        self.color_change = 0
        self.state = 'idle'

    def update(self):
        self.scale += self.change_scale
        if self.scale >= 1.3 or self.scale <= 1.1:
            self.change_scale = -self.change_scale
        
        self.angle += self.change_angle
        if self.angle >= 10 or self.angle <= -30:
            self.change_angle = -self.change_angle        

        if self.state == 'hit':
            self.color_change = -10
            if self.color_gb <= abs(self.color_change):
                self.state = 'recovering'
        if self.state == 'recovering':
            self.color_change = 10
        
        self.color_gb += self.color_change
        if self.color_gb == 255:
            self.color_change = 0
            self.state = 'idle'
        self.color = (255, self.color_gb, self.color_gb)


def take_one_hp():
    ''' снимает одно хп y игрока '''
    scene = game_view.scene
    for i in range(1, len(scene['Self Hp'])+1):
        hp = scene['Self Hp'][-i]
        if not hp.dying:
            hp.dying = True
            scene['Using Cards'].append(hp)
            break
    rearrange_lives()
    if not len(scene['Self Hp']):
        window.show_view(lose_view)


def take_death_hp():
    ''' снимает одно хп y смерти '''
    scene = game_view.scene
    for i in range(1, len(scene['Death Hp'])+1):
        hp = scene['Death Hp'][-i]
        if not hp.dying:
            hp.dying = True
            break
    if not len(scene['Death Hp']):
        window.show_view(win_view)


def create_card(num=None):
    ''' создает карту и добавляет в руку игрока '''
    scene = game_view.scene
    global card_pack
    if len(card_pack):
        if num == None:
            num = random.choice(card_pack)
            card_pack.remove(num)
        number = num
        if num < 10:
            num = '0'+str(num)
        else:
            num = str(num)
        card = Card('taro/827_'+num+'.jpg', 1280+125, center_y=200, scene = scene, number=number)
        scene['Deck'].append(card)
        new_card_sound.play(volume=0.3)
        rearrange_cards(scene)
        return card
    if not len(card_pack) and len(scene['Card Giver']):
        scene['Card Giver'].clear()


def rearrange_cards(sort = True):
    ''' расставляет карты руке по экрану '''
    scene = game_view.scene
    if sort:
        scene['Deck'].sort(key=attrgetter('center_x'))
    ld = len(scene['Deck'])
    width = 1150/(ld+1)
    for i in range(ld):
        scene['Deck'][i].origin_x = 65+((i+1)*width)


def rearrange_lives():
    ''' расставляет жизни по экрану '''
    scene = game_view.scene
    ld = len(scene['Self Hp'])
    width = 1280-42-42
    width /= ld+1
    for i in range(ld):
        scene['Self Hp'][i].origin_x = (i+1)*width + 42

def change_text(text):
    game_view.text = text
    game_view.instruction.value = ''

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.mouse = (0,0)
        self.scene = arcade.Scene()
        self.cards = arcade.SpriteList()
        self.cards_hovered = arcade.SpriteList()
        self.all_cards = arcade.SpriteList()
        self.text = ''

    def setup(self):
        # здоровье смерти
        self.scene.add_sprite_list('Death Hp')
        for i in range(105):
            self.scene['Death Hp'].append(DeathHp((i%21)*60+35, 760-(i//21)*60))

        # здоровье игрока
        self.scene.add_sprite_list('Self Hp')
        for i in range(10):
            self.scene['Self Hp'].append(SelfHp())
        rearrange_lives()
        
        self.scene.add_sprite('Death', Death())
        self.scene.add_sprite('Card Giver', CardGiver())
        self.scene.add_sprite_list('Deck', sprite_list=self.cards)
        self.scene.add_sprite_list('Hovered Cards', sprite_list=self.cards_hovered)
        self.scene.add_sprite_list('Using Cards')
        
        for i in range(10):
            create_card()
        self.scene.last_card_number = None

        self.instruction = arcade.Text('', 100, 350, font_size=14, font_name=('Gora Free'), multiline=True, width = 1000)
        self.timer = 0
        self.last_letter = 0
        self.period = .07

    def play_text(self):
        lt = len(self.instruction.value)+1
        if lt <= len(self.text):
            self.instruction.value = self.text[:lt]
            pick_sound.play(.3)

    def on_show_view(self):
        self.setup()

    def on_draw(self):
        self.clear()
        self.instruction.draw()
        self.scene.draw()
        for c in self.scene['Using Cards']:
            c.draw()

    def on_update(self, dt):
        self.timer += dt
        if self.timer - self.last_letter >= self.period:
            self.last_letter = self.timer
            self.play_text()

        # проверяем, касаемся ли мы уже какой-то карты или нет
        for card in self.scene['Hovered Cards']:
            if not card.collides_with_point(self.mouse):
                self.scene['Hovered Cards'].remove(card)
                rearrange_cards()

        # если нет, проверяем - коснулись ли новой карты
        if not len(self.scene['Hovered Cards']):
            for i in range(1, len(self.scene['Deck'])+1):
                card = self.scene['Deck'][-i]
                if card.collides_with_point(self.mouse):
                    self.scene['Hovered Cards'].clear()
                    self.scene['Hovered Cards'].append(card)
                    pick_sound.play(volume=.3)
                    self.scene['Deck'].remove(card)
                    self.scene['Deck'].append(card)
                    break

        self.scene.update()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse = (x, y)
        for c in self.scene['Hovered Cards']:
            if c.dragged:
                c.center_x += dx
                c.center_y += dy

    def on_mouse_press(self, *kwargs):
        global cards_played
        for c in self.scene['Hovered Cards']:
            c.dragged = True
            take_sound.play(volume = 0.3)
        if len(self.scene['Card Giver']):
            if self.scene['Card Giver'][0].collides_with_point(self.mouse):
                if not cards_played[26]:
                    cards_played[26] = True
                    change_text(card_hints[26])
                create_card()
                for i in range(1, len(self.scene['Self Hp'])+1):
                    hp = self.scene['Self Hp'][-i]
                    if not hp.dying:
                        hp.dying = True
                        self.scene['Using Cards'].append(hp)
                        break

    def on_mouse_release(self, *kwargs):
        for c in self.scene['Hovered Cards']:
            if c.dragged:
                c.release()
            if c.collides_with_sprite(self.scene['Death'][0]):
                c.use()
            else:
                error_sound.play(volume=0.3)


class StartView(arcade.View):
    def __init__(self):
        super().__init__()
        self.scene = arcade.Scene()

    def setup(self):
        self.scene.add_sprite('Death', Death())
        self.scene['Death'][0].alpha = 0
        self.instruction = arcade.Text('', 100, 300, font_size=26, font_name=('Gora Free'), multiline=True, width = 1000)
        self.timer = 0
        self.last_letter = 0
        self.period = .07
        self.stage = 0
        self.texts = {
            0: 'ты пришел ко мне, смертный...',
            1: 'пришел узнать ответ на свой самый главный вопрос',
            2: 'раз ты осмелился, я отвечу на него...',
            3: '...но сначала сыграем в карты',
            4: 'эти карты настолько сильны, что каждая сыгранная карта будет стоить тебе частичку твоей жизни',
        }
        music.play(0.2)

    def on_draw(self):
        self.clear()
        self.scene.draw()
        self.instruction.draw()

    def update_text(self):
        if self.stage != 5:
            self.last_letter = self.timer
            if not self.instruction.value in self.texts[self.stage]:
                self.instruction.value = ''
            if self.stage < len(self.texts):
                lt = len(self.instruction.value)+1
                self.instruction.value = self.texts[self.stage][:lt]
                pick_sound.play(.3)
                if lt == len(self.texts[self.stage]):
                    self.stage += 1
                    self.last_letter += 3

    def on_update(self, dt):
        self.timer += dt
        if self.timer - self.last_letter >= self.period:
            self.update_text()
        self.scene.update()
        if self.stage != 5 and self.scene['Death'][0].alpha < 255:
            self.scene['Death'][0].alpha+=1
        if self.stage == 5:
            self.scene['Death'][0].alpha-=1
            self.instruction.color = [self.scene['Death'][0].alpha]*3
            if self.scene['Death'][0].alpha == 0:
                window.show_view(game_view)      
    
    def on_show_view(self):
        self.setup()


class WinView(arcade.View):
    def __init__(self):
        super().__init__()
        self.scene = arcade.Scene()

    def setup(self):
        self.scene.add_sprite('Death', Death())
        self.scene['Death'][0].alpha = 0
        self.instruction = arcade.Text('', 100, 300, font_size=26, font_name=('Gora Free'), multiline=True, width = 1000)
        self.timer = 0
        self.last_letter = 0
        self.period = .07
        self.stage = 0
        self.texts = {
            0: 'ты победил...',
            1: 'ты обыграл и убил саму СМЕРТЬ',
            2: 'раз так, я дам ответ на твой самый главный вопрос...',
            3: '...',
            4: 'сорок два',
        }

    def on_draw(self):
        self.clear()
        self.scene.draw()
        self.instruction.draw()

    def update_text(self):
        if self.stage != 5:
            self.last_letter = self.timer
            if not self.instruction.value in self.texts[self.stage]:
                self.instruction.value = ''
            if self.stage < len(self.texts):
                lt = len(self.instruction.value)+1
                self.instruction.value = self.texts[self.stage][:lt]
                pick_sound.play(.3)
                if lt == len(self.texts[self.stage]):
                    self.stage += 1
                    self.last_letter += 3

    def on_update(self, dt):
        self.timer += dt
        if self.timer - self.last_letter >= self.period:
            self.update_text()
        self.scene.update()
        if self.stage != 5 and self.scene['Death'][0].alpha < 255:
            self.scene['Death'][0].alpha+=1
        if self.stage == 5 and self.scene['Death'][0].alpha != 0:
            self.scene['Death'][0].alpha-=1
            self.instruction.color = [self.scene['Death'][0].alpha]*3
    
    
    def on_show_view(self):
        self.setup()


class LoseView(arcade.View):
    def __init__(self):
        super().__init__()
        self.scene = arcade.Scene()

    def setup(self):
        self.scene.add_sprite('Death', Death())
        self.scene['Death'][0].alpha = 0
        self.instruction = arcade.Text('', 100, 300, font_size=26, font_name=('Gora Free'), multiline=True, width = 1000)
        self.timer = 0
        self.last_letter = 0
        self.period = .07
        self.stage = 0
        self.texts = {
            0: 'ты проиграл...',
            1: 'тебя убила сама СМЕРТЬ в чистом виде',
            2: 'ты даже не заслуживал этой игры',
            3: '...',
            4: 'прощай',
        }

    def on_draw(self):
        self.clear()
        self.scene.draw()
        self.instruction.draw()

    def update_text(self):
        if self.stage != 5:
            self.last_letter = self.timer
            if not self.instruction.value in self.texts[self.stage]:
                self.instruction.value = ''
            if self.stage < len(self.texts):
                lt = len(self.instruction.value)+1
                self.instruction.value = self.texts[self.stage][:lt]
                pick_sound.play(.3)
                if lt == len(self.texts[self.stage]):
                    self.stage += 1
                    self.last_letter += 3

    def on_update(self, dt):
        self.timer += dt
        if self.timer - self.last_letter >= self.period:
            self.update_text()
        self.scene.update()
        if self.stage != 5 and self.scene['Death'][0].alpha < 255:
            self.scene['Death'][0].alpha+=1
        if self.stage == 5 and self.scene['Death'][0].alpha != 0:
            self.scene['Death'][0].alpha-=1
            self.instruction.color = [self.scene['Death'][0].alpha]*3
    
    
    def on_show_view(self):
        self.setup()


window = arcade.Window(1280, 800, 'after death', center_window=True)
arcade.load_font('gora-free-regular1.ttf')
game_view = GameView()
start_view = StartView()
win_view = WinView()
lose_view = LoseView()
window.show_view(start_view)
arcade.run()
