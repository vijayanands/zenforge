import base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def get_base64_of_bytes(bytes_data):
    return base64.b64encode(bytes_data).decode()
