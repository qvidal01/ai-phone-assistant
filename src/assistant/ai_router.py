"""Smart AI Router for selecting optimal backend based on query analysis."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.assistant.claude_handler import ClaudeHandler
from src.assistant.gateway_handler import GatewayHandler
from src.assistant.ollama_handler import OllamaHandler
from src.utils.logger import setup_logger


class BackendType(Enum):
    """Available AI backend types."""

    OLLAMA_FAST = "ollama_fast"  # quick-responder - simple queries
    OLLAMA_SMART = "ollama_smart"  # llama3.3:70b - complex local
    OLLAMA_CHAT = "ollama_chat"  # cyberque-chat - custom assistant
    CLAUDE = "claude"  # Claude API - best quality
    GATEWAY_FAST = "gateway_fast"  # AI Gateway 1B - edge simple
    GATEWAY_SMART = "gateway_smart"  # AI Gateway 8B/70B - edge complex
    HYBRID = "hybrid"  # Try Ollama first, fallback to Claude
    HYBRID_EDGE = "hybrid_edge"  # Try Gateway first, fallback to Ollama


class QueryComplexity(Enum):
    """Query complexity levels."""

    SIMPLE = "simple"  # Greetings, yes/no, basic info
    MODERATE = "moderate"  # Status checks, simple scheduling
    COMPLEX = "complex"  # Multi-step, reasoning, nuanced


@dataclass
class RoutingDecision:
    """Result of routing decision."""

    backend: BackendType
    model: Optional[str]
    reason: str
    complexity: QueryComplexity


class AIRouter:
    """
    Smart router that selects the optimal AI backend based on query analysis.

    Routing Strategy:
    - Simple queries (greetings, yes/no) → Ollama fast (quick-responder)
    - Moderate queries (status, basic scheduling) → Ollama chat (cyberque-chat)
    - Complex queries (reasoning, multi-step) → Claude or Ollama smart
    - Unknown/ambiguous → Hybrid (try Ollama, fallback Claude)
    """

    def __init__(
        self,
        claude_handler: Optional[ClaudeHandler] = None,
        ollama_handler: Optional[OllamaHandler] = None,
        gateway_handler: Optional[GatewayHandler] = None,
        default_strategy: str = "hybrid",
        prefer_local: bool = True,
        prefer_edge: bool = False,
    ):
        """
        Initialize the AI Router.

        Args:
            claude_handler: Claude API handler (optional)
            ollama_handler: Ollama handler (optional)
            gateway_handler: AI Gateway handler (optional)
            default_strategy: Default routing strategy
            prefer_local: Prefer local Ollama over Claude when quality is similar
            prefer_edge: Prefer edge AI Gateway for simple queries
        """
        self.claude = claude_handler
        self.ollama = ollama_handler
        self.gateway = gateway_handler
        self.default_strategy = default_strategy
        self.prefer_local = prefer_local
        self.prefer_edge = prefer_edge
        self.logger = setup_logger(__name__)

        # Track backend availability
        self._ollama_available: Optional[bool] = None
        self._claude_available: Optional[bool] = None
        self._gateway_available: Optional[bool] = None

        # Simple query patterns (fast response needed)
        self.simple_patterns = [
            r"^(hi|hello|hey|good\s*(morning|afternoon|evening)|greetings)\b",
            r"^(yes|no|yeah|nope|sure|ok|okay|yep|nah)\b",
            r"^(thanks|thank\s*you|bye|goodbye|see\s*you)\b",
            r"^(what|who)\s*(is|are)\s*(your|the)\s*name",
            r"^how\s*are\s*you",
        ]

        # Moderate query patterns (standard handling)
        self.moderate_patterns = [
            r"(status|update|check)\s*(on|for|of)",
            r"(is\s*(my|the|it)\s*\w+\s*ready)",
            r"(when|what\s*time|how\s*long)",
            r"(schedule|book|appointment|available)",
            r"(price|cost|how\s*much)",
            r"(hours|open|close|location|address)",
        ]

        # Complex query patterns (needs powerful model)
        self.complex_patterns = [
            r"(explain|describe|tell\s*me\s*(about|more)|elaborate)",
            r"(why|how\s*does|how\s*do\s*I|what\s*should\s*I)",
            r"(compare|difference|between|versus|vs)",
            r"(recommend|suggest|advice|opinion)",
            r"(problem|issue|trouble|not\s*working|broken)",
            r"(multiple|several|many|list|all)",
            r"(if|when|then|because|however|although)",
        ]

        # Appointment/scheduling keywords (needs structured handling)
        self.appointment_keywords = [
            "appointment",
            "schedule",
            "book",
            "reserve",
            "cancel",
            "reschedule",
            "change",
            "available",
            "slot",
            "time",
            "date",
            "calendar",
        ]

    def analyze_query(self, query: str) -> QueryComplexity:
        """
        Analyze query to determine complexity.

        Args:
            query: User's query text

        Returns:
            QueryComplexity: Determined complexity level
        """
        query_lower = query.lower().strip()
        word_count = len(query_lower.split())

        # Very short queries are usually simple
        if word_count <= 3:
            for pattern in self.simple_patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return QueryComplexity.SIMPLE

        # Check for complex patterns first (higher priority)
        for pattern in self.complex_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryComplexity.COMPLEX

        # Check for moderate patterns
        for pattern in self.moderate_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryComplexity.MODERATE

        # Check for simple patterns
        for pattern in self.simple_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return QueryComplexity.SIMPLE

        # Long queries tend to be more complex
        if word_count > 15:
            return QueryComplexity.COMPLEX
        elif word_count > 8:
            return QueryComplexity.MODERATE

        return QueryComplexity.MODERATE  # Default to moderate

    def is_appointment_query(self, query: str) -> bool:
        """
        Check if query is related to appointments/scheduling.

        Args:
            query: User's query text

        Returns:
            bool: True if appointment-related
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.appointment_keywords)

    def check_backend_availability(self) -> dict[str, bool]:
        """
        Check availability of all backends.

        Returns:
            Dict of backend availability
        """
        availability = {}

        if self.ollama:
            self._ollama_available = self.ollama.check_health_sync()
            availability["ollama"] = self._ollama_available

        if self.claude:
            # Claude is assumed available if configured
            self._claude_available = bool(self.claude.client)
            availability["claude"] = self._claude_available

        if self.gateway:
            self._gateway_available = self.gateway.check_health_sync()
            availability["gateway"] = self._gateway_available

        return availability

    def route(self, query: str, context: Optional[dict] = None) -> RoutingDecision:
        """
        Route query to optimal backend.

        Args:
            query: User's query text
            context: Optional conversation context

        Returns:
            RoutingDecision: Selected backend and reasoning
        """
        complexity = self.analyze_query(query)
        is_appointment = self.is_appointment_query(query)

        # Check backend availability
        availability = self.check_backend_availability()
        ollama_up = availability.get("ollama", False)
        claude_up = availability.get("claude", False)
        gateway_up = availability.get("gateway", False)

        # If prefer_edge and Gateway available, use it for simple queries
        if self.prefer_edge and gateway_up and complexity == QueryComplexity.SIMPLE:
            return RoutingDecision(
                backend=BackendType.GATEWAY_FAST,
                model="llama-3.2-1b",
                reason="Simple query, using edge AI Gateway for low latency",
                complexity=complexity,
            )

        # If only Gateway available
        if gateway_up and not ollama_up and not claude_up:
            model = self._select_gateway_model(complexity)
            return RoutingDecision(
                backend=(
                    BackendType.GATEWAY_FAST
                    if complexity == QueryComplexity.SIMPLE
                    else BackendType.GATEWAY_SMART
                ),
                model=model,
                reason="Only AI Gateway available",
                complexity=complexity,
            )

        # If only one traditional backend available, use it
        if ollama_up and not claude_up and not gateway_up:
            model = self._select_ollama_model(complexity)
            return RoutingDecision(
                backend=(
                    BackendType.OLLAMA_FAST
                    if complexity == QueryComplexity.SIMPLE
                    else BackendType.OLLAMA_CHAT
                ),
                model=model,
                reason="Only Ollama available",
                complexity=complexity,
            )

        if claude_up and not ollama_up and not gateway_up:
            return RoutingDecision(
                backend=BackendType.CLAUDE,
                model=None,
                reason="Only Claude available",
                complexity=complexity,
            )

        if not ollama_up and not claude_up and not gateway_up:
            self.logger.error("No AI backends available!")
            return RoutingDecision(
                backend=BackendType.CLAUDE,  # Try anyway
                model=None,
                reason="No backends confirmed available, trying Claude",
                complexity=complexity,
            )

        # Multiple backends available - smart routing
        if complexity == QueryComplexity.SIMPLE:
            # Simple queries → fast local model
            return RoutingDecision(
                backend=BackendType.OLLAMA_FAST,
                model="quick-responder:latest",
                reason="Simple query, using fast local model",
                complexity=complexity,
            )

        elif complexity == QueryComplexity.MODERATE:
            if is_appointment:
                # Appointment queries need reliable handling
                return RoutingDecision(
                    backend=BackendType.OLLAMA_CHAT,
                    model="cyberque-chat:latest",
                    reason="Appointment query, using custom chat model",
                    complexity=complexity,
                )
            else:
                # Standard moderate queries
                if self.prefer_local:
                    return RoutingDecision(
                        backend=BackendType.OLLAMA_CHAT,
                        model="cyberque-chat:latest",
                        reason="Moderate query, preferring local model",
                        complexity=complexity,
                    )
                else:
                    return RoutingDecision(
                        backend=BackendType.CLAUDE,
                        model=None,
                        reason="Moderate query, using Claude for quality",
                        complexity=complexity,
                    )

        else:  # COMPLEX
            if self.prefer_local:
                # Try smart local model for complex queries
                return RoutingDecision(
                    backend=BackendType.HYBRID,
                    model="llama3.3:70b",
                    reason="Complex query, trying local smart model with Claude fallback",
                    complexity=complexity,
                )
            else:
                return RoutingDecision(
                    backend=BackendType.CLAUDE,
                    model=None,
                    reason="Complex query, using Claude for best quality",
                    complexity=complexity,
                )

    def _select_ollama_model(self, complexity: QueryComplexity) -> str:
        """
        Select appropriate Ollama model based on complexity.

        Args:
            complexity: Query complexity level

        Returns:
            str: Model name
        """
        if complexity == QueryComplexity.SIMPLE:
            return "quick-responder:latest"
        elif complexity == QueryComplexity.MODERATE:
            return "cyberque-chat:latest"
        else:
            return "llama3.3:70b"

    def _select_gateway_model(self, complexity: QueryComplexity) -> str:
        """
        Select appropriate AI Gateway model based on complexity.

        Args:
            complexity: Query complexity level

        Returns:
            str: Model name
        """
        if complexity == QueryComplexity.SIMPLE:
            return "llama-3.2-1b"
        elif complexity == QueryComplexity.MODERATE:
            return "llama-3.1-8b"
        else:
            return "llama-3.3-70b"

    def generate_response(
        self, query: str, system_prompt: Optional[str] = None, context: Optional[dict] = None
    ) -> tuple[str, RoutingDecision]:
        """
        Generate response using smart routing.

        Args:
            query: User's query
            system_prompt: Optional system prompt
            context: Optional conversation context

        Returns:
            Tuple of (response text, routing decision)
        """
        decision = self.route(query, context)
        self.logger.info(f"Routing decision: {decision.backend.value} - {decision.reason}")

        response = ""

        try:
            if decision.backend == BackendType.OLLAMA_FAST:
                response = self.ollama.generate_response(query, system_prompt, model=decision.model)

            elif decision.backend == BackendType.OLLAMA_CHAT:
                response = self.ollama.generate_response(query, system_prompt, model=decision.model)

            elif decision.backend == BackendType.OLLAMA_SMART:
                response = self.ollama.generate_response(query, system_prompt, model=decision.model)

            elif decision.backend == BackendType.CLAUDE:
                response = self.claude.generate_response(query, system_prompt)

            elif decision.backend == BackendType.GATEWAY_FAST:
                response = self.gateway.generate_response(
                    query, system_prompt, model=decision.model
                )

            elif decision.backend == BackendType.GATEWAY_SMART:
                response = self.gateway.generate_response(
                    query, system_prompt, model=decision.model
                )

            elif decision.backend == BackendType.HYBRID_EDGE:
                # Try Gateway first
                response = self.gateway.generate_response(
                    query, system_prompt, model=decision.model
                )
                # Fallback to Ollama if Gateway fails
                if not response or len(response.strip()) < 5:
                    self.logger.info("Gateway response insufficient, falling back to Ollama")
                    response = self.ollama.generate_response(query, system_prompt)
                    decision = RoutingDecision(
                        backend=BackendType.OLLAMA_CHAT,
                        model="cyberque-chat:latest",
                        reason="Hybrid fallback to Ollama",
                        complexity=decision.complexity,
                    )

            elif decision.backend == BackendType.HYBRID:
                # Try Ollama first
                response = self.ollama.generate_response(query, system_prompt, model=decision.model)

                # Fallback to Claude if Ollama fails or returns empty
                if not response or len(response.strip()) < 5:
                    self.logger.info("Ollama response insufficient, falling back to Claude")
                    response = self.claude.generate_response(query, system_prompt)
                    decision = RoutingDecision(
                        backend=BackendType.CLAUDE,
                        model=None,
                        reason="Hybrid fallback to Claude",
                        complexity=decision.complexity,
                    )

        except Exception as e:
            self.logger.error(f"Error with {decision.backend.value}: {e}")

            # Fallback logic
            if decision.backend != BackendType.CLAUDE and self.claude:
                self.logger.info("Falling back to Claude due to error")
                try:
                    response = self.claude.generate_response(query, system_prompt)
                    decision = RoutingDecision(
                        backend=BackendType.CLAUDE,
                        model=None,
                        reason=f"Fallback to Claude after {decision.backend.value} error",
                        complexity=decision.complexity,
                    )
                except Exception as claude_error:
                    self.logger.error(f"Claude fallback also failed: {claude_error}")
                    response = "I apologize, but I'm having trouble processing that. Could you please try again?"

        if not response:
            response = (
                "I apologize, but I'm having trouble processing that. Could you please try again?"
            )

        return response, decision

    def reset_conversations(self):
        """Reset conversation history on all backends."""
        if self.ollama:
            self.ollama.reset_conversation()
        if self.claude:
            self.claude.reset_conversation()
        if self.gateway:
            self.gateway.reset_conversation()

    def get_conversation_summary(self) -> str:
        """
        Get conversation summary from the active backend.

        Returns:
            str: Conversation summary
        """
        # Prefer Ollama for summary (free), then Gateway, then Claude
        if self.ollama and self.ollama.conversation_history:
            return self.ollama.get_conversation_summary()
        elif self.gateway and self.gateway.conversation_history:
            return self.gateway.get_conversation_summary()
        elif self.claude and self.claude.conversation_history:
            return self.claude.get_conversation_summary()
        return "No conversation history."
