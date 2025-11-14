"""
Mock data generators for testing.

Provides realistic test data for extraction results including contacts and users.
"""
from faker import Faker
from typing import List, Dict, Any

fake = Faker()


def generate_mock_contacts(count: int) -> List[Dict[str, Any]]:
    """
    Generate mock contact records with realistic data.
    
    Args:
        count: Number of contact records to generate
        
    Returns:
        List of dictionaries containing contact data with fields:
        - email
        - first_name
        - last_name
        - id_from_service
        - phone (optional)
        - company (optional)
        - created_at
    """
    contacts = []
    for i in range(count):
        contact = {
            'id_from_service': f'contact_{fake.uuid4()}',
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'phone': fake.phone_number() if i % 3 == 0 else None,  # Not all contacts have phone
            'company': fake.company() if i % 2 == 0 else None,  # Not all contacts have company
            'created_at': fake.iso8601(),
            'updated_at': fake.iso8601(),
        }
        contacts.append(contact)
    return contacts


def generate_mock_users(count: int) -> List[Dict[str, Any]]:
    """
    Generate mock user records with realistic data.
    
    Args:
        count: Number of user records to generate
        
    Returns:
        List of dictionaries containing user data with fields:
        - email
        - first_name
        - last_name
        - id_from_service
        - username
        - role (optional)
        - created_at
    """
    users = []
    roles = ['admin', 'user', 'viewer', 'editor']
    
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        user = {
            'id_from_service': f'user_{fake.uuid4()}',
            'email': fake.email(),
            'first_name': first_name,
            'last_name': last_name,
            'username': f"{first_name.lower()}.{last_name.lower()}{i}",
            'role': fake.random_element(elements=roles) if i % 3 == 0 else None,
            'created_at': fake.iso8601(),
            'last_login': fake.iso8601() if i % 2 == 0 else None,
        }
        users.append(user)
    return users


def generate_mock_extraction_response(
    record_type: str = 'contacts',
    count: int = 10,
    page: int = 1,
    per_page: int = 10,
    has_more: bool = False
) -> Dict[str, Any]:
    """
    Generate a complete mock API response for data extraction.
    
    Args:
        record_type: Type of records ('contacts' or 'users')
        count: Number of records to generate
        page: Current page number
        per_page: Records per page
        has_more: Whether there are more pages
        
    Returns:
        Dictionary mimicking external API response structure
    """
    if record_type == 'contacts':
        records = generate_mock_contacts(count)
    elif record_type == 'users':
        records = generate_mock_users(count)
    else:
        raise ValueError(f"Invalid record_type: {record_type}")
    
    return {
        'success': True,
        'data': records,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': count * 2 if has_more else count,
            'has_more': has_more,
        },
        'metadata': {
            'request_id': fake.uuid4(),
            'timestamp': fake.iso8601(),
        }
    }


def generate_sample_records(count: int, record_type: str = 'mixed') -> List[Dict[str, Any]]:
    """
    Generate sample extraction records for database seeding.
    
    Args:
        count: Number of records to generate
        record_type: 'contacts', 'users', or 'mixed'
        
    Returns:
        List of record dictionaries
    """
    if record_type == 'contacts':
        return generate_mock_contacts(count)
    elif record_type == 'users':
        return generate_mock_users(count)
    elif record_type == 'mixed':
        # Mix of contacts and users
        half = count // 2
        contacts = generate_mock_contacts(half)
        users = generate_mock_users(count - half)
        return contacts + users
    else:
        raise ValueError(f"Invalid record_type: {record_type}")


