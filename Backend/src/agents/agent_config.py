import os
import logging
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_config_list():
    """
    Get LLM configuration list for AutoGen.
    Uses API key from environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")
    
    # Define configuration for the OpenAI models
    config_list = [
        {
            "model": "gpt-3.5-turbo",
            "api_key": api_key,
        }
    ]
    
    logger.info("LLM configuration loaded successfully")
    return config_list

def create_agents():
    """
    Create and configure the AutoGen agents for Skill Bridge.
    
    Returns:
        tuple: (user_proxy, document_agent, skill_agent, gap_agent, resource_agent, group_chat_manager)
    """
    logger.info("Starting agent creation...")
    
    try:
        # Only import these modules when needed
        import autogen
        from autogen import AssistantAgent, UserProxyAgent
        
        logger.info("AutoGen modules imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import AutoGen: {str(e)}")
        raise ImportError(f"Failed to import AutoGen. Please make sure it's installed: {str(e)}")
    
    try:
        config_list = get_config_list()
        logger.info("Got config list")
        
        # Create code execution config to disable Docker
        code_execution_config = {
            "use_docker": False,  # This disables the Docker requirement
            "last_n_messages": 2,
            "work_dir": "workspace"
        }
        
        # Define the user proxy agent (no human in the loop)
        user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config=code_execution_config  # Add this to disable Docker
        )
        logger.info("Created user proxy agent")
        
        # Define LLM config that includes both the model config and code execution config
        llm_config = {
            "config_list": config_list,
            "code_execution_config": code_execution_config  # Add this to disable Docker
        }
        
        # Document processing agent
        document_agent = AssistantAgent(
            name="DocumentAgent",
            system_message="I process job descriptions and resumes to extract clean text.",
            llm_config=llm_config
        )
        logger.info("Created document agent")
        
        # Skill extraction agent
        skill_agent = AssistantAgent(
            name="SkillAgent",
            system_message="I extract skills from job descriptions and resumes using specialized NLP models.",
            llm_config=llm_config
        )
        logger.info("Created skill agent")
        
        # Gap analysis agent
        gap_agent = AssistantAgent(
            name="GapAgent",
            system_message="I analyze skills to identify gaps between job requirements and a candidate's resume.",
            llm_config=llm_config
        )
        logger.info("Created gap agent")
        
        # Resource recommendation agent
        resource_agent = AssistantAgent(
            name="ResourceAgent",
            system_message="I find learning resources for skills that need development.",
            llm_config=llm_config
        )
        logger.info("Created resource agent")
        
        # Create a group chat
        groupchat = autogen.GroupChat(
            agents=[user_proxy, document_agent, skill_agent, gap_agent, resource_agent],
            messages=[],
            max_round=10
        )
        logger.info("Created group chat")
        
        # Create a group chat manager
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config
        )
        logger.info("Created group chat manager")
        
        return user_proxy, document_agent, skill_agent, gap_agent, resource_agent, manager
        
    except Exception as e:
        logger.error(f"Error creating agents: {str(e)}")
        raise Exception(f"Failed to create agents: {str(e)}")