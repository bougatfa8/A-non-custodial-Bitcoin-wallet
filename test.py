from bitcoinlib.wallets import Wallet
from bitcoinlib.keys import HDKey

k1 = HDKey.from_passphrase('escape summer skill stem family mandate cannon female pipe trouble endorse comic')
w = Wallet.create(name='peeps', keys=k1)
w.info()

