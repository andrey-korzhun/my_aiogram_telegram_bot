import os
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI


client = AsyncOpenAI(api_key=os.getenv('AI_TOKEN'))


async def gpt4(question):
    response = await client.chat.completions.create(
        messages=[{"role": "user",
               "content": str(question)}],
        model="gpt-4o"
    )
    return response
