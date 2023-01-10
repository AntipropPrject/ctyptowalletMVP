import io

import qrcode
import segno


async def qr_code(wallet):
    qr_img = qrcode.make(str(wallet))
    bio = io.BytesIO()
    qr_img.save(bio, 'PNG')
    bio.seek(0)
    return bio.read()


async def pretty_qr_code(address_str: str):
    qrcod = segno.make(address_str, error='h')
    bio = io.BytesIO()
    qrcod.to_artistic(background='Bot/assets/crypt.png', target=bio, scale=6, kind='png')
    bio.seek(0)
    return bio.read()
