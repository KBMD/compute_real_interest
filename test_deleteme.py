class Test:

    instances = {}

    @classmethod
    def get_instance(cls, code):
        """Checks to see if an investment exists (i.e. has already been seen
            while reading the .csv file). Returns the investment object if it
            exists; otherwise returns None.
        """
        if code in cls.instances:
            return cls.instances[code]
        else:
            return None

    def __init__(self, code, p0):
        instance = Test.get_instance(code)
        if instance is None:  # then this is its first appearance; we need to initialize it
            # add the new instance to the instances dictionary:
            Test.instances[code] = self
            self.code = code
            self.p0 = p0
        else:  # then we've seen this investment before and are adding to the principal
            self = instance
            self.code = code
            self.p0 += p0

