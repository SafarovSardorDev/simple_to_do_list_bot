from aiogram.dispatcher.filters.state import State, StatesGroup

class TaskState(StatesGroup):
    title = State()

