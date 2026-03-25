"""
Tests for multiplier validation logic.

This test file verifies that invalid contacts (e.g. busted calls) are NOT
counted as multipliers, and that the multiplier credit is correctly passed
to the next valid contact.
"""

import pytest
from datetime import datetime, timedelta
from src.core.rules import (
    RulesEngine,
    Contact,
    load_sa10m_rules
)

class TestMultiplierValidation:
    """Test multiplier validation logic."""
    
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
    
    def test_invalid_contact_not_multiplier(self, engine):
        """
        Test that an invalid contact is not counted as a multiplier.
        
        Scenario:
        1. Contact 1: W3LPL (Zone 5) - Invalid (Busted Call)
           - Should NOT be a multiplier
           - Should have 0 points
        2. Contact 2: W3PP (Zone 5) - Valid
           - Should be a multiplier (W3 prefix and Zone 5)
           - Should have points
        """
        # 1. Invalid Contact (W3LPL)
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='W3LPL',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        # Mark as invalid
        contact1.validation_errors.append('busted_call')
        
        result1 = engine.process_contact(contact1)
        
        # Assertions for Contact 1
        assert result1.points == 0
        assert result1.is_multiplier is False
        assert len(result1.multiplier_types) == 0
        
        # 2. Valid Contact (W3PP) - Same Zone, Same Prefix (W3)
        contact2 = Contact(
            timestamp=datetime.now() + timedelta(minutes=5),
            callsign='W3PP',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        result2 = engine.process_contact(contact2)
        
        # Assertions for Contact 2
        assert result2.points > 0
        assert result2.is_multiplier is True
        assert 'wpx_prefix' in result2.multiplier_types
        assert 'cq_zone' in result2.multiplier_types
        
    def test_invalid_contact_wpx_logic(self, engine):
        """
        Test specifically for WPX prefix multiplier logic with invalid contacts.
        """
        # 1. Invalid Contact (K1ABC) - New Prefix K1
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='K1ABC',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        contact1.validation_errors.append('not_in_log')
        
        result1 = engine.process_contact(contact1)
        
        assert result1.is_multiplier is False
        
        # 2. Valid Contact (K1DEF) - Same Prefix K1
        contact2 = Contact(
            timestamp=datetime.now() + timedelta(minutes=5),
            callsign='K1DEF',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        )
        
        result2 = engine.process_contact(contact2)
        
        assert result2.is_multiplier is True
        assert 'wpx_prefix' in result2.multiplier_types

    def test_invalid_contact_zone_logic(self, engine):
        """
        Test specifically for Zone multiplier logic with invalid contacts.
        """
        # 1. Invalid Contact (JA1ABC) - Zone 25 (New Zone)
        contact1 = Contact(
            timestamp=datetime.now(),
            callsign='JA1ABC',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '25'}
        )
        contact1.validation_errors.append('time_mismatch')
        
        result1 = engine.process_contact(contact1)
        
        assert result1.is_multiplier is False
        
        # 2. Valid Contact (JA1DEF) - Zone 25
        contact2 = Contact(
            timestamp=datetime.now() + timedelta(minutes=5),
            callsign='JA1DEF',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '25'}
        )
        
        result2 = engine.process_contact(contact2)
        
        assert result2.is_multiplier is True
        assert 'cq_zone' in result2.multiplier_types

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
