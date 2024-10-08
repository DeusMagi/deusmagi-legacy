#!/usr/bin/python3
#*************************************************************************
#*            Atrinik, a Multiplayer Online Role Playing Game            *
#*                                                                       *
#*    Copyright (C) 2009-2014 Alex Tokar and Atrinik Development Team    *
#*                                                                       *
#* Fork from Crossfire (Multiplayer game for X-windows).                 *
#*                                                                       *
#* This program is free software; you can redistribute it and/or modify  *
#* it under the terms of the GNU General Public License as published by  *
#* the Free Software Foundation; either version 2 of the License, or     *
#* (at your option) any later version.                                   *
#*                                                                       *
#* This program is distributed in the hope that it will be useful,       *
#* but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#* GNU General Public License for more details.                          *
#*                                                                       *
#* You should have received a copy of the GNU General Public License     *
#* along with this program; if not, write to the Free Software           *
#* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.             *
#*                                                                       *
#* The author can be reached at admin@atrinik.org                        *
#*************************************************************************

# Application to check Atrinik maps for common errors.

import sys, os, getopt, re, webbrowser, subprocess
try:
    from ConfigParser import ConfigParser
    from StringIO import StringIO
# Python 3.x
except:
    from configparser import ConfigParser
    from io import StringIO

# We will need some recursion.
sys.setrecursionlimit(50000)

# Defines for different types of errors.
class errors:
    # A warning; often not an error, but should be checked anyway.
    warning = 0
    # Low priority.
    low = 1
    # Medium.
    medium = 2
    # High.
    high = 3
    # A critical error.
    critical = 4

    # Text representations of the above.
    text = ["WARNING", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    # ANSI escape sequences to make colors for above errors.
    colors = ["\033[30m", "\033[35m", "\033[36m", "\033[34m", "\033[31m"]
    # Pango (Hex/word) colors for above errors.
    pango_colors = ["black", "magenta", "cyan", "blue", "red"]

# Common escape sequences.
class colors:
    bold = "\033[1m"
    underscore = "\033[4m"
    end = "\033[0m"

# Object types.
class types:
    spawn_point = 81
    scroll = 111
    potion = 5
    monster = 80
    spawn_point_mob = 83
    random_drop = 102
    quest_container = 120
    ability = 110
    waypoint = 119
    player = 1
    exit = 66
    teleporter = 41
    floor = 71
    shop_floor = 68
    event_object = 118
    beacon = 126
    sign = 98
    creator = 42
    map_event_object = 127
    wall = 77
    magic_mirror = 28
    door = 20
    gate = 91
    book = 8
    magic_ear = 29
    light_source = 74
    bow = 14

# Configuration related to the application and some other defines.
class checker:
    # Name of the application.
    name = "Atrinik Map Checker"
    # Version.
    version = "1.0"
    # Copyright.
    copyright = "Copyright \xc2\xa9 2010-2012 Alex Tokar and Atrinik Development Team"
    # GNU GPL license.
    license = "This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.\n\nThis program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA."
    # Description of the application.
    description = "Application to check Atrinik maps for common errors."
    # Authors.
    authors = ["Alex Tokar"]
    # Website URL.
    website = "http://www.atrinik.org/"
    # Website URL for reporting bugs in the application.
    website_bug = "http://bugzilla.atrinik.org/"

    # Highest layer value any archetype can have.
    max_layers = 7
    # Number of sub-layers.
    num_sub_layers = 5
    # Maximum level.
    max_level = 115
    ## Known plugins.
    plugins = ["Python", "Arena"]

# Print usage.
def usage():
    print("\n" + colors.bold + colors.underscore + "Use:" + colors.end + colors.end)
    print("\nGUI/CLI application to check Atrinik maps for common errors.\n")
    print(colors.bold + colors.underscore + "Options:" + colors.end + colors.end)
    print("\n\t-h, --help:\n\t\tDisplay this help.")
    print("\n\t-c, --cli:\n\t\tCommand Line Interface mode. Default is to start in GUI.")
    print("\n\t-d " + colors.underscore + "directory" + colors.end + ", --directory=" + colors.underscore + "directory" + colors.end + ":\n\t\tSpecify directory where to start checking map files (recursively). Default is '../../maps'.")
    print("\n\t-a " + colors.underscore + "arch" + colors.end + ", --arch=" + colors.underscore + "arch" + colors.end + ":\n\t\tSpecify where 'arch' directory is located (to get artifacts, archetypes, etc from). Default is '../../arch'.")
    print("\n\t-r " + colors.underscore + "file" + colors.end + ", --regions=" + colors.underscore + "file" + colors.end + ":\n\t\tSpecify where the 'regions.reg' file is located. Default is '../../maps/regions.reg.")
    print("\n\t-m " + colors.underscore + "map" + colors.end + ", --map=" + colors.underscore + "map" + colors.end + ":\n\t\tSpecify the only map to check for errors.")
    print("\n\t--non-rec:\n\t\tDo not go through directories recursively.")

# Try to parse our command line options.
try:
    opts, args = getopt.getopt(sys.argv[1:], "hcd:m:a:r:", ["help", "cli", "directory=", "map=", "arch=", "regions=", "non-rec", "text-only"])
except getopt.GetoptError as err:
    # Invalid option, show the error, print usage, and exit.
    print(err)
    usage()
    sys.exit(2)

# The default values.
path = "../../maps"
arch_dir = "../../arch"
regions_file = "../../maps/regions.reg"
one_map = None
cli = False
rec = True
text_only = False

# Parse options.
for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-c", "--cli"):
        cli = True
    elif o in ("-d", "--directory"):
        path = a
    elif o in ("-m", "--map"):
        one_map = a
    elif o in ("-a", "--arch"):
        arch_dir = a
    elif o in ("-r", "--regions"):
        regions_file = a
    elif o == "--non-rec":
        rec = False
    elif o == "--text-only":
        text_only = True

if text_only:
    colors.bold = ""
    colors.underscore = ""
    colors.end = ""
    errors.colors = [""] * len(errors.colors)

# Errors we found in maps/objects.
errors_l = []
errors_l_last_map = None
# Errors from artifacts file.
errors_artifacts = []
# Errors from archetypes file.
errors_archetypes = []
# Errors from regions file.
errors_regions = []
# Loaded archetypes.
archetypes = {}
# Artifacts.
artifacts = {}
# Regions.
regions = {}
# List of beacons.
beacons = []

# Default config.
default_cfg = StringIO("""
[Suppress]
medium = off
high = off
warning = off
critical = off
low = off
[Errors]
map_no_music = off
map_no_region = on
decor_wall_l2 = off
decor_wall_l3 = off
decor_wall_l4 = off
sys_not_on_top = on
deprecated_control_chars = off
layer_changed = off
[Ignore]
ignore_events = on
""")

config = ConfigParser()
config.read_file(default_cfg)
config.read(['config.cfg'])

# Add error to errors_l.
# @param map Map file.
# @param msg Description of the error.
# @param severity Severity of the error, from 'errors'.
# @param x X position of object.
# @param y Y position of object.
def add_error(map, msg, severity, x = -1, y = -1):
    global errors_l_last_map

    if errors_l_last_map != map or not errors_l:
        errors_l_last_map = map
        errors_l.append([map, []])

    errors_l[len(errors_l) - 1][1].append((msg, severity, x, y))

# Load the map.
# @param fp File pointer.
# @return Dictionary of the map data, empty dictionary if the map
# is not valid.
def load_map(fp):
    d = {}
    in_map = False
    in_msg = False
    msg_buf = ""

    for line in fp:
        if line == "arch map\n":
            in_map = True
            continue
        elif not in_map:
            return {}
        elif line == "end\n":
            # Store the map's file name.
            d["file"] = fp.name

            # Strip off 'path' if possible.
            if d["file"][:len(path)] == path:
                d["file"] = d["file"][len(path) + 1:]

            # Load the objects on this map.
            parser = ObjectParser(fp)
            d["tiles"] = parser.map(d["file"])

            return d

        # Start of message.
        if line == "msg\n":
            in_msg = True
        # End of message.
        elif line == "endmsg\n":
            in_msg = False
            # Add it to the dictionary, removing the last newline.
            d["msg"] = msg_buf[:-1]
        # Store it in a buffer.
        elif in_msg:
            msg_buf += line
        # Map's attributes.
        else:
            space_pos = line.find(" ")
            # Our value.
            value = line[space_pos + 1:-1]

            if isint(value):
                value = int(value)

            # Add it to the dictionary.
            d[line[:space_pos]] = value

    return {}

# Check map.
# @param map Map to check.
def check_map(map):
    tiles = []

    # Go through the attributes.
    for attribute in map:
        if attribute[:10] == "tile_path_":
            # Map being tiled into itself is a critical error.
            if map["file"][len(map["file"]) - len(map[attribute]):] == map[attribute]:
                add_error(map["file"], "Map is tiled into itself (tile #{0}).".format(attribute[10:]), errors.critical)
                continue

            # Map having two same tiles is also a critical error.
            for tile in tiles:
                if tile == map[attribute]:
                    add_error(map["file"], "Map is tiled to '{0}' more than once.".format(tile), errors.critical)

            tiles.append(map[attribute])

    # No difficulty? Not really an error, but the server will drop a warning and change
    # the difficulty to 1.
    if not "difficulty" in map:
        add_error(map["file"], "Map is missing difficulty.", errors.low)
        map["difficulty"] = 1
    # This is an error, if the difficulty is set, and it's lower than 1 or higher than max level.
    elif map["difficulty"] < 1 or map["difficulty"] > checker.max_level:
        add_error(map["file"], "Map has invalid difficulty: {0}. Valid difficulties are 1-{1}.".format(map["difficulty"], checker.max_level), errors.medium)

    if "bg_music" in map:
        if not re.match("([a-zA-Z0-9_\-]+)\.(\w+)[ 0-9\-]?", map["bg_music"]):
            add_error(map["file"], "Map's background music attribute ('{0}') is not in a valid format. Valid format is (example): ocean.ogg".format(map["bg_music"]), errors.high)

    # Map missing 'width' or 'height' is a serious error.
    if not "width" in map:
        add_error(map["file"], "Map is missing width.", errors.high)

    if not "height" in map:
        add_error(map["file"], "Map is missing height.", errors.high)

    # Do we have a region, but it's not a valid one?
    if "region" in map and not map["region"] in regions:
        add_error(map["file"], "Map's region '{0}' is not defined in regions.reg file.".format(map["region"]), errors.high)

    if not "msg" in map:
        add_error(map["file"], "Map is missing message.", errors.low)
    else:
        if not re.match(r"^Created\:\s*\d{4}-\d{2}-\d{2} [^\n]*(\nModified\:\s*\d{4}-\d{2}-\d{2} [^\n]*)?$", map["msg"]):
            add_error(map["file"], "Map's message is in incorrect format.", errors.low)

    # If there is no height or width, there's no point going on.
    if not "height" or not "width":
        return

    # Skip object checking for empty world maps.
    if map["name"] == "World":
        if "region" in map:
            add_error(map["file"], "Empty world map has a region.", errors.warning)
    else:
        if config.getboolean("Errors", "map_no_region") and not "region" in map:
            add_error(map["file"], "Map is missing region.", errors.medium)

        if config.getboolean("Errors", "map_no_music") and not "bg_music" in map:
            add_error(map["file"], "Map is missing background music.", errors.low)

    # Go through all the spaces on the map.
    for x in range(0, map["width"]):
        for y in range(0, map["height"]):
            if not x in map["tiles"] or not y in map["tiles"][x]:
                continue

            # Our layers.
            layers = [[0] * checker.num_sub_layers for i in range(checker.max_layers + 1)]
            # Number of objects. Layer 0 objects are not counted.
            obj_count = 0
            # Total number of objects, with layer 0 objects.
            obj_count_all = 0
            is_shop = False
            sys_below_floor = False
            have_sys = False
            sys_not_on_top = False

            # Go through the objects on this map space.
            for obj in map["tiles"][x][y]:
                # Get our layer and sub-layer.
                layer = "layer" in obj and obj["layer"] or 0
                sub_layer = "sub_layer" in obj and obj["sub_layer"] or 0
                
                try:
                    # Increase number of layers.
                    layers[layer][sub_layer] += 1
                except IndexError:
                    continue
                
                # Increase number of objects, if we're not on layer 0.
                if layer != 0:
                    obj_count += 1

                # The total count of objects.
                obj_count_all += 1

                # Now recursively check the object.
                check_obj(obj, map)

                if "type" in obj:
                    if obj["type"] == types.shop_floor:
                        is_shop = True

                    if layer == 0:
                        have_sys = True
                    elif have_sys:
                        if layer == 1:
                            sys_below_floor = True
                        else:
                            sys_not_on_top = True

            # No layer 1 objects and there are other non-layer-0 objects? Missing floor.
            if sum(layers[1]) == 0 and obj_count > 0:
                add_error(map["file"], "Missing layer 1 object on tile with some objects -- missing floor?", errors.medium, x, y)

            # Go through the layers (ignoring layer 0), and check if we have more than one
            # object of the same layer on this space.
            for i in range(1, checker.max_layers):
                for j in range(0, checker.num_sub_layers):
                    if layers[i][j] > 1:
                        add_error(map["file"], "More than 1 object ({0}) with layer {1}, sub-layer {2} on same tile.".format(layers[i][j], i, j), errors.warning, x, y)

            if sum(layers[5]) and sum(layers[2]) and config.getboolean("Errors", "decor_wall_l2"):
                add_error(map["file"], "Layer 5 object on tile with layer 2 object(s).", errors.warning, x, y)

            if sum(layers[5]) and sum(layers[3]) and config.getboolean("Errors", "decor_wall_l3"):
                add_error(map["file"], "Layer 5 object on tile with layer 3 object(s).", errors.warning, x, y)

            if sum(layers[5]) and sum(layers[4]) and config.getboolean("Errors", "decor_wall_l4"):
                add_error(map["file"], "Layer 5 object on tile with layer 4 object(s).", errors.warning, x, y)

            if sys_below_floor:
                add_error(map["file"], "System object is below floor.", errors.low, x, y)

            if sys_not_on_top and config.getboolean("Errors", "sys_not_on_top"):
                add_error(map["file"], "System object is not on top.", errors.low, x, y)

            # Recheck all objects on this square if this is a shop...
            if is_shop:
                for obj in map["tiles"][x][y]:
                    if ("sys_object" in obj and obj["sys_object"] == 1) or ("no_pick" in obj and obj["no_pick"] == 1):
                        continue

                    if not "unpaid" in obj or obj["unpaid"] == 0:
                        add_error(map["file"], "Object '{0}' is on a shop tile but is not unpaid.".format(obj["archname"]), errors.high, x, y)

## Check for errors in object message.
## @param msg The message to check.
## @return List of the errors.
def check_obj_msg(msg):
    errors = []
    has_hello = False

    test_msg = re.sub(r"<(\/?[a-z_]+)([^>]*)>", r"\1\2", msg)

    if test_msg.find("[") != -1 or test_msg.find("]") != -1:
        errors.append("unescaped-markup")

    for line in msg.split("\n"):
        if line.startswith("@match "):
            line = line[7:]

            if line.find("^hello$") != -1 and line != "^hello$":
                errors.append("invalid-hello")

            if line == "^hello$":
                has_hello = True

            parts = line.split("|")

            for part in parts:
                if part == "*":
                    continue

                if part[:1] != "^" or part[-1:] != "$":
                    errors.append("suspicious-regex")
        else:
            if line.find("<a") != -1:
                errors.append("link-in-msg")

            if re.search(r"[\^\~\|].*[\^\~\|]", line):
                errors.append("control-chars")

    if not has_hello:
        errors.append("missing-hello")

    return errors

# Recursively check object.
# @param obj Object to check.
# @param map Map.
def check_obj(obj, map):
    # Check all inventory objects.
    for obj_inv in obj["inv"]:
        check_obj(obj_inv, map)

    env = get_env(obj)

    if not "type" in obj or not "type" in env:
        return

    archetype = get_archetype(obj["archname"])

    # Spawn point without an inventory is an error.
    if obj["type"] == types.spawn_point and not obj["inv"]:
        add_error(map["file"], "Empty spawn point object.", errors.medium, env["x"], env["y"])

    if obj["type"] == types.player:
        add_error(map["file"], "Object '{0}' is of type player.", errors.critical, env["x"], env["y"])

    if "env" in obj:
        if not obj["type"] in (types.spawn_point_mob, types.beacon, types.event_object) and obj["env"]["type"] == types.spawn_point:
            add_error(map["file"], "Object '{0}' is not a monster but is inside a spawn point.".format(obj["archname"]), errors.high, env["x"], env["y"])

        if obj["type"] == types.spawn_point or (obj["env"]["type"] != types.creator and obj["type"] in (types.exit, types.teleporter)):
            add_error(map["file"], "Object '{0}' is inside inventory of another object, but it's not allowed for that object to be inside of inventory.".format(obj["archname"]), errors.high, env["x"], env["y"])

        if "x" in obj:
            add_error(map["file"], "Object '{0}' has X position set but is in inventory of another object.".format(obj["archname"]), errors.medium, env["x"], env["y"])

        if "y" in obj:
            add_error(map["file"], "Object '{0}' has Y position set but is in inventory of another object.".format(obj["archname"]), errors.medium, env["x"], env["y"])

    if "modified_artifact" in obj and obj["archname"] in artifacts:
        add_error(map["file"], "Artifact '{0}' with modified attributes. Move to artifacts file to fix this.".format(obj["archname"]), errors.high, env["x"], env["y"])

    if get_entry(obj, "same_attributes") == True:
        add_error(map["file"], "Object '{0}' has attribute(s) with values same as the default.".format(obj["archname"]), errors.low, env["x"], env["y"])

    if get_entry(obj, "sys_object") == True and get_entry(obj, "layer") not in (0, None):
        if not "env" in obj or obj["env"]["type"] != types.spawn_point_mob:
            add_error(map["file"], "Object '{0}' is a system object but has a layer set.".format(obj["archname"]), errors.low, env["x"], env["y"])

    if obj["type"] == types.monster or obj["type"] == types.spawn_point_mob:
        if not "level" in obj:
            add_error(map["file"], "Monster '{0}' has unset level.".format(obj["archname"]), errors.medium, env["x"], env["y"])
        else:
            if obj["level"] < 0 or obj["level"] > checker.max_level:
                add_error(map["file"], "Monster '{0}' has invalid level ({1}).".format(obj["archname"], obj["level"]), errors.high, env["x"], env["y"])
            elif not is_friendly(obj) and obj["level"] >= 10 and map["difficulty"] == 1:
                add_error(map["file"], "Monster '{0}' is level {1} but map's difficulty is 1.".format(obj["archname"], obj["level"]), errors.medium, env["x"], env["y"])

        if not "race" in obj:
            add_error(map["file"], "Monster '{0}' is missing a race.".format(obj["archname"]), errors.medium, env["x"], env["y"])
        elif obj["race"] == "undead":
            if not "undead" in obj or obj["undead"] != 1:
                add_error(map["file"], "Monster '{0}' is of race 'undead', but has no 'undead 1' flag set.".format(obj["archname"]), errors.medium, env["x"], env["y"])

        if get_entry(obj, "friendly") == 1 and obj["name"] not in ("guard", "knight"):
            if obj["name"] == archetype["name"] and get_entry(map, "region") != "creation":
                has_say_event = False
                has_generic_guard_script = False

                for tmp in obj["inv"]:
                    if get_entry(tmp, "type") == types.event_object and get_entry(tmp, "sub_type") == 6:
                        if get_entry(tmp, "race") == "/python/generic/guard.py":
                            has_generic_guard_script = True

                        has_say_event = True
                        break

                if not has_generic_guard_script:
                    if "msg" in obj or has_say_event:
                        add_error(map["file"], "NPC '{0}' has no custom name, but has a dialog.".format(obj["archname"]), errors.warning, env["x"], env["y"])
            elif obj["name"][:1].istitle() and not re.match(r"^([A-Z][a-z\']*)( [A-Z][a-z\']*)?( (XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))?$", obj["name"]):
                add_error(map["file"], "NPC '{0}' has name in incorrect format.".format(obj["archname"]), errors.low, env["x"], env["y"])

    if obj["type"] == types.spawn_point_mob:
        if not "env" in obj or obj["env"]["type"] != types.spawn_point:
            add_error(map["file"], "Monster '{0}' is a spawn point monster but is not inside a spawn point.".format(obj["archname"]), errors.critical, env["x"], env["y"])

    if obj["type"] == types.monster:
        add_error(map["file"], "Monster '{0}' is outside spawn point.".format(obj["archname"]), errors.medium, env["x"], env["y"])

    if obj["type"] == types.random_drop or obj["type"] == types.quest_container:
        if not "env" in obj:
            add_error(map["file"], "Object '{0}' outside of inventory.".format(obj["archname"]), errors.high, env["x"], env["y"])

    if obj["type"] == types.quest_container:
        if not "name" in obj:
            add_error(map["file"], "Quest container '{0}' has no quest name.".format(obj["archname"]), errors.high, env["x"], env["y"])

    abilities = []
    wps = []
    events = []

    for tmp in obj["inv"]:
        if not "type" in tmp:
            continue

        if tmp["type"] == types.ability:
            abilities.append(tmp)
        elif tmp["type"] == types.waypoint:
            wps.append(tmp)
        elif tmp["type"] == types.event_object:
            events.append(tmp)

    for event in events:
        num = 0

        for event2 in events:
            if get_entry(event, "sub_type") == get_entry(event2, "sub_type"):
                num += 1

        if num > 1:
            add_error(map["file"], "NPC '{0}' has events with two or more events with the same event type.".format(obj["archname"]), errors.low, env["x"], env["y"])
            break

    if "can_cast_spell" in obj and obj["can_cast_spell"] == 1:
        if not abilities:
            add_error(map["file"], "Monster '{0}' can cast spells but has no ability objects.".format(obj["archname"]), errors.low, env["x"], env["y"])

        if not "maxsp" in obj or obj["maxsp"] == 0:
            add_error(map["file"], "Monster '{0}' can cast spells but has 0 mana.".format(obj["archname"]), errors.medium, env["x"], env["y"])

        if not "Dex" in obj or obj["Dex"] == 0:
            add_error(map["file"], "Monster '{0}' can cast spells but has unset ability usage.".format(obj["archname"]), errors.medium, env["x"], env["y"])
    else:
        if abilities:
            add_error(map["file"], "Monster '{0}' cannot cast spells but has ability objects.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    # Waypoints movement.
    if "movement_type" in obj and obj["movement_type"] == 176:
        if not wps:
            add_error(map["file"], "Monster '{0}' has waypoint movement enabled but no waypoints.".format(obj["archname"]), errors.medium, env["x"], env["y"])
        else:
            for wp in wps:
                if not "name" in wp:
                    add_error(map["file"], "Monster '{0}' has waypoint with no name.".format(obj["archname"]), errors.high, env["x"], env["y"])

                if "title" in wp:
                    found_one = False

                    for wp_next in wps:
                        if "name" in wp_next and wp_next["name"] == wp["title"]:
                            found_one = True
                            break

                    if not found_one:
                        add_error(map["file"], "Monster '{0}' has waypoint ('{1}') with nonexistent next waypoint.".format(obj["archname"], "name" in wp and wp["name"] or "<no name>"), errors.high, env["x"], env["y"])
    else:
        if wps:
            add_error(map["file"], "Monster '{0}' has waypoint movement disabled but has waypoints in inventory.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if obj["type"] == types.sign:
        # Is it a magic mouth?
        if get_entry(obj, "walk_on") == 1 or get_entry(obj, "fly_on") == 1:
            if get_entry(obj, "splitting") == 1 and get_entry(obj, "direction") == None:
                add_error(map["file"], "Magic mouth '{0}' has adjacent direction set but actual facing direction is not set.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if get_entry(obj, "direction") not in (None, 0) and get_entry(obj, "is_turnable") != 1 and get_entry(obj, "is_animated") != 1 and get_entry(obj, "draw_direction") != 1:
        add_error(map["file"], "Object '{0}' has direction but that type of object doesn't support directions.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if obj["type"] in (types.event_object, types.map_event_object):
        if not "name" in obj:
            add_error(map["file"], "Event object '{0}' is missing plugin name.".format(obj["archname"]), errors.high, env["x"], env["y"])
        elif not obj["name"] in checker.plugins:
            add_error(map["file"], "Event object '{0}' has unknown plugin '{1}'.".format(obj["archname"], obj["name"]), errors.critical, env["x"], env["y"])

        if "race" in obj:
            if obj["race"].startswith("..") and obj["race"].find("/python") != -1:
                add_error(map["file"], "Event object '{0}' is using a relative path to point to the global /python directory.".format(obj["archname"]), errors.warning, env["x"], env["y"])

            if obj["race"].startswith("/") and not os.path.isfile(os.path.join(os.path.dirname(__file__), path) + obj["race"]):
                add_error(map["file"], "Event object '{0}' has a path that doesn't exist.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if obj["type"] == types.beacon:
        if not "name" in obj:
            add_error(map["file"], "Beacon '{0}' is missing name.".format(obj["archname"]), errors.critical, env["x"], env["y"])
        elif obj["name"] in beacons:
            add_error(map["file"], "Beacon '{0}' with the name '{0}' already exists.".format(obj["archname"], obj["name"]), errors.critical, env["x"], env["y"])
        else:
            beacons.append(obj["name"])

    if get_entry(obj, "random_movement") == 1:
        if not get_entry(obj, "item_race") or not get_entry(obj, "item_level"):
            add_error(map["file"], "Monster '{0}' has random movement enabled but no max movement range X/Y.".format(obj["archname"]), errors.low, env["x"], env["y"])

    if get_entry(obj, "is_turnable") == 1 and get_entry(obj, "draw_direction") == 1:
        if get_entry(obj, "direction") in (5, 6, 4, 3, 2, 8):
            add_error(map["file"], "Object {0} has wrong direction {1}; must be facing either west or north.".format(obj["archname"], get_entry(obj, "direction")), errors.low, env["x"], env["y"])

    if obj["type"] in (types.door, types.gate, types.wall):
        if get_entry(obj, "damned") == 1:
            add_error(map["file"], "Object {0} has 'damned 1' flag set, but this is not supported.".format(obj["archname"]), errors.low, env["x"], env["y"])

        if get_entry(obj, "no_magic") == 1:
            add_error(map["file"], "Object {0} has 'no_magic 1' flag set, which may be an error, as this flag is usually set on floor objects.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if obj["type"] in (types.spawn_point_mob, types.magic_ear, types.book, types.sign):
        msg = get_entry(obj, "msg")

        if msg:
            is_mob_dialogue = obj["type"] == types.spawn_point_mob
            is_ear_dialogue = obj["type"] == types.magic_ear
            is_dialogue = is_mob_dialogue or is_ear_dialogue

            msg_errors = check_obj_msg(msg)

            if is_mob_dialogue:
                if "missing-hello" in msg_errors:
                    add_error(map["file"], "Object {0} has a @match dialogue that is missing '@match ^hello$'.".format(obj["archname"]), errors.low, env["x"], env["y"])

            if is_dialogue:
                if "invalid-hello" in msg_errors:
                    add_error(map["file"], "Object {0} has a @match dialogue that has invalid '@match ^hello$'.".format(obj["archname"]), errors.low, env["x"], env["y"])

                if "suspicious-regex" in msg_errors:
                    add_error(map["file"], "Object {0} has a @match that doesn't use regex.".format(obj["archname"]), errors.low, env["x"], env["y"])

                if "link-in-msg" in msg_errors:
                    add_error(map["file"], "Object {0} has a @match which uses links of some sort - this is not recommended.".format(obj["archname"]), errors.low, env["x"], env["y"])

            if "control-chars" in msg_errors and config.getboolean("Errors", "deprecated_control_chars"):
                add_error(map["file"], "Object {0} contains deprecated control characters in message.".format(obj["archname"]), errors.low, env["x"], env["y"])

            if "unescaped-markup" in msg_errors:
                add_error(map["file"], "Object {0} contains unescaped markup in message.".format(obj["archname"]), errors.low, env["x"], env["y"])

    if config.getboolean("Errors", "layer_changed") and "layer" in obj and obj["layer"] != 0 and "layer" in archetype and archetype["layer"] != 0 and obj["layer"] != archetype["layer"]:
        add_error(map["file"], "Object {0} has had layer changed to {1} from the default value of {2} - this is not recommended.".format(obj["archname"], obj["layer"], archetype["layer"]), errors.warning, env["x"], env["y"])

    if "carrying" in obj:
        add_error(map["file"], "Object {0} has carrying attribute set.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if "animation" in obj and obj["animation"] == "NONE":
        add_error(map["file"], "Object {0} has animation attribute set to NONE.".format(obj["archname"]), errors.warning, env["x"], env["y"])

    if get_entry(obj, "face") != get_entry(archetype, "face"):
        if get_entry(obj, "is_turnable") == 1 or get_entry(obj, "is_animated") == 1:
            add_error(map["file"], "Object {0} is animated/turnable but has had face changed.".format(obj["archname"]), errors.warning, env["x"], env["y"])

        if obj["type"] == types.light_source:
            add_error(map["file"], "Object {0} is a light source but has had face changed.".format(obj["archname"]), errors.warning, env["x"], env["y"])

def check_archetype(arch, errors_l):
    if not "type" in arch:
        return

    if get_entry(arch, "material") and not (get_entry(arch, "material_real") or get_entry(arch, "item_quality")) and not get_entry(arch, "no_pick"):
        errors_l.append(["Archetype '{0}' has material set but no material_real or item_quality.".format(arch["archname"]), errors.low])

    # Is the archetype (shop) floor with 'is_floor 1' not set?
    if arch["type"] in (types.floor, types.shop_floor) and get_entry(arch, "is_floor") != 1:
        errors_l.append(["Archetype '{0}' is of type floor but doesn't have 'is_floor 1' set.".format(arch["archname"]), errors.low])

    if arch["type"] == types.magic_mirror and get_entry(arch, "sys_object") != 1:
        errors_l.append(["Archetype '{0}' is a magic mirror but is not 'sys_object 1'.".format(arch["archname"]), errors.medium])

# Load map. If successfully loaded, we will check the map header
# and its objects with check_map().
# @param file Map to load.
def check_file(file):
    fp = open(file, "r")
    map = load_map(fp)
    fp.close()

    if map:
        check_map(map)

# Recursively scan directories and call check_file on found files.
# @param dir Directory to scan.
def scan_dirs(dir):
    files = os.listdir(dir)

    for file in files:
        if os.path.isdir(dir + "/" + file):
            # Skip obvious non-map directories. It's still possible to scan those
            # if you pass --directory option however.
            if file in ("styles", "python") or not rec:
                continue

            if file == "events" and config.getboolean("Ignore", "ignore_events"):
                continue

            scan_dirs(dir + "/" + file)
        else:
            check_file(dir + "/" + file)

# Do the scan. If 'one_map' argument was specified, we will use that,
# otherwise we will recursively scan 'path'.
def do_scan():
    if one_map:
        check_file(one_map)
    else:
        scan_dirs(path)

# Try to find an archetype by its arch name. This will also consider artifacts
# as archetypes.
# @param archname Arch name to find.
# @return The arch (or artifact) if found, None otherwise.
def get_archetype(archname):
    if archname in archetypes:
        return archetypes[archname]
    elif archname in artifacts:
        return artifacts[archname]

    return None

# Recursively look through object's environment value.
# @param obj Object.
# @return Object on map that has this object somewhere in its inventory.
def get_env(obj):
    ret = obj

    while "env" in ret:
        ret = ret["env"]

    return ret

# Check if monster object is friendly or not.
# @param obj Object.
# @return True if it's friendly, False otherwise.
def is_friendly(obj):
    if get_entry(obj, "friendly") == 1:
        return True

    return False

# Get entry identified by 's' from dictionary 'd'.
# @param d The dictionary.
# @param s What to get.
# @return The entry from the dictionary, None if there is no such entry.
def get_entry(d, s):
    try:
        return d[s]
    except KeyError:
        return None

# Check whether the passed string is an integer.
# @param s String.
# @return True if s is an integer, False otherwise.
def isint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# Object parser.
class ObjectParser:
    # Initializer.
    # @param fp File pointer to read data from.
    def __init__(self, fp):
        self.fp = fp
        self.dict = {}
        self.last_obj = None
        self.in_msg = False
        self.msg_buf = ""
        self.line_num = 0

    # Archetypes parser.
    # @return Archetypes.
    def archetypes(self):
        for line in self.fp:
            self.line_num += 1

            if line[:7] == "Object ":
                self.last_obj = line[7:-1]
                self.dict[self.last_obj] = {
                    "archname": self.last_obj,
                }
                continue
            elif not self.last_obj:
                continue
            elif line == "end\n":
                self.last_obj = None
                continue

            # Parse attributes.
            self.parse(line, self.dict[self.last_obj])

        return self.dict

    # Artifacts parser.
    # @return Artifacts.
    def artifacts(self):
        for line in self.fp:
            self.line_num += 1

            if line[:9] == "artifact ":
                self.last_obj = line[9:-1]
                self.dict[self.last_obj] = {}
                continue
            elif not self.last_obj:
                continue
            elif line[:9] == "def_arch ":
                archetype = line[9:-1]
                found = get_archetype(archetype)

                if not found and archetype in self.dict:
                    found = dict(self.dict[archetype])

                if not found:
                    errors_artifacts.append(["Artifact '{0}': Could not find archetype '{1}' for def_arch command (line: {2}).".format(self.last_obj, archetype, self.line_num), errors.critical])
                else:
                    self.dict[self.last_obj] = dict(found)
                    self.dict[self.last_obj]["archname"] = self.last_obj

                continue
            elif line == "end\n":
                self.last_obj = None
                continue

            # Parse attributes.
            self.parse(line, self.dict[self.last_obj])

        return self.dict

    # Map objects parser.
    # @param map_file Map file name we're loading objects for.
    # @return List of map tiles containing the found objects.
    def map(self, map_file):
        # Map tiles.
        self.tiles = {}
        self.map_file = map_file

        for line in self.fp:
            if line.startswith("arch "):
                arch = self.map_parse_rec(line[5:-1])
                self.map_add_tile(arch)

        return self.tiles

    # Add object to map's tiles.
    # @param arch Object to add.
    def map_add_tile(self, arch):
        x = arch["x"]
        y = arch["y"]

        if not x in self.tiles:
            self.tiles[x] = {}

        if not y in self.tiles[x]:
            self.tiles[x][y] = []

        self.tiles[x][y].append(arch)

    # Recursively parse objects on map.
    # @param archname Arch name we previously found.
    # @return Archetype, complete with its inventory.
    def map_parse_rec(self, archname, env = None):
        # Find the archetype first.
        def_archetype = get_archetype(archname)
        archetype = dict(def_archetype) if def_archetype else {}

        # Store its name.
        archetype["archname"] = archname
        # Inventory.
        archetype["inv"] = []

        if env:
            archetype["env"] = env
        else:
            archetype["x"] = 0
            archetype["y"] = 0

        for line in self.fp:
            # Another arch? That means it's inside the previous one.
            if line.startswith("arch "):
                # Add it to the object's inventory.
                archetype["inv"].append(self.map_parse_rec(line[5:-1], archetype))
            elif line == "end\n":
                break
            # Parse attributes.
            else:
                parsed = self.parse(line, archetype)

                if parsed and def_archetype:
                    (attr, value) = parsed

                    if not attr in ("x", "y", "identified", "unpaid", "no_pick", "level", "nrof", "value", "can_stack", "layer", "sub_layer", "z", "zoom", "zoom_x", "zoom_y", "alpha", "align"):
                        archetype["modified_artifact"] = True

                    def_value = get_entry(def_archetype, attr)

                    if def_value == value or (value in (0, 0.0) and def_value == None):
                        archetype["same_attributes"] = True

        if not def_archetype:
            env = get_env(archetype)
            add_error(self.map_file, "Invalid archetype '{0}' found.".format(archetype["archname"]), errors.critical, "x" in env and env["x"] or 0, "y" in env and env["y"] or 0)

        return archetype

    # Parse attributes from a line.
    # @param line Line to parse from.
    # @param dict Dictionary add parsed attributes to.
    def parse(self, line, d):
        # Message start?
        if line == "msg\n":
            self.in_msg = True
        # End of message.
        elif line == "endmsg\n":
            self.in_msg = False
            msg = self.msg_buf[:-1]
            # Add it to the dict without the last newline.
            d["msg"] = msg
            self.msg_buf = ""
            return ("msg", msg)
        # We are in a message, store it in a buffer.
        elif self.in_msg:
            self.msg_buf += line
        # Not a message, so attribute/value combo.
        else:
            # Find space.
            space_pos = line.find(" ")
            # Our value.
            value = line[space_pos + 1:-1]

            try:
                integer = int(value)
                value = integer
            except:
                pass

            attr = line[:space_pos]
            # Add it to the dictionary.
            d[attr] = value
            return (attr, value)

        return None

# Parse the archetypes.
# @return Dictionary of the archetypes.
def parse_archetypes():
    fp = open(arch_dir + "/archetypes")
    parser = ObjectParser(fp)
    d = parser.archetypes()
    fp.close()

    # Post-processing.
    for arch in d:
        if not "name" in d[arch]:
            d[arch]["name"] = arch

    for arch in d:
        check_archetype(d[arch], errors_archetypes)

    return d

# Parse the artifacts.
# @return Dictionary of the artifacts.
def parse_artifacts():
    fp = open(arch_dir + "/artifacts")
    parser = ObjectParser(fp)
    d = parser.artifacts()
    fp.close()

    for arch in d:
        check_archetype(d[arch], errors_artifacts)

    return d

# Parse the regions.
# @return Dictionary of the regions.
def parse_regions():
    fp = open(regions_file)
    d = {}
    region = None
    in_msg = False
    msg_buf = ""

    for line in fp:
        if line[:7] == "region ":
            region = line[7:-1]
            d[region] = {}
            continue
        elif not region:
            continue
        elif line == "end\n":
            region = None
            continue

        # Start of message.
        if line == "msg\n":
            in_msg = True
        # End of message.
        elif line == "endmsg\n":
            in_msg = False
            # Add it to the dictionary, removing the last newline.
            d[region]["msg"] = msg_buf[:-1]
        # Store it in a buffer.
        elif in_msg:
            msg_buf += line
        # Region's attributes.
        else:
            space_pos = line.find(" ")
            # Our value.
            value = line[space_pos + 1:-1]

            if isint(value):
                value = int(value)

            # Add it to the dictionary.
            d[region][line[:space_pos]] = value

    fp.close()
    return d

def config_save():
    with open("config.cfg", "w") as configfile:
        config.write(configfile)

# Find files in the specified path.
# @param where Where to look for the files.
# @param ext What the file must end with.
# @param rec Whether to go on recursively.
# @param ignore_dirs Whether to ignore directories.
# @param ignore_files Whether to ignore files.
# @param ignore_paths What paths to ignore.
# @return A list containing files/directories found based on the set criteria.
def find_files(where, ext = None, rec = True, ignore_dirs = True, ignore_files = False, ignore_paths = None):
    nodes = os.listdir(where)
    files = []

    for node in nodes:
        path = os.path.join(where, node)

        # Do we want to ignore this path?
        if ignore_paths and path in ignore_paths:
            continue

        # A directory.
        if os.path.isdir(path):
            # Do we want to go on recursively?
            if rec:
                files += find_files(path, ext)

            # Are we ignoring directories? If not, add it to the list.
            if not ignore_dirs:
                files.append(path)
        else:
            # Only add the file if we're not ignoring files and ext was not set or it matches.
            if not ignore_files and (not ext or path.endswith(ext)):
                files.append(path)

    return files

# Find .arc file of archetype definition.
# @param arch Archetype to find.
# @return Path to the .arc file, None if the archetype could not be found.
def find_archetype_file(arch):
    for file in find_files(arch_dir, ".arc"):
        fp = open(file, "r")

        for line in fp:
            if line == "Object " + arch + "\n":
                fp.close()
                return file

        fp.close()

    return None

# Find .art file of artifact definition.
# @param art Artifact to find.
# @return Path to the .art file, None if the artifact could not be found.
def find_artifact_file(art):
    for file in find_files(arch_dir, ".art"):
        fp = open(file, "r")

        for line in fp:
            if line == "artifact " + art + "\n":
                fp.close()
                return file

        fp.close()

    return None

archetypes = parse_archetypes()
artifacts = parse_artifacts()
regions = parse_regions()

# GUI.
if not cli:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    
    import re, webbrowser
    from datetime import datetime

    class pref_types:
        checkbox = 1

    # Preferences dialog.
    class PreferencesDialog:
        # Contents of the dialog window.
        tabs = [
            ["Errors", "Allow you to turn on/off specific types of error messages.", [
                [pref_types.checkbox, "Map with no region", ("Errors", "map_no_region")],
                [pref_types.checkbox, "Map with no music", ("Errors", "map_no_music")],
                [pref_types.checkbox, "Layer 2 object on square with a wall", ("Errors", "decor_wall_l2")],
                [pref_types.checkbox, "Layer 3 object on square with a wall", ("Errors", "decor_wall_l3")],
                [pref_types.checkbox, "Layer 4 object on square with a wall", ("Errors", "decor_wall_l4")],
                [pref_types.checkbox, "System object not on top of normal objects", ("Errors", "sys_not_on_top")],
                [pref_types.checkbox, "Check for deprecated control characters", ("Errors", "deprecated_control_chars")],
                [pref_types.checkbox, "Layer changed from the default value", ("Errors", "layer_changed")],
            ], "\n<b>Note:</b> You need to do a new scan to see the results."],
            ["Suppress", "These allow you to suppress an entire category of error messages.", [
                [pref_types.checkbox, "Warning", ("Suppress", "warning")],
                [pref_types.checkbox, "Low", ("Suppress", "low")],
                [pref_types.checkbox, "Medium", ("Suppress", "medium")],
                [pref_types.checkbox, "High", ("Suppress", "high")],
                [pref_types.checkbox, "Critical", ("Suppress", "critical")],
            ], None],
            ["Ignore", "Allows you to ignore certain maps from being checked in global-scan.", [
                [pref_types.checkbox, "Ignore event maps", ("Ignore", "ignore_events")],
            ], None],
        ]

        # Callback for applying settings in the dialog.
        # @param widget Widget.
        # @param data Our data. Includes things like the setting type, config section,
        # etc.
        def callback(self, widget, data = None):
            (pref_type, (config_section, config_name)) = data

            if pref_type == pref_types.checkbox:
                config.set(config_section, config_name, ("off", "on")[widget.get_active()])

            self.main.draw_errors()

        # Initializer.
        # @param main Class we're coming from.
        def __init__(self, main):
            # Make a new window.
            self.window = Gtk.Window(type = Gtk.WindowType.TOPLEVEL)
            # Set the window's parent.
            self.window.set_transient_for(main.window)
            # Center it on parent.
            self.window.set_position(Gtk.WIN_POS_CENTER_ON_PARENT)
            # Set title.
            self.window.set_title("Properties")
            # Set default size.
            self.window.resize(400, 20)
            self.main = main

            # Create vertical box.
            self.window.vbox = Gtk.VBox()
            self.window.add(self.window.vbox)

            # Create a new table, and add it to the box.
            table = Gtk.Table(2, 2, False)
            self.window.vbox.add(table)

            # Create a new GTK Notebook and add it to the table.
            notebook = Gtk.Notebook()
            notebook.set_tab_pos(Gtk.POS_LEFT)
            table.attach(notebook, 0, 1, 0, 1, xpadding = 10, ypadding = 5)

            # Now we create the contents.
            for (tab_name, desc, prefs, note) in self.tabs:
                # Set up alignment.
                vbox_alignment = Gtk.Alignment()
                vbox_alignment.set_padding(5, 5, 10, 10)
                # Create a vertical box, and add it to the alignment.
                vbox = Gtk.VBox(False, 2)
                vbox_alignment.add(vbox)

                # Create another alignment, set up label, add description contents,
                # and add it to the box.
                alignment = Gtk.Alignment()
                label = Gtk.Label()
                label.set_markup(desc)
                vbox.pack_start(alignment, False, True, 1)
                alignment.add(label)

                # Now we add the actual preferences.
                for (pref_type, pref_name, pref_config) in prefs:
                    # Alignment.
                    alignment = Gtk.Alignment()
                    alignment.set_padding(0, 0, 10, 5)
                    (config_section, config_name) = pref_config

                    # A checkbox?
                    if pref_type == pref_types.checkbox:
                        widget = Gtk.CheckButton(pref_name)
                        widget.set_active(config.getboolean(config_section, config_name))
                        widget.connect("toggled", self.callback, (pref_type, pref_config))

                    vbox.pack_start(alignment, False, True, 1)
                    alignment.add(widget)

                # If we have a note about the particular tab, add it like
                # description above.
                if note:
                    alignment = Gtk.Alignment()
                    label = Gtk.Label()
                    label.set_markup(note)
                    vbox.pack_start(alignment, False, True, 1)
                    alignment.add(label)

                # Create a label for the tab name, and actually append it to the
                # notebook.
                label = Gtk.Label(tab_name)
                notebook.append_page(vbox_alignment, label)

            # Create alignment, attach it to the table, and create a
            # close button.
            alignment = Gtk.Alignment(1)
            table.attach(alignment, 0, 1, 1, 2, xpadding = 10, ypadding = 5)
            button = Gtk.Button("Close", Gtk.STOCK_CLOSE)
            button.connect("clicked", self.quit_event)
            alignment.add(button)

            self.window.show_all()

        # Quit event. Destroy the preferences window.
        def quit_event(self, widget, event = None, data = None):
            self.window.destroy()
            return False

    # The GUI class.
    class GUI:
        # Our UI, with menu and toolbar.
        ui = '''<ui>
<menubar name="MenuBar">
    <menu action="File">
        <menuitem action="Scan" />
        <menuitem action="Save" />
        <menuitem action="Open Maps" />
        <separator />
        <menuitem action="Check File" />
        <menuitem action="Check Directory" />
        <separator />
        <menuitem action="Preferences" />
        <separator />
        <menuitem action="Quit" />
    </menu>
    <menu action="Reload">
        <menuitem action="Reload Archetypes" />
        <menuitem action="Reload Artifacts" />
        <menuitem action="Reload Regions" />
    </menu>
    <menu action="Help">
        <menuitem action="Report a Problem" />
        <menuitem action="About" />
    </menu>
</menubar>
<toolbar name="Toolbar">
    <toolitem action="Quit" />
    <separator />
    <toolitem action="Scan" />
    <toolitem action="Save" />
</toolbar>
</ui>'''

        # Initializer.
        def __init__(self):
            # Create a liststore.
            self.liststore = Gtk.ListStore(str, str, str)

            # The window.
            self.window = Gtk.Window(type = Gtk.WindowType.TOPLEVEL)
            # Set the title.
            self.window.set_title(checker.name)
            # 800x600 resolution.
            self.window.set_size_request(800, 600)
            self.window.connect("delete_event", self.quit_event)

            icon = self.find_icon()

            if icon:
                self.window.set_icon(icon)

            # New box.
            self.window.vbox = Gtk.VBox()
            self.window.add(self.window.vbox)

            # Create UIManager instance.
            uimanager = Gtk.UIManager()

            # Create an ActionGroup.
            self.actiongroup = Gtk.ActionGroup(name = "UIManager")

            # Create actions.
            self.actiongroup.add_actions([
                ("File", None, "_File"),
                ("Scan", Gtk.STOCK_EXECUTE, "_Scan", "<control>s", "Scan maps", self.scan_button),
                ("Save", Gtk.STOCK_SAVE, "_Save", "<control><shift>s", "Save", self.save_button),
                ("Open Maps", Gtk.STOCK_OPEN, "_Open Maps", "<control>o", "Open maps", self.open_maps_button),
                ("Check File", Gtk.STOCK_OPEN, "_Check File", "<control>f", "Check File", self.check_file_button),
                ("Check Directory", Gtk.STOCK_DIRECTORY, "_Check Directory", "<control>d", "Check Directory", self.check_directory_button),
                ("Preferences", Gtk.STOCK_PREFERENCES, "_Preferences", "<control>p", "Preferences", self.preferences_button),
                ("Quit", Gtk.STOCK_QUIT, "_Quit", "<control>q", "Quit the program", self.quit_button),
                ("Reload", None, "_Reload"),
                ("Reload Archetypes", None, "_Reload Archetypes", None, "Reload archetypes from file", self.reload_archetypes_button),
                ("Reload Artifacts", None, "_Reload Artifacts", None, "Reload artifacts from file", self.reload_artifacts_button),
                ("Reload Regions", None, "_Reload Regions", None, "Reload regions from file", self.reload_regions_button),
                ("Help", None, "_Help"),
                ("Report a Problem", None, "_Report a Problem", None, "Report a Problem", self.report_button),
                ("About", Gtk.STOCK_ABOUT, "_About", None, "About this application", self.about_button),
            ])

            # Add the actiongroup to the UIManager.
            uimanager.insert_action_group(self.actiongroup, 0)

            # Add UI description.
            uimanager.add_ui_from_string(self.ui)

            # Create a MenuBar.
            menubar = uimanager.get_widget("/MenuBar")
            self.window.vbox.pack_start(menubar, False, True, 0)

            # Create a Toolbar.
            toolbar = uimanager.get_widget("/Toolbar")
            self.window.vbox.pack_start(toolbar, False, True, 0)

            # Create scrolled window.
            self.window.sw = Gtk.ScrolledWindow()
            # So the scrollbars only appear if they're needed.
            self.window.sw.set_property("hscrollbar-policy", Gtk.PolicyType.AUTOMATIC)
            self.window.sw.set_property("vscrollbar-policy", Gtk.PolicyType.AUTOMATIC)

            # Tree model.
            self.window.sm = Gtk.TreeModelSort(model = self.liststore)
            # Set sort column.
            self.window.sm.set_sort_column_id(0, Gtk.SortType.ASCENDING)
            # Tree view.
            self.window.tv = Gtk.TreeView(model = self.window.sm)
            self.window.tv.connect("row-activated", self.row_click_event)
            self.window.vbox.pack_start(self.window.sw, True, True, 0)

            self.window.sw.add(self.window.tv)

            # Our columns.
            columns = [
                ["Map", False],
                ["Severity", True],
                ["Description", False],
            ]
            self.window.tv.column = [None] * 3
            self.window.tv.cell = [None] * 3

            for i in range(3):
                self.window.tv.cell[i] = Gtk.CellRendererText()

                # See if we want Pango markup or not.
                if columns[i][1]:
                    self.window.tv.column[i] = Gtk.TreeViewColumn(columns[i][0], self.window.tv.cell[i], markup = 1)
                else:
                    self.window.tv.column[i] = Gtk.TreeViewColumn(columns[i][0])

                self.window.tv.append_column(self.window.tv.column[i])
                self.window.tv.column[i].set_sort_column_id(i)

                # Pango markup doesn't need this.
                if not columns[i][1]:
                    self.window.tv.column[i].pack_start(self.window.tv.cell[i], True)
                    self.window.tv.column[i].set_attributes(self.window.tv.cell[i], text = i)

            # Draw any errors (there can be some from things like artifacts, archetypes, etc)
            self.draw_errors()

            # Now show it all.
            self.window.show_all()

        # Event that happens when we quit the application (X at top right, ctrl + q, etc).
        def quit_event(self, widget, event, data = None):
            Gtk.main_quit()
            return False

        # Event activated when row is clicked.
        def row_click_event(self, treeview, i, view_column):
            map_name = self.window.sm.get_model()[i][0]
            msg = self.window.sm.get_model()[i][2]

            if map_name == "Archetypes":
                arch = re.sub(r"[Aa]rchetype '([^']*)'(.*)", r"\1", msg)
                file = find_archetype_file(arch)

                if file:
                    webbrowser.open(file)
            elif map_name == "Regions":
                webbrowser.open(regions_file)
            elif map_name == "Artifacts":
                arch = re.sub(r"[Aa]rtifact '([^']*)'(.*)", r"\1", msg)
                file = find_artifact_file(arch)

                if file:
                    webbrowser.open(file)

        # Preferences dialog.
        def preferences_button(self, b):
            PreferencesDialog(self)

        # We pressed the quit button, so quit.
        def quit_button(self, b):
            Gtk.main_quit()

        # The report button. Take us to the Atrinik Bugzilla.
        def report_button(self, b):
            webbrowser.open(checker.website_bug)

        # About button.
        def about_button(self, b):
            about = Gtk.AboutDialog()
            about.set_transient_for(self.window)
            about.set_name(checker.name)
            about.set_version(checker.version)
            about.set_copyright(checker.copyright)
            about.set_license(checker.license)
            about.set_wrap_license(True)
            about.set_comments(checker.description)
            about.set_authors(checker.authors)
            about.set_website(checker.website)
            icon = self.find_icon()

            if icon:
                about.set_logo(icon)

            about.connect("response", lambda d, r: d.destroy())
            about.show()

        # Open maps button.
        def open_maps_button(self, b):
            maps = []

            for row in self.window.sm.get_model():
                # Ignore non-map errors.
                if row[0] == "Artifacts" or row[0] == "Archetypes" or row[0] == "Regions":
                    continue

                m_path = os.path.realpath(os.path.join(path, row[0]))

                if not m_path in maps:
                    maps.append(m_path)

            # Get default environment variables.
            envs = dict(os.environ)
            delimiter = ";" if sys.platform.startswith("win") else ":"
            # Extend the PATH environment variable with the script's dir.
            envs["PATH"] += delimiter + os.path.abspath(os.path.dirname(__file__))
            # Execute Gridarta.
            subprocess.Popen(["java", "-jar", os.path.realpath(arch_dir + "/../editor/AtrinikEditor.jar")] + maps, env = envs, cwd = os.path.realpath(arch_dir + "/../editor"))

        # The save button. Will save output in the tree view to file.
        def save_button(self, b):
            l = self.window.sm.get_model()

            # Nothing to save, display an error.
            if len(l) == 0:
                dialog = Gtk.MessageDialog(self.window, 0, Gtk.MESSAGE_ERROR, Gtk.BUTTONS_CLOSE, "There are no errors to save!")
                dialog.show_all()
                dialog.run()
                dialog.destroy()
                return

            # Create the file chooser dialog.
            fc = Gtk.FileChooserDialog("Save As...", None, Gtk.FILE_CHOOSER_ACTION_SAVE, (Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_SAVE, Gtk.RESPONSE_OK))
            # Set current directory.
            fc.set_current_folder(path)
            # Make up a file name that should be relatively unique.
            fc.set_current_name("atrinik_map_checker_" + datetime.now().strftime("%Y%m%d_%H-%M-%S") + ".txt")
            fc.set_default_response(Gtk.RESPONSE_OK)
            response = fc.run()

            if response == Gtk.RESPONSE_OK:
                # Now open the file name user chose for writing.
                fp = open(fc.get_filename(), "w")

                # Write the output to file. Note that we need to strip out Pango markup from 'severity'.
                for (map, severity, description) in l:
                    fp.write("{0}: {1}: {2}\n".format(map, re.sub(r"<[^>]*?>", "", severity), description))

                fp.close()

            fc.destroy()

        # Action for the scan button.
        def scan_button(self, b):
            # Clear out old errors.
            del errors_l[:]
            del beacons[:]
            # Re-scan.
            do_scan()
            # Draw the errors.
            self.draw_errors()

        # Check a directory of maps.
        def check_directory_button(self, b):
            # Create the file chooser dialog.
            fc = Gtk.FileChooserDialog("Select Directory...", None, Gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
            # Set current directory.
            fc.set_current_folder(path)
            fc.set_default_response(Gtk.RESPONSE_OK)
            response = fc.run()

            if response == Gtk.RESPONSE_OK:
                # Clear out old errors.
                del errors_l[:]
                del beacons[:]
                # Scan the directory.
                scan_dirs(fc.get_filename())
                # Draw the errors.
                self.draw_errors()

            fc.destroy()

        # Check a single map.
        def check_file_button(self, b):
            # Create the file chooser dialog.
            fc = Gtk.FileChooserDialog("Select File...", None, Gtk.FILE_CHOOSER_ACTION_OPEN, (Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
            # Set current directory.
            fc.set_current_folder(path)
            fc.set_default_response(Gtk.RESPONSE_OK)
            response = fc.run()

            if response == Gtk.RESPONSE_OK:
                # Clear out old errors.
                del errors_l[:]
                del beacons[:]
                # Check the map.
                check_file(fc.get_filename())
                # Draw errors.
                self.draw_errors()

            fc.destroy()

        # Reload archetypes.
        def reload_archetypes_button(self, b):
            del errors_archetypes[:]
            archetypes = parse_archetypes()
            self.draw_errors()

        # Reload artifacts.
        def reload_artifacts_button(self, b):
            del errors_artifacts[:]
            artifacts = parse_artifacts()
            self.draw_errors()

        # Reload regions.
        def reload_regions_button(self, b):
            del errors_regions[:]
            regions = parse_regions()
            self.draw_errors()

        # Common function to draw one error.
        # @param error Error to draw.
        # @param file File the error is in.
        def draw_one_error(self, error, file):
            # Check if we have suppressed this kind of errors.
            if config.getboolean("Suppress", errors.text[error[1]]):
                return

            pos = ""

            # We are on map, so add X/Y coordinates after the error description.
            if len(error) > 2 and error[2] != -1 and error[3] != -1:
                pos = " (" + str(error[2]) + ", " + str(error[3]) + ")"

            # Add the error.
            self.window.sm.get_model().append([file, "<span foreground=\"" + errors.pango_colors[error[1]] + "\">" + errors.text[error[1]] + "</span>", error[0] + pos])

        # Draw the errors.
        def draw_errors(self):
            # Clear out old drawn errors.
            self.window.sm.get_model().clear()

            # Draw map errors.
            for (map, map_errors) in errors_l:
                for error in map_errors:
                    self.draw_one_error(error, map)

            # Archetype errors.
            for error in errors_archetypes:
                self.draw_one_error(error, "Archetypes")

            # Artifact errors.
            for error in errors_artifacts:
                self.draw_one_error(error, "Artifacts")

            # Region errors.
            for error in errors_regions:
                self.draw_one_error(error, "Regions")

        # Try to find us an icon for the application.
        def find_icon(self):
            # Possible paths where our icon could be.
            paths = [
                "/usr/share/atrinik/bitmaps/icon.png",
                "../../client/bitmaps/icon.png",
            ]

            for path in paths:
                if os.path.exists(path):
                    return Gtk.gdk.pixbuf_new_from_file(path)

    try:
        # Initialize the GUI.
        gui = GUI()
        Gtk.main()
    finally:
        config_save()
# CLI.
else:
    # Common function to print one error on the CLI.
    # @param error Error to print.
    # @param map Map. If not None, we are drawing an error on map, otherwise a different error (artifacts,
    # archetypes, etc).
    def print_one_error(error, map):
        pos = ""

        # We are on map, so add X/Y coordinates before the error description.
        if map and error[2] != -1 and error[3] != -1:
            if text_only:
                pos = str(error[2]) + " " + str(error[3]) + " "
            else:
                pos = "(" + str(error[2]) + ", " + str(error[3]) + "): "

        if text_only:
            print(pos + "" + errors.text[error[1]] + " " + error[0])
        else:
            print("  " + errors.colors[error[1]] + errors.text[error[1]] + colors.end + ": " + pos + error[0])

    # Start the scan.
    do_scan()

    if not one_map:
        print(colors.bold + colors.underscore + "Scan complete. Results:\n" + colors.end + colors.end)

    # Print map errors.
    for (map, map_errors) in sorted(errors_l):
        if not one_map:
            print(colors.bold + map + ":" + colors.end)

        for error in map_errors:
            print_one_error(error, map)

    # Archetype errors.
    if errors_archetypes:
        print(colors.bold + "Archetypes:" + colors.end)

        for error in errors_archetypes:
            print_one_error(error, None)

    # Artifact errors.
    if errors_artifacts:
        print(colors.bold + "Artifacts:" + colors.end)

        for error in errors_artifacts:
            print_one_error(error, None)

    # Region errors.
    if errors_regions:
        print(colors.bold + "Regions:" + colors.end)

        for error in errors_regions:
            print_one_error(error, None)
