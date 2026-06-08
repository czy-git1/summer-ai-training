"""Unit tests for the myapp.handler module."""

from myapp.handler import APIResponse


class TestAPIResponse:
    """Tests for the APIResponse class."""

    def test_default_response(self) -> None:
        """APIResponse with no data should return code=0, msg=''."""
        response = APIResponse()
        assert response.data == {'code': 0, 'msg': ''}
        assert response.status_code == 200

    def test_with_data(self) -> None:
        """APIResponse should include 'data' key when data is provided."""
        response = APIResponse(data={'key': 'value'})
        assert response.data == {
            'code': 0,
            'msg': '',
            'data': {'key': 'value'},
        }

    def test_with_code_and_msg(self) -> None:
        """APIResponse should use custom code and msg values."""
        response = APIResponse(code=1, msg='Error occurred')
        assert response.data['code'] == 1
        assert response.data['msg'] == 'Error occurred'

    def test_custom_http_status(self) -> None:
        """APIResponse should accept a custom HTTP status code."""
        response = APIResponse(status=201)
        assert response.status_code == 201

    def test_extra_kwargs_merged(self) -> None:
        """APIResponse should merge extra kwargs into the response data."""
        response = APIResponse(extra_field='extra_value', count=42)
        assert response.data['extra_field'] == 'extra_value'
        assert response.data['count'] == 42

    def test_data_none_excluded(self) -> None:
        """APIResponse should NOT include 'data' key when data is None."""
        response = APIResponse(data=None)
        assert 'data' not in response.data

    def test_empty_dict_data_included(self) -> None:
        """APIResponse should include 'data' key even for empty dict."""
        response = APIResponse(data={})
        assert 'data' in response.data
        assert response.data['data'] == {}

    def test_headers_propagated(self) -> None:
        """APIResponse should propagate custom headers."""
        response = APIResponse(headers={'X-Custom': 'value'})
        assert response['X-Custom'] == 'value'

    def test_content_type_default(self) -> None:
        """APIResponse should have a Content-Type header set."""
        response = APIResponse()
        assert 'Content-Type' in response
        # Content-Type defaults to DRF's configured default (typically JSON)
