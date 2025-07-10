import json
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from uuid import uuid4
# from graph import Agent
from ..entities.users import User
from src.exceptions import UserNotFoundError
from langchain_core.messages import AIMessage, HumanMessage
import logging

class APIServices:

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.warning(f"User not found with ID: {user_id}")
            raise UserNotFoundError(user_id=user_id)
        logging.info(f"Successfully retrieved user with ID: {user_id}")
        return user

    @staticmethod
    def serialise_ai_message_chunck(chunck):
        if isinstance(chunck, AIMessage):
            return chunck.content
        else:
            raise TypeError(
                f'Object of type {type(chunck)} is not a correct fomat for serialisation.'
            )

    @staticmethod
    async def generate_chat_response(message: str, checkpoint_id: Optional[str] = None):
        from src.main import app
        is_new_conversation = checkpoint_id is None
        if is_new_conversation:
            checkpoint_id = str(uuid4())

            config = {
                "configurable":{
                    "thread_id": checkpoint_id,
                }
            }

            events = app.state.graph_app.astream_events({
                "messages": [HumanMessage(content=message)]
                }, config=config, version='v2')

            yield f'data: {{"type": "checkpoint", "checkpoint_id": "{checkpoint_id}"}}\n\n'
        else:
            config = {
                "configurable":{
                    "thread_id": checkpoint_id,
                }
            }

            events = app.state.graph_app.astream_events({
                "messages": [HumanMessage(content=message)]
                }, config=config, version='v2')

        async for event in events:
            event_type = event['event']

            if event_type == 'on_chat_model_stream':
                chuck_content = APIServices.serialise_ai_message_chunck(event['data']["chunk"])
                safe_content = chuck_content.replace("'", "\\'").replace("\n", "\\n")
                yield f'data: {{"type": "content", "content": "{safe_content}"}}\n\n'
            elif event_type == 'on_chat_model_end':
                tool_calls = event['data']['output'].tool_calls if hasattr(
                    event['data']['output'], 'tool_calls'
                ) else []
                all_tool_calls = [calls for calls in tool_calls]

                for each_Call in all_tool_calls:
                    if each_Call['name'] == 'search':
                        query = each_Call['args']['query']
                        
                    elif each_Call['name'] == 'get_current_date_time':
                        query = "get current date and time"

                    safe_query = query.replace("'", "\\'").replace("\n", "\\n")
                    yield f'data: {{"type": "tool_execution_call", "query": "{safe_query}"}}\n\n'
            elif event_type == 'on_tool_end':
                    if event['name'] == 'tavily_search':
                        output = event['data']['output']['results']
                        if isinstance(output, list):
                            urls = []
                            for items in output:
                                if isinstance(items, dict) and 'url' in items:
                                    urls.append(items['url'])
                            urls_json = json.dumps(urls)
                            yield f'data: {{"type": "tool_execution_response", "urls": {urls_json}}}\n\n'

                    elif event['name'] == 'get_current_date_time':
                        output = event['data']['output']
                        if isinstance(output, str):
                            safe_output = output.replace("'", "\\'").replace("\n", "\\n")
                            yield f'data: {{"type": "tool_execution_response", "current_date_time": "{safe_output}"}}\n\n'
            elif event_type == 'on_tool_start':
                pass

        yield 'data: {"type": "end"}\n\n' 