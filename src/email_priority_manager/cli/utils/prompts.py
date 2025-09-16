"""
Interactive Prompts for CLI

This module provides interactive prompt utilities for CLI operations.
"""

import sys
from typing import Any, List, Dict, Optional, Union, Callable
from pathlib import Path
import getpass

from .colors import Colors, ColorScheme, StyledOutput


class ConfirmPrompt:
    """Interactive confirmation prompts."""

    @staticmethod
    def confirm(
        message: str,
        default: bool = False,
        abort: bool = False,
        show_choices: bool = True
    ) -> bool:
        """
        Ask user for confirmation.

        Args:
            message: The confirmation message
            default: Default response if user just presses Enter
            abort: If True, user can abort with 'a' or 'abort'
            show_choices: Whether to show [Y/n] style choices

        Returns:
            True if user confirms, False otherwise
        """
        if show_choices:
            if default:
                choices = "[Y/n]" if not abort else "[Y/n/a]"
            else:
                choices = "[y/N]" if not abort else "[y/N/a]"
            prompt = f"{message} {choices} "
        else:
            prompt = f"{message} "

        while True:
            try:
                response = input(prompt).strip().lower()

                if not response:
                    return default

                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                elif abort and response in ['a', 'abort']:
                    print(f"\n{Colors.YELLOW}Operation aborted by user.{Colors.RESET}")
                    sys.exit(130)
                else:
                    if abort:
                        print(f"{Colors.RED}Please enter 'y', 'n', or 'a'{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}Please enter 'y' or 'n'{Colors.RESET}")

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)

    @staticmethod
    def confirm_dangerous(message: str, operation: str = "This operation") -> bool:
        """
        Ask for confirmation for dangerous operations with extra warnings.

        Args:
            message: The confirmation message
            operation: Description of the dangerous operation

        Returns:
            True if user confirms, False otherwise
        """
        print(f"\n{Colors.RED}⚠ WARNING: {operation} is irreversible!{Colors.RESET}")
        print(f"{Colors.RED}This action cannot be undone.{Colors.RESET}")
        print()

        # Ask user to type confirmation
        confirm_text = "CONFIRM"
        user_input = input(f"Type '{confirm_text}' to continue: ").strip()

        if user_input == confirm_text:
            return ConfirmPrompt.confirm(message, default=False)
        else:
            print(f"\n{Colors.YELLOW}Operation cancelled.{Colors.RESET}")
            return False


class SelectionPrompt:
    """Interactive selection prompts."""

    @staticmethod
    def select(
        message: str,
        options: List[str],
        default: Optional[int] = None,
        multiple: bool = False,
        show_indices: bool = True
    ) -> Union[int, List[int]]:
        """
        Ask user to select from options.

        Args:
            message: Selection message
            options: List of options to choose from
            default: Default option index
            multiple: Allow multiple selections
            show_indices: Whether to show option indices

        Returns:
            Selected index(es)
        """
        if not options:
            raise ValueError("No options provided")

        print(f"{Colors.BLUE}{message}{Colors.RESET}")
        print()

        for i, option in enumerate(options, 1):
            prefix = ""
            if show_indices:
                if default == i:
                    prefix = f"{Colors.GREEN}> {i}.{Colors.RESET} "
                else:
                    prefix = f"  {i}. "
            print(f"{prefix}{option}")

        print()

        while True:
            try:
                if multiple:
                    prompt = "Select options (e.g., 1,2,3 or 1-3)"
                    if default is not None:
                        prompt += f" [{default}]"
                    prompt += ": "
                else:
                    prompt = f"Select option (1-{len(options)})"
                    if default is not None:
                        prompt += f" [{default}]"
                    prompt += ": "

                response = input(prompt).strip()

                if not response and default is not None:
                    return [default] if multiple else default

                if multiple:
                    # Parse multiple selections
                    selections = []
                    parts = response.split(',')

                    for part in parts:
                        part = part.strip()
                        if '-' in part:  # Range selection
                            start, end = map(int, part.split('-'))
                            selections.extend(range(start, end + 1))
                        else:
                            selections.append(int(part))

                    # Validate selections
                    valid = all(1 <= s <= len(options) for s in selections)
                    if valid:
                        return selections
                    else:
                        print(f"{Colors.RED}Please enter valid option numbers between 1 and {len(options)}{Colors.RESET}")
                else:
                    # Single selection
                    choice = int(response)
                    if 1 <= choice <= len(options):
                        return choice
                    else:
                        print(f"{Colors.RED}Please enter a number between 1 and {len(options)}{Colors.RESET}")

            except ValueError:
                print(f"{Colors.RED}Please enter valid numbers{Colors.RESET}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)

    @staticmethod
    def select_with_descriptions(
        message: str,
        options: List[Dict[str, str]],
        key_field: str = "key",
        desc_field: str = "description",
        default: Optional[str] = None
    ) -> str:
        """
        Select from options with descriptions.

        Args:
            message: Selection message
            options: List of dictionaries with key and description
            key_field: Field name for the key
            desc_field: Field name for the description
            default: Default key value

        Returns:
            Selected key
        """
        print(f"{Colors.BLUE}{message}{Colors.RESET}")
        print()

        for i, option in enumerate(options, 1):
            key = option.get(key_field, "Unknown")
            desc = option.get(desc_field, "No description")
            default_marker = ""

            if default == key:
                default_marker = f" {Colors.GREEN}(default){Colors.RESET}"

            print(f"  {i}. {Colors.CYAN}{key}{Colors.RESET}: {desc}{default_marker}")

        print()

        while True:
            try:
                prompt = f"Select option (1-{len(options)})"
                if default is not None:
                    prompt += f" [{default}]"
                prompt += ": "

                response = input(prompt).strip()

                if not response and default is not None:
                    return default

                choice = int(response)
                if 1 <= choice <= len(options):
                    return options[choice - 1].get(key_field)
                else:
                    print(f"{Colors.RED}Please enter a number between 1 and {len(options)}{Colors.RESET}")

            except ValueError:
                print(f"{Colors.RED}Please enter a valid number{Colors.RESET}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)


class InputPrompt:
    """Interactive input prompts."""

    @staticmethod
    def text(
        message: str,
        default: Optional[str] = None,
        required: bool = False,
        validate: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input"
    ) -> str:
        """
        Get text input from user.

        Args:
            message: Input message
            default: Default value
            required: Whether input is required
            validate: Validation function
            error_message: Error message for validation failures

        Returns:
            User input
        """
        if default is not None:
            prompt = f"{message} [{Colors.CYAN}{default}{Colors.RESET}]: "
        else:
            prompt = f"{message}: "

        while True:
            try:
                response = input(prompt).strip()

                if not response:
                    if default is not None:
                        return default
                    elif required:
                        print(f"{Colors.RED}This field is required{Colors.RESET}")
                        continue
                    else:
                        return ""

                # Validate input if validator provided
                if validate and not validate(response):
                    print(f"{Colors.RED}{error_message}{Colors.RESET}")
                    continue

                return response

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)

    @staticmethod
    def password(message: str = "Password: ", confirm: bool = False) -> str:
        """
        Get password input from user.

        Args:
            message: Password prompt message
            confirm: Whether to confirm password

        Returns:
            Password
        """
        while True:
            try:
                password = getpass.getpass(message)

                if not password:
                    print(f"{Colors.RED}Password cannot be empty{Colors.RESET}")
                    continue

                if confirm:
                    confirm_password = getpass.getpass("Confirm password: ")
                    if password != confirm_password:
                        print(f"{Colors.RED}Passwords do not match{Colors.RESET}")
                        continue

                return password

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)

    @staticmethod
    def number(
        message: str,
        default: Optional[Union[int, float]] = None,
        integer: bool = True,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None
    ) -> Union[int, float]:
        """
        Get numeric input from user.

        Args:
            message: Input message
            default: Default value
            integer: Whether to expect integer
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Numeric value
        """
        default_str = str(default) if default is not None else ""

        while True:
            try:
                response = input(f"{message} [{Colors.CYAN}{default_str}{Colors.RESET}]: ").strip()

                if not response and default is not None:
                    return default

                if integer:
                    value = int(response)
                else:
                    value = float(response)

                # Validate range
                if min_val is not None and value < min_val:
                    print(f"{Colors.RED}Value must be at least {min_val}{Colors.RESET}")
                    continue

                if max_val is not None and value > max_val:
                    print(f"{Colors.RED}Value must be at most {max_val}{Colors.RESET}")
                    continue

                return value

            except ValueError:
                print(f"{Colors.RED}Please enter a valid {'integer' if integer else 'number'}{Colors.RESET}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)

    @staticmethod
    def path(
        message: str,
        default: Optional[str] = None,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        must_writable: bool = False
    ) -> str:
        """
        Get file/directory path from user.

        Args:
            message: Input message
            default: Default path
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory
            must_writable: Whether path must be writable

        Returns:
            Path string
        """
        while True:
            try:
                response = input(f"{message} [{Colors.CYAN}{default or ''}{Colors.RESET}]: ").strip()

                if not response and default is not None:
                    response = default

                if not response:
                    print(f"{Colors.RED}Path cannot be empty{Colors.RESET}")
                    continue

                path = Path(response)

                # Check existence
                if must_exist and not path.exists():
                    print(f"{Colors.RED}Path does not exist: {response}{Colors.RESET}")
                    continue

                # Check file/directory type
                if path.exists():
                    if must_be_file and not path.is_file():
                        print(f"{Colors.RED}Path is not a file: {response}{Colors.RESET}")
                        continue

                    if must_be_dir and not path.is_dir():
                        print(f"{Colors.RED}Path is not a directory: {response}{Colors.RESET}")
                        continue

                    if must_writable and not os.access(path, os.W_OK):
                        print(f"{Colors.RED}Path is not writable: {response}{Colors.RESET}")
                        continue
                else:
                    # Check parent directory for writable access
                    if must_writable:
                        parent = path.parent
                        if not parent.exists():
                            print(f"{Colors.RED}Parent directory does not exist: {parent}{Colors.RESET}")
                            continue
                        if not os.access(parent, os.W_OK):
                            print(f"{Colors.RED}Parent directory is not writable: {parent}{Colors.RESET}")
                            continue

                return str(path)

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)


class MenuPrompt:
    """Interactive menu prompts."""

    @staticmethod
    def menu(
        title: str,
        options: List[Dict[str, Any]],
        key_field: str = "key",
        display_field: str = "display",
        description_field: Optional[str] = None,
        allow_back: bool = True,
        allow_quit: bool = True
    ) -> Optional[str]:
        """
        Display an interactive menu.

        Args:
            title: Menu title
            options: List of option dictionaries
            key_field: Field name for the key
            display_field: Field name for display text
            description_field: Field name for description (optional)
            allow_back: Allow going back
            allow_quit: Allow quitting

        Returns:
            Selected key or None if back/quit
        """
        while True:
            print()
            print(StyledOutput.header(title))
            print()

            for i, option in enumerate(options, 1):
                key = option.get(key_field)
                display = option.get(display_field, key)
                description = option.get(description_field) if description_field else None

                line = f"{Colors.CYAN}{i}.{Colors.RESET} {display}"

                if description:
                    line += f" {Colors.GRAY}- {description}{Colors.RESET}"

                print(line)

            # Add special options
            special_options = []
            if allow_back:
                special_options.append(("b", "Back"))
            if allow_quit:
                special_options.append(("q", "Quit"))

            if special_options:
                print()
                for key, desc in special_options:
                    print(f"{Colors.YELLOW}{key.upper()}{Colors.RESET} - {desc}")

            print()

            # Get user choice
            try:
                choice = input("Select option: ").strip().lower()

                if choice == 'b' and allow_back:
                    return None
                elif choice == 'q' and allow_quit:
                    print(f"{Colors.YELLOW}Exiting...{Colors.RESET}")
                    sys.exit(0)

                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(options):
                        return options[choice_idx].get(key_field)
                    else:
                        print(f"{Colors.RED}Invalid option number{Colors.RESET}")
                except ValueError:
                    print(f"{Colors.RED}Please enter a valid option number{Colors.RESET}")

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                sys.exit(130)


# Convenience functions
def confirm_action(message: str, default: bool = False) -> bool:
    """Simple confirmation prompt."""
    return ConfirmPrompt.confirm(message, default=default)


def select_option(message: str, options: List[str], default: Optional[int] = None) -> int:
    """Simple selection prompt."""
    return SelectionPrompt.select(message, options, default=default)


def prompt_input(message: str, default: Optional[str] = None, required: bool = False) -> str:
    """Simple text input prompt."""
    return InputPrompt.text(message, default=default, required=required)


# Import os for path operations
import os