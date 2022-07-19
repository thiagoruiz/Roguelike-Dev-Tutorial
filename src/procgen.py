from __future__ import annotations

import random

from typing import Tuple, Iterator, List, TYPE_CHECKING

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from entity import Entity


class RectangularRoom:
    def __init__(self, top_left_x: int, top_left_y: int, width: int, height: int):
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.x = top_left_x + width
        self.y = top_left_y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.top_left_x + self.x) / 2)
        center_y = int((self.top_left_y + self.y) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.top_left_x + 1, self.x), slice(self.top_left_y + 1, self.y)

    def intersects(self, other: RectangularRoom):
        """Return True if this room overlaps with anotehr RectangularRoom."""
        return (
            self.top_left_x <= other.x
            and self.x >= other.top_left_x
            and self.top_left_y <= other.y
            and self.y >= other.top_left_y
        )


def place_entities(
        room: RectangularRoom, dungeon: GameMap, maximun_monsters: int,
) -> None:
    number_of_monsters = random.randint(0, maximun_monsters)

    for i in range(number_of_monsters):
        x = random.randint(room.top_left_x + 1, room.x - 1)
        y = random.randint(room.top_left_y + 1, room.y - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                entity_factories.troll.spawn(dungeon, x, y)


def tunnel_between(
        start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        max_monsters_per_room: int,
        player: Entity,
) -> GameMap:
    """Generate a new dungeon map."""
    dungeon = GameMap(map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # RectangularRoom class makes rectangles easier to work with
        new_room = RectangularRoom(top_left_x=x, top_left_y=y, width=room_width, height=room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.x, player.y = new_room.center
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x,y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        place_entities(new_room, dungeon, max_monsters_per_room)

        # Finally, append the new room to the list.
        rooms.append(new_room)

    return dungeon
