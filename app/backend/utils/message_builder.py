import unicodedata
import tiktoken


class MessageBuilder:
    """
    A class for building and managing messages in a chat conversation.
    Attributes:
        message (list): A list of dictionaries representing chat messages.
        model (str): The name of the ChatGPT model.
        token_count (int): The total number of tokens in the conversation.
    Methods:
        __init__(self, system_content: str, chatgpt_model: str): Initializes the MessageBuilder instance.
        insert_message(self, role: str, content: str, index: int = 1): Inserts a new message to the conversation.
    """

    def __init__(self, system_content: str, chatgpt_model: str):
        self.messages = [
            {"role": "system", "content": self.normalize_content(system_content)}
        ]
        self.model = chatgpt_model

    def num_tokens_from_messages(self, message: dict[str, str], model: str) -> int:
        """
        Calculate the number of tokens required to encode a message.
        Args:
            message (dict): The message to encode, represented as a dictionary.
            model (str): The name of the model to use for encoding.
        Returns:
            int: The total number of tokens required to encode the message.
        Example:
            message = {'role': 'user', 'content': 'Hello, how are you?'}
            model = 'gpt-3.5-turbo'
            num_tokens_from_messages(message, model)
            output: 11
        """
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = 2  # For "role" and "content" keys
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
        return num_tokens

    def insert_message(self, role: str, content: str, index: int = 1):
        """
        Inserts a message into the conversation at the specified index,
        or at index 1 (after system message) if no index is specified.
        Args:
            role (str): The role of the message sender (either "user" or "system").
            content (str): The content of the message.
            index (int): The index at which to insert the message.
        """
        self.messages.insert(
            index, {"role": role, "content": self.normalize_content(content)}
        )

    def count_tokens_for_message(self, message: dict[str, str]):
        return self.num_tokens_from_messages(message, self.model)

    def normalize_content(self, content: str):
        return unicodedata.normalize("NFC", content)
