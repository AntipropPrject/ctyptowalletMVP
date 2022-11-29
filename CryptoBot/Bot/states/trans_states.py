from aiogram.fsm.state import StatesGroup, State

class TransactionStates(StatesGroup):
    main = State()


class Trs_transfer(StatesGroup):
    main = State()
    new_transfer = State()
    set_network = State()
    address = State()
    confirm_transfer = State()


class Trs_exchange(StatesGroup):
    main = State()

class Trs_withdrawal(StatesGroup):
    main = State()
