def str_surround(str: str, surround: str = "%", start=True, end=True):

    if start:
        str = surround + str
    if end:
        str = str + surround
    return str


if __name__ == "__main__":
    print(str_surround("hello", "__"))
