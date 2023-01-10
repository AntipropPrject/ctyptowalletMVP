from pydantic import BaseModel


class ComissionStrategy(BaseModel):
    gas_price: int  # wei
    gas_amount: int
    comission: int  # wei
