"""
Rules Loader - Parse YAML contest definitions.

This module loads contest rules from YAML files and converts them into
Python objects for use by the rules engine.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime


class ExchangeField(BaseModel):
    """Definition of a field in the contest exchange."""
    field: str
    type: str
    required: bool = True
    description: Optional[str] = None
    validation: Optional[str] = None
    pattern: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None


class ScoringCondition(BaseModel):
    """A condition for scoring points."""
    type: str
    value: Optional[Any] = None
    values: Optional[Any] = None  # Can be list or string


class ScoringRule(BaseModel):
    """A rule for calculating points."""
    description: str
    conditions: List[ScoringCondition]
    value: int


class MultiplierRule(BaseModel):
    """Definition of a multiplier type."""
    type: str
    scope: str  # 'contest', 'per_band', 'per_mode', 'per_band_mode'
    description: Optional[str] = None
    applies_to: Optional[str] = None


class FinalScoreFormula(BaseModel):
    """Formula for calculating final score."""
    formula: str
    description: Optional[str] = None


class ScoringRules(BaseModel):
    """Complete scoring rules for a contest."""
    points: List[ScoringRule]
    multipliers: List[MultiplierRule]
    final_score: FinalScoreFormula


class ValidationFormat(BaseModel):
    """Validation format for exchange fields."""
    ssb_pattern: Optional[str] = None
    cw_pattern: Optional[str] = None
    pattern: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    description: Optional[str] = None


class DuplicateWindow(BaseModel):
    """Duplicate detection configuration."""
    type: str  # 'band_mode', 'band', 'mode', 'contest'


class ValidationRules(BaseModel):
    """Validation rules for the contest."""
    duplicate_window: DuplicateWindow
    exchange_format: Optional[Dict[str, ValidationFormat]] = None
    time_format: Optional[str] = None
    master_calls_file: Optional[str] = None  # Path to MASTER.SCP for unique-call verification


class CategoryDefinition(BaseModel):
    """Contest category definition."""
    name: str
    code: str
    description: Optional[str] = None


class ContestDefinition(BaseModel):
    """Main contest definition."""
    name: str
    slug: str
    description: Optional[str] = None
    website: Optional[str] = None
    bands: List[str]
    modes: List[str]
    duration_hours: int


class ExchangeDefinition(BaseModel):
    """Exchange format definition."""
    sent: List[ExchangeField]
    received: List[ExchangeField]


class ContestRules(BaseModel):
    """Complete contest rules configuration."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    contest: ContestDefinition
    categories: Optional[List[CategoryDefinition]] = None
    exchange: ExchangeDefinition
    scoring: ScoringRules
    validation: ValidationRules
    reference_data: Optional[Dict[str, Any]] = None



class RulesLoader:
    """Load and parse contest rules from YAML files."""

    def __init__(self, rules_dir: Optional[Path] = None):
        """
        Initialize the rules loader.

        Args:
            rules_dir: Directory containing contest YAML files.
                      Defaults to config/contests/
        """
        if rules_dir is None:
            # Default to config/contests relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            rules_dir = project_root / "config" / "contests"

        self.rules_dir = Path(rules_dir)
        if not self.rules_dir.exists():
            raise FileNotFoundError(f"Rules directory not found: {self.rules_dir}")

    def load_contest(self, contest_slug: str) -> ContestRules:
        """
        Load contest rules from YAML or DXLog TXT file.

        Args:
            contest_slug: The contest identifier (e.g., 'sa10m')

        Returns:
            ContestRules object with parsed configuration

        Raises:
            FileNotFoundError: If contest file doesn't exist
            ValueError: If file is invalid or doesn't match schema
        """
        # 1. Try YAML file
        yaml_file = self.rules_dir / f"{contest_slug}.yaml"

        if yaml_file.exists():
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    raw_data = yaml.safe_load(f)

                # Validate and parse using Pydantic
                rules = ContestRules(**raw_data)
                return rules

            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {yaml_file}: {e}")
            except Exception as e:
                raise ValueError(f"Error parsing contest rules from {yaml_file}: {e}")

        # 2. Try DXLog TXT file
        # Check for common DXLog naming conventions
        txt_candidates = [
            self.rules_dir / f"{contest_slug}.txt",
            self.rules_dir / f"{contest_slug.upper()}C.txt",  # e.g. SA10MC.txt
            self.rules_dir / f"{contest_slug.upper()}.txt"
        ]

        for txt_file in txt_candidates:
            if txt_file.exists():
                try:
                    # Import here to avoid circular dependency
                    from .dxlog_parser import DXLogParser
                    parser = DXLogParser()
                    return parser.parse_file(txt_file)
                except Exception as e:
                    raise ValueError(f"Error parsing DXLog rules from {txt_file}: {e}")

        raise FileNotFoundError(
            f"Contest rules file not found for '{contest_slug}'.\n"
            f"Checked: {yaml_file} and DXLog variants.\n"
            f"Available contests: {self.list_contests()}"
        )

    def list_contests(self) -> List[str]:
        """
        List all available contests.

        Returns:
            List of contest slugs
        """
        # List YAML files
        yaml_files = self.rules_dir.glob("*.yaml")
        contests = {f.stem for f in yaml_files if f.stem != 'template'}
        
        # List TXT files (DXLog)
        txt_files = self.rules_dir.glob("*.txt")
        for f in txt_files:
            # Handle SA10MC.txt -> sa10m
            name = f.stem
            if name.endswith('C') and name[:-1].isupper():
                contests.add(name[:-1].lower())
            else:
                contests.add(name.lower())
                
        return sorted(list(contests))

    def get_contest_info(self, contest_slug: str) -> Dict[str, Any]:
        """
        Get basic information about a contest without loading full rules.

        Args:
            contest_slug: The contest identifier

        Returns:
            Dictionary with contest name, description, bands, modes, etc.
        """
        rules = self.load_contest(contest_slug)
        return {
            'slug': rules.contest.slug,
            'name': rules.contest.name,
            'description': rules.contest.description,
            'website': rules.contest.website,
            'bands': rules.contest.bands,
            'modes': rules.contest.modes,
            'duration_hours': rules.contest.duration_hours,
            'categories': [
                {'name': cat.name, 'code': cat.code}
                for cat in (rules.categories or [])
            ]
        }

    def validate_rules_file(self, yaml_file: Path) -> tuple[bool, Optional[str]]:
        """
        Validate a contest rules YAML file.

        Args:
            yaml_file: Path to the YAML file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f)

            # Try to parse with Pydantic
            ContestRules(**raw_data)
            return (True, None)

        except yaml.YAMLError as e:
            return (False, f"Invalid YAML syntax: {e}")
        except Exception as e:
            return (False, f"Validation error: {e}")


def load_sa10m_rules() -> ContestRules:
    """
    Convenience function to load SA10M contest rules.

    Returns:
        ContestRules for SA10M contest
    """
    loader = RulesLoader()
    return loader.load_contest('sa10m')


if __name__ == '__main__':
    # Test loading SA10M rules
    loader = RulesLoader()

    print("Available contests:")
    for contest in loader.list_contests():
        print(f"  - {contest}")

    print("\nLoading SA10M rules...")
    sa10m = loader.load_contest('sa10m')

    print(f"\nContest: {sa10m.contest.name}")
    print(f"Bands: {', '.join(sa10m.contest.bands)}")
    print(f"Modes: {', '.join(sa10m.contest.modes)}")
    print(f"Duration: {sa10m.contest.duration_hours} hours")

    print(f"\nExchange sent: {[f.field for f in sa10m.exchange.sent]}")
    print(f"Exchange received: {[f.field for f in sa10m.exchange.received]}")

    print(f"\nScoring rules: {len(sa10m.scoring.points)} point rules")
    print(f"Multipliers: {len(sa10m.scoring.multipliers)} types")
    for mult in sa10m.scoring.multipliers:
        print(f"  - {mult.type} ({mult.scope}): {mult.description}")

    print(f"\nFinal score formula: {sa10m.scoring.final_score.formula}")

