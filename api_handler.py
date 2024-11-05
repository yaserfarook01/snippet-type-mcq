import requests
import json
import logging
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

def get_all_qbs(token, search=None, page=1, limit=100):
    url = os.getenv('GET_ALL_QB_API')
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'authorization': token,
        'content-type': 'application/json',
        'origin': os.getenv('LTI_ORGIN'),
        'referer': os.getenv('LTI_REFERER'),
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    payload = {
        "branch_id": "all",
        "page": page,
        "limit": limit,
        "visibility": "All",
        "department_id": ["617346bd-b9c8-468d-9099-12170fb3b570","8c9bb195-1e81-4506-bc39-c48e6450c2a0","58efa904-a695-4c14-8335-124c9ec5e95a","4b375029-26ec-4d20-bf46-1122dfc584ae","d40c4d09-8ac5-4a26-b969-ce9cc8685180","e0f02ce1-486b-4122-8f1b-d80f7076bee3","04c14795-d8b2-41c0-9c41-997a5630f455","074cbc54-a20f-4a5d-9c02-1ca6a1bed28f","da3f5269-34b1-49c4-8d38-30c18b4f6598","f04c0f04-f6d7-434d-b8c9-5c356805ffab","f0b8af1b-288a-4b41-97b1-27447014ada3","2b60843d-7972-4235-82cb-0ebc33d75d63","78b66861-c946-4d83-9754-75c32925b5a9","5d1e18e7-b9aa-4d43-93b3-eb0a7a3df0d6","82208516-6d07-4fc0-8ee4-4205601c6695","b55a5b74-7f4a-428e-a59b-377dd8c7e4ba","35700f99-19f6-42c2-a336-d32687690e4a","c47b433a-7f1d-4014-a5b9-415187ed118b","fb751a89-c97a-47a6-9795-a33b3ba2eede","c02099c7-354a-48a9-867c-91cd16c6de38","4bb74161-364a-4012-9122-be5597db9f9e","a9ac9b80-daf9-45c3-aa4e-3aecd0a3820b","91f6683d-2512-416a-a355-2c6eefe9507b","6aa4e718-9fd9-4911-85c0-b900eed73547","2d24fa30-2621-418b-9597-0442ff8997df","5d4d3d63-73cd-4b04-a579-6c4f9fdf7473","55faaca8-4375-4bc6-874e-740dbf3dd22e","e100cac4-4586-4f3a-b598-24ee8d6c7a92","ffa1501f-1747-4ea7-9b83-22b3ab409d51","97c0a54a-67d2-4bc6-87b6-74b369e15889","627f1e5a-3e5e-4e14-b948-eab0baf714c4","d7d9bd6a-7bdc-46aa-8929-458e674f94c5","c3d1f72d-aa83-4276-9976-c5fcb06f70f8","4bf536a6-a9fa-4215-a803-056f0074e3e7","2680fe23-89dc-4035-a7a6-eb1869630f81","1dce25ce-cb7a-4826-a7e4-ab4c189bf436","e641144f-f801-4f79-8f3b-cff27ab3a123","7296cb61-76ce-4064-8928-328f2a545666","48942306-1e80-4db5-bd3b-e3075202d9b8","0ba8c5fa-9754-4d7f-851a-aa4791b9b445","8b0329c3-626e-4644-b6f4-dcb0424ed9fa","969b5384-e5ac-46aa-996b-547e5c77c3bf","41b64d5f-bb55-47a7-ad77-208e27ccae80","0400731b-2ab3-4644-828e-7c1618b23aac","e024b5b6-d6db-4fe6-a445-8b49facf10bb","d5c3f38f-fc70-4ac8-af83-372cd006396f","09f0cbe3-5c20-4c75-9c50-b4ee6fa6d09a","8154bcaa-3ee6-423f-938e-e4ccfe6002a7","4d037902-f46b-4fcf-824a-8f65376dbdcc","4ced5ede-47de-42b8-a5e3-a5af9d0ce415","566994d3-6a6f-4174-899a-700468f4bc7a","ebd40260-e32b-4367-8b8f-c606793e423b","6adf26cd-4949-4501-99c4-336401d84b49","64195871-472d-4520-839b-be0b8cbf2a94","4af00c09-f6a8-4099-8699-1c6a57db677b","0eb0005e-01b2-412a-a325-d0ea0ab9d64c","282bae70-ecb4-469a-94d0-8df0917b6ed4","62024afb-ea1e-4a6b-ad01-cbf1e592ed3c","662bd1f5-9c20-411a-aad0-e00e1881a6f2","54d15165-fc20-4e2e-bc1a-19e46c6a6f30","3f3711bd-ba73-404a-b72a-dee82166d2b4","a17c1837-80dd-4d0f-9a05-629e8f00eeb5","617ce4f5-33ec-4ff6-b1a6-1c74220be379","bf6ce3d6-8552-4959-bc65-9068c8f7738b","3f0fd32e-4290-488f-8e93-ba49d4dc1ecd","51827123-a24e-4aac-a23b-cbf3b95177e5","7a309bfc-d490-4269-8c36-f2899e02de65","9a64ffc7-47af-4f28-8dfa-31718a16ea7b","bd3777c4-635f-435a-94da-3426f786d592","6204bdfd-9a00-42b5-b951-0ab9a7a22105","173df851-7e75-43f1-9185-19028621a66f","e9fecb8e-8553-4d23-ac96-eca3da15af90","8eeae087-ce46-4d8a-9d0d-aefef190f0cd","00522911-f5fa-48fd-acb2-333b40117b82","41698284-bb61-4f6c-aaf1-591182d9025d","901ff1b8-cc03-4bb3-96b9-42bb53e86701","5c490195-95f7-4577-a9cb-3096d940af5d","1b18fbbf-a4ca-45df-ab78-75480a154b4a","ef6771c4-b9f5-4593-b4f6-ae9cd8845ec2","b073f250-c7eb-4d6b-829e-3af6ceb94037","78dc3377-b4a2-4338-b17e-6d8dde7cfeb1","ba75398b-44ce-487a-9dcd-f57339241e8d","a09496c9-0412-4649-944f-2edca43cb252","756c5ccf-535e-4b26-8d5f-3acc607e9a81","34c1f447-25af-4a75-9abf-be10d1626076"],
        "mainDepartmentUser": True
    }
    
    if search:
        payload["search"] = search

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Question Banks: {e}")
        if hasattr(e, 'response'):
            logging.error(f"Response content: {e.response.content}")
        return None

def import_mcqs_to_examly(input_file, qb_id, created_by, token):
    with open(input_file, 'r', encoding='utf-8') as f:
        unique_questions = json.load(f)
    
    url = os.getenv('CREATE_QUESTION')
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'authorization': token,
        'content-type': 'application/json',
        'origin': os.getenv('LTI_ORGIN'),
        'referer': os.getenv('LTI_REFERER'),
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    
    successful_uploads = 0
    failed_uploads = 0

    for question in unique_questions:
        question_to_post = question.copy()
        question_to_post.pop('question_vector', None)
        question_to_post['qb_id'] = qb_id
        if not question_to_post['tags']:
            question_to_post['tags'] = [""]
        
        try:
            response = requests.post(url, json=question_to_post, headers=headers)
            response.raise_for_status()
            successful_uploads += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"Error posting question: {e}")
            failed_uploads += 1
    
    return successful_uploads, failed_uploads


    
def get_all_qbs_neowise(token, search=None, page=1, limit=25):
    url = os.getenv('GET_ALL_QB_API')
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'authorization': token,
        'content-type': 'application/json',
        'origin': os.getenv('NEOWISE_ORGIN'),
        'referer': os.getenv('NEOWISE_REFERER'),
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    payload = {
        "branch_id": "all",
        "page": page,
        "limit": limit,
        "visibility": "All",
        "department_id": ["135950e9-d50e-46e0-bd83-672abdd75a44","e7ff788f-c169-4912-becc-922f60c22f33","1eb3f9be-949f-4366-93ff-38e8bc294204","8ce00f56-d771-4022-9db3-9cce403018bb","828a7982-06ea-42e9-ab66-49d479b74a1b","5c7faff9-4310-4052-9436-87fc02c0c8c7","02ff769d-0bdc-4b25-9598-6dd51ece3f94","b2a160ce-3c07-4f76-9141-9b183c1bc6d8","fde42d90-8163-479c-a4ab-fde8215ad22f","061912a6-6a43-4ace-b2a0-148ced4eb965","86430ada-0377-4cc9-9d1c-457928599f80","607bcef9-d910-4aac-b8dd-9db51424b370","072ec628-8569-43b3-a232-b5048398bbb3","3127e585-28e1-4140-8322-4081a22bb52b","3b13d51e-8e1e-47be-97ed-0801312ebf5f","ea34c967-7202-493f-ac56-c79ae79e06c5","55e39f8a-919f-4da6-a1e3-a700cef45cf2","cef01ce9-8b8a-494e-a0f5-2c56925fb7bf","f03e4d7d-ab35-4164-a9e8-580fce7acc1f","dc8f9b62-4920-4405-90d9-4debfa298549","05542ae9-203f-48cb-8090-01409d1415e7","720ce887-66da-4927-ad6a-ab9c07aa9492","497de26c-ecf6-4734-aac8-86e87e75daa5"],
        "mainDepartmentUser": True
    }
    
    if search:
        payload["search"] = search

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Question Banks from Neowise: {e}")
        if hasattr(e, 'response'):
            logging.error(f"Response content: {e.response.content}")
        return None

def import_mcqs_to_neowise(input_file, qb_id, created_by, token):
    with open(input_file, 'r', encoding='utf-8') as f:
        unique_questions = json.load(f)
    
    url = os.getenv('CREATE_QUESTION')
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'authorization': token,
        'content-type': 'application/json',
        'origin': os.getenv('NEOWISE_ORGIN'),
        'referer': os.getenv('NEOWISE_REFERER'),
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    
    successful_uploads = 0
    failed_uploads = 0

    for question in unique_questions:
        question_to_post = question.copy()
        question_to_post.pop('question_vector', None)
        question_to_post['qb_id'] = qb_id
        if not question_to_post['tags']:
            question_to_post['tags'] = [""]
        
        try:
            response = requests.post(url, json=question_to_post, headers=headers)
            response.raise_for_status()
            successful_uploads += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"Error posting question to Neowise: {e}")
            failed_uploads += 1
    
    return successful_uploads, failed_uploads
