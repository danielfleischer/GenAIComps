# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
from typing import List, Optional

from langchain_community.vectorstores import Neo4jVector
from langchain_core.documents import Document

from comps import CustomLogger, OpeaComponent, ServiceType
from comps.vectorstores.src.utils import encode_filename, format_search_results_from_list

from .config import EMBED_ENDPOINT, EMBED_MODEL, NEO4J_PASSWORD, NEO4J_URL, NEO4J_USERNAME

logger = CustomLogger("neo4j_vectorstores")
logflag = os.getenv("LOGFLAG", False)


class OpeaNeo4jVectorstores(OpeaComponent):

    def __init__(
        self,
        embedder,
        name: str,
        description: str,
        config: dict = None,
        neo4j_url: str = NEO4J_URL,
        neo4j_username: str = NEO4J_USERNAME,
        neo4j_pwd: str = NEO4J_PASSWORD,
    ):
        super().__init__(name, ServiceType.DATAPREP.name.lower(), description, config)
        self.embedder = embedder
        self.neo4j_url = neo4j_url
        self.neo4j_username = neo4j_username
        self.neo4j_pwd = neo4j_pwd
        self.client = self._initialize_client()

    def _initialize_client(self) -> Neo4jVector:
        """Initializes the neo4j client."""
        if logflag:
            logger.info("[ initialize client ] initializing neo4j client...")

        try:
            client = Neo4jVector.from_existing_graph(
                embedding=self.embedder,
                url=self.neo4j_url,
                username=self.neo4j_username,
                password=self.neo4j_pwd,
                node_label="__Entity__",
                text_node_properties=["id", "description"],
                embedding_node_property="embedding",
            )
            if logflag:
                logger.info("[ initialize client ] neo4j client initialized successfully!")
            return client
        except Exception as e:
            logger.error(f"[ initialize client ] fail to initialize neo4j client: {e}")
            return None

    def check_health(self) -> bool:
        """Checks the health of the neo4j service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of neo4j")
        try:
            result = self.client.query("RETURN 1 AS result")
            if result and result[0].get("result") == 1:
                if logflag:
                    logger.info("[ check health ] Successfully connected to neo4j!")
                return True
            else:
                if logflag:
                    logger.info("[ check health ] fail to connect neo4j or return results are not correct.")
                return False
        except Exception as e:
            logger.info(f"[ check health ] Failed to connect to neo4j: {e}")
            return False

    def invoke(self, *args, **kwargs):
        pass

    def is_empty(self):
        """Check whether the milvus db is empty.

        Returns:
            True if milvus db is empty, False otherwise.
        """
        self.client = self._initialize_client()
        if not self.client.col:
            if logflag:
                logger.info("[ is empty ] Milvus db is empty")
            return True
        if logflag:
            logger.info("[ is empty ] Milvus db is not empty")
        return False

    async def ingest_chunks(self, file_name: str, chunks: List, batch_size: int = 32) -> bool:
        """Ingest string chunks into milvus database.

        Args:
            file_name (str): The name of the file.
            chunks (List): The list of string chunks.
            batch_size (int): The batch size for ingesting chunks into db.
        Returns:
            bool: True if the chunks are ingested successfully, False otherwise.
        """
        if logflag:
            logger.info(f"[ ingest chunks ] file name:{file_name}")

        # construct insert docs
        insert_docs = []
        for chunk in chunks:
            insert_docs.append(Document(page_content=chunk, metadata={self.partition_field_name: file_name}))

        num_chunks = len(chunks)
        for i in range(0, num_chunks, batch_size):
            if logflag:
                logger.info(f"[ ingest chunks ] Current batch: {i}")
            batch_docs = insert_docs[i : i + batch_size]

            try:
                _ = Milvus.from_documents(
                    batch_docs,
                    self.embedder,
                    collection_name=self.collection_name,
                    connection_args={"uri": self.milvus_uri},
                    partition_key_field=self.partition_field_name,
                )
            except Exception as e:
                if logflag:
                    logger.error(f"[ ingest chunks ] fail to ingest chunks into Milvus. error: {e}")
                return False

        if logflag:
            logger.info(f"[ ingest chunks ] File {file_name} ingested to Milvus collection {self.collection_name}.")

        return True

    async def check_file_existance(self, file_path: str) -> bool:
        """Check whether the file exists in milvus database.

        Args:
            file_path (str): The path of the file.
        Returns:
            bool: True if the file exists, False otherwise.
        """
        if logflag:
            logger.info(f"[ check file existence ] file path: {file_path}")

        self.client = self._initialize_client()
        encode_file = encode_filename(file_path)

        if self.client.col:
            logger.info("[ check file existence ] client.col exists")
            try:
                search_res = self.search_by_file(encode_file)
                logger.info(f"[ check file existence ] search res: {search_res}")
            except Exception as e:
                if logflag:
                    logger.info(
                        f"[ check file existence ] Failed when searching in Milvus db for file {file_path}. {e}"
                    )
            if len(search_res) > 0:
                if logflag:
                    logger.info(f"[ check file existence ] File {file_path} already exists.")
                return True

        if logflag:
            logger.info(f"[ check file existence ] File {file_path} does not exist.")
        return False

    async def get_file_list(self) -> List[dict]:
        """Get all ingested file list from milvus database.

        Returns:
            - [] if no data in db.
            - None if failed to get file list.
            - List[dict]: The list of file dictionaries.
                [{
                    "name": "File Name",
                    "id": "File Name",
                    "type": "File",
                    "parent": "",
                }]
        """

        if logflag:
            logger.info("[ get file list ] start to get file structure")

        self.client = self._initialize_client()
        # check index existence
        if not self.client.col:
            if logflag:
                logger.info(f"[ get file list ] collection {self.collection_name} does not exist.")
            return []

        # get all files from db
        try:
            all_data = self.search_all()
        except Exception as e:
            if logflag:
                logger.info(f"[ get file list ] Failed when searching in Milvus db for all files. {e}")
            return None

        # return [] if no data in db
        if len(all_data) == 0:
            return []

        res_file = [res["filename"] for res in all_data]
        unique_list = list(set(res_file))
        if logflag:
            logger.info(f"[ get file list ] unique list from db: {unique_list}")

        # construct result file list in format
        file_list = format_search_results_from_list(unique_list)

        if logflag:
            logger.info(f"[ get file list ] final file list: {file_list}")
        return file_list

    async def get_file_content(self, file_name: str) -> List[dict]:
        """Get file content from milvus database.

        Not implemented for now.
        """
        if logflag:
            logger.info(f"[ get file content ] file name: {file_name}")
        pass

    async def delete_all_files(self) -> bool:
        """Delete all files in milvus database.

        Returns:
            bool: True if all files are deleted successfully, False otherwise.
        """
        if logflag:
            logger.info("[ delete all files ] delete all files")

        self.client = self._initialize_client()
        if self.client.col:
            try:
                self.client.col.drop()
                if logflag:
                    logger.info("[ delete all files ] successfully delete all files.")
            except Exception as e:
                if logflag:
                    logger.info(f"[ delete all files ] {e}. Failed to delete all files.")
                return False
        return True

    async def delete_single_file(self, file_name: str) -> bool:
        """Delete single file in milvus database.

        Args:
            file_name (str): The name of the file.
        Returns:
            bool: True if the file is deleted successfully, False otherwise.
        """
        if logflag:
            logger.info(f"[ delete single file ] delete file: {file_name}")

        try:
            self.delete_by_partition_field(file_name)
        except Exception as e:
            if logflag:
                logger.info(f"[ delete single file ] {e}. File {file_name} delete failed.")
            return False

        if logflag:
            logger.info(f"[ delete single file ] File {file_name} deleted successfully.")
        return True

    async def similarity_search(
        self,
        input: str,
        embedding: list,
        search_type: str = "similarity",
        k: int = 4,
        distance_threshold: Optional[float] = None,
        score_threshold: Optional[float] = None,
        lambda_mult: float = 0.2,
    ):
        if logflag:
            logger.info(f"[ similarity search ] search type: {search_type}, input: {input}")

        self.client = self._initialize_client()
        if search_type == "similarity":
            search_res = await self.client.asimilarity_search_by_vector(embedding=embedding, k=k)
        elif search_type == "similarity_distance_threshold":
            if distance_threshold is None:
                raise ValueError("distance_threshold must be provided for " + "similarity_distance_threshold retriever")
            search_res = await self.client.asimilarity_search_by_vector(
                embedding=embedding, k=k, distance_threshold=distance_threshold
            )
        elif search_type == "similarity_score_threshold":
            docs_and_similarities = await self.client.asimilarity_search_with_relevance_scores(
                query=input, k=k, score_threshold=score_threshold
            )
            search_res = [doc for doc, _ in docs_and_similarities]
        elif search_type == "mmr":
            search_res = await self.client.amax_marginal_relevance_search(
                query=input, k=k, fetch_k=k, lambda_mult=lambda_mult
            )
        else:
            if logflag:
                logger.error(f"[ similarity search ] unsupported search type {search_type}")
            raise ValueError(f"{search_type} not valid")

        if logflag:
            logger.info(f"[ similarity search ] search result: {search_res}")
        return search_res

    #############################
    # Neo4j specific functions #
    #############################
