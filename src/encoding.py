from Crypto.Cipher import DES
from Crypto import Random
from base64 import b64encode, b64decode

from config import app_config
from profiling import profile, Scope

# generate new key:
# print(b64encode(Random.new().read(DES.block_size)).decode("utf-8"))


class Encoder():
    @profile(Scope.Core)
    def __init__(self):
        # we decode the key once per session
        self.decodedKey = b64decode(app_config['cryptokey'])

    @profile(Scope.Core)
    def encrypt(self, data):
        # could / should the iv be done once per session?
        iv = Random.new().read(DES.block_size)
        obj = DES.new(self.decodedKey, DES.MODE_OFB, iv)
        encrypted = iv + obj.encrypt(data)
        return b64encode(encrypted).decode("utf-8")

    @profile(Scope.Core)
    def decrypt(self, data):
        decoded_data = b64decode(data)
        obj = DES.new(self.decodedKey, DES.MODE_OFB, decoded_data[:DES.block_size])
        return obj.decrypt(decoded_data[DES.block_size:]).decode("utf-8")


encoder = Encoder()
