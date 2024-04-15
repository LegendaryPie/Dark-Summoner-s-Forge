import random
from typing import List
from typing import Tuple
import sys, asyncio, math, time, os, copy

import pygame

from user_interface import StartMenu, Overlay, DeathMenu, Button, ButtonGroup
from spritesheets import spritesheet

def point_along_line(from_point, to_point, distance):
    # Calculate the vector from "from" point to "to" point
    dx = to_point[0] - from_point[0]
    dy = to_point[1] - from_point[1]

    # Calculate the distance between the two points
    length = math.sqrt(dx**2 + dy**2)

    # Normalize the vector to get the direction
    if length > 0:
        dx /= length
        dy /= length

    # Scale the direction vector by the distance
    if distance > length:
        new_point = (from_point[0] + dx * length, from_point[1] + dy * length)
    else:
        new_point = (from_point[0] + dx * distance, from_point[1] + dy * distance)
    return new_point

def determine_direction(point1, point2):
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]

    if abs(dx) > abs(dy):
        if dx > 0:
            return 'right' 
        else:
            return 'left'
    else:
        if dy > 0:
            return 'down' 
        else:
            return 'up'

def format_large_number(number):
    suffixes = ['', 'K', 'M', 'B', 'T', 'Qa', 'Qi','Sx', 'Sp', 'O', 'N','D']  # List of suffixes for thousands, millions, billions, trillions, etc.

    if number < 1000:
        return str(number)  # Return the number as-is if it's less than 1000

    # Determine the appropriate suffix for the number
    magnitude = 0
    while abs(number) >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        number /= 1000.0

    # Format the number with the appropriate suffix
    formatted_number = '{:.2f}{}'.format(number, suffixes[magnitude])

    return formatted_number

class Gatherer:

    def __init__(self, props, name, description, max_capacity, gathering_speed, moving_speed, resources_gatherable,animations):
        self.props = props
        self.name = name
        self.description = description

        self.base_max_capacity = max_capacity
        self.max_capacity = max_capacity
        self.base_gathering_speed = gathering_speed
        self.gathering_speed = gathering_speed
        self.base_moving_speed = moving_speed
        self.moving_speed = moving_speed

        self.gathering_wait = 1/self.gathering_speed
        self.last_gather_time = 0
        self.resources_gatherable = resources_gatherable
        self.inventory = {}
        for resource in self.resources_gatherable:
            self.inventory[resource] = 0
        self.animations_file = animations
        self.height = 32
        self.width = 32
        self.animations = {'moving':{'down':animations.images_at([(i*self.width,0,self.width,32) for i in range(5)]),
                                     'up':animations.images_at([(i*self.width,self.height,self.width,32) for i in range(5)]),
                                     'left':animations.images_at([(i*self.width,self.height*2,self.width,32) for i in range(5)]),
                                     'right':animations.images_at([(i*self.width,self.height*3,self.width,32) for i in range(5)])}}
        self.current_frame = 0
        self.state = 'idle'
        self.position = (0,0)
        self.fixed_point = False
        self.fixed_size = False
        self.assignment = None
        self.moving = False
        self.first_gather = True

    def update_stats(self):
        self.max_capacity = (self.base_max_capacity+self.props.bonuses['max_capacity']['additive'])*self.props.bonuses['max_capacity']['multiplicative']
        self.gathering_speed = (self.base_gathering_speed+self.props.bonuses['gathering_speed']['additive'])*self.props.bonuses['gathering_speed']['multiplicative']
        self.moving_speed = (self.base_moving_speed+self.props.bonuses['moving_speed']['additive'])*self.props.bonuses['moving_speed']['multiplicative']
        self.gathering_wait = 1/self.gathering_speed

    def assign(self, selected_tile):
        if selected_tile[0] in self.props.assignments:
            self.props.tooltip = "Another Worker is already assigned to that resource"
            self.props.tooltip_ticks = 60
        elif selected_tile[2] in self.resources_gatherable:
            if self.assignment:
                del self.props.assignments[self.assignment[0]]
            self.assignment = selected_tile
            self.props.selected_gatherer = None
            self.state = 'gathering'
        else:
            self.props.tooltip = "I cannot gather that resource"
            self.props.tooltip_ticks = 60


    def run(self):
        if self.state == 'idle':
            pass
        elif self.state in 'gathering':
            self.gather()
        elif self.state == 'drop off':
            self.drop_off()
        
    def drop_off(self):
            if math.dist(self.position,(0,0)) > 0.5:
                self.position = point_along_line(self.position,(0,0),self.moving_speed)
                self.direction = determine_direction((self.assignment[1].x,self.assignment[1].y), self.screen_position)
                self.moving = True
            else:
                self.props.resource_quantities[self.assignment[2]] += self.inventory[self.assignment[2]]
                self.inventory[self.assignment[2]] = 0
                self.state = 'gathering'

    def gather(self):
        if self.assignment:
            x,y = self.assignment[0]
            self.assignment[1] = pygame.Rect(x * self.props.TILE_SIZE + self.props.player_x, y * self.props.TILE_SIZE + self.props.player_y, self.props.TILE_SIZE, self.props.TILE_SIZE)
            if math.dist(self.position,self.assignment[0]) > 0.5:
                self.position = point_along_line(self.position,self.assignment[0],self.moving_speed)
                self.direction = determine_direction(self.screen_position, (self.assignment[1].x,self.assignment[1].y))
                self.moving = True
            else:
                self.state = 'gathering'
                self.try_gather()

    def try_gather(self):
        current_time = time.time()
        if current_time - self.last_gather_time >= self.gathering_wait:
            if self.first_gather:
                self.inventory[self.assignment[2]] += 1
                self.first_gather = False
            else:
                self.inventory[self.assignment[2]] += math.ceil((current_time - self.last_gather_time) / self.gathering_wait)
            self.last_gather_time = current_time
            print(current_time,self.last_gather_time,self.gathering_wait)
            if self.inventory[self.assignment[2]] >= self.max_capacity:
                self.state = 'drop off'
                self.first_gather = True


    def render(self):
        self.run()
        if not self.fixed_point:
            self.screen_position = (self.position[0]*self.props.TILE_SIZE + self.props.player_x,self.position[1]*self.props.TILE_SIZE + self.props.player_y)
        else:
            self.screen_position = self.position

        if not self.fixed_size:
            self.size = (self.props.TILE_SIZE,self.props.TILE_SIZE)
        else:
            self.size = (32,32)

        self.rect = pygame.Rect(self.screen_position[0], self.screen_position[1],self.props.TILE_SIZE,self.props.TILE_SIZE)

        self.current_frame += 1
        if self.moving:
            if self.current_frame % 10 == 0:
                for direction, animation_frames in self.animations['moving'].items():
                    self.animations['moving'][direction] = animation_frames[1:] + [animation_frames[0]]


            # Render the current animation frame based on the direction
            self.props.screen.blit(pygame.transform.scale(self.animations['moving'][self.direction][0],self.size),self.screen_position)
        else:
            if self.state in ['idle','gathering']:
                self.props.screen.blit(pygame.transform.scale(self.animations['moving']['down'][0],self.size),self.screen_position)

    def copy(self):
        return Gatherer(self.props, self.name, self.description, self.max_capacity, self.gathering_speed, self.moving_speed, self.resources_gatherable,self.animations_file)

class TaskMaster:

    def __init__(self, props, name, description, moving_speed, animations, effect):
        self.props = props
        self.name = name
        self.description = description
        self.moving_speed = moving_speed
        self.effect = effect

        self.target_change_chance = 0.003
        
        self.animations_file = animations
        self.height = 64
        self.width = 64
        self.animations_file = animations
        self.animations = {'moving':{'right':animations.images_at([(i*self.width,0,self.width,self.height) for i in range(1)]),
                                     'left':animations.images_at([(i*self.width,self.height,self.width,self.height) for i in range(1)]),
                                     'up':animations.images_at([(i*self.width,self.height*2,self.width,self.height) for i in range(1)]),
                                     'down':animations.images_at([(i*self.width,self.height*3,self.width,self.height) for i in range(1)])}}
        self.current_frame = 0
        self.state = 'idle'
        self.position = (0,0)
        self.fixed_point = False
        self.fixed_size = False
        self.assignment = None
        self.moving = False
        self.direction = 'down'
        self.target = None

    def run(self):
        if self.target == None:
            self.find_target()
        if self.target:
            if math.dist(self.position,self.target.position) > 0.5:
                self.position = point_along_line(self.position,self.target.position,self.moving_speed)
                self.direction = determine_direction(self.screen_position, self.target.screen_position)
                self.moving = True
            if random.random() < self.target_change_chance:
                self.find_target()
        

    def find_target(self):
        choices = [x for x in self.props.gatherers if x not in [x.target for x in self.props.task_masters]]
        if choices:
            self.target = random.choice(choices)
        else:
            self.target = None

    def render(self):

        if not self.fixed_point:

            self.screen_position = (self.position[0]*self.props.TILE_SIZE + self.props.player_x,self.position[1]*self.props.TILE_SIZE + self.props.player_y)
        else:
            self.screen_position = self.position

        if not self.fixed_size:
            self.size = (self.props.TILE_SIZE,self.props.TILE_SIZE)
        else:
            self.size = (32,32)

        self.rect = pygame.Rect(self.screen_position[0], self.screen_position[1],self.props.TILE_SIZE,self.props.TILE_SIZE)

        self.current_frame += 1
        if self.moving:
            if self.current_frame % 10 == 0:
                for direction, animation_frames in self.animations['moving'].items():
                    self.animations['moving'][direction] = animation_frames[1:] + [animation_frames[0]]

                self.direction = 'down' #determine_direction(self.screen_position, (self.assignment[1].x,self.assignment[1].y))

            # Render the current animation frame based on the direction
            self.props.screen.blit(pygame.transform.scale(self.animations['moving'][self.direction][0],self.size),self.screen_position)
        else:
            if self.state in ['idle','gathering']:
                self.props.screen.blit(pygame.transform.scale(self.animations['moving']['down'][0],self.size),self.screen_position)
        self.run()

    def copy(self):
        return TaskMaster(self.props, self.name, self.description, self.moving_speed, self.animations_file, self.effect)


class Descriptions:
    def __init__(self, props, name, description):
        self.props = props
        self.name = name
        self.description = description

    def render(self):
        pass    


class PortalSummoning:
    
    def __init__(self,props):
        self.props = props

        self.summon_sound = pygame.mixer.Sound("Summon.wav")

        self.g_w_slime = Gatherer(props, 'Green Worker Slime','Basic Gathering Slime can collect Wood and Essence',10,1,0.02,['Wood','Essence'],spritesheet("SlimeWorker-Sheet.png"))
        self.b_w_slime = Gatherer(props, 'Blue Worker Slime','Gathering Slime can collect Iron, Wood, and Essence',25,3,0.03,['Iron', 'Wood', 'Essence'],spritesheet("BlueSlimeWorker-Sheet.png"))
        self.r_w_slime = Gatherer(props, 'Red Worker Slime','Gathering Slime can collect Iron, Gold, and Essence',50,5,0.04,['Iron', 'Gold','Essence'],spritesheet("RedSlimeWorker-Sheet.png"))
        self.p_w_slime = Gatherer(props, 'Purple Worker Slime','Gathering Slime can collect Rubies, Gold, and Essence',200,10,0.06,['Rubies', 'Gold', 'Essence'],spritesheet("PurpleSlimeWorker-Sheet.png"))
        self.bk_w_slime = Gatherer(props, 'Black Worker Slime','Gathering Slime can collect Rubies, Demonic Iron and Pure Essence',500,25,0.06,['Rubies', 'Demonic Iron',' Pure Essence'],spritesheet("BlackSlimeWorker-Sheet.png"))


        self.minor_demon = TaskMaster(props, 'Minor Demon', 'Increases the movement speed of workers',0.01,spritesheet('MinorDemon.png'),{'moving_speed':{'method':'additive','magnitude':0.01}})
        self.demon = TaskMaster(props, 'Demon', 'Increases the gathering speed and capacity of workers',0.01,spritesheet('Demon.png'),{'gathering_speed':{'method':'additive','magnitude':1},'max_capacity':{'method':'additive','magnitude':10}})
        self.major_demon = TaskMaster(props, 'Major Demon', 'Increases the gathering speed and capacity of workers',0.01,spritesheet('MajorDemon.png'),{'gathering_speed':{'method':'multiplicative','magnitude':1.2},'max_capacity':{'method':'multiplicative','magnitude':1.2}})
        self.demon_overlord = TaskMaster(props, 'Demon Overlord', 'Increases the gathering speed and capacity of workers',0.01,spritesheet('DemonOverlord.png'),{'gathering_speed':{'method':'multiplicative','magnitude':2},'max_capacity':{'method':'multiplicative','magnitude':2}})


        self.level_1_description = Descriptions(props,'Level 1','Gain access to Blue Worker Slime')
        self.level_2_description = Descriptions(props,'Level 2','Gain access to Minor Demon Taskmasters')
        self.level_3_description = Descriptions(props,'Level 3','Gain access to Demon Taskmasters')
        self.level_4_description = Descriptions(props,'Level 4','Gain access to Blue Worker Slime')
        self.level_5_description = Descriptions(props,'Level 5','Gain access to Minor Demon Taskmasters')
        self.level_6_description = Descriptions(props,'Level 6','Gain access to Major Demon Taskmasters')

        self.costs = {
            'Green Worker Slime':{'Essence':{'base':5,'multiplier':1.1}},
            'Blue Worker Slime': {'Essence':{'base':20,'multiplier':1.2}},
            'Red Worker Slime': {'Essence':{'base':200,'multiplier':1.2}},
            'Purple Worker Slime': {'Essence':{'base':10000,'multiplier':1.2}},
            'Black Worker Slime': {'Essence':{'base':100000,'multiplier':1.2}},
            'Minor Demon': {'Essence':{'base':50,'multiplier':2.5}},
            'Demon': {'Essence':{'base':200,'multiplier':2.5}},
            'Major Demon': {'Essence':{'base':2500,'multiplier':3}},
            'Demon Overlord': {'Pure Essence':{'base':250000,'multiplier':10}},
        }

        self.recipes = {
            0:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':20},
               'Upgrade Portal':{'reward':self.level_1_description,'cost':{'Wood':{'base':200,'multiplier':1.5}, 'bought':0}, 'quantity':1},},
            1:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Blue Worker Slime': {'reward':self.b_w_slime,'cost':{'Essence':self.costs['Blue Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Minor Demon': {'reward':self.minor_demon,'cost':{'Essence':self.costs['Minor Demon']['Essence'], 'bought':0},'quantity':2},
               'Upgrade Portal':{'reward':self.level_2_description,'cost':{'Wood':{'base':1000,'multiplier':1.8},'Iron':{'base':1000,'multiplier':1.8}, 'bought':0}, 'quantity':1},},
            2:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':20},
               'Blue Worker Slime': {'reward':self.b_w_slime,'cost':{'Essence':self.costs['Blue Worker Slime']['Essence'], 'bought':10},'quantity':10},
               'Red Worker Slime': {'reward':self.r_w_slime,'cost':{'Essence':self.costs['Red Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Minor Demon': {'reward':self.minor_demon,'cost':{'Essence':self.costs['Minor Demon']['Essence'], 'bought':2},'quantity':2},
               'Demon': {'reward':self.demon,'cost':{'Essence':self.costs['Demon']['Essence'], 'bought':0},'quantity':2},
               'Upgrade Portal':{'reward':self.level_3_description,'cost':{'Wood':{'base':5000,'multiplier':1.8}, 'Iron':{'base':5000,'multiplier':1.8}, 'Gold':{'base':5000,'multiplier':1.8}, 'bought':0}, 'quantity':1},},
            3:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':20},
               'Blue Worker Slime': {'reward':self.b_w_slime,'cost':{'Essence':self.costs['Blue Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Red Worker Slime': {'reward':self.r_w_slime,'cost':{'Essence':self.costs['Red Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Minor Demon': {'reward':self.minor_demon,'cost':{'Essence':self.costs['Minor Demon']['Essence'], 'bought':0},'quantity':2},
               'Demon': {'reward':self.demon,'cost':{'Essence':self.costs['Demon']['Essence'], 'bought':0},'quantity':2},
               'Major Demon': {'reward':self.major_demon,'cost':{'Essence':self.costs['Major Demon']['Essence'], 'bought':0},'quantity':2},
                'Upgrade Portal':{'reward':self.level_3_description,'cost':{'Wood':{'base':100000,'multiplier':1.8}, 'Iron':{'base':100000,'multiplier':1.8}, 'Gold':{'base':100000,'multiplier':1.8}, 'bought':0}, 'quantity':1},},
            4:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':20},
               'Blue Worker Slime': {'reward':self.b_w_slime,'cost':{'Essence':self.costs['Blue Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Red Worker Slime': {'reward':self.r_w_slime,'cost':{'Essence':self.costs['Red Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Purple Worker Slime': {'reward':self.p_w_slime,'cost':{'Essence':self.costs['Purple Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Minor Demon': {'reward':self.minor_demon,'cost':{'Essence':self.costs['Minor Demon']['Essence'], 'bought':0},'quantity':2},
               'Demon': {'reward':self.demon,'cost':{'Essence':self.costs['Demon']['Essence'], 'bought':0},'quantity':2},
               'Major Demon': {'reward':self.major_demon,'cost':{'Essence':self.costs['Major Demon']['Essence'], 'bought':0},'quantity':2},
               'Upgrade Portal':{'reward':self.level_3_description,'cost':{'Wood':{'base':1000000,'multiplier':1.8}, 'Iron':{'base':1000000,'multiplier':1.8}, 'Gold':{'base':1000000,'multiplier':1.8}, 'Rubies':{'base':1000000,'multiplier':1.8}, 'bought':0}, 'quantity':1},},
            5:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':20},
               'Blue Worker Slime': {'reward':self.b_w_slime,'cost':{'Essence':self.costs['Blue Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Red Worker Slime': {'reward':self.r_w_slime,'cost':{'Essence':self.costs['Red Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Purple Worker Slime': {'reward':self.p_w_slime,'cost':{'Essence':self.costs['Purple Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Black Worker Slime': {'reward':self.bk_w_slime,'cost':{'Essence':self.costs['Black Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Minor Demon': {'reward':self.minor_demon,'cost':{'Essence':self.costs['Minor Demon']['Essence'], 'bought':0},'quantity':2},
               'Demon': {'reward':self.demon,'cost':{'Essence':self.costs['Demon']['Essence'], 'bought':0},'quantity':2},
               'Major Demon': {'reward':self.major_demon,'cost':{'Essence':self.costs['Major Demon']['Essence'], 'bought':0},'quantity':2},
               'Demon Overlord': {'reward':self.demon_overlord,'cost':{'Pure Essence':self.costs['Demon Overlord']['Pure Essence'], 'bought':0},'quantity':2},
               'Upgrade Portal':{'reward':self.level_3_description,'cost':{'Wood':{'base':10000000,'multiplier':1.8}, 'Iron':{'base':10000000,'multiplier':1.8}, 'Gold':{'base':10000000,'multiplier':1.8}, 'Rubies':{'base':10000000,'multiplier':1.8}, 'Demonic Iron':{'base':10000000,'multiplier':1.8}, 'bought':0}, 'quantity':1},},
            6:{'Green Worker Slime':{'reward':self.g_w_slime,'cost':{'Essence':self.costs['Green Worker Slime']['Essence'], 'bought':0},'quantity':20},
               'Blue Worker Slime': {'reward':self.b_w_slime,'cost':{'Essence':self.costs['Blue Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Red Worker Slime': {'reward':self.r_w_slime,'cost':{'Essence':self.costs['Red Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Purple Worker Slime': {'reward':self.p_w_slime,'cost':{'Essence':self.costs['Purple Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Black Worker Slime': {'reward':self.bk_w_slime,'cost':{'Essence':self.costs['Black Worker Slime']['Essence'], 'bought':0},'quantity':10},
               'Minor Demon': {'reward':self.minor_demon,'cost':{'Essence':self.costs['Minor Demon']['Essence'], 'bought':0},'quantity':2},
               'Demon': {'reward':self.demon,'cost':{'Essence':self.costs['Demon']['Essence'], 'bought':0},'quantity':2},
               'Major Demon': {'reward':self.major_demon,'cost':{'Essence':self.costs['Major Demon']['Essence'], 'bought':0},'quantity':2},
               'Demon Overlord': {'reward':self.demon_overlord,'cost':{'Pure Essence':self.costs['Demon Overlord']['Pure Essence'], 'bought':0},'quantity':2},
               },
                        }
                        
        
        self.level = 0

    def update_recipes(self):
        for name, recipe_data in self.recipes[self.level-1].items():
            if name in self.recipes[self.level].keys():
                self.recipes[self.level][name]['quantity'] += recipe_data['quantity']
                self.recipes[self.level][name]['cost']['bought'] = recipe_data['cost']['bought']


    def render(self):    
        # Draw a box in the middle of the screen for the shop interface
        shop_box_width = 450
        shop_box_height = 750
        shop_box_x = (1200 - shop_box_width) // 2
        shop_box_y = (800 - shop_box_height) // 2
        pygame.draw.rect(self.props.screen, (200, 200, 200), (shop_box_x, shop_box_y, shop_box_width, shop_box_height))

        # Draw the 'x' button to exit the shop
        exit_button_x = shop_box_x + shop_box_width - 150
        exit_button_y = shop_box_y
        exit = Button(self.props, "Exit",self.props,'game', pygame.Rect(exit_button_x, exit_button_y, 150, 50), (200,200,200), background_box = False, outline = True)
        self.buttons = ButtonGroup(self.props, [exit])

        

        # Render each recipe in the shop
        recipe_y = shop_box_y + 50
        self.reward_description_text = None
        for recipe_name, recipe_data in self.recipes[self.level].items():
            # Render recipe name
            recipe_font = self.props.font
            recipe_text = recipe_font.render(recipe_name, True, (0,0,0))
            self.props.screen.blit(recipe_text, (shop_box_x + 20, recipe_y))
            recipe_data['name'] = recipe_name

            # Render recipe cost
            cost_texts = []
            for cost, value in recipe_data['cost'].items():
                if cost != 'bought':
                    cost_texts.append(f'{cost}: {format_large_number(round(value['base']*value['multiplier']**recipe_data['cost']['bought']))}')
            
            if len(cost_texts) <=3:
                cost_text = f"Cost: {', '.join(cost_texts)}"
                cost_font = self.props.font_small
                cost_text_render = cost_font.render(cost_text, True, (0,0,0))
                self.props.screen.blit(cost_text_render, (shop_box_x + 20, recipe_y + 30))
            else:
                cost_text = f"Cost: {', '.join(cost_texts[:3])}"
                cost_font = self.props.font_small
                cost_text_render = cost_font.render(cost_text, True, (0,0,0))
                self.props.screen.blit(cost_text_render, (shop_box_x + 20, recipe_y + 30))
                cost_text1 = ', '.join(cost_texts[3:])
                cost_text_render1 = cost_font.render(cost_text1, True, (0,0,0))
                self.props.screen.blit(cost_text_render1, (shop_box_x + 20, recipe_y + 44))


            if recipe_name != 'Upgrade Portal':
                recipe_data['reward'].position = (shop_box_x +240, recipe_y)
                recipe_data['reward'].fixed_point = True
                recipe_data['reward'].fixed_size = True
                if recipe_data['quantity'] > 0:
                    self.buttons.buttons.append(
                        Button(self.props, "Summon",self,{'summon':recipe_data}, 
                            pygame.Rect(shop_box_x + 300, recipe_y, 100, 50), (200,0,0), 
                            background_box = True, outline = True, activated = self.props.can_buy(recipe_data['cost']), tooltip = 'Insufficient Resources'))
                else:
                    self.buttons.buttons.append(
                        Button(self.props, "Portal Limited", self, {'summon':recipe_data}, 
                            pygame.Rect(shop_box_x + 300, recipe_y, 100, 50), (200,0,0), 
                            background_box = True, outline = True, activated = False, tooltip = 'Upgrade your portal to summon more'))
            else:
                self.buttons.buttons.append(
                        Button(self.props, "Upgrade",self,{'upgrade':recipe_data}, 
                            pygame.Rect(shop_box_x + 300, recipe_y, 100, 50), (200,0,0), 
                            background_box = True, outline = True, activated = self.props.can_buy(recipe_data['cost']), tooltip = 'Insufficient Resources'))

            recipe_data['reward'].render()

            # Check if mouse is hovering over the recipe to display reward description
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if shop_box_x + 20 <= mouse_x <= shop_box_x + 20 + 200 and recipe_y <= mouse_y <= recipe_y + 50:
                # Render pop-out box with reward description
                reward_description_font = self.props.font_small
                self.reward_description_text = reward_description_font.render(recipe_data['reward'].description, True, (0,0,0))
                
                

            recipe_y += 70

        self.buttons.render()
        if self.reward_description_text:
            self.props.screen.blit(self.reward_description_text, (mouse_x + 5, mouse_y + 5))

    def events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
            self.buttons.events(event)

    def trigger(self, event):
        if 'summon' in event:
            self.props.pay(event['summon']['cost'])
            reward = event['summon']['reward'].copy()
            reward.position = (0,3)
            self.recipes[self.level][event['summon']['name']]['quantity'] -= 1
            self.recipes[self.level][event['summon']['name']]['cost']['bought'] += 1
            if isinstance(reward,Gatherer):
                reward.update_stats()
                self.props.gatherers.append(reward)
                self.props.selected_gatherer = reward
                if self.recipes[self.level][event['summon']['name']]['cost']['bought'] == 1:
                    self.props.tooltip = "Click a resource for your slime to gather"
                    self.props.tooltip_ticks = 120
                if self.recipes[self.level][event['summon']['name']]['cost']['bought'] == 2:
                    self.props.tooltip = ["You can change what your slime is gathering",
                                            "by clicking the slime then a new resource"]
                    self.props.tooltip_ticks = 120
            elif isinstance(reward,TaskMaster):
                self.props.task_masters.append(reward)
                self.props.calculate_bonuses()
            self.summon_sound.set_volume(self.props.effects_volume / 100)
            self.summon_sound.play()
            

            self.props.state = 'game'
        if 'upgrade' in event:
            self.props.pay(event['upgrade']['cost'])
            self.level += 1
            self.update_recipes()
            self.props.state = 'game'
            if event['upgrade']['reward'].name == 'Level 2':
                 self.props.tooltip = "You can zoom out with the mouse wheel"
                 self.props.tooltip_ticks = 120
            if event['upgrade']['reward'].name == 'Level 3':
                 self.props.tooltip = "You can move around the map with the arrow keys"
                 self.props.tooltip_ticks = 120
                




class Game:
    
    def __init__(self):
        self.state = 'start menu'
        self.game_states = ['start menu', 'game', 'portal']
        
        pygame.init()
        pygame.display.set_caption("Summoning Factory")
        self.height = 800
        self.width = 1200
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.font = pygame.font.Font('Fondamento-Regular.ttf', 24)
        self.font_small = pygame.font.Font('Fondamento-Regular.ttf', 12)
        self.font_large = pygame.font.Font('Fondamento-Regular.ttf', 80)
        self.volume = 20
        self.effects_volume = 10

        # Load the music track
        pygame.mixer.music.load("Game.wav")  # Replace "background_music.mp3" with your music file

        # Set the volume (optional)
        pygame.mixer.music.set_volume(self.volume/100)  # Adjust the volume (0.0 to 1.0)

        # Play the music in a loop
        pygame.mixer.music.play(-1)  # -1 indicates looping

        self.selected_tile = None
        self.selected_gatherer = None

        self.assignments = {}
        self.gatherers = []
        self.task_masters = []

        # Constants
        self.GRID_SIZE = 1000
        self.TILE_SIZE = 16
        self.CHUNK_SIZE = 16
        self.RESOURCE_PROBABILITY = 0.005
        self.SEED = 12345
        self.chunks = {(0,0):{(0,0):None}}
        self.border_thickness = 3
        self.manual_gathering = 1

        self.tooltip = "Click on the green cystals to gather essence"
        self.tooltip_ticks = 6000
        
        self.player_x, self.player_y = self.width//2, self.height//2  # Player position

        self.main_portal = PortalSummoning(self)

        # Set seed for randomization
        random.seed(self.SEED)

        self.nearby_resources = {
            "Essence":2,
            "Wood":1,
        }

        self.range1_resources = {
            "Essence":3,
            "Iron":2,
            "Wood":1,
            "Gold":1
        }

        self.range2_resources = {
            "Rubies":3,
            "Essence":2,
            "Demonic Iron":1,
        }

        self.range3_resources = {
            "Demonic Iron":2,
            "Pure Essence":2,
            "Rubies":1
        }

        self.resource_colors = {
            "Essence":(0,255,0),
            "Wood":(139,69,19),
            "Gold":(255,255,0),
            "Iron":(100,100,100),
            "Rubies":(255,0,0),
            "Demonic Iron":(220,220,220),
            "Pure Essence":(200,255,200),
        }

        self.resource_quantities = {
            "Essence":0,
            "Wood":0,
            "Gold":0,
            "Iron":0,
            "Rubies":0,
            "Demonic Iron":0,
            "Pure Essence":0,
        }

        self.manual_resource_gathering = {
            "Essence":True,
            "Wood":False,
            "Gold":False,
            "Iron":False,
            "Rubies":False,
            "Demonic Iron":False,
            "Pure Essence":False,
        }

        sheet = spritesheet("Resources-Sheet.png")

        self.resource_sprites = {
            "Essence":{'tile':sheet.image_at((0,0,64,64)),'item':sheet.image_at((0,64,64,64))},
            "Wood":{'tile':sheet.image_at((64,0,64,64)),'item':sheet.image_at((64,64,64,64))},
            "Gold":{'tile':sheet.image_at((128,0,64,64)),'item':sheet.image_at((128,64,64,64))},
            "Iron":{'tile':sheet.image_at((192,0,64,64)),'item':sheet.image_at((192,64,64,64))},
            "Rubies":{'tile':sheet.image_at((256,0,64,64)),'item':sheet.image_at((256,64,64,64))},
            "Demonic Iron":{'tile':sheet.image_at((320,0,64,64)),'item':sheet.image_at((320,64,64,64))},
            "Pure Essence":{'tile':sheet.image_at((384,0,64,64)),'item':sheet.image_at((384,64,64,64))},
        }

        self.unlocked_resources = ["Essence"]

        # Generate a mapping of random integers to resources
        self.nearby_resource_mapping = {}
        self.range1_resouce_mapping = {}
        self.range2_resouce_mapping = {}
        self.range3_resouce_mapping = {}

        for i in range(1, 101):
            # Assign resources based on probabilities
            self.nearby_resource_mapping[i] = random.choices(list(self.nearby_resources.keys()),list(self.nearby_resources.values()), k=1)[0]
            self.range1_resouce_mapping[i] = random.choices(list(self.range1_resources.keys()),list(self.range1_resources.values()), k=1)[0]
            self.range2_resouce_mapping[i] = random.choices(list(self.range2_resources.keys()),list(self.range2_resources.values()), k=1)[0]
            self.range3_resouce_mapping[i] = random.choices(list(self.range3_resources.keys()),list(self.range3_resources.values()), k=1)[0]


        # Define central summoning portal
        self.portal_x, self.portal_y = self.GRID_SIZE // 2, self.GRID_SIZE // 2
        
        self.start_menu = StartMenu(self)
        self.death_menu = DeathMenu(self)
        self.overlay = Overlay(self)

        self.base_bonuses = {'max_capacity':{'additive':0,'multiplicative':1},
                        'gathering_speed':{'additive':0,'multiplicative':1},
                        'moving_speed':{'additive':0,'multiplicative':1},}
        self.bonuses = {'max_capacity':{'additive':0,'multiplicative':1},
                        'gathering_speed':{'additive':0,'multiplicative':1},
                        'moving_speed':{'additive':0,'multiplicative':1},}

    def calculate_bonuses(self):
        self.bonuses = self.base_bonuses
        for task_master in self.task_masters:
            for effect, change in task_master.effect.items():
                if change['method'] == 'additive':
                    self.bonuses[effect]['additive'] += change['magnitude']
                elif change['method'] == 'multiplicative':
                    self.bonuses[effect]['multiplicative'] *= change['magnitude']
        print(self.bonuses)
        for gatherer in self.gatherers:
            gatherer.update_stats()

    def can_buy(self,costs):
        for resource, cost in costs.items():
            if resource != 'bought':
                total_cost = round(cost['base']*cost['multiplier']**costs['bought'])
                if total_cost > self.resource_quantities[resource]:
                    return False
        return True
    
    def pay(self,costs):
        for resource, cost in costs.items():
            if resource != 'bought':
                total_cost = round(cost['base']*cost['multiplier']**costs['bought'])
                self.resource_quantities[resource] -= total_cost

    def generate_chunk(self, chunk_x, chunk_y):
        print(chunk_x,chunk_y)
        chunk = {}
        for x in range(chunk_x * self.CHUNK_SIZE, (chunk_x + 1) * self.CHUNK_SIZE):
            for y in range(chunk_y * self.CHUNK_SIZE, (chunk_y + 1) * self.CHUNK_SIZE):
                if random.random() < self.RESOURCE_PROBABILITY:
                    # Check neighboring tiles to determine resource span
                    span_x = random.randint(1, 5)  # Random span along x-axis
                    span_y = random.randint(1, 5)  # Random span along y-axis
                    if abs(chunk_x)+abs(chunk_y)<=2:
                        resource = self.nearby_resource_mapping[random.randint(1, 100)]  # Resource complexity levels
                    elif abs(chunk_x)+abs(chunk_y)<=4:
                        resource = self.range1_resouce_mapping[random.randint(1, 100)]  # Resource complexity levels
                    elif abs(chunk_x)+abs(chunk_y)<=6:
                        resource = self.range2_resouce_mapping[random.randint(1, 100)]  # Resource complexity levels
                    else:
                        resource = self.range3_resouce_mapping[random.randint(1, 100)]  # Resource complexity levels
                    for i in range(span_x):
                        for j in range(span_y):
                            # Check if the neighboring tile is within the grid bounds
                            if chunk_x * self.CHUNK_SIZE <= x + i < (chunk_x + 1) * self.CHUNK_SIZE and chunk_y * self.CHUNK_SIZE <= y + j < (chunk_y + 1) * self.CHUNK_SIZE:
                                chunk[(x+i, y+j)] = resource
        return chunk
    
    def render(self):
        self.screen.fill((0,0,0))
        if self.state == 'game':
            self.render_grid()
            for gatherer in self.gatherers:
                gatherer.render()
            for task_master in self.task_masters:
                task_master.render()
            
            i=0
            
            for resource,sprites in self.resource_sprites.items():
                if (self.resource_quantities[resource] > 0) and (resource not in self.unlocked_resources):
                    self.unlocked_resources.append(resource)
                if resource in self.unlocked_resources:
                    self.screen.blit(pygame.transform.scale(sprites['item'],(32,32)), (20,20+32*i,32,32))
                    self.screen.blit(self.font.render(format_large_number(self.resource_quantities[resource]), False, (255, 255, 255)), (54,20+32*i,32,32))
                    if pygame.Rect(20,20+32*i,64,32).collidepoint(pygame.mouse.get_pos()):
                        # Render pop-out box with reward description
                        self.tooltip = resource
                        self.tooltip_ticks = 30
                    i+=1

        if self.tooltip_ticks:
            x,y = pygame.mouse.get_pos()
            if isinstance(self.tooltip, str):
                self.screen.blit(self.font_small.render(self.tooltip, False, (255,255,255)),(x+5,y-10))
            else:
                for count, tip in enumerate(self.tooltip):
                    self.screen.blit(self.font_small.render(tip, False, (255,255,255)),(x+10,y-10+count*20))
            self.tooltip_ticks -= 1
        elif self.tooltip == "Right click on any object to get information about it":
            self.tooltip = "You can summon entities in the central portal"
        elif (abs(self.player_x)+abs(self.player_y) > 1500) & (self.tooltip != "You can press the C key to return to the center of the map"):
            self.tooltip = "You can press the C key to return to the center of the map"
            self.tooltip_ticks = 180
            

        if self.state == 'start menu':
            self.screen.fill((0,0,0))
            self.start_menu.render()

        if self.state == 'portal':
            self.main_portal.render()
            
        if self.state == 'death':
            self.death_menu.render()
            
        pygame.display.flip()

    def render_grid(self):
        # Calculate the top-left corner of the visible area
        self.visible_rects = []

        for chunk in self.chunks.values():
            for (x, y), resource in chunk.items():
                if resource:
                    screen_x = x * self.TILE_SIZE + self.player_x
                    screen_y = y * self.TILE_SIZE + self.player_y
                    if -self.TILE_SIZE <= screen_x < self.width and -self.TILE_SIZE <= screen_y < self.height:
                        color = (255, 255, 255)  # Default color
                        rect = [(x,y),pygame.Rect(screen_x, screen_y, self.TILE_SIZE, self.TILE_SIZE), resource]
                        self.visible_rects.append(rect)
                        self.screen.blit(pygame.transform.scale(self.resource_sprites[resource]['tile'],(self.TILE_SIZE, self.TILE_SIZE)), rect[1])
        screen_x = self.player_x - round(56/16*self.TILE_SIZE)
        screen_y = self.player_y -round(56/16*self.TILE_SIZE)
        if -self.TILE_SIZE <= screen_x < self.width and -self.TILE_SIZE <= screen_y < self.height:
            rect = [(0,0),pygame.Rect(screen_x, screen_y, round(112/16*self.TILE_SIZE),round(112/16*self.TILE_SIZE)), "Main Portal"]
            self.visible_rects.append(rect)
            sheet = spritesheet('PortalResource-Sheet.png')
            current_portal = sheet.image_at((self.main_portal.level*112,0,112,112))
            self.screen.blit(pygame.transform.scale(current_portal,(112/16*self.TILE_SIZE, 112/16*self.TILE_SIZE)), (screen_x,screen_y))


    def trigger(self, event):
        if event in self.game_states:
            self.state = event
        if event == 'quit':
            pygame.quit()


async def main():
    game = Game()

    mining_sound = pygame.mixer.Sound("Mine.wav")
    
    # Generate chunks around the player if they don't exist
    for x in range(-32,33):
        for y in range(-32,33):
            if (x, y) not in game.chunks:
                game.chunks[(x, y)] = game.generate_chunk(x, y)
    
    terminated = False
    while not terminated:
        if game.state == 'game':
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print('quit')
                    game.terminated = True 
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        game.player_x = game.width//2
                        game.player_y = game.height//2
                    if event.key == pygame.K_p:
                        game.trigger('portal')
                    if event.key == pygame.K_ESCAPE:
                        game.trigger('start menu')
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button ==1:
                        game.selected_gatherers = [gatherer for gatherer in game.gatherers if gatherer.rect.collidepoint(event.pos)]
                        if game.selected_gatherers:
                            game.selected_gatherer = game.selected_gatherers[0]
                            print(game.selected_gatherer)
                        else:

                            game.selected_tiles = [square for square in game.visible_rects if square[1].collidepoint(event.pos)]
                            if game.selected_tiles:
                                game.selected_tile = game.selected_tiles[0]
                                print(game.selected_tile[2])
                                if game.selected_tile[2] == 'Main Portal':
                                    game.trigger('portal')
                                elif game.selected_gatherer != None:
                                    game.selected_gatherer.assign(game.selected_tile)
                                    game.assignments[game.selected_tile[0]] = game.selected_gatherer
                                    
                                else:
                                    if game.tooltip == "Click on the green cystals to gather essence":
                                        game.tooltip = "Right click on any object to get information about it"
                                    game.resource_quantities[game.selected_tile[2]] += game.manual_gathering
                                    mining_sound.set_volume(game.effects_volume / 100)
                                    mining_sound.play()
                            else:
                                game.selected_tile = None
                                game.selected_gatherer = None
                        
                    if event.button == 3:
                        print('click')
                        game.selected_taskmasters = [gatherer for gatherer in game.task_masters if gatherer.rect.collidepoint(event.pos)]
                        game.selected_gatherers = [gatherer for gatherer in game.gatherers if gatherer.rect.collidepoint(event.pos)]
                        game.selected_tiles = [square for square in game.visible_rects if square[1].collidepoint(event.pos)]
                        if game.selected_gatherers:
                            game.tooltip = [game.selected_gatherers[0].name,
                                            f"Currently Gathering: {None if game.selected_gatherers[0].assignment == None else game.selected_gatherers[0].assignment[2]}",
                                            f"Can gather: {", ".join(game.selected_gatherers[0].resources_gatherable)}",
                                            f"Inventory: {0 if game.selected_gatherers[0].assignment == None else game.selected_gatherers[0].inventory[game.selected_gatherers[0].assignment[2]]}/{game.selected_gatherers[0].max_capacity}",
                                            f"Gathering Speed {game.selected_gatherers[0].gathering_speed}/sec",
                                            f"Moving Speed {game.selected_gatherers[0].moving_speed}"]
                            game.tooltip_ticks = 60

                        elif game.selected_taskmasters:
                            game.tooltip = [game.selected_taskmasters[0].name] + [f"Increases workers {name} by {value['magnitude']} {value['method']}" for name, value in game.selected_taskmasters[0].effect.items()]
                            game.tooltip_ticks = 60
                        
                        elif game.selected_tiles:
                            resource = game.selected_tiles[0][2]
                            if resource == 'Essence':
                                game.tooltip = f"This is a resource node for Essence it is used to summon new entities."
                            elif resource == 'Main Portal':
                                game.tooltip = f"This is your portal, this is where you summon new entities from."
                            else:
                                game.tooltip = f"This is a resource node for {resource} it is used to upgrade your portal."
                            game.tooltip_ticks = 60

                        
                    if event.button == 4:  # Scroll up
                        game.TILE_SIZE = min(64, game.TILE_SIZE + 1)
                    elif event.button == 5:  # Scroll down
                        game.TILE_SIZE = max(8,game.TILE_SIZE-1)

                
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RIGHT]:
                game.player_x -= 5
            if keys[pygame.K_LEFT]:
                game.player_x += 5
            if keys[pygame.K_DOWN]:
                game.player_y -= 5
            if keys[pygame.K_UP]:
                game.player_y += 5
            

            
                
        elif game.state == 'start menu':
            for event in pygame.event.get():
                game.start_menu.events(event)
                if event.type == pygame.QUIT:
                    game.terminated = True 
                    pygame.quit()
                    sys.exit()
        
        elif game.state == 'portal':
            for event in pygame.event.get():
                game.main_portal.events(event)
                if event.type == pygame.QUIT:
                    game.terminated = True
                    pygame.quit()
                    sys.exit()
                    
        elif game.state == 'death':
            for event in pygame.event.get():
                game.death_menu.events(event)
                if event.type == pygame.QUIT:
                    game.terminitated = True
                    pygame.quit()
                    sys.exit()
                    

        game.render()
        game.clock.tick(50)
        await asyncio.sleep(0)

asyncio.run(main())