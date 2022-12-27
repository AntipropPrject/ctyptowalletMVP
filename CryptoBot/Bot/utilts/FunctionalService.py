from aiogram.types import Message

from Bot.handlers.service_handlers.loader_hand import loader
from Bot.utilts.fee_strategy import getFeeStrategy
from Bot.utilts.settings import DEBUG_MODE
from Dao.DB_Postgres.session import AlchemyMaster
from Dao.models.Address import Address
from Dao.models.Token import Token
from Dao.models.Transaction import Transaction
from Services.EntServices.AddressService import Maker_Factory
from Services.EntServices.TransactionService import TransactionService


async def perform_sending(address: Address,
                          amount: float,
                          token: Token,
                          to_address: str,
                          message: Message = None,
                          chait_id: int = None) -> Transaction or str:
    await loader(message, chait_id, 1, "Проверяем баланс...")

    service_fee = await getFeeStrategy(token)
    my_transaction: Transaction = await TransactionService.create_transaction(token=token,
                                                                              owner_address=address.address,
                                                                              foreign_address=to_address,
                                                                              amount=amount,
                                                                              fee=service_fee,
                                                                              transaction_type='sending')

    await loader(message, chait_id, 1, "Проверяем нагрузку сети...")
    await loader(message, chait_id, 1, "Вычисляем блоки...")
    await loader(message, chait_id, 2, "Запрос к блокчейну...")
    await loader(message, chait_id, 2, "Проверяем количество энергии.")
    await loader(message, chait_id, 2, "Проверяем количество энергии..")
    await loader(message, chait_id, 2, "Проверяем количество энергии...")
    await loader(message, chait_id, 3, "Проверяем количество энергии...")
    await loader(message, chait_id, 3, "Формируем транзакци...")
    await loader(message, chait_id, 3, "Отправляем запрос в блокчейн...")
    await loader(message, chait_id, 4, "Совершаем транзакцию...")
    transaction_maker = Maker_Factory.get_maker(token)
    transaction_dict = await transaction_maker.transfer(my_transaction)
    transaction_dict = transaction_dict.txn_resp
    try:
        network_fee = transaction_dict[
            "network_fee"]  # TODO Здесь важно получать в словаре network_fee: float  - сумма выплаченого газа в токене адреса
                            # TODO *Макс - я бы рад, но пока у нас нет такой возможности так как инфа о транзе не выдвет результат, я покапаюсь
    except:
        network_fee = 0

    print("TANSFER", transaction_dict)
    if transaction_dict.get("status") == "SUCCESS":
        if transaction_dict.get(
                "result") != "FAILED":
                                        # TODO *Макс - транзы не считаются завершенными пока блокчейн не скажет гуд, SUCCESS - успешнае оформление транзы и отправка в блокчейн

            my_transaction.tnx_id = transaction_dict.get("txn")
            if service_fee < 1:
                my_transaction.service_fee = network_fee * service_fee
            else:
                my_transaction.service_fee = service_fee

            my_transaction.status = transaction_dict.get("status")
            await loader(message, chait_id, 5, "Совершаем транзакцию...")
            session = await AlchemyMaster.create_session()
            await loader(message, chait_id, 5, "Завершаем транзакцию...")
            async with session() as session:
                local_object = await session.merge(my_transaction)
                session.add(local_object)
                await session.commit()
                await session.close()
                await loader(message, chait_id, 6, "Записываем данные в базу...")
                await loader(message, chait_id, 7, "Записываем данные в базу...")
                return my_transaction
        else:
            await message.answer("Ошибка транзакции")

    else:
        return "Недостаточно средств"


def debug_filter(token: Token):
    if not DEBUG_MODE == token.network.mainnet:
        return True
    else:
        return False
