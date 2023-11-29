import re
from typing import Any, AsyncGenerator, Union, Dict, List
from llm.tools import cognitive_search_tool
from utils import nonewlines, build_filters, MessageBuilder
from config import logger, az, gpt
from azure.search.documents.models import VectorizedQuery

SYSTEM = "system"
USER = "user"
ASSISTANT = "assistant"
NO_RESPONSE = "0"

system_message_chat_conversation = """Assistant helps the PedanticGeek employees with their questions about company documents. Be brief in your answers.
Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
For tabular information return it as an html table. Do not return markdown format. If the question is not in English, answer in the language used in the question.
Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. Use square brackets to reference the source, for example [info1.txt]. Don't combine sources, list each source separately, for example [info1.txt][info2.pdf].
{follow_up_questions_prompt}
"""

follow_up_questions_prompt_content = """Generate 3 very brief follow-up questions that the user would likely ask next.
Enclose the follow-up questions in double angle brackets. Example:
<<What are the company policies?>>
<<How many incidents were recorded in September this year?>>
<<What are our current partnerships?>>
Do no repeat questions that have already been asked.
Make sure the last question ends with ">>"."""

query_prompt_template = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in the documentation knowledge base.
You have access to Azure Cognitive Search index with 100's of documents.
Generate a search query based on the conversation and the new question.
Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
Do not include any text inside [] or <<>> in the search query terms.
Do not include any special characters like '+'.
If the question is not in English, translate the question to English before generating the search query.
If you cannot generate a search query, return just the number 0.
"""

query_prompt_few_shots = [
    {"role": USER, "content": "What were the highest sales this year?"},
    {"role": ASSISTANT, "content": "Show all sales figures for this year"},
    {"role": USER, "content": "What are the most common Health and Safety incidents?"},
    {"role": ASSISTANT, "content": "Show all Health and Safety incidents"},
]


class Chat:
    """
    Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
    top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion
    (answer) with that prompt.
    """

    def __init__(self) -> None:
        self.retrieval_mode = "hybrid"
        self.use_semantic_captions = True
        self.top = 5
        self.max_history_tokens = 32000

    async def search_sources(self, query_text: str, filters: str):
        logger.info(f"Searching for: {query_text}")
        logger.info(f"Cognitive search filters: {filters}")
        embedding = gpt.client.embeddings.create(
            model=gpt.EMB_MODEL_NAME, input=query_text
        )
        vector_query = VectorizedQuery(
            vector=embedding.data[0].embedding,
            k_nearest_neighbors=3,
            fields="embedding",
        )
        r = await az.search_client.search(
            query_text,
            filter=filters,
            query_type="semantic",
            semantic_configuration_name="semantic-config",
            top=self.top,
            query_caption="extractive",
            vector_queries=[vector_query],
        )
        if self.use_semantic_captions:
            results = [
                doc["sourcepage"]
                + ": "
                + nonewlines(" . ".join([c.text for c in doc["@search.captions"]]))
                async for doc in r
            ]
        else:
            results = [
                doc["sourcepage"] + ": " + nonewlines(doc["content"]) async for doc in r
            ]

        logger.info(f"Search results: {results}")
        return results

    async def run_until_final_call(
        self,
        history: List[dict[str, str]],
        overrides: Dict[str, Any],
        should_stream: bool = False,
    ) -> tuple:
        filters = build_filters(overrides)

        original_user_query = history[-1]["content"]
        user_query_request = "Generate search query for: " + original_user_query

        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
        messages = self.get_messages_from_history(
            system_prompt=query_prompt_template,
            model_id=gpt.CHATGPT_MODEL,
            history=history,
            user_content=user_query_request,
            few_shots=query_prompt_few_shots,
        )

        chat_completion = gpt.client.chat.completions.create(
            model=gpt.CHATGPT_MODEL,
            messages=messages,
            temperature=0.0,
            n=1,
            tools=[cognitive_search_tool],
            tool_choice="auto",
        )

        query_text = self.get_search_query(chat_completion, original_user_query)
        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query
        results = await self.search_sources(query_text, filters)
        content = "\n".join(results)
        # STEP 3: Generate a contextual and content specific answer using the search results and chat history
        system_message = system_message_chat_conversation.format(
            follow_up_questions_prompt=follow_up_questions_prompt_content,
        )

        messages = self.get_messages_from_history(
            system_prompt=system_message,
            model_id=gpt.CHATGPT_MODEL,
            history=history,
            user_content=original_user_query + "\n\nSources:\n" + content,
        )
        msg_to_display = "\n\n".join([str(message) for message in messages])

        extra_info = {
            "data_points": results,
            "thoughts": f"Searched for:<br>{query_text}<br><br>Conversations:<br>"
            + msg_to_display.replace("\n", "<br>"),
        }

        chat_coroutine = gpt.client.chat.completions.create(
            model=gpt.CHATGPT_MODEL,
            messages=messages,
            temperature=0.7,
            n=1,
            stream=should_stream,
        )
        return (extra_info, chat_coroutine)

    async def run_with_streaming(
        self,
        history: List[Dict[str, str]],
        overrides: Dict[str, Any],
        session_state: Any = None,
    ) -> AsyncGenerator[Dict, None]:
        extra_info, chat_coroutine = await self.run_until_final_call(
            history, overrides, should_stream=True
        )
        yield {
            "choices": [
                {
                    "delta": {"role": ASSISTANT},
                    "context": extra_info,
                    "session_state": session_state,
                    "finish_reason": None,
                    "index": 0,
                }
            ],
            "object": "chat.completion.chunk",
        }

        followup_questions_started = False
        followup_content = ""
        for event in chat_coroutine:
            if event.choices:
                # if event contains << and not >>, it is start of follow-up question, truncate
                content = event.choices[0].delta.content or ""
                if overrides.get("suggest_followup_questions") and "<<" in content:
                    followup_questions_started = True
                    earlier_content = content[: content.index("<<")]
                    if earlier_content:
                        event.choices[0].delta.content = earlier_content
                        yield event
                    followup_content += content[content.index("<<") :]
                elif followup_questions_started:
                    followup_content += content
                else:
                    yield event
        if followup_content:
            _, followup_questions = self.extract_followup_questions(followup_content)
            yield {
                "choices": [
                    {
                        "delta": {"role": ASSISTANT},
                        "context": {"followup_questions": followup_questions},
                        "finish_reason": None,
                        "index": 0,
                    }
                ],
                "object": "chat.completion.chunk",
            }

    async def run(
        self,
        messages: List[Dict],
        session_state: Any = None,
        context: Dict[str, Any] = {},
    ) -> AsyncGenerator[Dict[str, Any], None]:
        return self.run_with_streaming(
            history=messages,
            overrides=context.get("overrides", {}),
            session_state=session_state,
        )

    def get_messages_from_history(
        self,
        system_prompt: str,
        model_id: str,
        history: List[Dict[str, str]],
        user_content: str,
        few_shots=[],
    ) -> List:
        message_builder = MessageBuilder(system_prompt, model_id)

        # Add examples to show the chat what responses we want. It will try to mimic any responses and make sure they match the rules laid out in the system message.
        for shot in reversed(few_shots):
            message_builder.insert_message(shot.get("role"), shot.get("content"))

        append_index = len(few_shots) + 1

        message_builder.insert_message(USER, user_content, index=append_index)
        total_token_count = message_builder.count_tokens_for_message(
            message_builder.messages[-1]
        )

        newest_to_oldest = list(reversed(history[:-1]))
        for message in newest_to_oldest:
            potential_message_count = message_builder.count_tokens_for_message(message)
            if (total_token_count + potential_message_count) > self.max_history_tokens:
                logger.debug(
                    f"Reached max tokens of {self.max_history_tokens}, history will be truncated"
                )
                break
            message_builder.insert_message(
                message["role"], message["content"], index=append_index
            )
            total_token_count += potential_message_count
        return message_builder.messages

    def get_search_query(self, chat_completion: dict[str, Any], user_query: str):
        response_message = chat_completion.choices[0].message
        if function_call := response_message.function_call:
            if function_call.name == "search_sources":
                arg = eval(function_call.arguments)
                search_query = arg.get("search_query", NO_RESPONSE)
                if search_query != NO_RESPONSE:
                    return search_query
        elif query_text := response_message.content:
            if query_text.strip() != NO_RESPONSE:
                return query_text
        return user_query

    def extract_followup_questions(self, content: str):
        return content.split("<<")[0], re.findall(r"<<([^>>]+)>>", content)
