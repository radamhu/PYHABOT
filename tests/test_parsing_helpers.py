"""
Unit tests for HardverApró parsing helper functions.
"""

import pytest
from datetime import datetime

from src.pyhabot.adapters.scraping.hardverapro import convert_date, convert_price


class TestConvertDate:
    """Test cases for convert_date function."""
    
    def test_date_format_yyyy_mm_dd(self):
        """Test converting YYYY-MM-DD format."""
        result = convert_date("2025-10-30")
        expected = "2025-10-30 00:00"
        assert result == expected
    
    def test_time_format_ma_today(self):
        """Test converting 'ma HH:MM' format (today)."""
        # Mock the current date for consistent testing
        with pytest.MonkeyPatch().context() as m:
            # Set a fixed date for testing
            fixed_datetime = datetime(2025, 10, 30, 14, 30)
            m.setattr("src.pyhabot.adapters.scraping.hardverapro.datetime", 
                     type('MockDateTime', (), {
                         'now': lambda: fixed_datetime,
                         'strptime': datetime.strptime
                     })())
            
            result = convert_date("ma 14:30")
            expected = "2025-10-30 14:30"
            assert result == expected
    
    def test_time_format_tegnap_yesterday(self):
        """Test converting 'tegnap HH:MM' format (yesterday)."""
        with pytest.MonkeyPatch().context() as m:
            fixed_datetime = datetime(2025, 10, 30, 14, 30)
            m.setattr("src.pyhabot.adapters.scraping.hardverapro.datetime", 
                     type('MockDateTime', (), {
                         'now': lambda: fixed_datetime,
                         'strptime': datetime.strptime
                     })())
            
            result = convert_date("tegnap 10:15")
            expected = "2025-10-29 10:15"
            assert result == expected
    
    def test_pinned_ad(self):
        """Test converting 'előresorolva' (pinned ad)."""
        result = convert_date("előresorolva")
        assert result == "pinned"
    
    def test_pinned_ad_lowercase(self):
        """Test converting 'előresorolva' in lowercase."""
        result = convert_date("Előresorolva")
        assert result == "pinned"
    
    def test_invalid_date_format(self):
        """Test handling invalid date format."""
        result = convert_date("invalid date")
        assert result is None
    
    def test_malformed_date(self):
        """Test handling malformed date."""
        result = convert_date("2025-13-45")  # Invalid month/day
        assert result is None
    
    def test_malformed_time(self):
        """Test handling malformed time."""
        result = convert_date("ma 25:99")  # Invalid time
        assert result is None
    
    def test_empty_string(self):
        """Test handling empty string."""
        result = convert_date("")
        assert result is None
    
    def test_whitespace_only(self):
        """Test handling whitespace-only string."""
        result = convert_date("   ")
        assert result is None


class TestConvertPrice:
    """Test cases for convert_price function."""
    
    def test_regular_price_with_spaces(self):
        """Test converting regular price with spaces."""
        result = convert_price("100 000 Ft")
        assert result == 100000
    
    def test_regular_price_no_spaces(self):
        """Test converting regular price without spaces."""
        result = convert_price("50000 Ft")
        assert result == 50000
    
    def test_million_price_with_decimal(self):
        """Test converting million price with decimal."""
        result = convert_price("1.5M Ft")
        assert result == 1500000
    
    def test_million_price_with_comma(self):
        """Test converting million price with comma decimal."""
        result = convert_price("2,5M Ft")
        assert result == 2500000
    
    def test_whole_million_price(self):
        """Test converting whole million price."""
        result = convert_price("3M Ft")
        assert result == 3000000
    
    def test_keresem_wanted(self):
        """Test converting 'keresem' (wanted ad)."""
        result = convert_price("keresem")
        assert result is None
    
    def test_keresem_mixed_case(self):
        """Test converting 'keresem' in mixed case."""
        result = convert_price("Keresem")
        assert result is None
    
    def test_price_with_extra_spaces(self):
        """Test converting price with extra spaces."""
        result = convert_price("  75 000  Ft  ")
        assert result == 75000
    
    def test_invalid_price_format(self):
        """Test handling invalid price format."""
        result = convert_price("invalid price")
        assert result is None
    
    def test_price_without_ft(self):
        """Test handling price without Ft suffix."""
        result = convert_price("100000")
        assert result is None
    
    def test_empty_string(self):
        """Test handling empty string."""
        result = convert_price("")
        assert result is None
    
    def test_whitespace_only(self):
        """Test handling whitespace-only string."""
        result = convert_price("   ")
        assert result is None
    
    def test_zero_price(self):
        """Test converting zero price."""
        result = convert_price("0 Ft")
        assert result == 0
    
    def test_very_large_price(self):
        """Test converting very large price."""
        result = convert_price("999 999 999 Ft")
        assert result == 999999999
    
    def test_price_with_leading_zeros(self):
        """Test converting price with leading zeros."""
        result = convert_price("001 000 Ft")
        assert result == 1000