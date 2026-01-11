"""
LLM module for generating communication choices using LangChain.
Supports OpenAI and Anthropic providers with structured output.
"""
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


class ChoiceWithProbability(BaseModel):
    """A choice option with probability score"""
    text: str = Field(description="The text of the choice (word or phrase)")
    probability: float = Field(
        description="Probability score between 0.0 and 1.0 indicating how likely this choice is given the context",
        ge=0.0,
        le=1.0
    )


class ChoicesOutput(BaseModel):
    """Structured output containing 2-8 choices with probabilities"""
    choices: List[ChoiceWithProbability] = Field(
        description="List of 2 to 8 choices, ordered by probability (highest first)",
        min_length=2,
        max_length=8
    )


class LLMService:
    """Service for generating communication choices using LLM"""
    
    def __init__(self, provider: str = "openai", model: str = "", temperature: float = 0.7):
        """
        Initialize LLM service.
        
        Args:
            provider: "openai" or "anthropic"
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            temperature: Temperature for generation (0.0 to 2.0)
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """Create the appropriate LLM instance based on provider"""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            model_name = self.model or "gpt-4"
            return ChatOpenAI(
                model=model_name,
                temperature=self.temperature,
                api_key=api_key
            )
        
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            
            model_name = self.model or "claude-3-opus-20240229"
            return ChatAnthropic(
                model=model_name,
                temperature=self.temperature,
                api_key=api_key
            )
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Supported: 'openai', 'anthropic'")
    
    def generate_choices(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_notes: Optional[str] = None,
        caregiver_description: Optional[str] = None,
        current_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate communication choices based on context.
        
        Args:
            system_prompt: System prompt from config
            conversation_history: List of messages in format [{"role": "user"/"assistant", "content": "..."}]
            user_notes: Notes about the user from user profile
            caregiver_description: Description of the caregiver
            current_text: Current text being composed by the user
        
        Returns:
            List of choices with text and probability, sorted by probability (highest first)
        """
        # Build context string
        context_parts = []
        
        if user_notes:
            context_parts.append(f"User Profile:\n{user_notes}\n")
        
        if caregiver_description:
            context_parts.append(f"Caregiver Profile:\n{caregiver_description}\n")
        
        if current_text:
            context_parts.append(f"Current text being composed: {current_text}\n")
        
        context = "\n".join(context_parts)
        
        # Build conversation history
        messages = []
        
        # Add system message with prompt and context
        system_content = system_prompt
        if context:
            system_content += f"\n\nContext:\n{context}"
        
        messages.append(SystemMessage(content=system_content))
        print(f"System message: {system_content}")
        print(f"Conversation history: {conversation_history}")
        print(f"User notes: {user_notes}")
        print(f"Caregiver description: {caregiver_description}")
        print(f"Current text: {current_text}")
        
        # Add conversation history
        for msg in conversation_history:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "user" or role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "assistant" or role == "ai":
                messages.append(AIMessage(content=content))
        
        # Use structured output
        structured_llm = self.llm.with_structured_output(ChoicesOutput)
        
        try:
            # Generate choices
            result = structured_llm.invoke(messages)
            
            # Convert to list of dicts with text and probability
            choices = [
                {
                    "text": choice.text,
                    "probability": choice.probability
                }
                for choice in result.choices
            ]
            
            # Sort by probability (highest first)
            choices.sort(key=lambda x: x["probability"], reverse=True)
            print(f"--> Generated Choices: {choices}")
            return choices
        
        except Exception as e:
            # Fallback to default choices if LLM fails
            print(f"Error generating choices with LLM: {e}")
            return [
                {"text": "Yes", "probability": 0.5},
                {"text": "No", "probability": 0.5},
                {"text": "More", "probability": 0.3},
                {"text": "Done", "probability": 0.2}
            ]
    
    def update_config(self, provider: str, model: str, temperature: float):
        """Update LLM configuration"""
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.llm = self._create_llm()


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service(provider: str = "openai", model: str = "", temperature: float = 0.7) -> LLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService(provider=provider, model=model, temperature=temperature)
    else:
        # Update if config changed
        if (_llm_service.provider != provider.lower() or 
            _llm_service.model != model or 
            _llm_service.temperature != temperature):
            _llm_service.update_config(provider, model, temperature)
    
    return _llm_service

