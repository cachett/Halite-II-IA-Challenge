import hlt
import logging
from collections import OrderedDict
import numpy as np
import random
import os
import time

import keras
import tensorflow as tf
from keras.models import load_model

#Silence TF and load model
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '99'
tf.logging.set_verbosity(tf.logging.ERROR)
model = load_model('model_checkpoint_256_batch_10_epochs2.77_best.h5')

VERSION = 4.1

HM_ENT_FEATURES = 5
PCT_CHANGE_CHANCE = 15
DESIRED_SHIP_COUNT = 180

game = hlt.Game("Shady{}".format(VERSION))
logging.info("Shady-{} Start".format(VERSION))

ship_plans = {}

# if os.path.exists("c{}_input.vec".format(VERSION)):
#     os.remove("c{}_input.vec".format(VERSION))
#
# if os.path.exists("c{}_out.vec".format(VERSION)):
#     os.remove("c{}_out.vec".format(VERSION))



def key_by_value(dictionary, value):
    for k,v in dictionary.items():
        if v[0] == value:
            return k
    return -99


def fix_data(data):
    new_list = []
    last_known_idx = 0
    for i in range(HM_ENT_FEATURES):
        try:
            if i < len(data):
                last_known_idx=i
            new_list.append(data[last_known_idx][0])
        except:
            new_list.append(-99)

    return new_list



while True:
    t1 = time.clock()
    game_map = game.update_map()
    command_queue = []

    team_ships = game_map.get_me().all_ships()
    all_ships = game_map._all_ships()
    enemy_ships = [ship for ship in game_map._all_ships() if ship not in team_ships]

    my_ship_count = len(team_ships)
    enemy_ship_count = len(enemy_ships)
    all_ship_count = len(all_ships)

    my_id = game_map.get_me().id



    hm_owned_dock = 0
    hm_free_dock = 0
    hm_empty_planets = 0

    for p in game_map.all_planets():
        if not p.is_owned():
            hm_empty_planets += 1
            hm_free_dock += p.num_docking_spots
        elif p.owner.id == game_map.get_me().id:
            hm_owned_dock += p.num_docking_spots - len(p._docked_ship_ids)



    for ship in game_map.get_me().all_ships():
        try:
            if (time.clock() - t1) > 1.85:
                break
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship
                continue

            shipid = ship.id
            change = False
            if random.randint(1,100) <= PCT_CHANGE_CHANCE:
                change = True


            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))

            #closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
            #closest_empty_planet_distances = [distance for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]

            closest_my_planets = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].is_owned() and entities_by_distance[distance][0].owner.id == my_id]
            #closest_my_planets_distances = [distance for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].is_owned() and (entities_by_distance[distance][0].owner.id == my_id)]

            #closest_enemy_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0] not in closest_my_planets and entities_by_distance[distance][0] not in closest_empty_planets]
            closest_enemy_planets = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].is_owned() and entities_by_distance[distance][0].owner.id != my_id]


            closest_undocked_team_ships = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id == my_id and entities_by_distance[distance][0].docking_status == ship.DockingStatus.UNDOCKED]
            closest_docked_team_ships = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id == my_id and entities_by_distance[distance][0].docking_status != ship.DockingStatus.UNDOCKED]


            closest_enemy_ships = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != my_id]
            #closest_enemy_ships_distances = [distance for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner != my_id]

            closest_undocked_enemy_ships = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != my_id and entities_by_distance[distance][0].docking_status == ship.DockingStatus.UNDOCKED]
            #closest_undocked_enemy_ships_distances = [distance for distance in closest_enemy_ships_distances if ship.docking_status == ship.DockingStatus.UNDOCKED]

            closest_docked_enemy_ships = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != my_id and entities_by_distance[distance][0].docking_status != ship.DockingStatus.UNDOCKED]
            #closest_docked_enemy_ships_distances = [distance for distance in closest_enemy_ships_distances if ship.docking_status != ship.DockingStatus.UNDOCKED]

            closest_opendock_planets = [(distance, entities_by_distance[distance][0]) for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].num_docking_spots > len(entities_by_distance[distance][0]._docked_ship_ids) and (entities_by_distance[distance][0].owner == None or entities_by_distance[distance][0].owner.id == my_id)]
            #closest_opendock_planets_distances = [distance for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and entities_by_distance[distance][0].num_docking_spots > len(entities_by_distance[distance][0]._docked_ship_ids) and (entities_by_distance[distance][0].owner == None or entities_by_distance[distance][0].owner.id == my_id)]


            # largest_empty_planet_distances = []
            # largest_our_planet_distances = []
            # largest_enemy_planet_distances = []
            #
            # for i in range(HM_ENT_FEATURES):
            #     try: largest_empty_planet_distances.append(key_by_value(entities_by_distance, empty_planet_sizes[empty_planet_keys[i]]))
            #     except:largest_empty_planet_distances.append(-99)
            #
            #     try: largest_our_planet_distances.append(key_by_value(entities_by_distance, our_planet_sizes[our_planet_keys[i]]))
            #     except:largest_our_planet_distances.append(-99)
            #
            #     try: largest_enemy_planet_distances.append(key_by_value(entities_by_distance, enemy_planet_sizes[enemy_planet_keys[i]]))
            #     except:largest_enemy_planet_distances.append(-99)


            entity_lists = [fix_data(closest_opendock_planets),
                            fix_data(closest_my_planets),
                            fix_data(closest_enemy_planets),
                            fix_data(closest_undocked_team_ships),
                            fix_data(closest_enemy_ships),
                            fix_data(closest_undocked_enemy_ships),
                            fix_data(closest_docked_enemy_ships)]


            input_vector = []

            for i in entity_lists:
                for ii in i[:HM_ENT_FEATURES]:
                    input_vector.append(ii)

            input_vector += [my_ship_count,
                             enemy_ship_count,
                             len(closest_my_planets),
                             hm_empty_planets,
                             len(closest_enemy_planets),
                             hm_free_dock,
                             hm_owned_dock]


            if my_ship_count > DESIRED_SHIP_COUNT:
                '''ATTACK: [1,0,0]'''

                output_vector = 3*[0] #[0,0,0]
                output_vector[0] = 1 #[1,0,0]
            #    ship_plans[ship.id] = output_vector

            # elif change:
            #     '''Integrate some random'''
            #     output_vector = 3*[0]
            #     output_vector[random.randint(0,2)] = 1

            else:
                '''
                pick new "plan"
                '''
                input_vector = [round(item,3) for item in input_vector]
                output_vector = model.predict(np.array([input_vector]))[0]
                output_max = np.argmax(output_vector)
                argmax_vector = [0,0,0]
                argmax_vector[output_max] = 1
                output_vector = argmax_vector
            #    logging.info(output_max)
            #    ship_plans[ship.id] = output_vector

            #
            # else:
            #     '''continue to execute existing plan'''
            #     output_vector = ship_plans[ship.id]




            try:

                # ATTACK ENEMY SHIP #
                if np.argmax(output_vector) == 0: #[1,0,0]
                    '''
                    type: 0
                    Attack!
                    '''
                    if len(closest_docked_enemy_ships) > 0 and closest_docked_enemy_ships[0][0] < 2.5 * closest_enemy_ships[0][0]: # and random.randint(0,1) == 0:
                        navigate_command = ship.navigate(
                                    ship.closest_point_to(closest_docked_enemy_ships[0][1]),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)

                    elif len(closest_enemy_ships) > 0:
                        navigate_command = ship.navigate(
                                    ship.closest_point_to(closest_enemy_ships[0][1]),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)



                # Mine
                elif np.argmax(output_vector) == 1: #[0,1,0]
                    '''
                    type: 1
                    Mine! (If possible, otherwise attack)
                    '''
                    if len(closest_opendock_planets) > 0:
                        target = closest_opendock_planets[0][1]
                        if ship.can_dock(target):
                            command_queue.append(ship.dock(target))
                        else:
                            navigate_command = ship.navigate(
                                        ship.closest_point_to(target),
                                        game_map,
                                        speed=int(hlt.constants.MAX_SPEED),
                                        ignore_ships=False)

                            if navigate_command:
                                command_queue.append(navigate_command)
                    elif len(closest_enemy_ships) > 0:
                        #attack
                        navigate_command = ship.navigate(
                                    ship.closest_point_to(closest_enemy_ships[0][1]),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)




                # FLEE #
                else:
                    '''
                    type: 2
                    Flee! (or go to the closest ally ship sans le toucher ce serait bien hein)
                    '''
                    if len(closest_undocked_enemy_ships) > 0 and closest_undocked_enemy_ships[0][0] < 20:
                        if len(closest_docked_team_ships) > 1:
                            pos_to_go = ship.closest_point_to(closest_docked_team_ships[0][1])
                        else:
                            nearby_enemy = closest_undocked_enemy_ships[0][1]
                            pos_to_go = hlt.entity.Position(ship.x - (nearby_enemy.x - ship.x)*2, ship.y - (nearby_enemy.y - ship.y)*2)#fuit!
                        navigate_command = ship.navigate(
                                    pos_to_go,
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)
                    elif len(closest_undocked_team_ships) > 0 and closest_undocked_team_ships[0][0] > 5.1 :#go to ally!
                        nearby_ally = closest_undocked_team_ships[0][1]
                        navigate_command = ship.navigate(
                                    ship.closest_point_to(nearby_ally),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)
                    else:
                        #attaque
                        navigate_command = ship.navigate(
                                    ship.closest_point_to(closest_enemy_ships[0][1]),
                                    game_map,
                                    speed=int(hlt.constants.MAX_SPEED),
                                    ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)





            except Exception as e:
                logging.exception("message")

            # with open("c{}_input.vec".format(VERSION),"a") as f:
            #     f.write(str( [round(item,3) for item in input_vector] ))
            #     f.write('\n')
            #
            # with open("c{}_out.vec".format(VERSION),"a") as f:
            #     f.write(str(output_vector))
            #     f.write('\n')

        except Exception as e:
            logging.exception("message")

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
