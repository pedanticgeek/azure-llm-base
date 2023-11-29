"""
This file builds GPT assistants, which were introduced on the 8th Nov by OpenAI. Many of its features are still in beta as of today (the 9th Nov) and may not be available in Azure OpenAI yet. They require openai>= 1.1.2
"""
from typing import Union
import openai


document_categories = ["General", "Legal", "Marketing", "IT", "Finance"]

reserved_categories = [
    "Assessment Criteria",
    "Business Summary Document",
    "Draft Offer",
    "Offer Template",
]

document_summarization_template = (
    f"""You are an intelligent librarian helping the company, named PedanticGeek, to organize their electronic documentation. 
You will be presented with a document pages. Please summarize the document, identify its title and its category from the list of categories below.\n{document_categories}\n
Use only the provided categories. 
Your summary should be brief but informative. 
You title should include maximum 5 words. 
Your response should be in the following JSON format:"""
    + """
### RESPONSE FORMAT ###
{"title": <document_title>,"category": <document_category>,"summary": <document_summary>}
### RESPONSE FORMAT END ###
"""
)

page_scanning_template = """You are provided with a page from a business document that presents an investment opportunity. 
Please scan this image and return all informative data from it. 
Please ignore all the data that you are not allowed to or cannot extract from the image.
Please ignore all logos, images, and other non-textual and non-informative data.
Please use '~' symbol to indicate approximate numeric values. 
Your response must include only the extracted data and nothing else. 
Your output will be embedded and stored in Microsoft Cognitive Search to be used for investment analysis."""


prompts = {
    "document-summarization": document_summarization_template,
    "page-scanning": page_scanning_template,
}


def get_or_create_assistant_by_name(model, name, tools=[]):
    try:
        return get_assistant_by_name(name)
    except StopIteration:
        return create_assistant(model, name, tools)


def create_assistant(model, name, tools=[]):
    return openai.beta.assistants.create(
        name=f"pedantic-geek-{name}",
        instructions=prompts[name],
        model=model,
        tools=tools,
    )


def get_assistant_by_name(name):
    return next(
        _ for _ in openai.beta.assistants.list() if _.name == f"pedantic-geek-{name}"
    )


def get_assistant_by_id(assistant_id: Union[str, None]):
    """Useful when you have pre-built assistants and want to use them. (Not in this project)"""
    return openai.beta.assistants.retrieve(assistant_id)
