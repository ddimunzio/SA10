"""
Tests for the Rules Engine components.

This test file verifies that the RulesLoader, RulesValidator, and RulesEngine
components work correctly for the SA10M contest.
"""

import pytest
from datetime import datetime
from src.core.rules import (
    RulesLoader,
    RulesValidator,
    RulesEngine,
    Contact,
    load_sa10m_rules,
    validate_contest_rules
)


class TestRulesLoader:
    """Test the RulesLoader component."""
    
    def test_load_sa10m_rules(self):
        """Test loading SA10M contest rules."""
        loader = RulesLoader()
        rules = loader.load_contest('sa10m')
        
        assert rules.contest.name == "South America 10m Contest"
        assert rules.contest.slug == "sa10m"
        assert "10m" in rules.contest.bands
        assert "SSB" in rules.contest.modes
        assert "CW" in rules.contest.modes
    
    def test_list_contests(self):
        """Test listing available contests."""
        loader = RulesLoader()
        contests = loader.list_contests()
        
        assert "sa10m" in contests
    
    def test_get_contest_info(self):
        """Test getting contest information."""
        loader = RulesLoader()
        info = loader.get_contest_info('sa10m')
        
        assert info['name'] == "South America 10m Contest"
        assert info['slug'] == "sa10m"
        assert '10m' in info['bands']
    
    def test_load_nonexistent_contest(self):
        """Test loading a contest that doesn't exist."""
        loader = RulesLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_contest('nonexistent_contest')


class TestRulesValidator:
    """Test the RulesValidator component."""
    
    def test_validate_sa10m_rules(self):
        """Test validating SA10M rules."""
        rules = load_sa10m_rules()
        validator = RulesValidator(rules)
        
        is_valid, errors, warnings = validator.validate()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_cq_zone_valid(self):
        """Test validating valid CQ zone."""
        rules = load_sa10m_rules()
        validator = RulesValidator(rules)
        
        is_valid, error = validator.validate_exchange_value('cq_zone', '13', 'SSB')
        assert is_valid is True
        assert error is None
    
    def test_validate_cq_zone_invalid(self):
        """Test validating invalid CQ zone."""
        rules = load_sa10m_rules()
        validator = RulesValidator(rules)
        
        is_valid, error = validator.validate_exchange_value('cq_zone', '99', 'SSB')
        assert is_valid is False
        assert error is not None
    
    def test_validate_rs_rst_ssb(self):
        """Test validating SSB signal report."""
        rules = load_sa10m_rules()
        validator = RulesValidator(rules)
        
        # Valid SSB report
        is_valid, error = validator.validate_exchange_value('rs_rst', '59', 'SSB')
        assert is_valid is True
        
        # Invalid - too many digits for SSB
        is_valid, error = validator.validate_exchange_value('rs_rst', '599', 'SSB')
        assert is_valid is False
    
    def test_validate_rs_rst_cw(self):
        """Test validating CW signal report."""
        rules = load_sa10m_rules()
        validator = RulesValidator(rules)
        
        # Valid CW report
        is_valid, error = validator.validate_exchange_value('rs_rst', '599', 'CW')
        assert is_valid is True
        
        # Invalid - letters not allowed
        is_valid, error = validator.validate_exchange_value('rs_rst', '5NN', 'CW')
        assert is_valid is False


class TestRulesEngine:
    """Test the RulesEngine component."""
    
    @pytest.fixture
    def engine(self):
        """Create a RulesEngine instance for testing."""
        rules = load_sa10m_rules()
        operator_info = {
            'callsign': 'LU1ABC',
            'continent': 'SA',
            'dxcc': 100,
            'cq_zone': 13
        }
        return RulesEngine(rules, operator_info)
    
    def test_wpx_prefix_extraction(self, engine):
        """Test WPX prefix extraction."""
        assert engine._extract_wpx_prefix('W1AW') == 'W1'
        assert engine._extract_wpx_prefix('K3LR') == 'K3'
        assert engine._extract_wpx_prefix('LU3DRP') == 'LU3'
        assert engine._extract_wpx_prefix('CE7VP') == 'CE7'
        assert engine._extract_wpx_prefix('9A3YT') == '9A3'
    
    def test_sa_to_non_sa_contact(self, engine):
        """Test SA station contacting non-SA station (4 points)."""
        contact = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        result = engine.process_contact(contact)
        assert result.points == 4
        assert result.is_duplicate is False
    
    def test_sa_to_sa_different_dxcc(self, engine):
        """Test SA station contacting different SA station (2 points)."""
        contact = Contact(
            timestamp=datetime.now(),
            callsign='CE7VP',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '12'}
        )
        
        result = engine.process_contact(contact)
        assert result.points == 2
        assert result.is_duplicate is False
    
    def test_duplicate_detection(self, engine):
        """Test duplicate detection (same band/mode)."""
        # First contact
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        # Same callsign, same band/mode - should be duplicate
        contact2 = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        result1 = engine.process_contact(contact1)
        result2 = engine.process_contact(contact2)
        
        assert result1.is_duplicate is False
        assert result1.points == 4
        
        assert result2.is_duplicate is True
        assert result2.points == 0
    
    def test_not_duplicate_different_mode(self, engine):
        """Test that same callsign on different mode is not duplicate."""
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        contact2 = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='CW',
            frequency=28010,
            rst_sent='599',
            rst_received='599',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        result1 = engine.process_contact(contact1)
        result2 = engine.process_contact(contact2)
        
        assert result1.is_duplicate is False
        assert result2.is_duplicate is False
    
    def test_wpx_multiplier(self, engine):
        """Test WPX prefix multiplier."""
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        contact2 = Contact(
            timestamp=datetime.now(),
            callsign='W2ABC',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        result1 = engine.process_contact(contact1)
        result2 = engine.process_contact(contact2)
        
        assert result1.is_multiplier is True
        assert 'wpx_prefix' in result1.multiplier_types
        
        assert result2.is_multiplier is True
        assert 'wpx_prefix' in result2.multiplier_types
    
    def test_zone_multiplier(self, engine):
        """Test CQ zone multiplier."""
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        contact2 = Contact(
            timestamp=datetime.now(),
            callsign='K3LR',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '4'}
        )
        
        result1 = engine.process_contact(contact1)
        result2 = engine.process_contact(contact2)
        
        assert result1.is_multiplier is True
        assert 'cq_zone' in result1.multiplier_types
        
        assert result2.is_multiplier is True
        assert 'cq_zone' in result2.multiplier_types
    
    def test_final_score_calculation(self, engine):
        """Test final score calculation."""
        contacts = [
            Contact(
                timestamp=datetime.now(),
                callsign='W1AW',
                band='10m',
                mode='SSB',
                frequency=28500,
                rst_sent='59',
                rst_received='59',
                exchange_sent={'cq_zone': '13'},
                exchange_received={'cq_zone': '5'}
            ),
            Contact(
                timestamp=datetime.now(),
                callsign='K3LR',
                band='10m',
                mode='SSB',
                frequency=28510,
                rst_sent='59',
                rst_received='59',
                exchange_sent={'cq_zone': '13'},
                exchange_received={'cq_zone': '5'}
            ),
            Contact(
                timestamp=datetime.now(),
                callsign='CE7VP',
                band='10m',
                mode='SSB',
                frequency=28520,
                rst_sent='59',
                rst_received='59',
                exchange_sent={'cq_zone': '13'},
                exchange_received={'cq_zone': '12'}
            ),
        ]
        
        processed = [engine.process_contact(c) for c in contacts]
        score = engine.calculate_final_score(processed)
        
        assert score['total_qsos'] == 3
        assert score['valid_qsos'] == 3
        assert score['duplicate_qsos'] == 0
        assert score['total_points'] == 10  # 4+4+2
        assert score['wpx_multipliers'] == 3  # W1, K3, CE7
        assert score['zone_multipliers'] == 2  # Zone 5, Zone 12
        assert score['final_score'] == 50  # 10 * (3 + 2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

