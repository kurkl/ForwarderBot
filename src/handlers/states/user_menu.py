from aiogram.dispatcher.fsm.state import State, StatesGroup


class UserMenuNavState(StatesGroup):
    current_position = State()
