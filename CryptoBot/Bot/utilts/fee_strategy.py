from Dao.models.Owner import Owner
from Dao.models.Token import Token


async def getFeeStrategy(token: Token, owner: Owner = None) -> float: #TODO ВНИМАНИЕ ЭТО ХАРдкод надо придумать адекватную систему с динамической выработкой фии с индивидуальными планами для овнеров
    # fee_strategy_plan = owner.fee_strategy_plan # TODO для випов свой фи стретеджи и для каждого токена
    if token.token_name == "USDT":
        if token.algorithm.name == "ERC-20":
            return 11.0
        if token.algorithm.name == "TRC-20":
            return 2.0
        else:
            return 0.0
    else:
        return 0
        # Todo для родных токенов это доля от network_fee


