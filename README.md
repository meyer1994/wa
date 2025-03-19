# WhatsApp API Infrastructure

This project contains AWS CDK code to deploy a WhatsApp API application to AWS with:
- API Gateway
- Lambda Function
- Two DynamoDB tables

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS CDK v2 installed
- Python 3.9 or later
- Node.js 14 or later (required by CDK)

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
pip install -r requirements.txt
```

2. Bootstrap your AWS account for CDK (if not already done):

```bash
cdk bootstrap
```

3. Deploy the infrastructure:

```bash
cdk deploy
```

## Infrastructure Components

- **API Gateway**: HTTP API that accepts GET and POST requests at the /webhook endpoint
- **Lambda Function**: Hosts the FastAPI application
- **DynamoDB Tables**:
  - `ConversationsTable`: Stores conversation data with conversation_id as the partition key
  - `UsersTable`: Stores user data with phone_number as the partition key

## Local Development

To run the FastAPI application locally:

```bash
python lambda_handler.py
```

The server will be available at http://localhost:8000
