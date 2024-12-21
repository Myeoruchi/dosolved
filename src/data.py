import asyncio
import aiofiles
import json
from pathlib import Path

DB_PATH = Path("./../db/user.json")
FILE_LOCK = asyncio.Lock()

async def get_accounts() -> dict:
    """계정 목록을 파일에서 읽어 반환하는 함수입니다.

    Returns:
        dict: 멤버 ID를 Key로 하는 dictionary.
    """

    if not DB_PATH.is_file():
        return {}
    
    try:
        async with FILE_LOCK:
            async with aiofiles.open(DB_PATH, 'r', encoding='utf8') as f:
                data = await f.read()
                return json.loads(data)
         
    except Exception as e:
        print("Error occurred in get_accounts: {e}")
        return {}
        
async def write_accounts(accounts: dict) -> None:
    """계정 목록을 파일에 작성하는 함수입니다.

    Args:
        accounts (dict): 파일에 작성할 계정 목록 dictionary.
    """
    
    try:
        async with FILE_LOCK:
            async with aiofiles.open(DB_PATH, 'w', encoding='utf8') as f:
                await f.write(json.dumps(accounts, indent=4, ensure_ascii=False))

    except Exception as e:
        print("Error occurred in write_accounts: {e}")