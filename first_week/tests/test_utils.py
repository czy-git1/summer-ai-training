"""Unit tests for the myapp.utils module."""
import datetime
import hashlib
from unittest.mock import MagicMock

from myapp import utils


class TestGetTimestamp:
    """Tests for get_timestamp()."""

    def test_returns_int(self) -> None:
        """get_timestamp should return an integer."""
        result = utils.get_timestamp()
        assert isinstance(result, int)

    def test_returns_positive_value(self) -> None:
        """get_timestamp should return a positive millisecond value."""
        result = utils.get_timestamp()
        assert result > 1_700_000_000_000  # well past year 2023 in ms


class TestMd5Value:
    """Tests for md5value()."""

    def test_known_hash(self) -> None:
        """md5value should produce the correct MD5 hex digest."""
        result = utils.md5value('123456')
        expected = hashlib.md5('123456'.encode('utf-8')).hexdigest().lower()
        assert result == expected

    def test_empty_string(self) -> None:
        """md5value should handle empty string input."""
        result = utils.md5value('')
        expected = hashlib.md5(''.encode('utf-8')).hexdigest().lower()
        assert result == expected

    def test_special_characters(self) -> None:
        """md5value should handle unicode/special characters."""
        result = utils.md5value('测试密码!@#')
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hex digest is always 32 chars


class TestDictFetchall:
    """Tests for dict_fetchall()."""

    def test_returns_list_of_dicts(self) -> None:
        """dict_fetchall should convert cursor rows to a list of dicts."""
        cursor = MagicMock()
        cursor.description = [('id',), ('name',)]
        cursor.fetchall.return_value = [(1, 'Alice'), (2, 'Bob')]

        result = utils.dict_fetchall(cursor)
        assert result == [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
        ]

    def test_empty_result(self) -> None:
        """dict_fetchall should return an empty list when no rows."""
        cursor = MagicMock()
        cursor.description = [('id',), ('name',)]
        cursor.fetchall.return_value = []

        result = utils.dict_fetchall(cursor)
        assert result == []


class TestGetIp:
    """Tests for get_ip()."""

    def test_x_forwarded_for_single(self) -> None:
        """get_ip should extract IP from HTTP_X_FORWARDED_FOR header."""
        request = MagicMock()
        request.META = {'HTTP_X_FORWARDED_FOR': '192.168.1.100'}
        assert utils.get_ip(request) == '192.168.1.100'

    def test_x_forwarded_for_multiple(self) -> None:
        """get_ip should use the first IP when multiple are present."""
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '10.0.0.1, 192.168.1.1, 172.16.0.1'
        }
        assert utils.get_ip(request) == '10.0.0.1'

    def test_fallback_to_remote_addr(self) -> None:
        """get_ip should fall back to REMOTE_ADDR when no X-Forwarded-For."""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        assert utils.get_ip(request) == '127.0.0.1'

    def test_returns_none_when_missing(self) -> None:
        """get_ip should return None when neither header is present."""
        request = MagicMock()
        request.META = {}
        assert utils.get_ip(request) is None


class TestGetUa:
    """Tests for get_ua()."""

    def test_returns_user_agent(self) -> None:
        """get_ua should extract User-Agent from request META."""
        request = MagicMock()
        request.META = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 Test Browser'
        }
        assert utils.get_ua(request) == 'Mozilla/5.0 Test Browser'

    def test_truncates_to_200_chars(self) -> None:
        """get_ua should truncate User-Agent strings longer than 200 chars."""
        long_ua = 'A' * 250
        request = MagicMock()
        request.META = {'HTTP_USER_AGENT': long_ua}
        result = utils.get_ua(request)
        assert len(result) == 200
        assert result == long_ua[:200]

    def test_returns_empty_when_missing(self) -> None:
        """get_ua should return empty string when no User-Agent header."""
        request = MagicMock()
        request.META = {}
        assert utils.get_ua(request) == ''


class TestGetWeekDays:
    """Tests for get_week_days()."""

    def test_returns_7_days(self) -> None:
        """get_week_days should return exactly 7 date strings."""
        result = utils.getWeekDays()
        assert len(result) == 7

    def test_ascending_order(self) -> None:
        """get_week_days should return dates in ascending chronological order."""
        result = utils.getWeekDays()
        dates = [
            datetime.datetime.strptime(d, '%Y-%m-%d') for d in result
        ]
        for i in range(len(dates) - 1):
            assert dates[i] < dates[i + 1]

    def test_ends_with_today_or_yesterday(self) -> None:
        """get_week_days last entry should be near today."""
        result = utils.getWeekDays()
        last_date = datetime.datetime.strptime(result[-1], '%Y-%m-%d')
        today = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        diff = (today - last_date).days
        assert diff <= 1  # could be today or yesterday depending on time


class TestGetMonday:
    """Tests for get_monday()."""

    def test_returns_monday(self) -> None:
        """get_monday should return the Monday of the current week."""
        result = utils.get_monday()
        date = datetime.datetime.strptime(result, '%Y-%m-%d')
        assert date.weekday() == 0  # Monday

    def test_monday_not_in_future(self) -> None:
        """get_monday should not return a future date."""
        result = utils.get_monday()
        date = datetime.datetime.strptime(result, '%Y-%m-%d')
        today = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        assert date <= today
