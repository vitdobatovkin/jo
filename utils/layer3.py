import asyncio
from eth_account.messages import encode_defunct
from config import *
from curl_cffi.requests import AsyncSession
from utils.wallet import *
from fake_useragent import UserAgent
from hexbytes import HexBytes
from capmonster_python import RecaptchaV2Task


class Layer3(Wallet):
    def __init__(self,wallet: Wallet,to_address,PROXY):
        super().__init__(privatekey=wallet.privatekey)
        self.proxy = {'http': PROXY, 'https': PROXY}
        self.max_retries = 2
        self.to_address = to_address
        self.headers  = {
                'accept': '*/*',
                'accept-language': 'et',
                'content-type': 'application/json',
                'origin': 'https://claim.layer3foundation.org',
                'referer': 'https://claim.layer3foundation.org/',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'user-agent': UserAgent().chrome,
                'x-api-key': 'QuNx0GFARi2eDffPZGxrg3GqCKt6nmsp2AObymMJ',
            }



    async def send_requst(self,method,url,headers,params = None,json_data = None, cookies = None,retry=0):
        try:
            async with AsyncSession() as session:
                if method == "GET":
                    response = await session.get(url=url,impersonate="chrome120", proxies=self.proxy,params=params,headers=headers,cookies=cookies)
                    if response.status_code in [200, 201]:
                        return response
                if method == "POST":
                    response = await session.post(url=url,headers=headers, params=params, json=json_data,proxies=self.proxy,cookies=cookies)
                    if response.status_code in [200, 201]:
                        self.cookies = response.cookies
                        return response.json()
                await asyncio.sleep(1)
                raise ValueError(f'Ошибка при отправке запроса {url}: {response.text}')
                       
                

        except Exception as e:
            logger.error(f'{self.address} | Ошибка {e}')
            if retry<self.max_retries:
                await asyncio.sleep(10)
                return await self.send_requst(method,url,headers,params = params,json_data = json_data, cookies = cookies, retry=retry+1)
            else:
                return 
    
    async def eligible(self,retry=0):
        try:
            capmonster = RecaptchaV2Task(CAPMONSTER_API)
            task_id = capmonster.create_task("https://api.layer3foundation.org", "6LcuLx0qAAAAACchAz_SNRPMRC3dv_Pr8paxTYRP")
            result = capmonster.join_task_result(task_id)['gRecaptchaResponse']


            #Login
         
            params = {
                'address': self.address,
                'recaptchaToken': result,
            }
            eligible = await self.send_requst('GET',f'https://api.layer3foundation.org/eligibility',self.headers,params,None)

            if eligible.json()['allocation'] == '0':
                return False
            else:
                return eligible.json()['allocation']
            



        except Exception as e:
            logger.error(f'{self.address} | Ошибка {e}')
            if retry<self.max_retries:
                await asyncio.sleep(10)
                return await self.eligible(retry=retry+1)
            else:
                return 

    async def get_proof(self,retry=0):
        try:
            capmonster = RecaptchaV2Task(CAPMONSTER_API)
            task_id = capmonster.create_task("https://api.layer3foundation.org", "6LcuLx0qAAAAACchAz_SNRPMRC3dv_Pr8paxTYRP")
            result = capmonster.join_task_result(task_id)['gRecaptchaResponse']


            #Login
         
            json_data = {
                'address': self.address,
                'recaptchaToken': result,
                'tosHash': '554fdddd6669d69687673a64e1f0478d4cc16153dad4a0b1abcb8ca79faf7608',
            }
            proof = await self.send_requst('POST',f'https://api.layer3foundation.org/claim',self.headers,None,json_data)

            return proof



        except Exception as e:
            logger.error(f'{self.address} | Ошибка {e}')
            if retry<self.max_retries:
                await asyncio.sleep(10)
                return await self.get_proof(retry=retry+1)
            else:
                return 
    
    async def claim_drop(self,retry=0):
        try:
            proof_req = await self.get_proof()

            amount = int(proof_req['allocation'])
            proof = proof_req['proof']
            signature = proof_req['signature']

            contract = self.web3.eth.contract(
                    address=self.web3.to_checksum_address('0x6571e50e8769d236414f3fB9e9B1D05341f6f79a'),
                    abi='[{"inputs":[{"internalType":"bytes32","name":"_merkleRoot","type":"bytes32"},{"internalType":"address","name":"_signer","type":"address"},{"internalType":"contract IERC20","name":"_token","type":"address"},{"internalType":"address","name":"_staking","type":"address"},{"internalType":"address","name":"_owner","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"target","type":"address"}],"name":"AddressEmptyCode","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"AddressInsufficientBalance","type":"error"},{"inputs":[],"name":"AlreadyClaimed","type":"error"},{"inputs":[],"name":"ECDSAInvalidSignature","type":"error"},{"inputs":[{"internalType":"uint256","name":"length","type":"uint256"}],"name":"ECDSAInvalidSignatureLength","type":"error"},{"inputs":[{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"ECDSAInvalidSignatureS","type":"error"},{"inputs":[],"name":"FailedInnerCall","type":"error"},{"inputs":[],"name":"InvalidNewSigner","type":"error"},{"inputs":[],"name":"InvalidProof","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[],"name":"InvalidToken","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"SafeERC20FailedOperation","type":"error"},{"inputs":[],"name":"ZeroAmount","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_account","type":"address"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"Claimed","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_account","type":"address"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_lockupPeriod","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"_timestamp","type":"uint256"}],"name":"ClaimedAndStaked","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_owner","type":"address"},{"indexed":true,"internalType":"contract IERC20","name":"_token","type":"address"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"DustCollected","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"EmergencyWithdrawn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferStarted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_oldSigner","type":"address"},{"indexed":true,"internalType":"address","name":"_newSigner","type":"address"}],"name":"SignerUpdated","type":"event"},{"inputs":[],"name":"MERKLE_ROOT","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"STAKING","outputs":[{"internalType":"contract IStaking","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"TOKEN","outputs":[{"internalType":"contract IERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"acceptOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32[]","name":"merkleProof","type":"bytes32[]"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"uint32","name":"lockupPeriod","type":"uint32"}],"name":"claimAndStake","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IERC20","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"collectDust","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"emergencyWithdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"hasClaimed","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pendingOwner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"signer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newSigner","type":"address"}],"name":"updateSigner","outputs":[],"stateMutability":"nonpayable","type":"function"}]',
            )



            tx_params = contract.functions.claim(
                    amount,
                    proof,
                    signature
            )

            self.cheсk_gas_eth()

            tx_hash = self.sent_tx(chain_name='eth', tx=tx_params, tx_label=f'Claim {amount/10**18} $L3', tx_raw=False ,value=0)

            if tx_hash:
                logger.success(f'{self.address} | Успешно заклеймили ')

                await asyncio.sleep(random.randint(SLEEP_AFTER_TX[0], SLEEP_AFTER_TX[1]))

                return True
            else:
                logger.error(f'{self.address} | Ошибка клейма ')
                return False




        except Exception as e:
            logger.error(f'{self.address} | Ошибка {e}')
            if retry<self.max_retries:
                await asyncio.sleep(10)
                return await self.claim_drop(retry=retry+1)
            else:
                return 
            

    async def transfer(self,retry=0):
        try:

            amount = self.get_balance('eth',False,'0x88909d489678dd17aa6d9609f89b0419bf78fd9a')




            contract = self.web3.eth.contract(
                    address=self.web3.to_checksum_address('0x88909d489678dd17aa6d9609f89b0419bf78fd9a'),
                    abi='[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"target","type":"address"}],"name":"AddressEmptyCode","type":"error"},{"inputs":[],"name":"ECDSAInvalidSignature","type":"error"},{"inputs":[{"internalType":"uint256","name":"length","type":"uint256"}],"name":"ECDSAInvalidSignatureLength","type":"error"},{"inputs":[{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"ECDSAInvalidSignatureS","type":"error"},{"inputs":[{"internalType":"address","name":"implementation","type":"address"}],"name":"ERC1967InvalidImplementation","type":"error"},{"inputs":[],"name":"ERC1967NonPayable","type":"error"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"allowance","type":"uint256"},{"internalType":"uint256","name":"needed","type":"uint256"}],"name":"ERC20InsufficientAllowance","type":"error"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"uint256","name":"balance","type":"uint256"},{"internalType":"uint256","name":"needed","type":"uint256"}],"name":"ERC20InsufficientBalance","type":"error"},{"inputs":[{"internalType":"address","name":"approver","type":"address"}],"name":"ERC20InvalidApprover","type":"error"},{"inputs":[{"internalType":"address","name":"receiver","type":"address"}],"name":"ERC20InvalidReceiver","type":"error"},{"inputs":[{"internalType":"address","name":"sender","type":"address"}],"name":"ERC20InvalidSender","type":"error"},{"inputs":[{"internalType":"address","name":"spender","type":"address"}],"name":"ERC20InvalidSpender","type":"error"},{"inputs":[{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"ERC2612ExpiredSignature","type":"error"},{"inputs":[{"internalType":"address","name":"signer","type":"address"},{"internalType":"address","name":"owner","type":"address"}],"name":"ERC2612InvalidSigner","type":"error"},{"inputs":[],"name":"FailedInnerCall","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"currentNonce","type":"uint256"}],"name":"InvalidAccountNonce","type":"error"},{"inputs":[],"name":"InvalidInitialization","type":"error"},{"inputs":[],"name":"NotInitializing","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},{"inputs":[],"name":"UUPSUnauthorizedCallContext","type":"error"},{"inputs":[{"internalType":"bytes32","name":"slot","type":"bytes32"}],"name":"UUPSUnsupportedProxiableUUID","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[],"name":"EIP712DomainChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint64","name":"version","type":"uint64"}],"name":"Initialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferStarted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"implementation","type":"address"}],"name":"Upgraded","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"UPGRADE_INTERFACE_VERSION","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"acceptOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"burnFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"eip712Domain","outputs":[{"internalType":"bytes1","name":"fields","type":"bytes1"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"version","type":"string"},{"internalType":"uint256","name":"chainId","type":"uint256"},{"internalType":"address","name":"verifyingContract","type":"address"},{"internalType":"bytes32","name":"salt","type":"bytes32"},{"internalType":"uint256[]","name":"extensions","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"foundation","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pendingOwner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"proxiableUUID","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newImplementation","type":"address"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"upgradeToAndCall","outputs":[],"stateMutability":"payable","type":"function"}]',
            )

            if amount > 10:

                tx_params = contract.functions.transfer(
                        self.web3.to_checksum_address(self.to_address),
                        amount
                )

                
                self.cheсk_gas_eth()


                tx_hash = self.sent_tx(chain_name='eth', tx=tx_params, tx_label=f'Transfer {amount/10**18} $L3 to {self.to_address}', tx_raw=False ,value=0)

                if tx_hash:
                    logger.success(f'{self.address} | Успешно Отправил ')
                    await asyncio.sleep(random.randint(SLEEP_AFTER_TX[0], SLEEP_AFTER_TX[1]))
                    return True
                else:
                    logger.error(f'{self.address} | Ошибка отправки ')
                    return False
            else:
                logger.error(f'{self.address} | Нет токена для отправки ')
                return False




        except Exception as e:
            logger.error(f'{self.address} | Ошибка {e}')
            if retry<self.max_retries:
                await asyncio.sleep(10)
                return await self.transfer(retry=retry+1)
            else:
                return 
            

    