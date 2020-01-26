"""Module to load a module view and controller"""
from typing import TYPE_CHECKING

from gi.repository.Gtk import Widget

from skytemple.core.module_controller import AbstractController
from skytemple.core.task import AsyncTaskRunner
from skytemple.core.ui_signals import SIGNAL_VIEW_LOADED_ERROR, SIGNAL_VIEW_LOADED

if TYPE_CHECKING:
    from skytemple.core.abstract_module import AbstractModule


async def load_controller(module: 'AbstractModule', controller_class, item_id: int, go=None):
    # TODO
    try:
        controller: AbstractController = controller_class(module, item_id)
        AsyncTaskRunner.emit(go, SIGNAL_VIEW_LOADED, module, controller, item_id)
    except Exception as err:
        if go:
            AsyncTaskRunner.emit(go, SIGNAL_VIEW_LOADED_ERROR, err)
