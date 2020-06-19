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
from enum import Enum
from typing import TYPE_CHECKING, Type, List

import cairo
from gi.repository import Gtk, GLib

from skytemple.controller.main import MainController
from skytemple.core.module_controller import AbstractController
from skytemple.core.string_provider import StringType
from skytemple.module.portrait.portrait_provider import IMG_DIM
from skytemple_files.data.md.model import Gender, PokeType, MovementType, IQGroup, Ability, EvolutionMethod, \
    NUM_ENTITIES

if TYPE_CHECKING:
    from skytemple.module.monster.module import MonsterModule


class MonsterController(AbstractController):
    def __init__(self, module: 'MonsterModule', item_id: int):
        self.module = module
        self.item_id = item_id
        self.entry = self.module.get_entry(self.item_id)

        self.builder = None
        self._is_loading = False
        self._string_provider = module.project.get_string_provider()
        self._sprite_provider = module.project.get_sprite_provider()
        self._portrait_provider = module.project.get_module('portrait').get_portrait_provider()

    def get_view(self) -> Gtk.Widget:
        self.builder = self._get_builder(__file__, 'monster.glade')

        self._sprite_provider.reset()
        self._portrait_provider.reset()

        self._init_language_labels()
        self._init_entity_id()
        self._init_stores()
        self._init_sub_pages()

        self._is_loading = True
        self._init_values()
        self._is_loading = False

        self._update_pre_evo_label()
        self._update_base_form_label()

        self.builder.connect_signals(self)
        self.builder.get_object('draw_sprite').queue_draw()

        self.builder.get_object('settings_grid').check_resize()
        return self.builder.get_object('box_main')

    def on_draw_portrait_draw(self, widget: Gtk.DrawingArea, ctx: cairo.Context):
        scale = 2
        portrait = self._portrait_provider.get(self.entry.md_index - 1, 0,
                                               lambda: GLib.idle_add(widget.queue_draw), True)
        ctx.scale(scale, scale)
        ctx.set_source_surface(portrait)
        ctx.get_source().set_filter(cairo.Filter.NEAREST)
        ctx.paint()
        ctx.scale(1 / scale, 1 / scale)
        if widget.get_size_request() != (IMG_DIM * scale, IMG_DIM * scale):
            widget.set_size_request(IMG_DIM * scale, IMG_DIM * scale)

    def on_draw_sprite_draw(self, widget: Gtk.DrawingArea, ctx: cairo.Context):
        if self.entry.entid > 0:
            sprite, x, y, w, h = self._sprite_provider.get_monster(self.entry.md_index, 0,
                                                                   lambda: GLib.idle_add(widget.queue_draw))
        else:
            sprite, x, y, w, h = self._sprite_provider.get_error()
        ctx.set_source_surface(sprite)
        ctx.get_source().set_filter(cairo.Filter.NEAREST)
        ctx.paint()
        if widget.get_size_request() != (w, h):
            widget.set_size_request(w, h)

    def on_cb_type_primary_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_cb_type_secondary_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_entry_national_pokedex_number_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_cb_gender_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_entry_lang1_changed(self, w, *args):
        self.builder.get_object('label_id_name').set_text(f'${self.entry.md_index:04d}: {w.get_text()}')
        self._update_lang_from_entry(w, 0)
        self.module.refresh(self.item_id)
        self.mark_as_modified()

    def on_entry_lang2_changed(self, w, *args):
        self._update_lang_from_entry(w, 1)
        self.mark_as_modified()

    def on_entry_lang3_changed(self, w, *args):
        self._update_lang_from_entry(w, 2)
        self.mark_as_modified()

    def on_entry_lang4_changed(self, w, *args):
        self._update_lang_from_entry(w, 3)
        self.mark_as_modified()

    def on_entry_lang5_changed(self, w, *args):
        self._update_lang_from_entry(w, 4)
        self.mark_as_modified()

    def on_entry_body_size_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_cb_movement_type_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_cb_iq_group_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_cb_ability_primary_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_cb_ability_secondary_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_entry_exp_yield_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_recruit_rate1_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_recruit_rate2_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_base_hp_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_weight_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_base_atk_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_base_sp_atk_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_base_def_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_base_sp_def_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_size_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_evo_param1_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_evo_param2_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_pre_evo_index_changed(self, w, *args):
        self._update_from_entry(w)
        self._update_pre_evo_label()
        self.mark_as_modified()

    def on_cb_evo_method_changed(self, w, *args):
        self._update_from_cb(w)
        self.mark_as_modified()

    def on_btn_help_evo_params_clicked(self, w, *args):
        md = Gtk.MessageDialog(
            MainController.window(),
            Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK,
            f"Values depend on Evolution Type:\n"
            f"- None: n/a - n/a\n"
            f"- Level: Level required to evolve - Optional evolutionary item ID\n"
            f"- IQ: IQ required - Optional evolutionary item ID\n"
            f"- Items: Regular Item ID - Optional evolutionary item ID\n"
            f"- Unknown: ? - ?\n"
            f"- Link Cable: 0 - 1",
            title="Evolution Parameters"
        )
        md.run()
        md.destroy()

    def on_entry_exclusive_item1_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_exclusive_item2_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_exclusive_item3_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_exclusive_item4_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_bitflag1_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk31_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk1_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk17_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk18_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk19_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk21_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk20_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk27_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk29_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk28_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_unk30_changed(self, w, *args):
        self._update_from_entry(w)
        self.mark_as_modified()

    def on_entry_base_form_index_changed(self, w, *args):
        self._update_from_entry(w)
        self._update_base_form_label()
        self.mark_as_modified()

    def _init_language_labels(self):
        langs = self._string_provider.get_languages()
        for lang_id in range(0, 5):
            gui_id = lang_id + 1
            gui_label: Gtk.Label = self.builder.get_object(f'label_lang{gui_id}')
            gui_entry: Gtk.Entry = self.builder.get_object(f'entry_lang{gui_id}')
            if lang_id < len(langs):
                # We have this language
                gui_label.set_text(langs[lang_id].name + ':')
            else:
                # We don't.
                gui_label.set_text("")
                gui_entry.set_sensitive(False)

    def _init_entity_id(self):
        self.builder.get_object(f'label_base_id').set_text(f'#{self.entry.md_index_base:03}')
        self.builder.get_object(f'label_ent_id').set_text(f'{self.entry.entid:03}')
        name = self._string_provider.get_value(StringType.POKEMON_NAMES, self.entry.md_index_base)
        self.builder.get_object('label_id_name').set_text(f'${self.entry.md_index:04d}: {name}')

    def _init_stores(self):
        # Genders
        self._comboxbox_for_enum(['cb_gender'], Gender)
        # Types
        self._comboxbox_for_enum(['cb_type_primary', 'cb_type_secondary'], PokeType)
        # Movement Types
        self._comboxbox_for_enum(['cb_movement_type'], MovementType)
        # IQ Groups
        self._comboxbox_for_enum(['cb_iq_group'], IQGroup)
        # Abilities
        self._comboxbox_for_enum(['cb_ability_primary', 'cb_ability_secondary'], Ability)
        # Evolution Methods
        self._comboxbox_for_enum(['cb_evo_method'], EvolutionMethod)

    def _init_values(self):
        # Names
        langs = self._string_provider.get_languages()
        for lang_id in range(0, 5):
            gui_id = lang_id + 1
            gui_entry: Gtk.Entry = self.builder.get_object(f'entry_lang{gui_id}')
            if lang_id < len(langs):
                # We have this language
                gui_entry.set_text(self._string_provider.get_value(StringType.POKEMON_NAMES,
                                                                   self.entry.md_index_base,
                                                                   langs[lang_id]))

        # Stats
        self._set_entry('entry_unk31', self.entry.unk31)
        self._set_entry('entry_national_pokedex_number', self.entry.national_pokedex_number)
        self._set_entry('entry_unk1', self.entry.unk1)
        self._set_entry('entry_pre_evo_index', self.entry.pre_evo_index)
        self._set_entry('entry_base_form_index', self.entry.base_form_index)
        self._set_cb('cb_evo_method', self.entry.evo_method.value)
        self._set_entry('entry_evo_param1', self.entry.evo_param1)
        self._set_entry('entry_evo_param2', self.entry.evo_param2)
        self._set_cb('cb_gender', self.entry.gender.value)
        self._set_entry('entry_body_size', self.entry.body_size)
        self._set_cb('cb_type_primary', self.entry.type_primary.value)
        self._set_cb('cb_type_secondary', self.entry.type_secondary.value)
        self._set_cb('cb_movement_type', self.entry.movement_type.value)
        self._set_cb('cb_iq_group', self.entry.iq_group.value)
        self._set_cb('cb_ability_primary', self.entry.ability_primary.value)
        self._set_cb('cb_ability_secondary', self.entry.ability_secondary.value)
        self._set_entry('entry_bitflag1', self.entry.bitflag1)
        self._set_entry('entry_exp_yield', self.entry.exp_yield)
        self._set_entry('entry_recruit_rate1', self.entry.recruit_rate1)
        self._set_entry('entry_base_hp', self.entry.base_hp)
        self._set_entry('entry_recruit_rate2', self.entry.recruit_rate2)
        self._set_entry('entry_base_atk', self.entry.base_atk)
        self._set_entry('entry_base_sp_atk', self.entry.base_sp_atk)
        self._set_entry('entry_base_def', self.entry.base_def)
        self._set_entry('entry_base_sp_def', self.entry.base_sp_def)
        self._set_entry('entry_weight', self.entry.weight)
        self._set_entry('entry_size', self.entry.size)
        self._set_entry('entry_unk17', self.entry.unk17)
        self._set_entry('entry_unk18', self.entry.unk18)
        self._set_entry('entry_unk19', self.entry.unk19)
        self._set_entry('entry_unk20', self.entry.unk20)
        self._set_entry('entry_unk21', self.entry.unk21)
        self._set_entry('entry_exclusive_item1', self.entry.exclusive_item1)
        self._set_entry('entry_exclusive_item2', self.entry.exclusive_item2)
        self._set_entry('entry_exclusive_item3', self.entry.exclusive_item3)
        self._set_entry('entry_exclusive_item4', self.entry.exclusive_item4)
        self._set_entry('entry_unk27', self.entry.unk27)
        self._set_entry('entry_unk28', self.entry.unk28)
        self._set_entry('entry_unk29', self.entry.unk29)
        self._set_entry('entry_unk30', self.entry.unk30)

    def mark_as_modified(self):
        if not self._is_loading:
            self.module.mark_as_modified(self.item_id)

    def _comboxbox_for_enum(self, names: List[str], enum: Type[Enum]):
        store = Gtk.ListStore(int, str)  # id, name
        for entry in enum:
            store.append([entry.value, self._enum_entry_to_str(entry)])
        for name in names:
            self._fast_set_comboxbox_store(self.builder.get_object(name), store, 1)

    @staticmethod
    def _fast_set_comboxbox_store(cb: Gtk.ComboBox, store: Gtk.ListStore, col):
        cb.set_model(store)
        renderer_text = Gtk.CellRendererText()
        cb.pack_start(renderer_text, True)
        cb.add_attribute(renderer_text, "text", col)

    def _enum_entry_to_str(self, entry):
        if hasattr(entry, 'print_name'):
            return entry.print_name
        return entry.name.capitalize()

    def _set_entry(self, entry_name, text):
        self.builder.get_object(entry_name).set_text(str(text))

    def _set_cb(self, cb_name, value):
        cb: Gtk.ComboBox = self.builder.get_object(cb_name)
        l_iter: Gtk.TreeIter = cb.get_model().get_iter_first()
        while l_iter:
            row = cb.get_model()[l_iter]
            if row[0] == value:
                cb.set_active_iter(l_iter)
                return
            l_iter = cb.get_model().iter_next(l_iter)

    def _update_from_entry(self, w: Gtk.Entry):
        attr_name = Gtk.Buildable.get_name(w)[6:]
        try:
            val = int(w.get_text())
        except ValueError:
            return
        setattr(self.entry, attr_name, val)

    def _update_from_cb(self, w: Gtk.ComboBox):
        attr_name = Gtk.Buildable.get_name(w)[3:]
        val = w.get_model()[w.get_active_iter()][0]
        current_val = getattr(self.entry, attr_name)
        if isinstance(current_val, Enum):
            enum_class = current_val.__class__
            val = enum_class(val)
        setattr(self.entry, attr_name, val)

    def _update_lang_from_entry(self, w: Gtk.Entry, lang_index):
        lang = self._string_provider.get_languages()[lang_index]
        self._string_provider.get_model(lang).strings[
            self._string_provider.get_index(StringType.POKEMON_NAMES, self.entry.md_index_base)
        ] = w.get_text()

    def _init_sub_pages(self):
        notebook: Gtk.Notebook = self.builder.get_object('main_notebook')
        tab_label: Gtk.Label = Gtk.Label.new('Portraits')
        notebook.append_page(self.module.get_portrait_view(self.item_id), tab_label)

    def _update_base_form_label(self):
        label: Gtk.Label = self.builder.get_object('label_base_form_index')
        entry: Gtk.Entry = self.builder.get_object('entry_base_form_index')
        try:
            entry_id = int(entry.get_text())
            if entry_id > NUM_ENTITIES:
                raise ValueError()
            entry = self.module.monster_md[entry_id]
            name = self._string_provider.get_value(StringType.POKEMON_NAMES, entry.md_index_base)
            label.set_text(f'#{entry.md_index_base:03d}: {name}')
        except BaseException:
            label.set_text(f'??? Enter a valid Base ID (#)')

    def _update_pre_evo_label(self):
        label: Gtk.Label = self.builder.get_object('label_pre_evo_index')
        entry: Gtk.Entry = self.builder.get_object('entry_pre_evo_index')
        try:
            entry_id = int(entry.get_text())
            entry = self.module.monster_md[entry_id]
            name = self._string_provider.get_value(StringType.POKEMON_NAMES, entry.md_index_base)
            label.set_text(f'${entry.md_index:04d}: {name} ({entry.gender.name[0]})')
        except BaseException:
            label.set_text(f'??? Enter a valid Entry ID ($)')