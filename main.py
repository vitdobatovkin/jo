
from utils.wallet import *
from utils.layer3 import Layer3
import asyncio
from config import SLEEP_AFTER_ACCOUNT
import os
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())






async def claim_and_transfer(layer3, semaphore):
    async with semaphore:


        eligible = await layer3.eligible()

        if eligible:
            logger.info(f'{layer3.address} | Доступно для клейма {int(eligible) / 10**18} $L3')

            claim_token = await layer3.claim_drop()
            
            transfer = await layer3.transfer()


            await asyncio.sleep(random.randint(SLEEP_AFTER_ACCOUNT[0], SLEEP_AFTER_ACCOUNT[1]))
        else:
            logger.info(f'{layer3.address} | Not eligible')

        

        
        print()


async def execute_task(line, semaphore, task_func):
    wallet = Wallet(line.split(';')[0])
    layer3 = Layer3(wallet,line.split(';')[1],line.split(';')[2])    
    await task_func(layer3, semaphore)

async def main(task_func):
    with open('wallets.txt', 'r') as file:
        lines = [line.strip() for line in file.readlines()]

    random.shuffle(lines)
    semaphore = asyncio.Semaphore(1)
    tasks = [execute_task(line, semaphore, task_func) for line in lines]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("Выберите задачу:")
    print("1: Заклеймить и отправить")
    choice = input("Введите число 1: ")

    task_dict = {
        '1': claim_and_transfer,
    }

    task_func = task_dict.get(choice)
    if task_func:
        asyncio.run(main(task_func))
    else:
        print("Неверный выбор. Пожалуйста, введите 1, 2 или 3.")