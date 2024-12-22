from aiohttp import ClientSession

async def get_streak(session: ClientSession, account: str) -> dict | str:
    """API 요청을 통해 streak 정보를 반환하는 함수입니다.

    Args:
        session (ClientSession): API 호출에 사용할 세션.
        account (str): API 호출에 사용할 계정.

    Returns:
        dict | str: streak 정보가 dictionary로 반환되나, 호출 실패에는 에러 메세지가 반환됨.
    """

    try:
        response = session.get(f"https://solved.ac/api/v3/user/grass?handle={account}&topic=default")
        if response.status == 200:
            return await response.json()
        elif response.status == 404:
            return "NOT_EXIST"
        return "ERROR"
    
    except Exception as e:
        print(f"Error occured in get_streak: {e}")
        return "ERROR"
        
async def get_user(session: ClientSession, account: str) -> dict | str:
    """API 요청을 통해 user 정보를 반환하는 함수입니다.

    Args:
        session (ClientSession): API 호출에 사용할 세션.
        account (str): API 호출에 사용할 계정.

    Returns:
        dict | str: user 정보가 dictionary로 반환되나, 호출 실패에는 에러 메세지가 반환됨.
    """

    try:
        response = session.get(f"https://solved.ac/api/v3/user/show?handle={account}")
        if response.status == 200:
            return await response.json()
        elif response.status == 404:
            return "NOT_EXIST"
        return "ERROR"
    
    except Exception as e:
        print(f"Error occured in get_streak: {e}")
        return "ERROR"
    
async def get_background(session: ClientSession, id: str) -> dict | str:
    """API 요청을 통해 background 정보를 반환하는 함수입니다.

    Args:
        session (ClientSession): API 호출에 사용할 세션.
        id (str): API 호출에 사용할 background id.

    Returns:
        dict | str: background 정보가 dictionary로 반환되나, 호출 실패에는 에러 메세지가 반환됨.
    """

    try:
        response = session.get(f"https://solved.ac/api/v3/background/show?backgroundId={id}")
        if response.status == 200:
            return await response.json()
        elif response.status == 404:
            return "NOT_EXIST"
        return "ERROR"
    
    except Exception as e:
        print(f"Error occured in get_streak: {e}")
        return "ERROR"