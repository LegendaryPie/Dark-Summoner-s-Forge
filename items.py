import pygame

from spritesheets import spritesheet
from buttons import Button, ButtonGroup

class Items:
    
    def __init__(self,props, inventory, data, index = 0, quantity = None, base_data = "GameData/Items/Base.json"):
        self.props = props
        self.inventory = inventory
        self.index = index
        self.font = pygame.font.Font(None, 18)
        
        if data == 'create_new':
            with open(base_data, 'r') as file:
                data = json.load(file)
            self.load_data(data)
        elif isinstance(data, str):
            with open("GameData/Items/"+data+".json", 'r') as file:
                data = json.load(file)
            self.load_data(data)
        else:
            self.load_data(data)
        self.selected = False
        
        if quantity != None:
            self.quantity = quantity
            
        if isinstance(self.sprite_png, list):
            sheet = spritesheet(self.sprite_png[0])
            self.sprite = sheet.image_at(tuple(self.sprite_png[1]))
        else:
            self.sprite = pygame.image.load(self.sprite_png)
        if isinstance(self.hot_bar_sprite_png, list):
            sheet = spritesheet(self.hot_bar_sprite_png[0])
            self.hot_bar_sprite = sheet.image_at(tuple(self.hot_bar_sprite_png[1]))
        else:
            self.hot_bar_sprite = pygame.image.load(self.hot_bar_sprite_png)
        if isinstance(self.inventory_background_png, list):
            sheet = spritesheet(self.inventory_background_png[0])
            self.inventory_background = sheet.image_at(tuple(self.inventory_background_png[1]))
        else:
            self.inventory_background = pygame.image.load(self.inventory_background_png)
        if isinstance(self.ht_sprite_png, list):
            sheet = spritesheet(self.ht_sprite_png[0])
            self.ht_sprite = sheet.image_at(tuple(self.ht_sprite_png[1]))
        else:
            self.ht_sprite = pygame.image.load(self.ht_sprite_png)
        if isinstance(self.hotbar_background_png, list):
            sheet = spritesheet(self.hotbar_background_png[0])
            self.hotbar_background = sheet.image_at(tuple(self.hotbar_background_png[1]))
        else:
            self.hotbar_background = pygame.image.load(self.hotbar_background_png)
        self.sprite_rect = self.sprite.get_rect()
        self.moving_rect = self.ht_sprite.get_rect()
        
            
    def load_data(self, data):       
        for key in data:
            if key in ['initial_pos', 'pos']:
                setattr(self, key, tuple(data[key]))
            else:
                setattr(self, key, data[key])
        self.data = data
            
    def consume(self):
        self.entity.trigger(self.effect)
        self.quantity -= 1
        if self.quantity == 0:
            self.entity.inventory.remove(self)
            
    def equip(self):
        self.entity.inventory.items.append(self.entity.equipment[self.equipable])
        self.entity.equipment[self.equipable] = self
        self.entity.inventory.items.remove(self)
        
    def move(self):
        self.inventory.try_move(self)
            
    def render(self, x=0,y=0):
        self.text = self.font.render(str(self.quantity), False, (255, 255, 255))
        if self.selected == True:
            if x != 0:
                if self.index <= self.inventory.columns:
                    self.props.screen.blit(self.hotbar_background,(x,y,32,32))
                else:    
                    self.props.screen.blit(self.inventory_background,(x,y,32,32))
            self.props.screen.blit(self.ht_sprite, self.moving_rect)
        elif self.index <= self.inventory.columns-1:
            self.sprite_rect.x = x
            self.sprite_rect.y = y
            self.props.screen.blit(self.hot_bar_sprite,self.sprite_rect)
            self.props.screen.blit(self.text,(x,y))
            self.moving_rect.x = x
            self.moving_rect.y = y
        else:
            self.sprite_rect.x = x
            self.sprite_rect.y = y
            self.props.screen.blit(self.sprite,self.sprite_rect)
            self.props.screen.blit(self.text,(x,y))
            self.moving_rect.x = x
            self.moving_rect.y = y
        
        
class PlayerInventory:
    
    def __init__(self, props, entity, data):
        self.props = props
        self.entity = entity
        self.data = data
        self.load_data(self.data)
        if len(self.items) != 30:
            self.items = self.items + [None]*30
            del self.items[30:]
        self.exit_button = Button(props,"Back",self.props,'game', pygame.Rect(20,20, 50, 40), (200,200,200))
        self.buttons = ButtonGroup(self.props, [self.exit_button])
        self.active_box = None
        sheet = spritesheet("Assets/BG 6.png")
        self.empty_sprite = sheet.image_at((352,0,32,32))
        sheet1 = spritesheet("Assets/BG 9.png")
        self.empty_hotbar_sprite = sheet1.image_at((352,0,32,32))
        self.depositable = True
    
    def try_move(self, item):        
        if (self.x <= item.moving_rect.x <= self.x+self.width*self.columns) & (self.y <= item.moving_rect.x <= self.x+self.height*self.rows):
            c,r = round((item.moving_rect.x-self.x)/self.width), round((item.moving_rect.y-self.y)/self.height)
            index = r*self.columns+c
            print(self.items,index,c,r,self.columns)
            other_item = self.items[index]
            self.items[index] = item
            if item.inventory == self:
                self.items[item.index] = other_item
                if self.items[item.index]:
                    self.items[item.index].index = item.index
            elif item.inventory.depositable == True:
                item.inventory.items[item.index] = other_item
                if item.inventory.items[item.index]:
                    item.inventory.items[item.index].index = item.index
            elif self.find_empty_slot():
                self.items[self.empty_slot] = other_item
                if self.items[self.empty_slot]:
                    self.items[self.empty_slot].index = self.empty_slot
            else:
                other_item.drop()
                
            item.index = index 

    def find_empty_slot(self):
        for i, item in enumerate(self.items):
            if item is None:
                self.empty_slot = i
                return True
        return False

    def load_data(self, data):
        self.items = []
        for key in data:
            if key == 'items':
                for item in data[key]:
                    self.items.append(Items(self.props, self, item, index = len(self.items), quantity = data[key][item]))
            else:
                setattr(self, key, data[key])
        self.data = data
    
    def get_data(self):
        data = []
        for item in self.items:
            data.append(item.get_data())
        return data
    
    def render(self):
        for row in range(self.rows):
            for column in range(self.columns):
                item = self.items[row*self.columns+column]
                if item:
                    item.render(self.x+column*self.width, self.y+row*self.height)
                elif row == 0:
                    self.props.screen.blit(self.empty_hotbar_sprite, (self.x+column*self.width,self.y+row*self.height,self.width,self.height))
                else:
                    self.props.screen.blit(self.empty_sprite,(self.x+column*self.width,self.y+row*self.height,self.width,self.height))
        self.buttons.render()
        if self.active_box != None:
            self.items[self.active_box].render()
            
    def render_hotbar(self):
        for column in range(self.columns):
            item = self.items[column]
            if item:
                item.render(self.props.width-320+column*self.width,self.props.height-48)
            else:
                self.props.screen.blit(self.empty_hotbar_sprite, (self.props.width-320+column*self.width,self.props.height-48,self.width,self.height))
            
    def events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.buttons.events(event)
                for num, box in enumerate(self.items):
                    if box:
                        if box.sprite_rect.collidepoint(event.pos):
                            box.selected = True
                            self.active_box = num
                            print(self.active_box)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.active_box != None:
                    if self.items[self.active_box] != None:
                        self.items[self.active_box].selected = False
                        self.items[self.active_box].move()
                    self.active_box = None
                    print(self.active_box)

        if event.type == pygame.MOUSEMOTION:
            if self.active_box != None:
                self.items[self.active_box].moving_rect.move_ip(event.rel)
    
class ResourceInventory:
    
    def __init__(self, props, entity, data):
        self.props = props
        self.entity = entity
        self.data = data
        self.load_data(self.data)
        if len(self.items) != 30:
            self.items = self.items + [None]*30
            del self.items[30:]
        self.exit_button = Button(props,"Back",self.props,'game', pygame.Rect(20,20, 50, 40), (200,200,200))
        self.buttons = ButtonGroup(self.props, [self.exit_button])
        self.active_box = None
        sheet = spritesheet("Assets/BG 6.png")
        self.empty_sprite = sheet.image_at((352,0,32,32))
        sheet1 = spritesheet("Assets/BG 9.png")
        self.empty_hotbar_sprite = sheet1.image_at((352,0,32,32))
        self.depositable = True
    
    def try_move(self, item):        
        if (self.x <= item.moving_rect.x <= self.x+self.width*self.columns) & (self.y <= item.moving_rect.x <= self.x+self.height*self.rows):
            c,r = round((item.moving_rect.x-self.x)/self.width), round((item.moving_rect.y-self.y)/self.height)
            index = r*self.columns+c
            print(self.items,index,c,r,self.columns)
            other_item = self.items[index]
            self.items[index] = item
            if item.inventory == self:
                self.items[item.index] = other_item
                if self.items[item.index]:
                    self.items[item.index].index = item.index
            elif item.inventory.depositable == True:
                item.inventory.items[item.index] = other_item
                if item.inventory.items[item.index]:
                    item.inventory.items[item.index].index = item.index
            elif self.find_empty_slot():
                self.items[self.empty_slot] = other_item
                if self.items[self.empty_slot]:
                    self.items[self.empty_slot].index = self.empty_slot
            else:
                other_item.drop()
                
            item.index = index 

    def find_empty_slot(self):
        for i, item in enumerate(self.items):
            if item is None:
                self.empty_slot = i
                return True
        return False

    def load_data(self, data):
        self.items = []
        for key in data:
            if key == 'items':
                for item in data[key]:
                    self.items.append(Items(self.props, self, item, index = len(self.items), quantity = data[key][item]))
            else:
                setattr(self, key, data[key])
        self.data = data
    
    def get_data(self):
        data = []
        for item in self.items:
            data.append(item.get_data())
        return data
    
    def render(self):
        for row in range(self.rows):
            for column in range(self.columns):
                item = self.items[row*self.columns+column]
                if item:
                    item.render(self.x+column*self.width, self.y+row*self.height)
                elif row == 0:
                    self.props.screen.blit(self.empty_hotbar_sprite, (self.x+column*self.width,self.y+row*self.height,self.width,self.height))
                else:
                    self.props.screen.blit(self.empty_sprite,(self.x+column*self.width,self.y+row*self.height,self.width,self.height))
        self.buttons.render()
        if self.active_box != None:
            self.items[self.active_box].render()
            
    def render_hotbar(self):
        for column in range(self.columns):
            item = self.items[column]
            if item:
                item.render(self.props.width-320+column*self.width,self.props.height-48)
            else:
                self.props.screen.blit(self.empty_hotbar_sprite, (self.props.width-320+column*self.width,self.props.height-48,self.width,self.height))
            
    def events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.buttons.events(event)
                for num, box in enumerate(self.items):
                    if box:
                        if box.sprite_rect.collidepoint(event.pos):
                            box.selected = True
                            self.active_box = num
                            print(self.active_box)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.active_box != None:
                    if self.items[self.active_box] != None:
                        self.items[self.active_box].selected = False
                        self.items[self.active_box].move()
                    self.active_box = None
                    print(self.active_box)

        if event.type == pygame.MOUSEMOTION:
            if self.active_box != None:
                self.items[self.active_box].moving_rect.move_ip(event.rel)
        