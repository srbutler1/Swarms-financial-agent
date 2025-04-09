"""
Custom AgentRearrange class that properly handles string output without JSON parsing.
"""
import traceback
from typing import Dict, List, Optional, Any
from swarms.structs.rearrange import AgentRearrange as BaseAgentRearrange
from swarms.structs.agent import Agent
from swarms.utils.loguru_logger import initialize_logger

logger = initialize_logger(log_folder="custom_rearrange")

class CustomAgentRearrange(BaseAgentRearrange):
    """
    A custom version of AgentRearrange that properly handles string output without JSON parsing.
    This class overrides the _catch_error method to handle JSON parsing errors gracefully.
    """
    
    def __init__(
        self,
        agents: List[Agent] = None,
        flow: str = None,
        max_loops: int = 1,
        verbose: bool = True,
        output_type: str = "string",
        *args,
        **kwargs
    ):
        """Initialize the CustomAgentRearrange with string output type by default."""
        super().__init__(
            agents=agents,
            flow=flow,
            max_loops=max_loops,
            verbose=verbose,
            output_type=output_type,
            *args,
            **kwargs
        )
    
    def _catch_error(self, e: Exception) -> None:
        """
        Custom error handler that captures the conversation output even when JSON parsing fails.
        
        Args:
            e (Exception): The exception that was raised
        """
        error_message = f"An error occurred with your swarm {self.__class__.__name__}: Error: {str(e)} Traceback: {traceback.format_exc()}"
        logger.error(error_message)
        
        # If this is a JSON parsing error and we have a conversation, return the conversation as a string
        if "Expecting value" in str(e) and hasattr(self, 'conversation'):
            try:
                # Return the conversation as a string
                return self.conversation.get_str()
            except Exception as conv_error:
                logger.error(f"Could not retrieve conversation: {str(conv_error)}")
                return f"Error: {str(e)}"
        
        # For other errors, return the error message
        return f"Error: {str(e)}"
    
    def run(self, task: str = None, *args, **kwargs) -> Any:
        """
        Override the run method to handle JSON parsing errors gracefully.
        
        Args:
            task (str, optional): The task to execute. Defaults to None.
            
        Returns:
            Any: The result of the execution or error message
        """
        try:
            return super().run(task=task, *args, **kwargs)
        except Exception as e:
            # If there's a JSON parsing error, try to return the conversation
            if "Expecting value" in str(e) and hasattr(self, 'conversation'):
                try:
                    logger.info("JSON parsing error encountered, returning conversation as string")
                    return self.conversation.get_str()
                except Exception as conv_error:
                    logger.error(f"Could not retrieve conversation: {str(conv_error)}")
            
            # Log the error and return a meaningful message
            logger.error(f"Error during execution: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error during execution: {str(e)}"
