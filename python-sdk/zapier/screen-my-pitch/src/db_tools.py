import boto3
from botocore.exceptions import ClientError
import time
from typing import Optional


def write_use_to_dynamodb(
        email: str,
        timestamp: int,
        table_name: str,
        region_name: str = 'us-east-1',
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
) -> bool:
    """
    Write an email address and timestamp to a DynamoDB table.

    Args:
        email (str): The email address to store
        timestamp (int): The timestamp to store
        table_name (str): Name of the DynamoDB table
        region_name (str): AWS region name (default: 'us-east-1')
        aws_access_key_id (str, optional): AWS access key ID
        aws_secret_access_key (str, optional): AWS secret access key

    Returns:
        bool: True if successful, False otherwise

    Raises:
        ValueError: If email or timestamp is invalid
        ClientError: If DynamoDB operation fails
    """

    # Validate inputs
    if not email or '@' not in email:
        raise ValueError("Invalid email address")

    if not isinstance(timestamp, int) or timestamp < 0:
        raise ValueError("Timestamp must be a positive integer")

    try:
        # Initialize DynamoDB client
        if aws_access_key_id and aws_secret_access_key:
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        else:
            # Use default credentials (IAM role, environment variables, etc.)
            dynamodb = boto3.resource('dynamodb', region_name=region_name)

        # Get table reference
        table = dynamodb.Table(table_name)

        # Write item to table
        response = table.put_item(
            Item={
                'email': email,
                'usedAt': timestamp
            }
        )

        print(f"Successfully wrote email '{email}' with timestamp {timestamp} to table '{table_name}'")
        return True

    except ClientError as e:
        print(f"DynamoDB error: {e.response['Error']['Message']}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False


def count_items_for_email(
        email: str,
        table_name: str,
        region_name: str = 'us-east-1',
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
) -> int:
    """
    Count the number of items in the DynamoDB table for a given email.

    Args:
        email (str): The email address to count items for
        table_name (str): Name of the DynamoDB table
        region_name (str): AWS region name (default: 'us-east-1')
        aws_access_key_id (str, optional): AWS access key ID
        aws_secret_access_key (str, optional): AWS secret access key

    Returns:
        int: Number of items found for the email

    Raises:
        ValueError: If email is invalid
        ClientError: If DynamoDB operation fails
    """

    # Validate inputs
    if not email or '@' not in email:
        raise ValueError("Invalid email address")

    try:
        # Initialize DynamoDB client
        if aws_access_key_id and aws_secret_access_key:
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        else:
            # Use default credentials (IAM role, environment variables, etc.)
            dynamodb = boto3.resource('dynamodb', region_name=region_name)

        # Get table reference
        table = dynamodb.Table(table_name)

        # Query items for the email (partition key)
        response = table.query(
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={
                ':email': email
            },
            Select='COUNT'  # Only return count, not actual items
        )

        count = response['Count']
        print(f"Found {count} items for email '{email}' in table '{table_name}'")
        return count

    except ClientError as e:
        print(f"DynamoDB error: {e.response['Error']['Message']}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise