from Bot.utilts.FunctionalService import debug_filter
from Bot.utilts.USDT_Calculator import USDT_Calculator
from Dao.DB_Redis import DataRedis
from Dao.models.Address import Address
from Services.EntServices.AddressService import AddressService
from Services.EntServices.OwnerService import OwnerService
from Services.EntServices.TokenService import TokenService


async def all_wallets_text(u_id: str):
    user_tokens = await OwnerService.get_tokens(u_id)
    text = ""
    if user_tokens:
        user_wallets = await OwnerService.get_wallets(u_id)

        sum = 'SUM'
        text = f'<b>Криптовалюты ≈ {sum} USDT</b>\n'
        text += "<code>——————————————————————</code>\n"
        fee = 0
        for blockchain in user_wallets:
            addressess = user_wallets[blockchain].addresses
            for address in addressess:
                adress_obj = addressess.get(address)
                balances = await AddressService.get_address_balances(address=address)
                for token in adress_obj.tokens:
                    if debug_filter(token):
                        balance = balances.get(token.token_name, 'Iternal Error!')
                        text += f"{token.token_name}: {balance}\n"
                    try:
                        fee += USDT_Calculator().calculate(adress_obj.get_address_freezed_fee(), token.token_name)
                    except:
                        fee += 0

        text += "<code>——————————————————————</code>\n"
        if fee:
            text += f'За пользование сервисом была заморожена комиссия: {fee} USDT\n' #TODO  Здесь сделать детализацию для каждого токена в сети
    else:
        text += '<i>▫️ Вы пока не отслеживаете ни один токен.</i>'
    return text


async def detail_view_text(user_id: int, token_name: str, token_network: str):
    u_id = await DataRedis.find_user(user_id)
    token_and_address = await TokenService.find_address_token(token_name=token_name,
                                                              token_network=token_network,
                                                              u_id=u_id)
    token = token_and_address.token
    address: Address = token_and_address.address

    balance = (await AddressService.get_address_balances(address=address.address, specific=[token]))[token.token_name]
    transactions = [str(address.transactions[transaction]) for transaction in address.transactions]

    text = f"<b>Токен: {token.token_name}\nСеть: {token.network}\nТекущий баланс: {balance}</b>\n\n"
    text += f"<b>Публичный адрес:</b> <code>{address.address}</code>\n"
    text += f"<i>- - Используйте его для получения транзакций - -</i>\n\n"
    text += f"<b>Список последних транзакций:</b>\n"
    if transactions:
        count = 0
        for trsc in transactions:
            if count < 3:
                text += f"<code>\n{trsc}\n</code>"
    else:
        text += f"<i>- - Список пока пуст - -</i>"
    return text, address.address
