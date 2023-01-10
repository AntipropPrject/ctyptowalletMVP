from aiogram.fsm.state import StatesGroup, State


class WalletStates(StatesGroup):
    inspect_address = State()
    rename_wallet = State()
    qr = State()
    transaction_history_send = State()
    transaction_history_start = State()
    send_start = State()
    replenish_network = State()
    replenish_token = State()
    main = State()
    replenish = State()
    choose_address = State()
    add_token = State()
    delete_token = State()
    inspect_token = State()
    choose_currency = State()
    create_wallet = State()
    use_wallet = State()


class WalletSendMoney(StatesGroup):
    send_money_start = State()
    send_money_where = State()
    send_money_how_many = State()
    send_money_confirm = State()
