import pygame

from user_interface import render_text_outline

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
    
    def __init__(self,props, text, char, event, rect = None,color = (0,0,0), text_size = 'default', background_box = True, outline = False):
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
        self.char = char
        self.event = event
        self.color = color
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.background_box = background_box
        self.outline = outline
    
    def render(self, screen):
        if self.background_box:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, self.highlight_color, self.rect)
            else:
                pygame.draw.rect(screen, self.color, self.rect)

        if self.outline:
            screen.blit(render_text_outline(self.text_raw,self.font),self.text_rect)
        else:
            screen.blit(self.text,self.text_rect)

    def trigger(self):
        print(self.event)
        self.char.trigger(event = self.event)
    
    @property
    def highlight_color(self):
        """Color of the hexagon tile when rendering highlight"""
        offset = 15
        brighten = lambda x, y: x + y if x + y < 255 else 255
        return tuple(brighten(x, offset) for x in self.color)