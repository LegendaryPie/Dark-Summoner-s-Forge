import pygame

import sys

_circle_cache = {}
def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points

def render_text_outline(text, font, gfcolor=(0,0,0), ocolor=(255, 255, 255), opx=2):
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf

class ButtonGroup:
    
    def __init__(self, props, buttons=[]):
        self.buttons = buttons
        self.props = props
        
    def events(self,event):
        for button in self.buttons:
            if button.rect.collidepoint(event.pos):
                button.trigger()
        
    def render(self):
        for button in self.buttons:
            button.render(self.props.screen)

class Button:
    
    def __init__(self,props, text, char, event, rect = None,color = (0,0,0), text_size = 'default', background_box = True, outline = False, activated = True, tooltip = None):
        # Create a font object

        self.props = props

        if text_size == 'default':
            self.font = props.font
        elif text_size == 'small':
            self.font = props.font_small
        elif text_size == 'large':
            self.font = props.font_large

        self.text_raw = text
        
        self.text = self.font.render(text, True, (0, 0, 0))
        self.rect = rect
        self.char = char
        self.event = event
        self.normal_color = color
        self.color = color
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.background_box = background_box
        self.outline = outline
        self.activated = activated
        self.tooltip = tooltip
    
    def render(self, screen):
        if not self.activated: 
            self.color = tuple([max(self.color)]*3)
        else:
            self.color = self.normal_color

        if self.rect.collidepoint(pygame.mouse.get_pos()) & self.activated:
            if self.background_box:
                pygame.draw.rect(screen, self.highlight_color, self.rect)
            if self.outline:
                screen.blit(render_text_outline(self.text_raw,self.font),self.text_rect)
            else:
                screen.blit(self.text,self.text_rect)
        else:
            if self.background_box:
                pygame.draw.rect(screen, self.color, self.rect)
            if self.outline:
                screen.blit(render_text_outline(self.text_raw,self.font, ocolor = (180,180,180)),self.text_rect)
            else:
                screen.blit(self.text,self.text_rect)
        if self.rect.collidepoint(pygame.mouse.get_pos()) and not self.activated and self.tooltip:
            screen.blit(render_text_outline(self.tooltip,self.props.font_small),pygame.mouse.get_pos())


    def trigger(self):
        if self.activated:
            print(self.event)
            self.char.trigger(event = self.event)
    
    @property
    def highlight_color(self):
        """Color of the hexagon tile when rendering highlight"""
        offset = 15
        brighten = lambda x, y: x + y if x + y < 255 else 255
        return tuple(brighten(x, offset) for x in self.color)

class Menu:
    
    def __init__(self, props, buttons = [], text_boxes = [], background = None, background_rect = None):
        self.props = props
        self.buttons = ButtonGroup(props, buttons)
        self.text_boxes = text_boxes
        self.background = background
        self.background_rect = background_rect
        
        
    def render(self):
        if self.background:
            self.props.screen.blit(self.background, self.background_rect if self.background_rect else (0,0))
        if self.text_boxes:
            for text_box in self.text_boxes:
                text_box.render()
        self.buttons.render()
        
    def events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
            self.buttons.events(event)

class Slider:

    def __init__(self, props, text, variable, slider_x = 500, slider_y=230, slider_width=200, slider_height=20, slider_knob_radius=10, slider_min=0, slider_max=100):
        self.props = props
        self.text = text
        self.variable = variable
        self.slider_x = slider_x
        self.slider_y = slider_y
        self.slider_width = slider_width
        self.slider_height = slider_height
        self.slider_knob_radius = slider_knob_radius
        self.slider_min = slider_min
        self.slider_max = slider_max
        self.font = self.props.font
    
    def render(self):
        self.props.screen.blit(render_text_outline(self.text, self.font, gfcolor=(0,0,0), ocolor=(255, 255, 255), opx=2),(500,self.slider_y-30))
        pygame.draw.rect(self.props.screen, (100,100,100), (self.slider_x, self.slider_y, self.slider_width, self.slider_height))
        knob_x = self.slider_x + int(self.variable / self.slider_max * self.slider_width)
        pygame.draw.circle(self.props.screen, (50,200,50), (knob_x, self.slider_y + self.slider_height // 2), self.slider_knob_radius)

    def events(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.slider_x <= mouse_x <= self.slider_x + self.slider_width and self.slider_y - self.slider_knob_radius <= mouse_y <= self.slider_y + self.slider_height + self.slider_knob_radius:
                    # Update volume based on mouse position
                    self.variable = int((mouse_x - self.slider_x) / self.slider_width * (self.slider_max - self.slider_min))
        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:  # Left mouse button is held down
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if self.slider_x <= mouse_x <= self.slider_x + self.slider_width:
                    # Update volume based on mouse position
                    self.props.volume = int((mouse_x - self.slider_x) / self.slider_width * (self.slider_max - self.slider_min))
        
class StartOptionsMenu:
    
    def __init__(self, props, start_menu):

        self.buttons = ButtonGroup(props,[Button(props, "Exit",start_menu,'start', pygame.Rect(props.width/2-75, props.height/2+60, 150, 50), (200,200,200), background_box = False, outline = True)])
        self.props = props
        self.font = self.props.font
        self.start_menu = start_menu
        self.volume_control = Slider(self.props,'Volume Control',self.props.volume, slider_max=25)
        self.effects_volume_control = Slider(self.props,'Effect Volume Control',self.props.effects_volume, slider_y = 300, slider_max=10)
    
    def render(self):
        self.props.screen.blit(render_text_outline("Options", self.font, gfcolor=(0,0,0), ocolor=(255, 255, 255), opx=2),(500,100))
        self.volume_control.render()
        self.effects_volume_control.render()
        self.buttons.render()
        
    def events(self, event):
        self.buttons.events(event)   
        self.volume_control.events(event)
        self.effects_volume_control.events(event)
        pygame.mixer.music.set_volume(self.volume_control.variable / 100)

                         
            
        

class StartMenu(Menu):
    
    def __init__(self, props):
        self.state = 'start'
        self.states = ['start','options','saves']
        self.font = props.font_large
        self.text1 = self.font.render("Dark Summoner's",True, (0,0,0))
        self.text2 = self.font.render("Forge",True, (0,0,0))
         
        

        play = Button(props, "Play",props,'game', pygame.Rect(props.width/2-75, props.height/2-120, 150, 50), (200,200,200), background_box = False, outline = True)
        options = Button(props, "Options",self,'options', pygame.Rect(props.width/2-75, props.height/2-60, 150, 50), (200,200,200), background_box = False, outline = True)
        exit = Button(props, "Exit",props,'quit', pygame.Rect(props.width/2-75, props.height/2, 150, 50), (200,200,200), background_box = False, outline = True)
        buttons = [play,options,exit]
        background = pygame.transform.scale(pygame.image.load('PortalResource-export.png').convert_alpha(),(props.height,props.height))
        super().__init__(props, buttons, background = background, background_rect= ())
        
        self.options_menu = StartOptionsMenu(self.props, self)
        
        #self.name = TextBox(props, "Dark Summoner's Forge",pygame.Rect(props.width/2-300, props.height/2-250, 600, 150), (200,200,200), text_size = 'large')
    
    def trigger(self,event):
        if event in self.states:
            self.state = event
            
    def render(self):
        if self.state == 'start':
            if self.background:
                self.props.screen.blit(self.background, (200,0))
            self.buttons.render()
            self.props.screen.blit(render_text_outline("Dark Summoner's", self.font, gfcolor=(0,0,0), ocolor=(255, 255, 255), opx=2),(300,100))  
            self.props.screen.blit(render_text_outline("Forge", self.font, gfcolor=(0,0,0), ocolor=(255, 255, 255), opx=2),(500,550))          
            
        elif self.state == 'options':
            self.options_menu.render()
        elif self.state == 'saves':
            self.save_menu.render()
        
    def events(self,event):
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.props.terminated = True 
                    pygame.quit()
                    sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
            if self.state == 'start':
                self.buttons.events(event)
            elif self.state == 'saves':
                self.save_menu.events(event)
            elif self.state == 'options':
                self.options_menu.events(event)
                

class DeathMenu(Menu):
    
    def __init__(self, props):
        self.props = props
        respawn = Button(props, "Respawn",self,'respawn', pygame.Rect(props.width/2-75, props.height/2, 150, 50), (200,200,200))
        message = [TextBox(self.props, "You Died",pygame.Rect(props.width/2-75, props.height/2-60, 150, 50), (200,200,200))]
        buttons = [respawn]
        super().__init__(props, buttons, message, None)

    def trigger(self,event):
        if event == 'respawn':
            self.props.player.trigger('respawn')
        

    
    
class Overlay:
    
    def __init__(self, props):
        self.props = props
        
    def render(self):
        self.props.player.inventory.render_hotbar()


class TextBox:
    
    def __init__(self, props, text, rect, color, text_size = 'default', sizing = 'static', centering = None):
        # Create a font object
        if text_size == 'default':
            self.font = props.font
        elif text_size == 'small':
            self.font = props.font_small
        elif text_size == 'large':
            self.font = props.font_large
        
        self.text_raw = text
        self.text = self.font.render(text, True, (0, 0, 0))
        self.rect = rect
        self.color = color
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.props = props
        self.sizing = sizing
        self.centering = centering
    
    def render(self):
        if isinstance(self.text_raw,str):
            self.text = self.font.render(self.text_raw,True, (0,0,0))
            if self.sizing == 'dynamic':
                self.rect.width = self.font.size(self.text_raw)[0] + 10
        if self.centering == 'horizontal':
            self.rect.x = self.props.width/2-self.rect.width/2
        pygame.draw.rect(self.props.screen, self.color, self.rect)
        self.props.screen.blit(self.text,self.text_rect)
        
class ConfirmationBox:
    
    def __init__(self, props, char, text, pos = 'center'):
        self.props = props
        self.text = text
        self.char = char
        
        self.yes = Button(props, "Yes",self,'yes', pygame.Rect(props.width/2-80, props.height/2-70, 75, 50), (200,200,200))
        self.no = Button(props, "No",self,'no', pygame.Rect(props.width/2+5, props.height/2-70, 75, 50), (200,200,200))
        
        self.buttons = ButtonGroup(props, [self.yes, self.no])
        
        self.answer = None
        
    def render(self):
        self.confirmation_textbox = TextBox(self.props, self.text, pygame.Rect(self.props.width/2-200, self.props.height/2-120, 400, 50), (150,150,150))
        self.confirmation_textbox.render()
        pygame.draw.rect(self.props.screen, (180,180,180), pygame.Rect(self.props.width/2-200, self.props.height/2-70, 400, 100))
        self.buttons.render()
        
        
    def trigger(self, event):
        print(event)
        if event == 'yes':
            self.answer = 'yes'
            self.char.trigger('yes')
        if event == 'no':
            self.answer = 'no'
            self.char.trigger('yes')
            
    def events(self, event):
        self.buttons.events(event)
                         




class Bar:
    def __init__(self, props, entity, x, y, w, h, attribute_name, max_attribute_name, top_color, bottom_color):
        self.props = props
        self.entity = entity
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.attribute_name = attribute_name
        self.max_attribute_name = max_attribute_name
        self.attribute = getattr(self.entity, self.attribute_name)
        self.max_attribute = getattr(self.entity, self.max_attribute_name)
        self.top_color = top_color
        self.bottom_color = bottom_color

    def draw(self,x = None, y = None):
        #calculate health ratio
        if x:
            self.x = x
        if y:
            self.y = y
        self.attribute = getattr(self.entity, self.attribute_name)
        self.max_attribute = getattr(self.entity, self.max_attribute_name)
        ratio = self.attribute / self.max_attribute
        pygame.draw.rect(self.props.screen, self.bottom_color, (self.x, self.y, self.w, self.h))
        pygame.draw.rect(self.props.screen, self.top_color, (self.x, self.y, self.w * ratio, self.h))

        