"""
DXLog Rules Parser - Parse DXLog.net contest definition files.

This module parses the key-value format used by DXLog contest definitions
and converts them into the internal ContestRules format.
"""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from .rules_loader import (
    ContestRules, ContestDefinition, ScoringRules, ScoringRule, 
    ScoringCondition, MultiplierRule, FinalScoreFormula,
    ValidationRules, DuplicateWindow, ExchangeDefinition, ExchangeField,
    ValidationFormat
)

class DXLogParser:
    """Parser for DXLog.net contest definition files."""

    def parse_file(self, file_path: Path) -> ContestRules:
        """
        Parse a DXLog contest file.

        Args:
            file_path: Path to the .txt file

        Returns:
            ContestRules object
        """
        config = self._read_config(file_path)
        
        # Determine slug from filename, handling SA10MC -> sa10m
        slug = file_path.stem.lower()
        if slug.endswith('c') and len(slug) > 1:
             # Check if it looks like a contest slug (heuristic)
             slug = slug[:-1]
             
        return self._convert_to_rules(config, slug)

    def _read_config(self, file_path: Path) -> Dict[str, List[str]]:
        """Read file into a dictionary of keys and values."""
        config = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key not in config:
                        config[key] = []
                    config[key].append(value)
        return config

    def _convert_to_rules(self, config: Dict[str, List[str]], slug: str) -> ContestRules:
        """Convert raw config to ContestRules."""
        
        # 1. Contest Definition
        contest = ContestDefinition(
            name=config.get('CONTESTNAME', ['Unknown'])[0],
            slug=slug.lower(),
            description=f"Imported from DXLog: {slug}",
            website=config.get('CONTESTWEB', [None])[0],
            bands=config.get('BANDS', ['10'])[0].split(';'),
            modes=config.get('MODES', ['SSB'])[0].split(';'),
            duration_hours=24 # Default, not usually in DXLog file
        )

        # 2. Scoring Rules
        points_rules = []
        for rule_str in config.get('POINTS_FIELD_BAND_MODE', []):
            rule = self._parse_points_rule(rule_str)
            if rule:
                points_rules.append(rule)

        # 3. Multipliers
        multipliers = []
        # Mult 1
        if 'MULT1_TYPE' in config:
            multipliers.append(MultiplierRule(
                type=self._map_mult_type(config['MULT1_TYPE'][0]),
                scope=self._map_mult_scope(config.get('MULT1_COUNT', ['ALL'])[0]),
                description=f"Multiplier 1: {config['MULT1_TYPE'][0]}"
            ))
        
        # Mult 2
        if 'MULT2_TYPE' in config:
            multipliers.append(MultiplierRule(
                type=self._map_mult_type(config['MULT2_TYPE'][0]),
                scope=self._map_mult_scope(config.get('MULT2_COUNT', ['ALL'])[0]),
                description=f"Multiplier 2: {config['MULT2_TYPE'][0]}"
            ))

        # 4. Final Score
        score_formula = self._determine_score_formula(config, multipliers)

        scoring = ScoringRules(
            points=points_rules,
            multipliers=multipliers,
            final_score=score_formula
        )

        # 5. Validation
        dup_rule = config.get('DOUBLE_QSO', ['NONE'])[0]
        
        # Create validation rules including exchange format
        exchange_format = self._create_exchange_validation(config)
        
        validation = ValidationRules(
            duplicate_window=DuplicateWindow(
                type=self._map_dup_type(dup_rule)
            ),
            exchange_format=exchange_format
        )

        # 6. Exchange
        exchange = self._determine_exchange(config)

        return ContestRules(
            contest=contest,
            scoring=scoring,
            validation=validation,
            exchange=exchange
        )

    def _create_exchange_validation(self, config: Dict[str, List[str]]) -> Dict[str, ValidationFormat]:
        """Create validation rules for exchange fields."""
        formats = {}
        
        # RST Validation
        formats['rs_rst'] = ValidationFormat(
            ssb_pattern=r'^[1-5][1-9]$',  # 59
            cw_pattern=r'^[1-5][1-9][1-9N]$', # 599 or 5NN
            description="Signal Report"
        )
        
        # Zone Validation
        rcvd_type = config.get('FIELD_RCVD_TYPE', ['TEXT'])[0]
        if rcvd_type == 'CQZONE':
            formats['cq_zone'] = ValidationFormat(
                min=1,
                max=40,
                pattern=r'^\d+$',
                description="CQ Zone (1-40)"
            )
            
        return formats

    def _determine_exchange(self, config: Dict[str, List[str]]) -> ExchangeDefinition:
        """Determine exchange format from config."""
        # Always include RST
        sent = [ExchangeField(field='rst', type='rst')]
        received = [ExchangeField(field='rst', type='rst')]
        
        rcvd_type = config.get('FIELD_RCVD_TYPE', ['TEXT'])[0]
        
        if rcvd_type == 'CQZONE':
            sent.append(ExchangeField(field='zone', type='integer'))
            received.append(ExchangeField(field='zone', type='integer'))
        elif rcvd_type == 'SERIAL':
            sent.append(ExchangeField(field='serial', type='integer'))
            received.append(ExchangeField(field='serial', type='integer'))
        elif rcvd_type == 'DXCC':
            sent.append(ExchangeField(field='dxcc', type='text'))
            received.append(ExchangeField(field='dxcc', type='text'))
        else:
            # Default generic exchange
            sent.append(ExchangeField(field='exchange', type='text'))
            received.append(ExchangeField(field='exchange', type='text'))
            
        return ExchangeDefinition(sent=sent, received=received)

    def _determine_score_formula(self, config: Dict[str, List[str]], multipliers: List[MultiplierRule]) -> FinalScoreFormula:
        """Determine scoring formula."""
        score_val = config.get('SCORE', [''])[0]
        
        # If explicit formula (heuristic)
        if '*' in score_val or '+' in score_val:
             return FinalScoreFormula(formula=score_val, description="From Config")
             
        # Derive from multipliers
        mult_count = len(multipliers)
        if mult_count == 0:
            return FinalScoreFormula(formula="TOTAL_POINTS", description="Total Points")
        elif mult_count == 1:
            return FinalScoreFormula(formula="TOTAL_POINTS * MULT1", description="Points * Mult")
        else:
            # Default to (M1 + M2) which is common for Zone+Country or Zone+Prefix
            return FinalScoreFormula(formula="TOTAL_POINTS * (MULT1 + MULT2)", description="Points * (Mult1 + Mult2)")

    def _parse_points_rule(self, rule_str: str) -> Optional[ScoringRule]:
        """
        Parse a POINTS_FIELD_BAND_MODE line.
        Format: CONDITION1;...;BAND;MODE;[?];POINTS;[CONDITION2]
        """
        parts = rule_str.split(';')
        if len(parts) < 4:
            return None

        # Find the points field (integer)
        points_idx = -1
        points = 0
        
        # Try second to last (case with trailing condition)
        try:
            points = int(parts[-2])
            points_idx = len(parts) - 2
        except ValueError:
            # Try last (case without trailing condition)
            try:
                points = int(parts[-1])
                points_idx = len(parts) - 1
            except ValueError:
                return None

        # Determine how many fixed fields precede points (2 or 3)
        # Candidates: parts[points_idx-3], parts[points_idx-2], parts[points_idx-1]
        
        # Check if parts[points_idx-3] looks like a band/mode/ALL
        # If it looks like a condition (contains ->), then it's not a fixed field
        
        fixed_fields_start = points_idx - 2 # Default to 2 fields (Band, Mode)
        
        if points_idx >= 3:
            candidate = parts[points_idx - 3]
            if '->' not in candidate and ':' not in candidate:
                # Likely a fixed field (Band/Mode/?)
                fixed_fields_start = points_idx - 3

        conditions = []
        
        # Parse all parts before fixed fields as conditions
        for i in range(fixed_fields_start):
            cond = self._parse_condition(parts[i])
            if cond:
                conditions.append(cond)
                
        # Parse trailing condition if exists
        if points_idx < len(parts) - 1:
            cond = self._parse_condition(parts[-1])
            if cond:
                conditions.append(cond)

        return ScoringRule(
            description=f"DXLog Rule: {rule_str}",
            conditions=conditions,
            value=points
        )

    def _parse_condition(self, cond_str: str) -> Optional[ScoringCondition]:
        """
        Parse a condition string like 'DEST->CONT:^SA$'
        """
        if not cond_str or cond_str == 'ALL':
            return None

        # Check for negation
        is_negated = cond_str.startswith('!')
        if is_negated:
            cond_str = cond_str[1:]

        if '->' not in cond_str:
            return None

        target, check = cond_str.split('->', 1)
        
        if ':' in check:
            field, value = check.split(':', 1)
        else:
            field = check
            value = None

        # Map fields to our internal types
        # DEST = Contact, SOURCE/CONFIG = Operator
        
        if target == 'DEST':
            if field == 'CONT':
                val = value.replace('^', '').replace('$', '')
                return ScoringCondition(
                    type='contact_continent',
                    value=f"!{val}" if is_negated else val
                )
            elif field == 'DXCC':
                # Special case: SOURCE->DXCC:DEST->DXCC
                pass # Handled in logic below if value refers to SOURCE
            elif field == 'CALL':
                # Regex match on callsign
                # We map /[AM]M$ to callsign_suffix
                if '[AM]M' in value:
                    return ScoringCondition(
                        type='contact_callsign_suffix',
                        values=['/AM', '/MM']
                    )

        elif target == 'SOURCE' or target == 'CONFIG':
            if field == 'DXCC':
                if value == 'DEST->DXCC':
                    return ScoringCondition(
                        type='different_dxcc' if is_negated else 'same_dxcc'
                    )
            elif field == 'CONT':
                val = value.replace('^', '').replace('$', '')
                return ScoringCondition(
                    type='operator_continent',
                    value=f"!{val}" if is_negated else val
                )
            elif field == 'CQZONE':
                # Regex zone match: ^(09|1[0123])$ -> 9,10,11,12,13
                if '09|1[0123]' in value:
                    return ScoringCondition(
                        type='operator_zone',
                        values=['9', '10', '11', '12', '13']
                    )
            elif field == 'CALL':
                 if '[AM]M' in value:
                    return ScoringCondition(
                        type='callsign_suffix',
                        values=['/AM', '/MM']
                    )

        return None

    def _map_mult_type(self, dxlog_type: str) -> str:
        mapping = {
            'WPX': 'wpx_prefix',
            'CQZONE': 'cq_zone',
            'DXCC': 'dxcc_entity'
        }
        return mapping.get(dxlog_type, dxlog_type.lower())

    def _map_mult_scope(self, dxlog_count: str) -> str:
        mapping = {
            'ALL': 'contest',
            'PER_BAND': 'per_band',
            'PER_MODE': 'per_mode',
            'PER_BAND_MODE': 'per_band_mode'
        }
        return mapping.get(dxlog_count, 'contest')

    def _map_dup_type(self, dxlog_dup: str) -> str:
        mapping = {
            'PER_MODE': 'mode',
            'PER_BAND': 'band',
            'PER_BAND_MODE': 'band_mode',
            'NONE': 'none'
        }
        return mapping.get(dxlog_dup, 'band_mode')
