import os
from azure.identity import DefaultAzureCredential
from azure.storage.queue import QueueServiceClient
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswParameters,
    SearchableField,
    SearchField,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SimpleField,
    VectorSearch,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
    SemanticSearch,
)


class AzureConfig:
    # Azure services
    SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
    RESOURCE_GROUP = os.environ["AZURE_RESOURCE_GROUP"]
    STORAGE_ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT"]
    STORAGE_CONTAINER = os.environ["AZURE_STORAGE_CONTAINER"]
    STORAGE_QUEUE = os.environ["AZURE_STORAGE_QUEUE"]
    SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
    SEARCH_SERVICE = os.environ["AZURE_SEARCH_SERVICE"]
    FORMRECOGNIZER_SERVICE = os.environ["AZURE_FORMRECOGNIZER_SERVICE"]

    def configure_clients(self):
        self.credential = DefaultAzureCredential()
        self.blob_client = BlobServiceClient(
            account_url=f"https://{self.STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=self.credential,
        )
        self.blob_container = self.blob_client.get_container_client(
            self.STORAGE_CONTAINER
        )

        self.queue_service = QueueServiceClient(
            account_url=f"https://{self.STORAGE_ACCOUNT}.queue.core.windows.net",
            credential=self.credential,
        )

        self.queue = self.queue_service.get_queue_client(self.STORAGE_QUEUE)

        self.search_client = SearchClient(
            endpoint=f"https://{self.SEARCH_SERVICE}.search.windows.net",
            index_name=self.SEARCH_INDEX,
            credential=self.credential,
        )
        self.form_recognizer = DocumentAnalysisClient(
            endpoint=f"https://{self.FORMRECOGNIZER_SERVICE}.cognitiveservices.azure.com/",
            credential=self.credential,
            headers={"x-ms-useragent": "pedantic-geek/1.0.0"},
        )

    def attrs_to_dict(self):
        attributes = {}
        for attr in dir(self):
            # Filter out special methods, non-uppercase attributes, and methods
            if not attr.startswith("__") and not attr.endswith("__") and attr.isupper():
                value = getattr(self, attr)
                if not callable(value):
                    attributes[attr] = value
        return attributes

    def create_search_index(self):
        self.search_index_client = SearchIndexClient(
            endpoint=f"https://{self.SEARCH_SERVICE}.search.windows.net/",
            credential=self.credential,
        )
        if self.SEARCH_INDEX not in self.search_index_client.list_index_names():
            fields = [
                SimpleField(name="id", type="Edm.String", filterable=True, key=True),
                SearchableField(
                    name="content", type="Edm.String", analyzer_name="en.microsoft"
                ),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    hidden=False,
                    searchable=True,
                    filterable=False,
                    sortable=False,
                    facetable=False,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="myHnswProfile",
                ),
                SimpleField(
                    name="is_summary",
                    type="Edm.Boolean",
                    filterable=True,
                    facetable=True,
                    default_value=False,
                ),
                SimpleField(
                    name="is_assessment",
                    type="Edm.Boolean",
                    filterable=True,
                    facetable=True,
                    default_value=False,
                ),
                SimpleField(
                    name="title", type="Edm.String", filterable=True, facetable=True
                ),
                SimpleField(
                    name="category", type="Edm.String", filterable=True, facetable=True
                ),
                SimpleField(
                    name="sourcepage",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                ),
                SimpleField(
                    name="sourcefile",
                    type="Edm.String",
                    filterable=True,
                    facetable=True,
                ),
            ]
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="myHnsw",
                        kind=VectorSearchAlgorithmKind.HNSW,
                        parameters=HnswParameters(
                            m=4,
                            ef_construction=400,
                            ef_search=500,
                            metric=VectorSearchAlgorithmMetric.COSINE,
                        ),
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="myHnswProfile",
                        algorithm_configuration_name="myHnsw",
                    ),
                ],
            )
            semantic_config = SemanticConfiguration(
                name="semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    keywords_fields=[SemanticField(field_name="category")],
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
            semantic_search = SemanticSearch(configurations=[semantic_config])
            index = SearchIndex(
                name=self.SEARCH_INDEX,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
            )
            self.search_index_client.create_index(index)
