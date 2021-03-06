import json
import grequests
from pprint import pprint
import sys
from .Constants.constants import *

# Get number of stats from nested dict/lists
def get_total_keys(data):

    if not isinstance(data, dict):
        return 0

    nested_keys = sum(get_total_keys(value) for key, value in data.items())
    return len(data) + nested_keys

# Get number of bytes from nested dict/lists
def get_total_bytes(data):

    if not isinstance(data, dict):
        return sys.getsizeof(data)

    nested_bytes = sum(get_total_keys(value) for key, value in data.items())
    return sys.getsizeof(data) + nested_bytes


# ! # Add stats from achievements
# Returns formatted Smash Heroes Stats
def getSmashHeroes(raw_stats, achievements):

    # Setup better naming
    CLASS_STATS = raw_stats.get("class_stats", {})

    # Setup container to hold stats
    sorted_stats = {"general": {}, "booster": {}}

    # Exp Booster stats
    sorted_stats["booster"]["active_exp_booster"] = raw_stats.get("expired_booster", False)
    sorted_stats["booster"]["exp_booster_count"] = sum(map(lambda x: raw_stats.get(f"expBooster_purchases_{str(x)}_plays",0) * x,[10,30,50,100]))
    # For every proper stat in names
    for stat, stat_proper in smash_stat_name_conversions.items():

        # Check if key is in dict, if not set as 0
        sorted_stats["general"][stat_proper] = raw_stats.get(stat, 0)

    # For every stat in names
    for stat in smash_stat_names:

        # Check if key is in dict, if not set as 0
        sorted_stats["general"][stat] = raw_stats.get(stat, 0)

    # Setup class container
    sorted_stats.update({
        smash_class_proper: {"class_deaths": {}}
        for smash_class, smash_class_proper in smash_classes.items()
    })

    # For every class in smash classes
    for smash_class, smash_class_proper in smash_classes.items():

        # Add stats with default as 0
        sorted_stats[smash_class_proper]["overall"] = {
            smash_stat: CLASS_STATS[smash_class].get(smash_stat, 0)
            for smash_stat in smash_class_stats
            }

        # Add proper class stats with default as 0
        sorted_stats[smash_class_proper]["overall"].update({
            smash_stat_proper: CLASS_STATS[smash_class].get(smash_stat, 0)
            for smash_stat, smash_stat_proper in smash_class_stat_conversions.items()
            })

        # Add stats from general section with default as 0
        sorted_stats[smash_class_proper]["overall"].update({
            smash_stat_proper: int(raw_stats.get( (smash_stat + smash_class), 0))
            for smash_stat, smash_stat_proper in smash_class_stats_from_general.items()
            })

        # For every gamemode in gamemodes
        for gm, gm_proper in smash_gamemodes.items():
            # Add gamemode-specific stats with default as 0
            sorted_stats[smash_class_proper][gm_proper] = {
                smash_stat: CLASS_STATS[smash_class].get( f"{smash_stat}_{gm}", 0)
                for smash_stat in smash_class_stats
            }

        """
        class_deaths = {
            class_1: total_deaths_to_class_1,
            class_2: total_deaths_to_class_2,
            ...,
            class_n: total_deaths_to_class_n,
        }
        """
        def get_total_deaths_by_class(class_stats, killer_class):
            """
            class_stats: stats of the class which we want the total deaths of
            killer_class: the class that killed the class of `class_stats`
            """
            return sum(
                class_stats.get(ability, {}).get("smashed", 0)
                for ability in smash_classes_abilities.get(killer_class, {})
            )

        for c_smash_class, smash_class_proper in smash_classes.items():
            class_stats = CLASS_STATS[c_smash_class]

            sorted_stats[smash_class_proper]["class_deaths"] = {
                killer_class: get_total_deaths_by_class(class_stats, killer_class)
                for killer_class in smash_classes
            }

    # Return cleaned up stats
    return sorted_stats

# ! # Add stats from achievements
# Returns formatted Bedwars stats
def getBedwars(raw_stats, achievements):

    # Setup container to hold stats
    sorted_stats = {"general": {}, "cosmetic_boxes": {}}

    # Cosmetic box stats
    sorted_stats["cosmetic_boxes"] = {
        cm_stat_proper: raw_stats.get(cm_stat, 0)
        for cm_stat, cm_stat_proper in bedwars_cosmetic_stat_names.items()
        }

    # Start general stats
    sorted_stats["general"] = {
        bw_stat_proper: raw_stats.get(bw_stat, 0)
        for bw_stat, bw_stat_proper in bedwars_stat_names.items()
        }

    # Finish general stats
    for bw_stat, bw_stat_proper in bedwars_stat_name_conversions.items():

        # Check if subsection of stats
        if( isinstance(bw_stat_proper, dict) ):
            sorted_stats["general"][bw_stat] = {
                sub_bw_stat_proper: raw_stats.get(sub_bw_stat, 0)
                for sub_bw_stat, sub_bw_stat_proper in bw_stat_proper.items()
                }

        # If individual stat
        else:
            sorted_stats["general"][bw_stat_proper] = raw_stats.get(bw_stat, 0)

    # Gamemode stats
    for gm, gm_proper in bedwars_gamemodes.items():

        # Initialize container for gamemode-specific stats
        sorted_stats[gm_proper] = {}

        # For every stat that can be gamemode-specific
        for bw_stat, bw_stat_proper in bedwars_stat_name_conversions.items():

            # If individual stat
            if(not isinstance(bw_stat_proper, dict)):

                # Get the stat, default to 0
                sorted_stats[gm_proper][bw_stat_proper] = raw_stats.get(f"{gm}_{bw_stat}", 0)

            # If substats
            else:

                # Create subdict of stats
                sorted_stats[gm_proper][bw_stat] = {
                sub_bw_stat_proper: raw_stats.get(f"{gm}_{sub_bw_stat}", 0)
                for sub_bw_stat, sub_bw_stat_proper in bw_stat_proper.items()
                }

    # Active stats
    sorted_stats["active"] = {
        a_stat_proper: raw_stats.get(a_stat, "")
        for a_stat, a_stat_proper in bedwars_active_stats.items()
        }

    # Return cleaned up stats
    return sorted_stats


# Returns formatted Quake stats
# ! # Add shop stats
def getQuake(raw_stats, achievements):
    # Setup container to hold stats
    sorted_stats = {}

    # Set general stats
    sorted_stats["general"] = {
        q_stat: int(raw_stats.get(q_stat, 0))
        for q_stat in quake_stat_names
        }

    # Set gamemode stats
    for gm, gm_proper in quake_gamemodes.items():
        sorted_stats[gm_proper] = {
            q_stat: raw_stats.get(f"{q_stat}{gm}", 0)
            for q_stat in quake_mode_stats
            }

    # Set active stats
    sorted_stats["active"] = {
        q_stat_proper: raw_stats.get(q_stat, 0)
        for q_stat, q_stat_proper in quake_active_stats.items()
        }

    # Set general stats
    sorted_stats["general"].update({
        q_stat: sum( [ sorted_stats["solo"].get(q_stat, 0), sorted_stats["teams"].get(q_stat, 0), sorted_stats["tournament"].get(q_stat, 0) ] )
        for q_stat in quake_mode_stats
        })

    # Fix post_update stats
    sorted_stats["solo"]["post_update_kills"] = raw_stats.get("kills_since_update_feb_2017", 0)
    sorted_stats["teams"]["post_update_kills"] = raw_stats.get("kills_since_update_feb_2017_teams", 0)

    # Fix dash cooldown and power
    sorted_stats["general"]["dash_cooldown"] += 1
    sorted_stats["general"]["dash_power"] += 1

    # Add stats from tiered achievements
    sorted_stats["general"]["godlikes"] = achievements.get("quake_godlikes", 0)
    sorted_stats["general"]["weapons"] = achievements.get("quake_weapon_arsenal", 0)

    def computeBest(armor_part,armor_name):
        try: return raw_stats.get(armor_name, False) or raw_stats["packages"][list(filter(lambda x:\
             x in raw_stats["packages"],list(armor_part)))[0]]
        except: return "NONE"
    
    # Get best armor set
    sorted_stats["active"]["armor"] = {
        "hat": computeBest(map(lambda x:x[0],quake_hats), "hat"),
        "chestplate": computeBest(map(lambda x:x[0],quake_chestplates),"chestplate"),
        "leggings": computeBest(map(lambda x:x[0]+"_leggings",quake_lowers),"leggings"),
        "boots": computeBest(map(lambda x:x[0]+"_boots",quake_lowers),"boots"),
        }

    # Current weapon build
    quake_current_weapon_parts = (
        sorted_stats["active"]["case"],
        sorted_stats["active"]["laser"],
        sorted_stats["active"]["barrel"],
        sorted_stats["active"]["muzzle"],
        sorted_stats["active"]["trigger"]
        )

    # Get current weapon name
    for q_weapon, q_weapon_parts in quake_weapons.items():
        if(quake_current_weapon_parts == q_weapon_parts):
            sorted_stats["active"]["weapon"] = q_weapon

    if("weapon" not in sorted_stats["active"]):
        def getWeaponName(part_name,pre="suf"): return quake_weapon_parts[f"quake_{part_name}_{pre}fixes"][sorted_stats["active"].get(part_name, None)]
        sorted_stats["active"]["weapon"] = f"{getWeaponName('case','pre') or 'WOOD_HOE'} {getWeaponName('laser','pre') or 'YELLOW'} Railgun "+\
        f"{getWeaponName('muzzle') or 'NONE'} {getWeaponName('trigger') or 'ONE_POINT_THREE'} {getWeaponName('barrel') or 'SMALL_BALL'}"
    
    #Total Amount of items purchased armorwise
    def amountOwned(armor_part):
        return len(set(raw_stats["packages"]).intersection(set(list(armor_part)))) or 0
    sorted_stats["items_purchased"] = sum([
        amountOwned(map(lambda x:x[0],quake_hats)),
        amountOwned(map(lambda x:x[0],quake_chestplates)),
        amountOwned(map(lambda x:x[0]+'_leggings',quake_lowers)),
        amountOwned(map(lambda x:x[0]+'_boots',quake_lowers))
    ])

    # Return cleaned up stats
    return sorted_stats



# Gets all player stats
def getAllStats(url):

    # Async call to url
    resp = grequests.get(url)

    # For every response
    for data in grequests.map([resp]):

        # Load data with JSON
        data = json.loads(data.content)

        # If response successful
        if(data["success"]):

            # Set up player container
            finalized_stats = {"game_stats": {}}

            # If stats for games are present
            if "stats" in data["player"]:

                # If no game stats, add default containers
                data["player"]["stats"] = {
                    gamemode: data["player"]["stats"].get(gamemode, {})
                    for gamemode in hypixel_stats_gamemodes
                }

                # Check every game
                for gm, gm_proper in hypixel_stats_gamemodes.items():

                    # Add proper stats to proper container
                    finalized_stats["game_stats"][gm_proper[0]] = gm_proper[1](data["player"]["stats"][gm], data["player"]["achievements"])

            # If achievements are present
            if "achievements" in data["player"]:
                #stats = getAchievements()
                pass
            else:
                data["player"]["achievements"] = {}


            # Return proper stats container
            return(finalized_stats)

# List of gamemodes
hypixel_stats_gamemodes = {
    "SuperSmash": ("smash_heroes", getSmashHeroes),
    "Bedwars": ("bedwars", getBedwars),
    "Quake": ("quake", getQuake),
    }