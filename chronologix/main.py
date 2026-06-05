"""
main.py

Entry point for running Chronologix workflows.
"""

from chronologix.workflow.demo_gipson_case_workflow import run_gipson_workflow


def main() -> None:
    run_gipson_workflow()


if __name__ == "__main__":
    main()