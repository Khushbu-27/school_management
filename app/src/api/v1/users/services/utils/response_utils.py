
class Response:
    """
    Return success and error response.
    """

    def __init__(self, status_code, message, data=None):
        self.status_code = status_code
        self.message = message
        self.data = data

    def send_success_response(self):
        """
        Return a successful response with the status code and message.
        :return: success response
        """
        return {
            "data": {
                'data': self.data
            },
            "meta": {
                'message': self.message,
                'status_code': self.status_code
            }
        }

    def send_error_response(self):
        """
        Return an error response with the status code and message.
        :return: error response
        """
        return {
            "meta": {
                'message': self.message,
                'status_code': self.status_code
            },
            "data": {}
        }