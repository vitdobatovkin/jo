from web3 import Web3
from utils import *
import time
import config as config
import config as settings
import random
from loguru import logger


class Wallet:
    def __init__(self,privatekey):
        self.web3 = Web3(Web3.HTTPProvider(settings.RPC))
        self.privatekey = privatekey
        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.web3.to_checksum_address(self.account.address)
        self.max_retries = 5



  
    def cheсk_gas_eth(self):
        try:
        
            while True:
                gas_res = (Web3.from_wei(self.web3.eth.gas_price, 'gwei'))
                if gas_res <= settings.MAX_GAS:
                    break
                else:
                    print(f"{round(gas_res,2)} GWEI сейчас / Жду газа {settings.MAX_GAS} GWEI",end="", flush=True)
                    time.sleep(10)  
                    print("\033[K", end="\r", flush=True)  
                    #print(f' gwei| Жду газ ниже...')
                    #time.sleep(120)
                    continue
        except:
            return 0

    def get_web3(self, chain_name: str):

        web3 = Web3(Web3.HTTPProvider(settings.RPC))
        return web3


    def sent_tx(self, chain_name: str, tx, tx_label, tx_raw=False, value=0,errors=True):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            if not tx_raw:
                if type(tx) != dict:
                    tx = tx.build_transaction({
                        'from': self.address,
                        'chainId': web3.eth.chain_id,
                        'nonce': web3.eth.get_transaction_count(self.address),
                        'value': value,
                        'maxPriorityFeePerGas': web3.eth.max_priority_fee, 
                        'maxFeePerGas': int(web3.eth.gas_price * 1.2),
                    })

            else:
                tx = tx
                tx["maxPriorityFeePerGas"]  =   self.web3.eth.max_priority_fee
                tx["maxFeePerGas"] = int(self.web3.eth.gas_price *1.5) 
                if errors:
                    tx['gas'] = int(web3.eth.estimate_gas(tx) *1.1)
                else:
                    tx['gas'] = random.randint(60000,90000)


            signed_tx = web3.eth.account.sign_transaction(tx, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'{config.CHAINS_DATA[chain_name]["explorer"]}{tx_hash}'
            logger.debug(f'[•] Web3 | {tx_label} tx sent: {tx_link}')

            status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=int(settings.TO_WAIT_TX * 60),poll_latency=5).status

            if status == 1:
                logger.info(f'[+] Web3 | {tx_label} tx confirmed\n')
                return tx_hash
            else:
                if errors:
                    raise ValueError(f'tx failed: {tx_link}')
                else:
                    return tx_hash


        except Exception as err:
            if 'already known' in str(err):
                try: raw_tx_hash
                except: raw_tx_hash = ''
                logger.warning(f'{tx_label} | Couldnt get tx hash, thinking tx is success ({raw_tx_hash})')
                time.sleep(15)

                return True

            try: encoded_tx = f'\nencoded tx: {tx._encode_transaction_data()}'
            except: encoded_tx = ''
            raise ValueError(f'tx failed error: {err}{encoded_tx}')

    def get_balance(self, chain_name: str, token_name=False, token_address=False, human=False):
        web3 = self.get_web3(chain_name=chain_name)
        if token_name: token_address = config.TOKEN_ADDRESSES[token_name]
        if token_address: contract = web3.eth.contract(address=web3.to_checksum_address(token_address),
                                     abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]')
        
        if token_name == False and token_address == False:
            check_adrs = self.web3.to_checksum_address(self.address)
            balance = web3.eth.get_balance(self.address)

            if not human: return balance
            return balance / 10 ** 18
        
        while True:
            try:
                if token_address: balance = contract.functions.balanceOf(self.address).call()
                else: balance = web3.eth.get_balance(self.address)

                decimals = contract.functions.decimals().call() if token_address else 18
                if not human: return balance
                return balance / 10 ** decimals
            except Exception as err:
                logger.warning(f'[•] Web3 | Get balance error: {err}')
                time.sleep(5)

   