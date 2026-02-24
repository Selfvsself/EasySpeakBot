from langchain_core.prompts import ChatPromptTemplate

BIO_UPDATE_INSTRUCTIONS = """
Role: You are a Profile Analyzer.
Task: Extract key information about the user from the latest dialogue and update their profile data.

Instructions:
1. Identify details: Name, hobbies, interests, occupation, English level, and their communication style.
2. Return ONLY a valid JSON object. 
3. If a field is unknown, omit it. 
4. Do not delete existing information unless it's outdated (e.g., user changed their job).

Output Format Example:
{{
    "name": "Ivan",
    "hobbies": ["football", "coding"],
    "interests": ["history of London", "jazz"],
    "occupation": "student",
    "english_level": "A2",
    "style": "friendly, uses lots of slang"
}}
"""

bio_update_prompt = ChatPromptTemplate.from_messages([
    ("system", BIO_UPDATE_INSTRUCTIONS),
    ("system", "Current user profile data: {current_bio}"),
    ("human", "New messages to analyze: {new_messages}"),
])
