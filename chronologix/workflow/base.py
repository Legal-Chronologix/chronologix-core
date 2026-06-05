"""
base.py

Small workflow runner for Chronologix.

A workflow is just an ordered list of steps.
Each step receives a shared context dict, adds/updates values, and returns it.
"""

from abc import ABC, abstractmethod
from typing import Any


class WorkflowStep(ABC):
    """
    Base class for one pipeline step.

    Each step receives the current context and returns the updated context.
    """

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Run one workflow step.
        """
        raise NotImplementedError


class Workflow:
    """
    Run a list of workflow steps in order.
    """

    def __init__(self, steps: list[WorkflowStep] | None = None):
        self.steps = steps or []

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Run every step with the shared context.
        """
        for step in self.steps:
            print(f"\nRunning step: {step.__class__.__name__}")
            context = step.run(context)

        return context