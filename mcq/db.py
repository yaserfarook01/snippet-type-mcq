import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import logging

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionBank:
    def __init__(self):
        try:
            elasticsearch_host = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')
            elasticsearch_port = os.getenv('ELASTICSEARCH_PORT', '9200')
            self.client = Elasticsearch(
                hosts=[f"http://{elasticsearch_host}:{elasticsearch_port}"],
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=30,
                retry_on_timeout=True
            )
            self.index_name = 'mcq_questions'
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            if self.client.ping():
                logger.info("Connected to Elasticsearch")
                self._create_index_if_not_exists()
            else:
                logger.error("Could not connect to Elasticsearch")
                
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch client: {e}")
            raise

    def _create_index_if_not_exists(self):
        try:
            if not self.client.indices.exists(index=self.index_name):
                index_body = {
                    'settings': {
                        'index': {
                            'number_of_shards': 1,
                            'number_of_replicas': 0
                        }
                    },
                    'mappings': {
                        'properties': {
                            'question_data': {'type': 'text'},
                            'options': {'type': 'nested'},
                            'answer': {'type': 'object'},
                            'difficulty': {'type': 'keyword'},
                            'tags': {'type': 'keyword'},
                            'question_vector': {
                                'type': 'dense_vector',
                                'dims': 384  # Dimension of the sentence transformer model
                            }
                        }
                    }
                }
                self.client.indices.create(index=self.index_name, body=index_body)
                logger.info(f"Created index: {self.index_name}")
            else:
                logger.info(f"Index {self.index_name} already exists")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def add_unique_questions(self, questions):
        unique_questions = []
        duplicates = 0
        for question in questions:
            question_text = question['question_data']
            if '$$$examly' in question_text:
                question_text = question_text.split('$$$examly')[0]
            
            logger.info(f"Checking question: {question_text[:50]}...")
            is_duplicate, existing_question = self.question_exists(question_text, question['options'])
            if not is_duplicate:
                # Generate the question vector
                question_vector = self.model.encode(question_text).tolist()
                question['question_vector'] = question_vector
                
                # Index the question in Elasticsearch
                response = self.client.index(index=self.index_name, body=question)
                if response['result'] == 'created':
                    unique_questions.append(question)
                    logger.info(f"Added unique question to Elasticsearch: {question_text[:50]}...")
                else:
                    logger.warning(f"Failed to add question to Elasticsearch: {question_text[:50]}...")
            else:
                duplicates += 1
                logger.info(f"Duplicate question skipped: {question_text[:50]}...")
                logger.info(f"Existing question: {existing_question[:50]}...")
        
        return unique_questions, duplicates

    def question_exists(self, question_data, options):
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "question_data": {
                                        "query": question_data,
                                        "slop": 3
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            result = self.client.search(index=self.index_name, body=query)
            if result['hits']['total']['value'] > 0:
                existing_question = result['hits']['hits'][0]['_source']['question_data']
                return True, existing_question
            return False, None
        except Exception as e:
            logger.error(f"Error checking if question exists: {e}")
            return False, None

    def find_similar_questions(self, query, num_results=5):
        try:
            query_vector = self.model.encode(query).tolist()
            search_body = {
                "size": num_results,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'question_vector') + 1.0",
                            "params": {"query_vector": query_vector}
                        }
                    }
                }
            }
            response = self.client.search(index=self.index_name, body=search_body)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Error finding similar questions: {e}")
            return []

    def get_all_questions(self):
        try:
            response = self.client.search(index=self.index_name, body={"query": {"match_all": {}}, "size": 10000})
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Error getting all questions: {e}")
            return []

# Create an instance of QuestionBank
try:
    question_bank = QuestionBank()
except Exception as e:
    logger.error(f"Failed to initialize QuestionBank: {e}")
    question_bank = None