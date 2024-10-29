from pymobiledevice3.exceptions import AfcException

if __name__ == "__main__":
    # This will raise an exception
    raise AfcException("This is an exception", status=1)
