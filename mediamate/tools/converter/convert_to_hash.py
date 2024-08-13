import hashlib
from typing import List, Union


class ConvertToHash:
    def __init__(self):
        self.hash_results = []

    def hash_file_content(self, file_name: str) -> str:
        """Hash the content of a file using SHA-256."""
        sha256 = hashlib.sha256()
        try:
            sha256.update(file_name.encode('utf-8'))
            with open(file_name, 'rb') as file:
                while chunk := file.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except FileNotFoundError:
            return f"File {file_name} not found."
        except Exception as e:
            return str(e)

    def hash_data(self, data: Union[str, bytes]) -> str:
        """Hash a string or bytes data using SHA-256."""
        sha256 = hashlib.sha256()
        if isinstance(data, str):
            sha256.update(data.encode('utf-8'))
        elif isinstance(data, bytes):
            sha256.update(data)
        return sha256.hexdigest()

    def process_input(self, input_data: Union[str, bytes, List[str]]) -> List[str]:
        """Process input and save hashed results to the hash_results list."""
        self.hash_results.clear()  # Clear previous results

        if isinstance(input_data, list):
            for item in input_data:
                self.hash_results.append(self.hash_file_content(item))
        else:
            self.hash_results.append(self.hash_data(input_data))

        return self.hash_results