cognitive_search_tool = {
    "type": "function",
    "function": {
        "name": "search_sources",
        "description": "Retrieve sources from the Azure Cognitive Search index",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "Query string to retrieve documents from azure search eg: 'Show company policies'",
                }
            },
            "required": ["search_query"],
        },
    },
}
