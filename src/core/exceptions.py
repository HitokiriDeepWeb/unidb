class NeighbouringProcessError(Exception):
    def __init__(self, message: str = "Error occured in neighbouring process."):
        super().__init__(f"{message}")
