#  Copyright 2020 Parakoopa
#
#  This file is part of SkyTemple.
#
#  SkyTemple is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SkyTemple is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SkyTemple.  If not, see <https://www.gnu.org/licenses/>.
import re
from abc import ABC, abstractmethod
from functools import partial
from itertools import zip_longest
from typing import TYPE_CHECKING, Optional, Dict

import cairo
from gi.repository import Gtk, GLib, GdkPixbuf

from skytemple.core.module_controller import AbstractController
from skytemple.core.string_provider import StringType
if TYPE_CHECKING:
    from skytemple.module.lists.module import ListsModule
ORANGE = 'orange'
ORANGE_RGB = (1, 0.65, 0)
PATTERN_MD_ENTRY = re.compile(r'.*\(\$(\d+)\).*')


class ListBaseController(AbstractController, ABC):
    def __init__(self, module: 'ListsModule', *args):
        self.module = module

        self.builder = None
        self._sprite_provider = self.module.project.get_sprite_provider()
        self._icon_pixbufs: Dict[any, GdkPixbuf.Pixbuf] = {}
        self._refresh_timer = None
        self._ent_names: Dict[int, str] = {}
        self._tree_iters_by_idx: Dict[int, Gtk.TreeIter] = {}
        self._tmp_path = None
        self._list_store: Optional[Gtk.ListStore] = None
        self._loading = False

    def load(self):
        self._loading = True

        self._init_monster_store()
        self.refresh_list()

        self.builder.connect_signals(self)
        self._loading = False

    def _init_monster_store(self):
        monster_md = self.module.get_monster_md()
        monster_store: Gtk.ListStore = self.builder.get_object('monster_store')
        for idx, entry in enumerate(monster_md.entries):
            if idx == 0:
                continue
            name = self.module.project.get_string_provider().get_value(StringType.POKEMON_NAMES, entry.md_index_base)
            self._ent_names[idx] = f'{name} ({entry.gender.name.capitalize()}) (${idx:04})'
            monster_store.append([self._ent_names[idx]])

    def on_draw_example_placeholder_draw(self, widget: Gtk.DrawingArea, ctx: cairo.Context):
        sprite, x, y, w, h = self._sprite_provider.get_actor_placeholder(
            9999, 0, lambda: GLib.idle_add(lambda: self.builder.get_object('draw_example_placeholder').queue_draw())
        )
        ctx.set_source_surface(sprite)
        ctx.get_source().set_filter(cairo.Filter.NEAREST)
        ctx.paint()
        if widget.get_size_request() != (w, h):
            widget.set_size_request(w, h)

    def on_completion_entities_match_selected(self, completion, model, tree_iter):
        pass

    def on_cr_entity_editing_started(self, renderer, editable, path):
        editable.set_completion(self.builder.get_object('completion_entities'))
        self._tmp_path = path

    @abstractmethod
    def refresh_list(self):
        pass

    @abstractmethod
    def get_tree(self):
        pass

    def can_be_placeholder(self):
        return False

    def _get_icon(self, entid, idx, force_placeholder=False):
        was_loading = self._loading
        if entid <= 0 or force_placeholder:
            sprite, x, y, w, h = self._sprite_provider.get_actor_placeholder(idx, 0,
                                                                             lambda: GLib.idle_add(
                                                                                 partial(self._reload_icon, 0, idx, was_loading)
                                                                             ))
            ctx = cairo.Context(sprite)
            ctx.set_source_rgb(*ORANGE_RGB)
            ctx.rectangle(0, 0, w, h)
            ctx.set_operator(cairo.OPERATOR_IN)
            ctx.fill()
            target = f'pl{idx}'

        else:
            sprite, x, y, w, h = self._sprite_provider.get_monster(entid, 0,
                                                                   lambda: GLib.idle_add(
                                                                       partial(self._reload_icon, entid, idx, was_loading)
                                                                   ))
            target = entid
        data = bytes(sprite.get_data())
        # this is painful.
        new_data = bytearray()
        for b, g, r, a in grouper(data, 4):
            new_data += bytes([r, g, b, a])
        self._icon_pixbufs[target] = GdkPixbuf.Pixbuf.new_from_data(
            new_data, GdkPixbuf.Colorspace.RGB, True, 8, w, h, sprite.get_stride()
        )
        return self._icon_pixbufs[target]

    def _reload_icon(self, entid, idx, was_loading):
        if not self._loading and not was_loading:
            row = self._list_store[self._tree_iters_by_idx[idx]]
            row[3] = self._get_icon(entid, idx, row[8] == ORANGE if self.can_be_placeholder() else False)
            return
        if self._refresh_timer is not None:
            GLib.source_remove(self._refresh_timer)
        self._refresh_timer = GLib.timeout_add_seconds(0.5, self._reload_icons_in_tree)

    def _reload_icons_in_tree(self):
        tree: Gtk.TreeView = self.get_tree()
        model: Gtk.ListStore = tree.get_model()
        self._loading = True
        for entry in model:
            # If the color is orange, this is a spcial actor and we render a placeholder instead.
            # TODO: it's a bit weird doing this over the color
            entry[3] = self._get_icon(entry[4], int(entry[0]), entry[8] == ORANGE if self.can_be_placeholder() else False)
        self._loading = False
        self._refresh_timer = None


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return ((bytes(bytearray(x))) for x in zip_longest(fillvalue=fillvalue, *args))